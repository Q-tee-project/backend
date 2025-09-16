from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator, List
from celery.result import AsyncResult
from datetime import datetime
import asyncio
import json

from ..database import get_db
from ..schemas.math_generation import (
    MathProblemGenerationRequest, 
    SchoolLevel,
    AssignmentCreate,
    AssignmentResponse,
    AssignmentDeployRequest,
    AssignmentDeploymentResponse,
    StudentAssignmentResponse
)
from ..services.math_generation_service import MathGenerationService
from ..models.math_generation import Assignment, AssignmentDeployment
from ..tasks import generate_math_problems_task, grade_problems_task, grade_problems_mixed_task
from ..celery_app import celery_app

router = APIRouter()
math_service = MathGenerationService()


@router.get("/curriculum/structure")
async def get_curriculum_structure(
    school_level: Optional[SchoolLevel] = Query(None, description="학교급 필터"),
    db: Session = Depends(get_db)
):
    try:
        structure = math_service.get_curriculum_structure(
            db, 
            school_level.value if school_level else None
        )
        return {"structure": structure}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"교육과정 구조 조회 중 오류: {str(e)}"
        )


@router.get("/curriculum/units")
async def get_units():
    try:
        units = math_service.get_units()
        return {"units": units}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대단원 목록 조회 중 오류: {str(e)}"
        )


@router.get("/curriculum/chapters")
async def get_chapters_by_unit(unit_name: str = Query(..., description="대단원명")):
    try:
        chapters = math_service.get_chapters_by_unit(unit_name)
        return {"chapters": chapters}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"소단원 목록 조회 중 오류: {str(e)}"
        )


@router.post("/generate")
async def generate_math_problems(
    request: MathProblemGenerationRequest,
    db: Session = Depends(get_db)
):
    try:
        task = generate_math_problems_task.delay(
            request_data=request.model_dump(),
            user_id=1
        )
        
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "문제 생성이 시작되었습니다. /tasks/{task_id} 엔드포인트로 진행 상황을 확인하세요."
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문제 생성 요청 중 오류 발생: {str(e)}"
        )


@router.get("/generation/history")
async def get_generation_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        history = math_service.get_generation_history(db, user_id=1, skip=skip, limit=limit)
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"생성 이력 조회 중 오류: {str(e)}"
        )


@router.get("/generation/{generation_id}")
async def get_generation_detail(
    generation_id: str,
    db: Session = Depends(get_db)
):
    try:
        session = math_service.get_generation_detail(db, generation_id, user_id=1)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 생성 세션을 찾을 수 없습니다"
            )
        
        from ..models.problem import Problem
        from ..models.worksheet import Worksheet
        worksheet = db.query(Worksheet)\
            .filter(Worksheet.generation_id == generation_id)\
            .first()
            
        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 생성 세션의 워크시트를 찾을 수 없습니다"
            )
        
        problems = db.query(Problem)\
            .filter(Problem.worksheet_id == worksheet.id)\
            .order_by(Problem.sequence_order)\
            .all()
        
        problem_list = []
        for problem in problems:
            import json
            problem_dict = {
                "id": problem.id,
                "problem_type": problem.problem_type.value,
                "difficulty": problem.difficulty.value,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else None,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "latex_content": problem.latex_content
            }
            problem_list.append(problem_dict)
        
        return {
            "generation_info": {
                "generation_id": session.generation_id,
                "school_level": session.school_level,
                "grade": session.grade,
                "semester": session.semester,
                "unit_name": session.unit_name,
                "chapter_name": session.chapter_name,
                "problem_count": session.problem_count,
                "difficulty_ratio": session.difficulty_ratio,
                "problem_type_ratio": session.problem_type_ratio,
                "user_text": session.user_text,
                "actual_difficulty_distribution": session.actual_difficulty_distribution,
                "actual_type_distribution": session.actual_type_distribution,
                "total_generated": session.total_generated,
                "created_at": session.created_at.isoformat()
            },
            "problems": problem_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 상세 조회 중 오류: {str(e)}"
        )


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        if result.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": "PENDING",
                "message": "태스크가 대기 중입니다."
            }
        elif result.state == 'PROGRESS':
            return {
                "task_id": task_id,
                "status": "PROGRESS",
                "current": result.info.get('current', 0),
                "total": result.info.get('total', 100),
                "message": result.info.get('status', '처리 중...')
            }
        elif result.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": result.result
            }
        elif result.state == 'FAILURE':
            return {
                "task_id": task_id,
                "status": "FAILURE",
                "error": str(result.info) if result.info else "알 수 없는 오류가 발생했습니다."
            }
        else:
            return {
                "task_id": task_id,
                "status": result.state,
                "info": result.info
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"태스크 상태 조회 중 오류: {str(e)}"
        )


