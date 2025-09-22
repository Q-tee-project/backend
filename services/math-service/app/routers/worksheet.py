from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..core.auth import get_current_teacher, get_current_user
from ..schemas.math_generation import MathProblemGenerationRequest
from ..schemas.problem_validation import ProblemGenerationRequestSchema, GenerationWithValidationResponseSchema
from ..services.math_generation_service import MathGenerationService
from ..services.ai_service import AIService
from ..tasks import generate_math_problems_task, grade_problems_mixed_task

router = APIRouter()
math_service = MathGenerationService()
ai_service = AIService()

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


@router.get("/worksheets")
async def get_worksheets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
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


@router.get("/worksheets/{worksheet_id}")
async def get_worksheet_detail(
    worksheet_id: int,
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
                "diagram_elements": json.loads(problem.diagram_elements) if problem.diagram_elements else None
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


@router.put("/worksheets/{worksheet_id}")
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


@router.delete("/worksheets/{worksheet_id}")
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


@router.post("/generate-with-validation")
async def generate_math_problems_with_validation(
    request: ProblemGenerationRequestSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """
    AI 검증이 포함된 수학 문제 생성

    기존 생성 방식과 달리, AI가 문제를 생성한 후 자동으로 검증을 수행합니다.
    - 수학적 정확성 검증
    - 정답 검증
    - 해설 품질 검증
    - LaTeX 문법 검증
    - 난이도 적절성 검증

    자동 승인된 문제는 바로 사용 가능하고,
    수동 검토가 필요한 문제는 교사가 최종 승인해야 합니다.
    """
    try:
        print(f"🚀 검증 포함 문제 생성 시작 - 사용자: {current_user['id']}")

        # 문제 생성 및 검증 수행
        result = ai_service.generate_math_problem(
            curriculum_data=request.curriculum_data,
            user_prompt=request.user_prompt,
            problem_count=request.problem_count,
            difficulty_ratio=request.difficulty_ratio,
            enable_validation=request.enable_validation
        )

        if "error" in result.get("summary", {}):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"문제 생성 중 오류: {result['summary']['error']}"
            )

        # 응답 데이터 구성
        response_data = {
            "problems": result["problems"],
            "validation_results": result["validation_results"],
            "summary": result["summary"],
            "generation_info": {
                "user_id": current_user["id"],
                "generated_at": datetime.utcnow().isoformat(),
                "curriculum_info": request.curriculum_data,
                "user_prompt": request.user_prompt,
                "requested_count": request.problem_count,
                "actual_count": len(result["problems"])
            }
        }

        print(f"✅ 검증 완료: {result['summary'].get('auto_approved', 0)}개 자동승인, {result['summary'].get('manual_review_needed', 0)}개 수동검토필요")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 검증 포함 문제 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"검증 포함 문제 생성 중 오류 발생: {str(e)}"
        )


@router.post("/validate-existing-problems")
async def validate_existing_problems(
    request: dict,  # {"problem_ids": [1, 2, 3]} or {"worksheet_id": 123}
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """
    기존 문제들에 대한 사후 검증

    이미 생성된 문제들을 AI로 검증합니다.
    문제 ID 리스트 또는 워크시트 ID를 제공하면 해당 문제들을 검증합니다.
    """
    try:
        from ..models.problem import Problem
        from ..models.worksheet import Worksheet

        problems_to_validate = []

        # 문제 조회
        if "problem_ids" in request:
            problem_ids = request["problem_ids"]
            problems = db.query(Problem).filter(Problem.id.in_(problem_ids)).all()
        elif "worksheet_id" in request:
            worksheet_id = request["worksheet_id"]
            # 권한 확인
            worksheet = db.query(Worksheet).filter(
                Worksheet.id == worksheet_id,
                Worksheet.teacher_id == current_user["id"]
            ).first()
            if not worksheet:
                raise HTTPException(status_code=404, detail="워크시트를 찾을 수 없습니다")

            problems = db.query(Problem).filter(Problem.worksheet_id == worksheet_id).all()
        else:
            raise HTTPException(status_code=400, detail="problem_ids 또는 worksheet_id를 제공해야 합니다")

        if not problems:
            raise HTTPException(status_code=404, detail="검증할 문제를 찾을 수 없습니다")

        # 문제 데이터를 검증 형식으로 변환
        import json
        for problem in problems:
            problem_data = {
                "id": problem.id,
                "question": problem.question,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "problem_type": problem.problem_type.value if hasattr(problem.problem_type, 'value') else str(problem.problem_type),
                "difficulty": problem.difficulty.value if hasattr(problem.difficulty, 'value') else str(problem.difficulty),
                "choices": json.loads(problem.choices) if problem.choices else None
            }
            problems_to_validate.append(problem_data)

        # 검증 수행
        validation_results = ai_service.validation_service.validate_problem_batch(problems_to_validate)

        # 검증 요약
        summary = ai_service.validation_service.get_validation_summary(validation_results)

        return {
            "message": f"{len(problems_to_validate)}개 문제 검증 완료",
            "problems": problems_to_validate,
            "validation_results": validation_results,
            "summary": summary,
            "validated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 기존 문제 검증 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기존 문제 검증 중 오류 발생: {str(e)}"
        )
