from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.schemas.schemas import (
    SubmissionRequest, GradingResultResponse, 
    GradingResultSummary, ReviewRequest
)
from app.models.models import (
    Worksheet, GradingResult, QuestionResult, Passage, Example
)
from app.services.new_grading_service import grade_worksheet_submission, review_ai_grading

router = APIRouter(tags=["Grading"])

@router.post("/worksheets/{worksheet_id}/submit")
async def submit_answers_and_grade(
    worksheet_id: str,
    submission_data: SubmissionRequest,
    db: Session = Depends(get_db)
):
    """답안을 제출하고 자동 채점을 수행합니다."""
    try:
        # 문제지 조회
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        student_name = "학생"  # 기본 이름 사용
        answers = submission_data.answers
        completion_time = submission_data.completion_time
        
        # 새로운 채점 서비스로 채점 수행
        grading_result = await grade_worksheet_submission(
            db, worksheet_id, student_name, answers, completion_time
        )
        
        # 결과 반환
        return {
            "status": "success",
            "message": "답안이 제출되고 채점이 완료되었습니다.",
            "grading_result": grading_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답안 제출 및 채점 중 오류: {str(e)}")

@router.get("/grading-results", response_model=List[GradingResultSummary])
async def get_grading_results(db: Session = Depends(get_db)):
    """모든 채점 결과 목록을 조회합니다."""
    try:
        results = db.query(GradingResult).join(Worksheet).order_by(GradingResult.created_at.desc()).all()
        
        result_summaries = []
        for result in results:
            result_summaries.append(GradingResultSummary(
                id=result.id,
                result_id=result.result_id,
                worksheet_id=result.worksheet_id,
                student_name=result.student_name,
                completion_time=result.completion_time,
                total_score=result.total_score,
                max_score=result.max_score,
                percentage=result.percentage,
                needs_review=result.needs_review,
                is_reviewed=result.is_reviewed,
                created_at=result.created_at,
                worksheet_name=result.worksheet.worksheet_name if result.worksheet else None
            ))
        
        return result_summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채점 결과 조회 중 오류: {str(e)}")

@router.get("/grading-results/{result_id}", response_model=GradingResultResponse)
async def get_grading_result(result_id: str, db: Session = Depends(get_db)):
    """특정 채점 결과의 상세 정보를 조회합니다."""
    try:
        result = db.query(GradingResult).filter(GradingResult.result_id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="채점 결과를 찾을 수 없습니다.")
        
        # 문제별 결과를 딕셔너리로 변환
        question_results = []
        for question_result in result.question_results:
            question_data = {
                "id": question_result.id,
                "question_id": question_result.question_id,
                "question_type": question_result.question_type,
                "student_answer": question_result.student_answer,
                "correct_answer": question_result.correct_answer,
                "score": question_result.score,
                "max_score": question_result.max_score,
                "is_correct": question_result.is_correct,
                "grading_method": question_result.grading_method,
                "ai_feedback": question_result.ai_feedback,
                "needs_review": question_result.needs_review,
                "reviewed_score": question_result.reviewed_score,
                "reviewed_feedback": question_result.reviewed_feedback,
                "is_reviewed": question_result.is_reviewed,
                "created_at": question_result.created_at
            }
            question_results.append(question_data)
        
        # 결과 객체 구성 (단순화)
        result_dict = {
            "id": result.id,
            "result_id": result.result_id,
            "worksheet_id": result.worksheet_id,
            "student_name": result.student_name,
            "completion_time": result.completion_time,
            "total_score": result.total_score,
            "max_score": result.max_score,
            "percentage": result.percentage,
            "needs_review": result.needs_review,
            "is_reviewed": result.is_reviewed,
            "reviewed_at": result.reviewed_at,
            "reviewed_by": result.reviewed_by,
            "created_at": result.created_at,
            "question_results": question_results
        }
        
        return result_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채점 결과 조회 중 오류: {str(e)}")

@router.put("/grading-results/{result_id}/review")
async def update_grading_review(
    result_id: str, 
    review_data: ReviewRequest, 
    db: Session = Depends(get_db)
):
    """AI 채점 결과의 검수를 업데이트합니다."""
    try:
        # 새로운 검수 서비스 사용
        review_result = await review_ai_grading(
            db, result_id, review_data.question_results, review_data.reviewed_by
        )
        
        return review_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검수 중 오류: {str(e)}")