@router.get("/tasks/{task_id}/stream")
async def stream_task_status(task_id: str):
    """SSE를 통한 실시간 태스크 상태 스트리밍"""
    
    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            result = AsyncResult(task_id, app=celery_app)
            
            while True:
                # 태스크 상태 확인
                if result.state == 'PENDING':
                    data = {
                        "task_id": task_id,
                        "status": "PENDING",
                        "message": "태스크가 대기 중입니다."
                    }
                elif result.state == 'PROGRESS':
                    data = {
                        "task_id": task_id,
                        "status": "PROGRESS",
                        "current": result.info.get('current', 0),
                        "total": result.info.get('total', 100),
                        "message": result.info.get('status', '처리 중...')
                    }
                elif result.state == 'SUCCESS':
                    data = {
                        "task_id": task_id,
                        "status": "SUCCESS",
                        "result": result.result
                    }
                    # 성공 시 스트림 종료
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    break
                elif result.state == 'FAILURE':
                    data = {
                        "task_id": task_id,
                        "status": "FAILURE",
                        "error": str(result.info) if result.info else "알 수 없는 오류가 발생했습니다."
                    }
                    # 실패 시 스트림 종료
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    break
                else:
                    data = {
                        "task_id": task_id,
                        "status": result.state,
                        "info": result.info
                    }
                
                # SSE 형식으로 데이터 전송
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                # 태스크가 완료되었으면 종료
                if result.state in ['SUCCESS', 'FAILURE']:
                    break
                
                # 1초 대기
                await asyncio.sleep(1)
                
        except Exception as e:
            error_data = {
                "task_id": task_id,
                "status": "ERROR",
                "error": f"스트리밍 중 오류: {str(e)}"
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/worksheets")
async def get_worksheets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Query(..., description="로그인한 사용자 ID"),
    db: Session = Depends(get_db)
):
    try:
        from ..models.worksheet import Worksheet
        
        worksheets = db.query(Worksheet)\
            .filter(Worksheet.teacher_id == user_id)\
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
    user_id: int = Query(..., description="로그인한 사용자 ID"),
    db: Session = Depends(get_db)
):
    try:
        from ..models.worksheet import Worksheet
        from ..models.problem import Problem
        
        worksheet = db.query(Worksheet)\
            .filter(Worksheet.id == worksheet_id, Worksheet.teacher_id == user_id)\
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


@router.post("/worksheets/{worksheet_id}/grade")
async def grade_worksheet(
    worksheet_id: int,
    answer_sheet: UploadFile = File(..., description="답안지 이미지 파일"),
    db: Session = Depends(get_db)
):
    try:
        from ..models.worksheet import Worksheet
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다."
            )
        
        if not answer_sheet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="답안지 이미지가 필요합니다."
            )
        
        allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        if not any(answer_sheet.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="지원되는 이미지 형식: JPG, PNG, BMP, TIFF"
            )
        
        image_data = await answer_sheet.read()
        
        task = grade_problems_task.delay(
            worksheet_id=worksheet_id,
            image_data=image_data,
            user_id=1
        )
        
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "답안지 OCR 처리 및 채점이 시작되었습니다. /tasks/{task_id} 엔드포인트로 진행 상황을 확인하세요.",
            "uploaded_file": answer_sheet.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채점 요청 중 오류 발생: {str(e)}"
        )


