from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..core.auth import get_current_user
from ..tasks import grade_problems_mixed_task, process_assignment_ai_grading_task
from ..models.grading_result import GradingSession, ProblemGradingResult
from ..models.math_generation import Assignment

router = APIRouter()

@router.post("/worksheets/{worksheet_id}/grade")
async def grade_worksheet(
    worksheet_id: int,
    answer_sheet: UploadFile = File(..., description="답안지 이미지 파일"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from ..models.worksheet import Worksheet
    if not db.query(Worksheet).filter(Worksheet.id == worksheet_id).first():
        raise HTTPException(status_code=404, detail="워크시트를 찾을 수 없습니다.")
    
    image_data = await answer_sheet.read()
    task = grade_problems_mixed_task.delay(
        worksheet_id=worksheet_id,
        multiple_choice_answers={},
        canvas_answers={"sheet": image_data},
        user_id=current_user["id"]
    )
    return {"task_id": task.id, "status": "PENDING"}

@router.post("/worksheets/{worksheet_id}/grade-canvas")
async def grade_worksheet_canvas(
    worksheet_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from ..models.worksheet import Worksheet
    if not db.query(Worksheet).filter(Worksheet.id == worksheet_id).first():
        raise HTTPException(status_code=404, detail="워크시트를 찾을 수 없습니다.")

    task = grade_problems_mixed_task.delay(
        worksheet_id=worksheet_id,
        multiple_choice_answers=request.get("multiple_choice_answers", {}),
        canvas_answers=request.get("canvas_answers", {}),
        user_id=current_user["id"]
    )
    return {"task_id": task.id, "status": "PENDING"}

@router.get("/assignments/{assignment_id}/results")
async def get_assignment_results(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """과제의 채점 결과를 조회 (선생님용)"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 해당 과제(워크시트)의 채점 결과들을 조회
    grading_sessions = db.query(GradingSession).filter(
        GradingSession.worksheet_id == assignment.worksheet_id
    ).all()

    results = []
    for session in grading_sessions:
        # 문제별 결과도 함께 조회
        problem_results = db.query(ProblemGradingResult).filter(
            ProblemGradingResult.grading_session_id == session.id
        ).all()

        results.append({
            "grading_session_id": session.id,
            "worksheet_id": session.worksheet_id,
            "total_problems": session.total_problems,
            "correct_count": session.correct_count,
            "total_score": session.total_score,
            "max_possible_score": session.max_possible_score,
            "points_per_problem": session.points_per_problem,
            "graded_at": session.graded_at.isoformat() if session.graded_at else None,
            "graded_by": session.graded_by,
            "problem_results": [
                {
                    "problem_id": pr.problem_id,
                    "user_answer": pr.user_answer,
                    "correct_answer": pr.correct_answer,
                    "is_correct": pr.is_correct,
                    "score": pr.score,
                    "problem_type": pr.problem_type,
                    "difficulty": pr.difficulty,
                    "input_method": pr.input_method,
                    "explanation": pr.explanation
                }
                for pr in problem_results
            ]
        })

    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "worksheet_id": assignment.worksheet_id,
        "results": results
    }

@router.post("/assignments/{assignment_id}/start-ai-grading")
async def start_ai_grading(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """과제의 손글씨 답안에 대해 OCR + AI 채점을 비동기로 시작"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 해당 과제의 모든 제출된 세션들을 찾기
    from ..models.math_generation import TestSession
    submitted_sessions = db.query(TestSession).filter(
        TestSession.assignment_id == assignment_id,
        TestSession.status == 'submitted'
    ).all()

    if not submitted_sessions:
        return {"message": "제출된 세션이 없습니다.", "task_id": None}

    # Celery 태스크로 비동기 처리 시작
    task = process_assignment_ai_grading_task.delay(
        assignment_id=assignment_id,
        user_id=current_user["id"]
    )

    return {
        "message": "OCR + AI 채점이 시작되었습니다.",
        "task_id": task.id,
        "status": "PENDING",
        "assignment_id": assignment_id
    }

@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Celery 태스크 상태 조회"""
    from celery.result import AsyncResult
    from ..celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
        "info": result.info,
        "ready": result.ready()
    }
