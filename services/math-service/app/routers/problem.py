from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.auth import get_current_teacher
from ..tasks import regenerate_single_problem_task

router = APIRouter()

@router.patch("/{problem_id}")
async def update_problem(
    problem_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    try:
        from ..models.problem import Problem

        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

        # Update problem fields
        if "question" in request:
            problem.question = request["question"]
        if "choices" in request:
            import json
            problem.choices = json.dumps(request["choices"], ensure_ascii=False)
        if "correct_answer" in request:
            problem.correct_answer = request["correct_answer"]
        if "explanation" in request:
            problem.explanation = request["explanation"]
        if "difficulty" in request:
            problem.difficulty = request["difficulty"]
        if "problem_type" in request:
            problem.problem_type = request["problem_type"]
        if "latex_content" in request:
            problem.latex_content = request["latex_content"]

        db.commit()
        db.refresh(problem)

        return {
            "message": "문제가 성공적으로 수정되었습니다.",
            "problem_id": problem_id,
            "updated_at": problem.updated_at.isoformat() if problem.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"문제 수정 중 오류 발생: {str(e)}"
        )

@router.post("/regenerate-async")
async def regenerate_problem_async(request: dict):
    problem_id = request.get("problem_id")
    if not problem_id:
        raise HTTPException(status_code=400, detail="problem_id가 필요합니다.")

    task = regenerate_single_problem_task.delay(
        problem_id=problem_id,
        requirements=request.get("requirements", ""),
        current_problem=request.get("current_problem", {})
    )
    return {"task_id": task.id, "status": "PENDING"}