@router.post("/worksheets/{worksheet_id}/grade-canvas")
async def grade_worksheet_canvas(
    worksheet_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    try:
        print(f"🔍 채점 요청 시작: worksheet_id={worksheet_id}")
        
        from ..models.worksheet import Worksheet
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
        if not worksheet:
            print(f"❌ 워크시트 {worksheet_id}를 찾을 수 없음")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다."
            )
        
        print(f"✅ 워크시트 발견: {worksheet.title}")
        
        multiple_choice_answers = request.get("multiple_choice_answers", {})
        canvas_answers = request.get("canvas_answers", {})
        
        print(f"🔍 요청 데이터: MC답안={len(multiple_choice_answers)}, 캔버스답안={len(canvas_answers)}")
        
        task = grade_problems_mixed_task.delay(
            worksheet_id=worksheet_id,
            multiple_choice_answers=multiple_choice_answers,
            canvas_answers=canvas_answers,
            user_id=1
        )
        
        print(f"✅ Celery 태스크 시작: {task.id}")
        
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "캔버스 채점이 시작되었습니다. 객관식은 라디오 버튼으로, 주관식은 캔버스 그림으로 처리됩니다.",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 채점 요청 오류: {str(e)}")
        print(f"❌ 오류 타입: {type(e).__name__}")
        import traceback
        print(f"❌ 스택 트레이스: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캔버스 채점 요청 중 오류 발생: {str(e)}"
        )


@router.post("/worksheets/{worksheet_id}/grade-mixed")
async def grade_worksheet_mixed(
    worksheet_id: int,
    multiple_choice_answers: dict = {},
    handwritten_answer_sheet: Optional[UploadFile] = File(None, description="손글씨 답안지 이미지 (서술형/단답형)"),
    db: Session = Depends(get_db)
):
    try:
        from ..models.worksheet import Worksheet
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다."
            )
        
        handwritten_image_data = None
        if handwritten_answer_sheet and handwritten_answer_sheet.filename:
            allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
            if not any(handwritten_answer_sheet.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="지원되는 이미지 형식: JPG, PNG, BMP, TIFF"
                )
            handwritten_image_data = await handwritten_answer_sheet.read()
        
        task = grade_problems_mixed_task.delay(
            worksheet_id=worksheet_id,
            multiple_choice_answers=multiple_choice_answers,
            handwritten_image_data=handwritten_image_data,
            user_id=1
        )
        
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "혼합형 채점이 시작되었습니다. 객관식은 체크박스로, 서술형/단답형은 OCR로 처리됩니다.",
            "multiple_choice_count": len(multiple_choice_answers),
            "has_handwritten_answers": handwritten_image_data is not None,
            "handwritten_file": handwritten_answer_sheet.filename if handwritten_answer_sheet else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"혼합형 채점 요청 중 오류 발생: {str(e)}"
        )


@router.put("/worksheets/{worksheet_id}")
async def update_worksheet(
    worksheet_id: int,
    request: dict,
    user_id: int = Query(..., description="로그인한 사용자 ID"),
    db: Session = Depends(get_db)
):
    try:
        from ..models.worksheet import Worksheet
        from ..models.problem import Problem
        
        worksheet = db.query(Worksheet)\
            .filter(Worksheet.id == worksheet_id, Worksheet.teacher_id == user_id)\
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


@router.put("/problems/{problem_id}")
async def update_problem(
    problem_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    try:
        from ..models.problem import Problem
        
        problem = db.query(Problem)\
            .join(Problem.worksheet)\
            .filter(Problem.id == problem_id)\
            .first()
        
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문제를 찾을 수 없습니다."
            )
        
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문제 수정 중 오류 발생: {str(e)}"
        )


