"""
데이터베이스 저장 관련 헬퍼 함수들
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.worksheet import Worksheet, Passage, Question


def assemble_worksheet(passages: List[Dict[str, Any]], questions: List[Dict[str, Any]], request_data: Dict[str, Any]) -> str:
    """워크시트 최종 조립"""

    print(f"🔧 워크시트 조립 시작...")

    school_level = request_data.get('school_level', '중학교')
    grade = request_data.get('grade', 1)
    total_questions = len(questions)

    # 영역 분포 계산
    subjects = set(q['question_subject'] for q in questions)
    if len(subjects) == 1:
        problem_type = list(subjects)[0]
    else:
        problem_type = '혼합형'

    # related_questions 업데이트
    for passage in passages:
        passage['related_questions'] = [
            q['question_id'] for q in questions
            if q.get('question_passage_id') == passage['passage_id']
        ]

    worksheet = {
        "worksheet_id": 1,
        "worksheet_name": "",
        "worksheet_date": datetime.now().strftime("%Y-%m-%d"),
        "worksheet_time": datetime.now().strftime("%H:%M"),
        "worksheet_duration": "60",
        "worksheet_subject": "english",
        "worksheet_level": school_level,
        "worksheet_grade": grade,
        "problem_type": problem_type,
        "total_questions": total_questions,
        "passages": passages,
        "questions": questions
    }

    print(f"✅ 워크시트 조립 완료! (총 {total_questions}문제, {len(passages)}지문)")

    return json.dumps(worksheet, ensure_ascii=False)


def save_worksheet_to_db(
    db: Session,
    passages: List[Dict[str, Any]],
    questions: List[Dict[str, Any]],
    request_data: Dict[str, Any],
    parsed_llm_response: Dict[str, Any]
) -> Optional[int]:
    """워크시트를 DB에 저장하고 worksheet_id를 반환"""

    teacher_id = request_data.get('teacher_id')

    if not teacher_id:
        print("⚠️ teacher_id가 없어 DB 저장을 건너뜁니다.")
        return None

    try:
        print(f"💾 DB 자동 저장 시작 (teacher_id: {teacher_id})...")

        # 문제지 제목 생성 (없으면 자동 생성)
        worksheet_name = request_data.get('worksheet_name')
        if not worksheet_name:
            school_level = request_data.get('school_level', '중학교')
            grade = request_data.get('grade', 1)
            worksheet_name = f"{school_level} {grade}학년 영어 문제지"

        # 1. Worksheet 저장
        db_worksheet = Worksheet(
            teacher_id=teacher_id,
            worksheet_name=worksheet_name,
            school_level=request_data.get('school_level', '중학교'),
            grade=str(request_data.get('grade', 1)),
            subject="영어",
            problem_type=parsed_llm_response.get('problem_type', '혼합형'),
            total_questions=request_data.get('total_questions', len(questions)),
            duration=request_data.get('duration', 60),
            created_at=datetime.now()
        )
        db.add(db_worksheet)
        db.flush()
        worksheet_id = db_worksheet.worksheet_id

        print(f"  ✅ Worksheet 저장 완료 (ID: {worksheet_id})")

        # 2. Passages 저장
        for passage_data in passages:
            db_passage = Passage(
                worksheet_id=worksheet_id,
                passage_id=passage_data['passage_id'],
                passage_type=passage_data['passage_type'],
                passage_content=passage_data['passage_content'],
                original_content=passage_data.get('original_content'),
                korean_translation=passage_data.get('korean_translation'),
                related_questions=passage_data.get('related_questions', []),
                created_at=datetime.now()
            )
            db.add(db_passage)

        print(f"  ✅ Passages 저장 완료 ({len(passages)}개)")

        # 3. Questions 저장
        for question_data in questions:
            db_question = Question(
                worksheet_id=worksheet_id,
                question_id=question_data['question_id'],
                question_text=question_data['question_text'],
                question_type=question_data['question_type'],
                question_subject=question_data['question_subject'],
                question_difficulty=question_data['question_difficulty'],
                question_detail_type=question_data.get('question_detail_type'),
                question_choices=question_data.get('question_choices'),
                passage_id=question_data.get('question_passage_id'),
                correct_answer=str(question_data.get('correct_answer')) if question_data.get('correct_answer') else None,
                example_content=question_data.get('example_content') or '',
                example_original_content=question_data.get('example_original_content'),
                example_korean_translation=question_data.get('example_korean_translation'),
                explanation=question_data.get('explanation'),
                learning_point=question_data.get('learning_point'),
                created_at=datetime.now()
            )
            db.add(db_question)

        print(f"  ✅ Questions 저장 완료 ({len(questions)}개)")

        # 커밋
        db.commit()
        print(f"✅ DB 자동 저장 완료! worksheet_id: {worksheet_id}")

        return worksheet_id

    except Exception as save_error:
        db.rollback()
        print(f"⚠️ DB 자동 저장 실패: {save_error}")
        import traceback
        traceback.print_exc()
        return None
