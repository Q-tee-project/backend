from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import httpx

from ..database import get_db
from ..models.grading_result import KoreanGradingSession
from ..models.korean_generation import Assignment, AssignmentDeployment
from ..schemas.grading_result import KoreanGradingSessionResponse, GradingApprovalRequest
from ..core.auth import get_current_teacher

router = APIRouter()

async def get_student_info(student_id: int) -> dict:
    """auth-service에서 학생 정보 조회"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://auth-service:8000/api/auth/students/{student_id}")
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "student_id": student_id,
                    "name": f"학생{student_id}",
                    "school": "정보없음",
                    "grade": "정보없음"
                }
    except Exception as e:
        return {
            "student_id": student_id,
            "name": f"학생{student_id}",
            "school": "정보없음",
            "grade": "정보없음"
        }

@router.get("/grading-sessions/{session_id}")
async def get_grading_session_details(session_id: int, db: Session = Depends(get_db)):
    """채점 세션 상세 정보 조회 (선생님 편집용)"""
    try:
        grading_session = db.query(KoreanGradingSession).filter(KoreanGradingSession.id == session_id).first()
        if not grading_session:
            raise HTTPException(status_code=404, detail="Grading session not found")

        # 문제별 채점 결과 조회
        from ..models.grading_result import KoreanProblemGradingResult
        problem_results = db.query(KoreanProblemGradingResult).filter(
            KoreanProblemGradingResult.grading_session_id == session_id
        ).all()

        # 학생 정보 조회
        try:
            student_info = await get_student_info(grading_session.student_id)
            student_name = student_info.get("name", f"학생{grading_session.student_id}")
        except Exception as e:
            print(f"학생 정보 조회 실패: {e}")
            student_name = f"학생{grading_session.student_id}"

        return {
            "id": grading_session.id,
            "worksheet_id": grading_session.worksheet_id,
            "student_id": grading_session.student_id,
            "graded_by": grading_session.graded_by,
            "student_name": student_name,
            "total_problems": grading_session.total_problems or 0,
            "correct_count": grading_session.correct_count or 0,
            "total_score": grading_session.total_score or 0,
            "max_possible_score": grading_session.max_possible_score or 100,
            "input_method": grading_session.input_method or "manual",
            "status": grading_session.status or "completed",
            "graded_at": grading_session.graded_at.isoformat() if grading_session.graded_at else None,
            "teacher_id": grading_session.teacher_id,
            "approved_at": grading_session.approved_at.isoformat() if grading_session.approved_at else None,
            "problem_results": [
                {
                    "problem_id": pr.problem_id,
                    "user_answer": pr.user_answer or "",
                    "correct_answer": pr.correct_answer or "",
                    "is_correct": pr.is_correct or False,
                    "score": pr.score or 0,
                    "problem_type": pr.problem_type or "객관식",
                    "input_method": pr.input_method or "manual",
                    "explanation": pr.explanation or "",
                    "question": ""  # 문제 텍스트는 별도 조회 필요
                }
                for pr in problem_results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"채점 세션 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")




@router.put("/grading-sessions/{session_id}/update")
async def update_grading_session(
    session_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_teacher: Dict[str, Any] = Depends(get_current_teacher)
):
    """채점 결과 업데이트 (선생님 편집용)"""
    session = db.query(KoreanGradingSession).filter(KoreanGradingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Grading session not found")

    try:
        # status만 직접 업데이트, total_score와 correct_count는 문제별 결과 기반으로 재계산
        if "status" in update_data:
            session.status = update_data["status"]

        # 선생님이 수정한 경우 teacher_id와 승인 시간 업데이트
        session.teacher_id = current_teacher["id"]
        session.approved_at = datetime.now()

        # 문제별 정답/오답 수정사항 적용
        if "problem_corrections" in update_data:
            from ..models.grading_result import KoreanProblemGradingResult
            corrections = update_data["problem_corrections"]

            for problem_id_str, is_correct in corrections.items():
                problem_id = int(problem_id_str)
                problem_result = db.query(KoreanProblemGradingResult).filter(
                    KoreanProblemGradingResult.grading_session_id == session_id,
                    KoreanProblemGradingResult.problem_id == problem_id
                ).first()

                if problem_result:
                    problem_result.is_correct = is_correct
                    # 기존 points_per_problem이 있으면 사용, 없으면 session에서 가져오기
                    if problem_result.points_per_problem:
                        points_per_problem = problem_result.points_per_problem
                    else:
                        points_per_problem = session.points_per_problem
                        if points_per_problem is None:
                            total_problems = session.total_problems or 10
                            points_per_problem = 10.0 if total_problems <= 10 else 5.0
                            session.points_per_problem = points_per_problem
                        problem_result.points_per_problem = points_per_problem
                    problem_result.score = points_per_problem if is_correct else 0
                else:
                    # 문제 결과가 없으면 생성
                    # grading_session에서 points_per_problem 값 가져오기, null인 경우 기본값 설정
                    points_per_problem = session.points_per_problem
                    if points_per_problem is None:
                        # 문제 수에 따른 기본 배점 계산 (10문제면 10점, 20문제면 5점)
                        total_problems = session.total_problems or 10
                        points_per_problem = 10.0 if total_problems <= 10 else 5.0
                        # session의 points_per_problem도 업데이트
                        session.points_per_problem = points_per_problem

                    new_result = KoreanProblemGradingResult(
                        grading_session_id=session_id,
                        problem_id=problem_id,
                        is_correct=is_correct,
                        score=points_per_problem if is_correct else 0,
                        points_per_problem=points_per_problem,
                        user_answer="",
                        correct_answer="",
                        problem_type="객관식",
                        input_method="manual"
                    )
                    db.add(new_result)

        # 업데이트된 정답들 처리 (선생님이 정답처리한 경우 학생 답안을 정답으로 설정)
        if "updated_correct_answers" in update_data:
            from ..models.grading_result import KoreanProblemGradingResult
            updated_answers = update_data["updated_correct_answers"]

            for problem_id_str, new_correct_answer in updated_answers.items():
                problem_id = int(problem_id_str)
                problem_result = db.query(KoreanProblemGradingResult).filter(
                    KoreanProblemGradingResult.grading_session_id == session_id,
                    KoreanProblemGradingResult.problem_id == problem_id
                ).first()

                if problem_result:
                    problem_result.correct_answer = new_correct_answer
                    print(f"🔄 국어 문제 {problem_id}의 정답을 '{new_correct_answer}'로 업데이트")

        # 모든 문제별 결과를 기반으로 총점과 정답 수 재계산
        if "problem_corrections" in update_data:
            all_problem_results = db.query(KoreanProblemGradingResult).filter(
                KoreanProblemGradingResult.grading_session_id == session_id
            ).all()

            correct_count = sum(1 for pr in all_problem_results if pr.is_correct)
            total_score = sum(pr.score for pr in all_problem_results)

            session.correct_count = correct_count
            session.total_score = total_score

        db.commit()
        db.refresh(session)

        return {
            "id": session.id,
            "status": session.status,
            "total_score": session.total_score,
            "correct_count": session.correct_count,
            "message": "채점 결과가 성공적으로 업데이트되었습니다."
        }

    except Exception as e:
        db.rollback()
        print(f"채점 결과 업데이트 오류: {e}")
        raise HTTPException(status_code=500, detail=f"채점 결과 업데이트 실패: {str(e)}")


@router.get("/assignments/{assignment_id}/results")
async def get_assignment_results(assignment_id: int, db: Session = Depends(get_db)):
    """과제의 채점 결과를 조회 (선생님용) - 학생별 구분 포함"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # 배포된 학생들과 제출 현황 조회
    deployed_students = db.query(AssignmentDeployment).filter(
        AssignmentDeployment.assignment_id == assignment_id
    ).all()

    results = []
    for deployment in deployed_students:
        student_id = deployment.student_id

        # 학생 정보 조회 (auth-service에서)
        student_info = await get_student_info(student_id)

        # 해당 학생의 채점 결과 조회
        grading_session = db.query(KoreanGradingSession).filter(
            KoreanGradingSession.worksheet_id == assignment.worksheet_id,
            KoreanGradingSession.student_id == student_id
        ).first()

        # 상태 결정 (completed 상태 추가)
        if deployment.status == "completed" or deployment.status == "submitted":
            status_text = "완료" if grading_session else "제출완료"
            completed_at = deployment.submitted_at.isoformat() if deployment.submitted_at else None
        elif deployment.status == "assigned":
            status_text = "미시작"
            completed_at = None
        else:
            status_text = "미완료"
            completed_at = None

        student_result = {
            "student_id": student_id,
            "student_name": student_info.get("name", f"학생{student_id}"),
            "school": student_info.get("school", "정보없음"),
            "grade": student_info.get("grade", "정보없음"),
            "status": status_text,
            "score": grading_session.total_score if grading_session else 0,
            "max_possible_score": 100,  # 국어는 기본 100점
            "completed_at": completed_at,
            "grading_session_id": grading_session.id if grading_session else None,
            "total_problems": grading_session.total_problems if grading_session else assignment.problem_count,
            "correct_count": grading_session.correct_count if grading_session else 0,
            "graded_at": grading_session.graded_at.isoformat() if grading_session and grading_session.graded_at else None,
        }

        results.append(student_result)

    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "worksheet_id": assignment.worksheet_id,
        "total_students": len(results),
        "completed_count": len([r for r in results if r["status"] == "완료"]),
        "results": results
    }