@router.get("/grading-history")
async def get_grading_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    worksheet_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """채점 이력 조회"""
    try:
        from ..models.grading_result import GradingSession
        
        query = db.query(GradingSession).filter(GradingSession.graded_by == 1)
        
        if worksheet_id:
            query = query.filter(GradingSession.worksheet_id == worksheet_id)
        
        grading_sessions = query.order_by(GradingSession.graded_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        result = []
        for session in grading_sessions:
            result.append({
                "grading_session_id": session.id,
                "worksheet_id": session.worksheet_id,
                "total_problems": session.total_problems,
                "correct_count": session.correct_count,
                "total_score": session.total_score,
                "max_possible_score": session.max_possible_score,
                "points_per_problem": session.points_per_problem,
                "input_method": session.input_method,
                "graded_at": session.graded_at.isoformat(),
                "celery_task_id": session.celery_task_id
            })
        
        return {"grading_history": result, "total": len(result)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채점 이력 조회 중 오류: {str(e)}"
        )


@router.get("/grading-history/{grading_session_id}")
async def get_grading_session_detail(
    grading_session_id: int,
    db: Session = Depends(get_db)
):
    """채점 세션 상세 조회"""
    try:
        from ..models.grading_result import GradingSession, ProblemGradingResult
        
        session = db.query(GradingSession)\
            .filter(GradingSession.id == grading_session_id, GradingSession.graded_by == 1)\
            .first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채점 세션을 찾을 수 없습니다"
            )
        
        problem_results = db.query(ProblemGradingResult)\
            .filter(ProblemGradingResult.grading_session_id == grading_session_id)\
            .all()
        
        problem_list = []
        for result in problem_results:
            problem_dict = {
                "problem_id": result.problem_id,
                "user_answer": result.user_answer,
                "actual_user_answer": result.actual_user_answer,
                "correct_answer": result.correct_answer,
                "is_correct": result.is_correct,
                "score": result.score,
                "points_per_problem": result.points_per_problem,
                "problem_type": result.problem_type,
                "input_method": result.input_method,
                "ai_score": result.ai_score,
                "ai_feedback": result.ai_feedback,
                "strengths": result.strengths,
                "improvements": result.improvements,
                "keyword_score_ratio": result.keyword_score_ratio,
                "explanation": result.explanation
            }
            problem_list.append(problem_dict)
        
        return {
            "grading_session": {
                "id": session.id,
                "worksheet_id": session.worksheet_id,
                "total_problems": session.total_problems,
                "correct_count": session.correct_count,
                "total_score": session.total_score,
                "max_possible_score": session.max_possible_score,
                "points_per_problem": session.points_per_problem,
                "ocr_text": session.ocr_text,
                "ocr_results": session.ocr_results,
                "multiple_choice_answers": session.multiple_choice_answers,
                "input_method": session.input_method,
                "graded_at": session.graded_at.isoformat(),
                "celery_task_id": session.celery_task_id
            },
            "problem_results": problem_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채점 세션 상세 조회 중 오류: {str(e)}"
        )


@router.post("/problems/{problem_id}/regenerate")
async def regenerate_single_problem(
    problem_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """개별 문제 재생성"""
    try:
        from ..models.problem import Problem
        from ..models.worksheet import Worksheet
        from ..services.ai_service import AIService
        
        # 기존 문제 조회
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문제를 찾을 수 없습니다."
            )
        
        # 워크시트 정보 조회 (교육과정 정보 필요)
        worksheet = db.query(Worksheet).filter(Worksheet.id == problem.worksheet_id).first()
        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다."
            )
        
        # 사용자 프롬프트 추출
        user_prompt = request.get("user_prompt", "")
        if not user_prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="문제 재생성을 위한 사용자 프롬프트가 필요합니다."
            )
        
        # 교육과정 정보 구성
        curriculum_data = {
            "grade": worksheet.grade,
            "semester": worksheet.semester,
            "unit_name": worksheet.unit_name,
            "chapter_name": worksheet.chapter_name
        }
        
        # 기존 문제의 난이도와 타입 유지하거나 요청에서 받기
        target_difficulty = request.get("difficulty", problem.difficulty)
        target_type = request.get("problem_type", problem.problem_type)
        
        # 난이도 비율 설정 (단일 문제이므로 해당 난이도 100%)
        difficulty_ratio = {"A": 0, "B": 0, "C": 0}
        difficulty_ratio[target_difficulty] = 100
        
        # AI 서비스를 통한 문제 재생성
        ai_service = AIService()
        new_problems = ai_service.generate_math_problem(
            curriculum_data=curriculum_data,
            user_prompt=f"{user_prompt} (난이도: {target_difficulty}단계, 유형: {target_type})",
            problem_count=1,
            difficulty_ratio=difficulty_ratio
        )
        
        if not new_problems or len(new_problems) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="문제 재생성에 실패했습니다."
            )
        
        new_problem_data = new_problems[0]
        
        # 기존 문제 정보 업데이트
        problem.question = new_problem_data.get("question", problem.question)
        problem.correct_answer = new_problem_data.get("correct_answer", problem.correct_answer)
        problem.explanation = new_problem_data.get("explanation", problem.explanation)
        problem.difficulty = new_problem_data.get("difficulty", target_difficulty)
        problem.problem_type = new_problem_data.get("problem_type", target_type)
        
        # 객관식인 경우 선택지 업데이트
        if new_problem_data.get("choices"):
            import json
            problem.choices = json.dumps(new_problem_data["choices"], ensure_ascii=False)
        
        # 다이어그램 정보 업데이트
        if "has_diagram" in new_problem_data:
            problem.has_diagram = str(new_problem_data["has_diagram"]).lower()
        if "diagram_type" in new_problem_data:
            problem.diagram_type = new_problem_data.get("diagram_type")
        if "diagram_elements" in new_problem_data:
            import json
            problem.diagram_elements = json.dumps(new_problem_data["diagram_elements"], ensure_ascii=False)
        
        db.commit()
        db.refresh(problem)
        
        return {
            "message": f"{problem.sequence_order}번 문제가 성공적으로 재생성되었습니다.",
            "problem_id": problem_id,
            "regenerated_problem": {
                "id": problem.id,
                "sequence_order": problem.sequence_order,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else None,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "difficulty": problem.difficulty,
                "problem_type": problem.problem_type,
                "has_diagram": problem.has_diagram == "true",
                "diagram_type": problem.diagram_type,
                "diagram_elements": json.loads(problem.diagram_elements) if problem.diagram_elements else None
            },
            "updated_at": problem.updated_at.isoformat() if problem.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"문제 재생성 오류: {str(e)}")
        print(f"오류 상세: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문제 재생성 중 오류 발생: {str(e)}"
        )


