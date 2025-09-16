from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator, List
from celery.result import AsyncResult
from datetime import datetime
import asyncio
import json
import uuid

from ..database import get_db
from ..schemas.korean_generation import (
    KoreanProblemGenerationRequest,
    KoreanWorksheetCreate,
    KoreanWorksheetResponse,
    KoreanProblemResponse,
    AssignmentCreate,
    AssignmentResponse,
    AssignmentDeployRequest,
    AssignmentDeploymentResponse,
    StudentAssignmentResponse
)
from ..services.korean_generation_service import KoreanGenerationService
from ..models.korean_generation import Assignment, AssignmentDeployment
from ..tasks import generate_korean_problems_task, grade_korean_problems_task
from ..celery_app import celery_app

router = APIRouter()
korean_service = KoreanGenerationService()


@router.post("/generate")
async def generate_korean_problems(
    request: KoreanProblemGenerationRequest,
    user_id: int = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """국어 문제 생성"""
    try:
        task = generate_korean_problems_task.delay(
            request_data=request.model_dump(),
            user_id=user_id
        )

        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "국어 문제 생성이 시작되었습니다. /tasks/{task_id} 엔드포인트로 진행 상황을 확인하세요."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"국어 문제 생성 요청 중 오류 발생: {str(e)}"
        )


@router.get("/generation/history")
async def get_generation_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_id: int = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """국어 문제 생성 이력 조회"""
    try:
        history = korean_service.get_generation_history(db, user_id=user_id, skip=skip, limit=limit)

        result = []
        for session in history:
            result.append({
                "generation_id": session.generation_id,
                "school_level": session.school_level,
                "grade": session.grade,
                "korean_type": session.korean_type,
                "question_type": session.question_type,
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
    user_id: int = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """국어 문제 생성 세션 상세 조회"""
    try:
        session = korean_service.get_generation_detail(db, generation_id, user_id=user_id)
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
            problem_dict = {
                "id": problem.id,
                "problem_type": problem.problem_type.value,
                "korean_type": problem.korean_type.value,
                "difficulty": problem.difficulty.value,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else None,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "source_text": problem.source_text,
                "source_title": problem.source_title,
                "source_author": problem.source_author
            }
            problem_list.append(problem_dict)

        return {
            "generation_info": {
                "generation_id": session.generation_id,
                "school_level": session.school_level,
                "grade": session.grade,
                "korean_type": session.korean_type,
                "question_type": session.question_type,
                "problem_count": session.problem_count,
                "korean_type_ratio": session.korean_type_ratio,
                "question_type_ratio": session.question_type_ratio,
                "difficulty_ratio": session.difficulty_ratio,
                "user_text": session.user_text,
                "actual_korean_type_distribution": session.actual_korean_type_distribution,
                "actual_question_type_distribution": session.actual_question_type_distribution,
                "actual_difficulty_distribution": session.actual_difficulty_distribution,
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
    """태스크 상태 조회"""
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


@router.get("/worksheets")
async def get_worksheets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Query(..., description="로그인한 사용자 ID"),
    db: Session = Depends(get_db)
):
    """국어 워크시트 목록 조회"""
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
                "korean_type": worksheet.korean_type,
                "question_type": worksheet.question_type,
                "difficulty": worksheet.difficulty,
                "problem_count": worksheet.problem_count,
                "korean_type_ratio": worksheet.korean_type_ratio,
                "question_type_ratio": worksheet.question_type_ratio,
                "difficulty_ratio": worksheet.difficulty_ratio,
                "user_text": worksheet.user_text,
                "actual_korean_type_distribution": worksheet.actual_korean_type_distribution,
                "actual_question_type_distribution": worksheet.actual_question_type_distribution,
                "actual_difficulty_distribution": worksheet.actual_difficulty_distribution,
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
    """국어 워크시트 상세 조회"""
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
            problem_dict = {
                "id": problem.id,
                "sequence_order": problem.sequence_order,
                "korean_type": problem.korean_type,
                "problem_type": problem.problem_type,
                "difficulty": problem.difficulty,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else None,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "source_text": problem.source_text,
                "source_title": problem.source_title,
                "source_author": problem.source_author
            }
            problem_list.append(problem_dict)

        return {
            "worksheet": {
                "id": worksheet.id,
                "title": worksheet.title,
                "school_level": worksheet.school_level,
                "grade": worksheet.grade,
                "korean_type": worksheet.korean_type,
                "question_type": worksheet.question_type,
                "difficulty": worksheet.difficulty,
                "problem_count": worksheet.problem_count,
                "korean_type_ratio": worksheet.korean_type_ratio,
                "question_type_ratio": worksheet.question_type_ratio,
                "difficulty_ratio": worksheet.difficulty_ratio,
                "user_text": worksheet.user_text,
                "generation_id": worksheet.generation_id,
                "actual_korean_type_distribution": worksheet.actual_korean_type_distribution,
                "actual_question_type_distribution": worksheet.actual_question_type_distribution,
                "actual_difficulty_distribution": worksheet.actual_difficulty_distribution,
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
    user_id: int = Query(..., description="로그인한 사용자 ID"),
    db: Session = Depends(get_db)
):
    """국어 워크시트 업데이트"""
    try:
        from ..models.worksheet import Worksheet
        
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
        
        db.commit()
        
        return {
            "message": "국어 워크시트가 성공적으로 업데이트되었습니다.",
            "worksheet_id": worksheet_id,
            "updated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"국어 워크시트 업데이트 중 오류 발생: {str(e)}"
        )