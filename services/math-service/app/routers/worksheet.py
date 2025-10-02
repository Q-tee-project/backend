from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..core.auth import get_current_teacher, get_current_user
from ..schemas.math_generation import MathProblemGenerationRequest
from ..services.math_generation_service import MathGenerationService
from ..tasks import generate_math_problems_task, grade_problems_mixed_task

router = APIRouter()
math_service = MathGenerationService()

@router.post("/generate")
async def generate_math_problems(
    request: MathProblemGenerationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    try:
        task = generate_math_problems_task.delay(
            request.model_dump(),
            current_user["id"]
        )
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "문제 생성이 시작되었습니다. /tasks/{task_id} 엔드포인트로 진행 상황을 확인하세요."
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"문제 생성 요청 중 오류 발생: {str(e)}")

@router.get("/generation/history")
async def get_generation_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    try:
        history = math_service.get_generation_history(db, user_id=current_user["id"], skip=skip, limit=limit)
        result = []
        for session in history:
            result.append({
                "generation_id": session.generation_id,
                "school_level": session.school_level,
                "grade": session.grade,
                "semester": session.semester,
                "chapter_name": session.chapter_name,
                "problem_count": session.problem_count,
                "total_generated": session.total_generated,
                "created_at": session.created_at.isoformat()
            })
        return {"history": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"생성 이력 조회 중 오류: {str(e)}")