@router.delete("/worksheets/{worksheet_id}")
async def delete_worksheet(
    worksheet_id: int,
    user_id: int = Query(..., description="로그인한 사용자 ID"),
    db: Session = Depends(get_db)
):
    """워크시트 삭제"""
    try:
        from ..models.worksheet import Worksheet
        from ..models.problem import Problem
        from ..models.grading_result import GradingSession, ProblemGradingResult
        
        # 워크시트 조회
        worksheet = db.query(Worksheet)\
            .filter(Worksheet.id == worksheet_id, Worksheet.teacher_id == user_id)\
            .first()
        
        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다."
            )
        
        # 관련된 채점 결과 삭제
        grading_sessions = db.query(GradingSession)\
            .filter(GradingSession.worksheet_id == worksheet_id)\
            .all()
        
        for session in grading_sessions:
            # 문제별 채점 결과 삭제
            db.query(ProblemGradingResult)\
                .filter(ProblemGradingResult.grading_session_id == session.id)\
                .delete()
            # 채점 세션 삭제
            db.delete(session)
        
        # 관련된 문제들 삭제
        db.query(Problem)\
            .filter(Problem.worksheet_id == worksheet_id)\
            .delete()
        
        # 워크시트 삭제
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


@router.delete("/problems/{problem_id}")
async def delete_problem(
    problem_id: int,
    user_id: int = Query(..., description="로그인한 사용자 ID"),
    db: Session = Depends(get_db)
):
    """개별 문제 삭제"""
    try:
        from ..models.problem import Problem
        from ..models.worksheet import Worksheet
        
        # 문제 조회
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문제를 찾을 수 없습니다."
            )
        
        # 워크시트 조회 (권한 확인)
        worksheet = db.query(Worksheet)\
            .filter(Worksheet.id == problem.worksheet_id, Worksheet.teacher_id == user_id)\
            .first()
        
        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 문제의 워크시트에 접근할 수 없습니다."
            )
        
        sequence_order = problem.sequence_order
        
        # 문제 삭제
        db.delete(problem)
        
        # 뒤의 문제들의 순서 번호 업데이트
        remaining_problems = db.query(Problem)\
            .filter(Problem.worksheet_id == problem.worksheet_id, Problem.sequence_order > sequence_order)\
            .all()
        
        for remaining_problem in remaining_problems:
            remaining_problem.sequence_order -= 1
        
        # 워크시트의 문제 수 업데이트
        current_problem_count = db.query(Problem).filter(Problem.worksheet_id == problem.worksheet_id).count() - 1
        worksheet.problem_count = current_problem_count
        
        db.commit()
        
        return {
            "message": f"{sequence_order}번 문제가 성공적으로 삭제되었습니다.",
            "deleted_problem_id": problem_id,
            "remaining_problems": current_problem_count,
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문제 삭제 중 오류 발생: {str(e)}"
        )


