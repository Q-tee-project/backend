from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.schemas import (
    SubmissionRequest, GradingResultResponse, 
    GradingResultSummary, ReviewRequest
)
from app.models import (
    Worksheet, GradingResult, QuestionResult, Passage
)
from app.services.grading.grading_service import GradingService

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
        
        student_name = submission_data.student_name
        answers = submission_data.answers
        completion_time = submission_data.completion_time
        
        # 새로운 채점 서비스로 채점 수행
        grading_service = GradingService(db)
        grading_result = await grading_service.grade_worksheet(
            worksheet_id, student_name, answers, completion_time
        )
        
        # 결과 반환 (grading_result 내용을 직접 반환)
        return {
            "status": "success",
            "message": "답안이 제출되고 채점이 완료되었습니다.",
            **grading_result  # grading_result의 모든 필드를 펼쳐서 포함
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
                id=result.result_id,  # result_id를 id로 사용
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
        # result_id (UUID)로 검색
        result = db.query(GradingResult).filter(
            GradingResult.result_id == result_id
        ).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="채점 결과를 찾을 수 없습니다.")
        
        # 문제별 결과를 딕셔너리로 변환 (깔끔한 구조)
        question_results = []
        for question_result in result.question_results:
            question_data = {
                "question_id": question_result.question_id,
                "question_type": question_result.question_type,
                "student_answer": question_result.student_answer,
                "correct_answer": question_result.correct_answer,
                "score": question_result.score,
                "max_score": question_result.max_score,
                "is_correct": question_result.is_correct,
                "grading_method": question_result.grading_method,
                "ai_feedback": question_result.ai_feedback
                # 불필요한 필드들 제거: id, needs_review, reviewed_*, created_at
            }
            question_results.append(question_data)
        
        # 학생 답안을 딕셔너리로 변환
        student_answers = {}
        for qr in result.question_results:
            student_answers[qr.question_id] = qr.student_answer
        
        # 문제지 데이터도 함께 조회
        from app.models import Worksheet, Passage, Question
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == result.worksheet_id).first()
        
        if not worksheet:
            raise HTTPException(status_code=404, detail="관련 문제지를 찾을 수 없습니다.")
        
        # 문제지 데이터 구성
        worksheet_data = {
            "worksheet_id": worksheet.worksheet_id,
            "worksheet_name": worksheet.worksheet_name,
            "worksheet_level": worksheet.school_level,
            "worksheet_grade": worksheet.grade,
            "worksheet_subject": worksheet.subject,
            "total_questions": worksheet.total_questions,
            "worksheet_duration": worksheet.duration,
            "passages": [],
            "examples": [],
            "questions": []
        }
        
        # 지문 데이터 추가 (한글 번역 포함)
        for passage in worksheet.passages:
            worksheet_data["passages"].append({
                "passage_id": passage.passage_id,
                "passage_type": passage.passage_type,
                "passage_content": passage.passage_content,
                "original_content": passage.original_content,
                "korean_translation": passage.korean_translation,
                "related_questions": passage.related_questions
            })
        
        # 예문 데이터 추가 (한글 번역 포함)
        for example in worksheet.examples:
            worksheet_data["examples"].append({
                "example_id": example.example_id,
                "example_content": example.example_content,
                "original_content": example.original_content,
                "korean_translation": example.korean_translation,
                "related_question": example.related_question
            })
        
        # 문제 데이터 추가 (답안 제외)
        for question in worksheet.questions:
            worksheet_data["questions"].append({
                "question_id": question.question_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "question_subject": question.question_subject,
                "question_difficulty": question.question_difficulty,
                "question_detail_type": question.question_detail_type,
                "question_choices": question.question_choices,
                "question_passage_id": question.passage_id,
                "question_example_id": question.example_id,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "learning_point": question.learning_point
            })
        
        # 결과 객체 구성 (문제지 데이터 포함)
        result_dict = {
            "result_id": result.result_id,
            "worksheet_id": result.worksheet_id,
            "student_name": result.student_name,
            "completion_time": result.completion_time,
            "total_score": result.total_score,
            "max_score": result.max_score,
            "percentage": result.percentage,
            "question_results": question_results,
            "student_answers": student_answers,
            "created_at": result.created_at,
            "worksheet_data": worksheet_data  # 문제지 데이터 포함
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
        # 검수 기능 (임시 구현)
        grading_result = db.query(GradingResult).filter(
            GradingResult.result_id == result_id
        ).first()

        if not grading_result:
            raise HTTPException(status_code=404, detail="채점 결과를 찾을 수 없습니다.")

        # 검수 완료 상태로 업데이트
        grading_result.is_reviewed = True
        grading_result.reviewed_by = review_data.reviewed_by
        grading_result.reviewed_at = datetime.now()

        db.commit()

        review_result = {"status": "success", "message": "검수가 완료되었습니다."}
        
        return review_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검수 중 오류: {str(e)}")