@router.get("/generation/{generation_id}")
async def get_generation_detail(
    generation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    try:
        session = math_service.get_generation_detail(db, generation_id, user_id=current_user["id"])
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 생성 세션을 찾을 수 없습니다")
        
        from ..models.problem import Problem
        from ..models.worksheet import Worksheet
        worksheet = db.query(Worksheet).filter(Worksheet.generation_id == generation_id).first()
        if not worksheet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 생성 세션의 워크시트를 찾을 수 없습니다")
        
        problems = db.query(Problem).filter(Problem.worksheet_id == worksheet.id).order_by(Problem.sequence_order).all()
        
        import json
        problem_list = [
            {
                "id": p.id, "problem_type": p.problem_type.value, "difficulty": p.difficulty.value,
                "question": p.question, "choices": json.loads(p.choices) if p.choices else None,
                "correct_answer": p.correct_answer, "explanation": p.explanation, "latex_content": p.latex_content
            } for p in problems
        ]
        
        return {
            "generation_info": session,
            "problems": problem_list
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"세션 상세 조회 중 오류: {str(e)}")


@router.get("/")
async def get_worksheets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    try:
        from ..models.worksheet import Worksheet

        worksheets = db.query(Worksheet)\
            .filter(Worksheet.teacher_id == current_user["id"])\
            .order_by(Worksheet.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

        result = []
        for worksheet in worksheets:
            result.append({
                "id": worksheet.id,
                "title": worksheet.title,
                "school_level": worksheet.school_level,
                "grade": worksheet.grade,
                "semester": worksheet.semester,
                "unit_name": worksheet.unit_name,
                "chapter_name": worksheet.chapter_name,
                "problem_count": worksheet.problem_count,
                "difficulty_ratio": worksheet.difficulty_ratio,
                "problem_type_ratio": worksheet.problem_type_ratio,
                "user_prompt": worksheet.user_prompt,
                "actual_difficulty_distribution": worksheet.actual_difficulty_distribution,
                "actual_type_distribution": worksheet.actual_type_distribution,
                "status": worksheet.status.value,
                "created_at": worksheet.created_at.isoformat()
            })

        return {"worksheets": result, "total": len(result)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"워크시트 목록 조회 중 오류: {str(e)}"
        )


@router.get("/{worksheet_id}")
async def get_worksheet_detail(
    worksheet_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    try:
        from ..models.worksheet import Worksheet
        from ..models.problem import Problem

        # 구매한 워크시트도 조회할 수 있도록 소유자 확인 완화
        worksheet = db.query(Worksheet)\
            .filter(Worksheet.id == worksheet_id)\
            .first()

        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다."
            )

        # 워크시트 소유자가 아닌 경우 추가 검증 (구매 여부 확인 등)
        if worksheet.teacher_id != current_user["id"]:
            # TODO: 구매 여부 확인 로직 추가
            print(f"[DEBUG] 다른 사용자의 워크시트 접근 시도: worksheet_id={worksheet_id}, owner={worksheet.teacher_id}, accessor={current_user['id']}")
            # 임시로 접근 허용
            pass

        problems = db.query(Problem)\
            .filter(Problem.worksheet_id == worksheet_id)\
            .order_by(Problem.sequence_order)\
            .all()

        problem_list = []
        for problem in problems:
            import json
            problem_dict = {
                "id": problem.id,
                "sequence_order": problem.sequence_order,
                "problem_type": problem.problem_type,
                "difficulty": problem.difficulty,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else None,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "latex_content": problem.latex_content,
                "has_diagram": problem.has_diagram == "true",
                "diagram_type": problem.diagram_type,
                "diagram_elements": json.loads(problem.diagram_elements) if problem.diagram_elements else None,
                "tikz_code": problem.tikz_code
            }
            problem_list.append(problem_dict)

        return {
            "worksheet": {
                "id": worksheet.id,
                "title": worksheet.title,
                "school_level": worksheet.school_level,
                "grade": worksheet.grade,
                "semester": worksheet.semester,
                "unit_name": worksheet.unit_name,
                "chapter_name": worksheet.chapter_name,
                "problem_count": worksheet.problem_count,
                "difficulty_ratio": worksheet.difficulty_ratio,
                "problem_type_ratio": worksheet.problem_type_ratio,
                "user_prompt": worksheet.user_prompt,
                "generation_id": worksheet.generation_id,
                "actual_difficulty_distribution": worksheet.actual_difficulty_distribution,
                "actual_type_distribution": worksheet.actual_type_distribution,
                "status": worksheet.status.value,
                "created_at": worksheet.created_at.isoformat()
            },
            "problems": problem_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"워크시트 상세 조회 중 오류: {str(e)}"
        )


@router.patch("/{worksheet_id}")
async def update_worksheet(
    worksheet_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    try:
        from ..models.worksheet import Worksheet
        from ..models.problem import Problem

        worksheet = db.query(Worksheet)\
            .filter(Worksheet.id == worksheet_id, Worksheet.teacher_id == current_user["id"])\
            .first()

        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다."
            )

        if "title" in request:
            worksheet.title = request["title"]
        if "user_prompt" in request:
            worksheet.user_prompt = request["user_prompt"]
        if "difficulty_ratio" in request:
            worksheet.difficulty_ratio = request["difficulty_ratio"]
        if "problem_type_ratio" in request:
            worksheet.problem_type_ratio = request["problem_type_ratio"]

        if "problems" in request:
            for problem_data in request["problems"]:
                problem_id = problem_data.get("id")
                if problem_id:
                    problem = db.query(Problem)\
                        .filter(Problem.id == problem_id, Problem.worksheet_id == worksheet_id)\
                        .first()

                    if problem:
                        if "question" in problem_data:
                            problem.question = problem_data["question"]
                        if "choices" in problem_data:
                            import json
                            problem.choices = json.dumps(problem_data["choices"], ensure_ascii=False)
                        if "correct_answer" in problem_data:
                            problem.correct_answer = problem_data["correct_answer"]
                        if "explanation" in problem_data:
                            problem.explanation = problem_data["explanation"]
                        if "difficulty" in problem_data:
                            problem.difficulty = problem_data["difficulty"]
                        if "problem_type" in problem_data:
                            problem.problem_type = problem_data["problem_type"]
                        if "latex_content" in problem_data:
                            problem.latex_content = problem_data["latex_content"]

        db.commit()
        db.refresh(worksheet)

        return {
            "message": "워크시트가 성공적으로 수정되었습니다.",
            "worksheet_id": worksheet_id,
            "updated_at": worksheet.updated_at.isoformat() if worksheet.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"워크시트 수정 중 오류 발생: {str(e)}"
        )


@router.delete("/{worksheet_id}")
async def delete_worksheet(
    worksheet_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    try:
        from ..models.worksheet import Worksheet
        from ..models.problem import Problem
        from ..models.grading_result import GradingSession, ProblemGradingResult
        from ..models.math_generation import Assignment, AssignmentDeployment

        worksheet = db.query(Worksheet)\
            .filter(Worksheet.id == worksheet_id, Worksheet.teacher_id == current_user["id"])\
            .first()

        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다."
            )

        # 1. 채점 세션 및 결과 삭제
        grading_sessions = db.query(GradingSession)\
            .filter(GradingSession.worksheet_id == worksheet_id)\
            .all()
        for session in grading_sessions:
            db.query(ProblemGradingResult)\
                .filter(ProblemGradingResult.grading_session_id == session.id)\
                .delete(synchronize_session=False)
            db.delete(session)
        
        # 2. 과제 및 배포 기록 삭제
        assignments = db.query(Assignment).filter(Assignment.worksheet_id == worksheet_id).all()
        for assignment in assignments:
            db.query(AssignmentDeployment)\
                .filter(AssignmentDeployment.assignment_id == assignment.id)\
                .delete(synchronize_session=False)
            db.delete(assignment)

        # 3. 문제 삭제
        db.query(Problem)\
            .filter(Problem.worksheet_id == worksheet_id)\
            .delete(synchronize_session=False)

        # 4. 워크시트 삭제
        db.delete(worksheet)
        
        db.commit()

        return {
            "message": "워크시트가 성공적으로 삭제되었습니다.",
            "worksheet_id": worksheet_id,
            "deleted_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"워크시트 삭제 중 오류 발생: {str(e)}"
        )


@router.post("/copy", status_code=status.HTTP_201_CREATED)
async def copy_worksheet_endpoint(
    request: dict,
    db: Session = Depends(get_db)
):
    """워크시트 복사 엔드포인트"""
    source_worksheet_id = request.get("source_worksheet_id")
    target_user_id = request.get("target_user_id")
    new_title = request.get("new_title")

    if not all([source_worksheet_id, target_user_id, new_title]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_worksheet_id, target_user_id, new_title are required."
        )

    new_worksheet_id = MathGenerationService.copy_worksheet(
        db,
        source_worksheet_id=source_worksheet_id,
        target_user_id=target_user_id,
        new_title=new_title
    )

    if not new_worksheet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source worksheet not found."
        )

    return {"new_worksheet_id": new_worksheet_id}