# ===== 과제 배포 관련 라우터 =====

@router.post("/assignments/deploy", response_model=List[AssignmentDeploymentResponse])
async def deploy_assignment(
    deploy_request: AssignmentDeployRequest,
    db: Session = Depends(get_db)
):
    """과제를 학생들에게 배포"""
    try:
        # 워크시트 존재 확인 (assignment_id가 실제로는 worksheet_id)
        from ..models.worksheet import Worksheet
        worksheet = db.query(Worksheet).filter(
            Worksheet.id == deploy_request.assignment_id
        ).first()
        
        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다"
            )
        
        # 기존 Assignment 확인 (같은 워크시트, 같은 클래스룸)
        assignment = db.query(Assignment).filter(
            Assignment.worksheet_id == worksheet.id,
            Assignment.classroom_id == deploy_request.classroom_id
        ).first()
        
        # Assignment가 없으면 새로 생성
        if not assignment:
            assignment = Assignment(
                title=worksheet.title,
                worksheet_id=worksheet.id,
                classroom_id=deploy_request.classroom_id,
                teacher_id=worksheet.teacher_id,
                unit_name=worksheet.unit_name,
                chapter_name=worksheet.chapter_name,
                problem_count=worksheet.problem_count,
                is_deployed="deployed"
            )
            db.add(assignment)
            db.flush()  # ID를 얻기 위해 flush
        else:
            # 기존 Assignment의 배포 상태 업데이트
            assignment.is_deployed = "deployed"
        
        # 배포 정보 생성 (중복 배포 방지)
        deployments = []
        for student_id in deploy_request.student_ids:
            # 기존 배포 정보 확인
            existing_deployment = db.query(AssignmentDeployment).filter(
                AssignmentDeployment.assignment_id == assignment.id,
                AssignmentDeployment.student_id == student_id
            ).first()
            
            if not existing_deployment:
                deployment = AssignmentDeployment(
                    assignment_id=assignment.id,
                    student_id=student_id,
                    classroom_id=deploy_request.classroom_id,
                    status="assigned"
                )
                db.add(deployment)
                deployments.append(deployment)
            else:
                deployments.append(existing_deployment)
        
        db.commit()
        
        # 응답 데이터 생성
        response_data = []
        for deployment in deployments:
            db.refresh(deployment)
            response_data.append(AssignmentDeploymentResponse(
                id=deployment.id,
                assignment_id=deployment.assignment_id,
                student_id=deployment.student_id,
                classroom_id=deployment.classroom_id,
                status=deployment.status,
                deployed_at=deployment.deployed_at.isoformat()
            ))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"과제 배포 중 오류 발생: {str(e)}"
        )


@router.get("/assignments/student/{student_id}", response_model=List[StudentAssignmentResponse])
async def get_student_assignments(
    student_id: int,
    db: Session = Depends(get_db)
):
    """학생의 과제 목록 조회"""
    try:
        print(f"🔍 학생 과제 목록 조회 - student_id: {student_id}")
        
        # 학생이 속한 클래스룸 확인
        from ..models.user import StudentJoinRequest
        student_classrooms = db.query(StudentJoinRequest).filter(
            StudentJoinRequest.student_id == student_id,
            StudentJoinRequest.status == "approved"
        ).all()
        
        print(f"📚 학생이 속한 클래스룸 수: {len(student_classrooms)}")
        for classroom in student_classrooms:
            print(f"  - 클래스룸 ID: {classroom.classroom_id}")
        
        # 학생이 속한 클래스룸의 과제 배포 정보 조회
        classroom_ids = [c.classroom_id for c in student_classrooms]
        print(f"📚 조회할 클래스룸 ID 목록: {classroom_ids}")
        
        if not classroom_ids:
            print("⚠️ 학생이 승인된 클래스룸에 속해있지 않습니다.")
            return []
        
        deployments = db.query(AssignmentDeployment).join(Assignment).filter(
            AssignmentDeployment.student_id == student_id,
            AssignmentDeployment.classroom_id.in_(classroom_ids)
        ).all()
        
        print(f"📚 찾은 배포 정보 수: {len(deployments)}")
        
        response_data = []
        for deployment in deployments:
            assignment = deployment.assignment
            print(f"  - 과제: {assignment.title} (ID: {assignment.id})")
            response_data.append(StudentAssignmentResponse(
                id=deployment.id,
                title=assignment.title,
                unit_name=assignment.unit_name,
                chapter_name=assignment.chapter_name,
                problem_count=assignment.problem_count,
                status=deployment.status,
                deployed_at=deployment.deployed_at.isoformat(),
                assignment_id=assignment.id
            ))
        
        print(f"📚 최종 응답 데이터 수: {len(response_data)}")
        return response_data
        
    except Exception as e:
        print(f"❌ 학생 과제 목록 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"학생 과제 목록 조회 중 오류 발생: {str(e)}"
        )


