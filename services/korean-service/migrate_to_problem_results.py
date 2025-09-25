#!/usr/bin/env python3
"""
국어 서비스 데이터 마이그레이션 스크립트
multiple_choice_answers -> problem_results 구조로 변환
"""

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import get_db, engine
from app.models.grading_result import KoreanGradingSession, KoreanProblemGradingResult
import json


def migrate_multiple_choice_to_problem_results():
    """multiple_choice_answers를 problem_results로 마이그레이션"""

    # 데이터베이스 세션 생성
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("🚀 국어 서비스 데이터 마이그레이션 시작...")

        # multiple_choice_answers가 있는 모든 세션 조회
        sessions_with_answers = db.query(KoreanGradingSession).filter(
            KoreanGradingSession.multiple_choice_answers.isnot(None)
        ).all()

        print(f"📊 마이그레이션 대상 세션: {len(sessions_with_answers)}개")

        migrated_count = 0

        for session in sessions_with_answers:
            print(f"\n🔄 세션 {session.id} 마이그레이션 중...")

            # 이미 problem_results가 있는지 확인
            existing_results = db.query(KoreanProblemGradingResult).filter(
                KoreanProblemGradingResult.grading_session_id == session.id
            ).count()

            if existing_results > 0:
                print(f"  ⚠️  이미 problem_results가 존재함 (count: {existing_results}), 건너뛰기")
                continue

            # multiple_choice_answers 파싱
            try:
                if isinstance(session.multiple_choice_answers, str):
                    answers = json.loads(session.multiple_choice_answers)
                else:
                    answers = session.multiple_choice_answers or {}

                if not answers:
                    print(f"  ⚠️  multiple_choice_answers가 비어있음, 건너뛰기")
                    continue

            except (json.JSONDecodeError, TypeError) as e:
                print(f"  ❌ multiple_choice_answers 파싱 실패: {e}")
                continue

            # 문제별로 problem_results 생성
            points_per_problem = session.points_per_problem or (
                10.0 if session.total_problems <= 10 else 5.0
            )

            created_results = 0

            for problem_id_str, user_answer in answers.items():
                try:
                    problem_id = int(problem_id_str)

                    # 실제 문제 정보 조회하여 정답 가져오기
                    problem_query = text("""
                        SELECT correct_answer
                        FROM korean_service.problems
                        WHERE id = :problem_id
                    """)

                    result = db.execute(problem_query, {"problem_id": problem_id})
                    problem_data = result.fetchone()
                    correct_answer = problem_data.correct_answer if problem_data else "1"

                    # 정답 여부 확인
                    is_correct = str(user_answer) == str(correct_answer)
                    score = points_per_problem if is_correct else 0.0

                    # KoreanProblemGradingResult 생성
                    problem_result = KoreanProblemGradingResult(
                        grading_session_id=session.id,
                        problem_id=problem_id,
                        user_answer=str(user_answer),
                        actual_user_answer=str(user_answer),
                        correct_answer=str(correct_answer),
                        is_correct=is_correct,
                        score=score,
                        points_per_problem=points_per_problem,
                        problem_type="객관식",
                        input_method="manual"
                    )

                    db.add(problem_result)
                    created_results += 1

                    print(f"    ✅ 문제 {problem_id}: {user_answer} -> {'정답' if is_correct else '오답'} ({score}점)")

                except (ValueError, TypeError) as e:
                    print(f"    ❌ 문제 {problem_id_str} 처리 실패: {e}")
                    continue

            if created_results > 0:
                # 총점과 정답 수 재계산
                total_score = sum(pr.score for pr in db.query(KoreanProblemGradingResult).filter(
                    KoreanProblemGradingResult.grading_session_id == session.id
                ).all())

                correct_count = db.query(KoreanProblemGradingResult).filter(
                    KoreanProblemGradingResult.grading_session_id == session.id,
                    KoreanProblemGradingResult.is_correct == True
                ).count()

                # 세션 업데이트
                session.total_score = total_score
                session.correct_count = correct_count

                print(f"  ✅ 세션 {session.id} 완료: {created_results}개 결과 생성, 총점 {total_score}, 정답 {correct_count}개")
                migrated_count += 1
            else:
                print(f"  ⚠️  세션 {session.id}: 생성된 결과 없음")

        # 변경사항 커밋
        db.commit()
        print(f"\n🎉 마이그레이션 완료! 총 {migrated_count}개 세션 처리")

        # 마이그레이션 결과 확인
        total_problem_results = db.query(KoreanProblemGradingResult).count()
        print(f"📊 현재 총 KoreanProblemGradingResult 개수: {total_problem_results}")

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_migration():
    """마이그레이션 결과 검증"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("\n🔍 마이그레이션 결과 검증...")

        # multiple_choice_answers가 있지만 problem_results가 없는 세션
        sessions_query = text("""
            SELECT
                gs.id,
                gs.multiple_choice_answers,
                COUNT(pgr.id) as problem_results_count
            FROM korean_service.grading_sessions gs
            LEFT JOIN korean_service.problem_grading_results pgr ON gs.id = pgr.grading_session_id
            WHERE gs.multiple_choice_answers IS NOT NULL
            GROUP BY gs.id, gs.multiple_choice_answers
            HAVING COUNT(pgr.id) = 0
        """)

        unmigrated = db.execute(sessions_query).fetchall()

        if unmigrated:
            print(f"⚠️  아직 마이그레이션되지 않은 세션: {len(unmigrated)}개")
            for row in unmigrated[:5]:  # 처음 5개만 표시
                print(f"    세션 ID: {row.id}")
        else:
            print("✅ 모든 세션이 성공적으로 마이그레이션됨!")

    finally:
        db.close()


if __name__ == "__main__":
    print("국어 서비스 multiple_choice_answers -> problem_results 마이그레이션")
    print("=" * 70)

    # 확인 메시지
    confirm = input("⚠️  이 작업은 데이터베이스를 수정합니다. 계속하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("마이그레이션을 취소했습니다.")
        sys.exit(0)

    # 마이그레이션 실행
    migrate_multiple_choice_to_problem_results()

    # 결과 검증
    verify_migration()

    print("\n🎯 다음 단계:")
    print("1. 백엔드 코드에서 multiple_choice_answers 관련 로직 제거")
    print("2. 프론트엔드에서 multiple_choice_answers 관련 로직 제거")
    print("3. KoreanGradingSession 모델에서 multiple_choice_answers 필드 제거 (나중에)")