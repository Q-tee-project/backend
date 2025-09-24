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

@router.get(
    "/grading-sessions/pending",
    response_model=List[KoreanGradingSessionResponse],
    summary="Get all grading sessions pending teacher approval",
    description="Retrieves a list of all Korean grading sessions that are awaiting teacher approval."
)
async def get_pending_grading_sessions(db: Session = Depends(get_db)):
    pending_sessions = db.query(KoreanGradingSession).filter(KoreanGradingSession.status == "pending_approval").all()
    return pending_sessions


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


@router.post(
    "/grading-sessions/{session_id}/approve",
    response_model=KoreanGradingSessionResponse,
    summary="Approve a grading session",
    description="Approves a Korean grading session, setting its status to 'approved' and recording the teacher's ID and approval timestamp."
)
async def approve_grading_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_teacher: Dict[str, Any] = Depends(get_current_teacher)
):
    session = db.query(KoreanGradingSession).filter(KoreanGradingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading session not found")

    if session.status != "pending_approval":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grading session is not pending approval")

    session.status = "approved"
    session.teacher_id = current_teacher["id"]
    session.approved_at = datetime.now()
    db.commit()
    db.refresh(session)
    return session


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

        # 상태 결정 (수학과 동일한 방식)
        if deployment.status == "submitted":
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