@router.get("/assignments/{assignment_id}/student/{student_id}", response_model=dict)
async def get_assignment_detail_for_student(
    assignment_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    """학생용 과제 상세 정보 조회 (문제 포함)"""
    try:
        print(f"🔍 학생 과제 상세 조회 - assignment_id: {assignment_id}, student_id: {student_id}")
        
        # 배포 정보 확인
        deployment = db.query(AssignmentDeployment).filter(
            AssignmentDeployment.assignment_id == assignment_id,
            AssignmentDeployment.student_id == student_id
        ).first()
        
        print(f"🔍 배포 정보 조회 결과: {deployment}")
        
        if not deployment:
            print(f"❌ 배포 정보를 찾을 수 없음 - assignment_id: {assignment_id}, student_id: {student_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"배포된 과제를 찾을 수 없습니다 (assignment_id: {assignment_id}, student_id: {student_id})"
            )
        
        assignment = deployment.assignment
        print(f"🔍 Assignment 정보: {assignment}")
        print(f"🔍 Assignment ID: {assignment.id}")
        print(f"🔍 Assignment Title: {assignment.title}")
        print(f"🔍 Worksheet ID: {assignment.worksheet_id}")
        
        # 워크시트 존재 여부 확인
        from ..models.worksheet import Worksheet
        worksheet = db.query(Worksheet).filter(Worksheet.id == assignment.worksheet_id).first()
        print(f"🔍 Worksheet 존재 여부: {worksheet is not None}")
        if worksheet:
            print(f"🔍 Worksheet Title: {worksheet.title}")
            print(f"🔍 Worksheet Status: {worksheet.status}")
        
        # 워크시트의 문제들 가져오기
        print(f"🔍 문제 조회 시작 - worksheet_id: {assignment.worksheet_id}")
        
        # 먼저 워크시트가 존재하는지 확인
        if not worksheet:
            print(f"❌ 워크시트가 존재하지 않음 - worksheet_id: {assignment.worksheet_id}")
            worksheet_problems = []
        else:
            print(f"✅ 워크시트 존재 확인 - Title: {worksheet.title}")
            worksheet_problems = math_service.get_worksheet_problems(db, assignment.worksheet_id)
            print(f"🔍 문제 개수: {len(worksheet_problems)}")
            
            # 문제가 없다면 데이터베이스에서 직접 확인
            if len(worksheet_problems) == 0:
                from ..models.problem import Problem
                direct_problems = db.query(Problem).filter(
                    Problem.worksheet_id == assignment.worksheet_id
                ).all()
                print(f"🔍 직접 조회한 문제 수: {len(direct_problems)}")
                for p in direct_problems:
                    print(f"  - 문제 ID: {p.id}, 순서: {p.sequence_order}, 텍스트: {p.question[:50]}...")
        
        response_data = {
            "assignment": {
                "id": assignment.id,
                "title": assignment.title,
                "unit_name": assignment.unit_name,
                "chapter_name": assignment.chapter_name,
                "problem_count": assignment.problem_count
            },
            "deployment": {
                "id": deployment.id,
                "status": deployment.status,
                "deployed_at": deployment.deployed_at.isoformat()
            },
            "problems": worksheet_problems
        }
        
        print(f"🔍 최종 응답 데이터:")
        print(f"  - Assignment: {response_data['assignment']}")
        print(f"  - Deployment: {response_data['deployment']}")
        print(f"  - Problems 개수: {len(response_data['problems'])}")
        print(f"  - Problems 내용: {response_data['problems']}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"과제 상세 정보 조회 중 오류 발생: {str(e)}"
        )