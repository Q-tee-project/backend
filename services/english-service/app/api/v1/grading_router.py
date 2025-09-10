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
    Worksheet, GradingResult, QuestionResult,
    AnswerPassage, AnswerExample
)
from app.services.grading_service import perform_grading

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
        
        # 채점 수행
        grading_result = await perform_grading(worksheet, answers, db, student_name, completion_time)
        
        # 결과 반환
        return {
            "status": "success",
            "message": "답안이 제출되고 채점이 완료되었습니다.",
            "grading_result": {
                "result_id": grading_result["result_id"],
                "student_name": student_name,
                "completion_time": completion_time,
                "total_score": grading_result["total_score"],
                "max_score": grading_result["max_score"],
                "percentage": grading_result["percentage"],
                "needs_review": grading_result["needs_review"],
                "passage_groups": grading_result.get("passage_groups", []),
                "example_groups": grading_result.get("example_groups", []),
                "standalone_questions": grading_result.get("standalone_questions", [])
            }
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
        
        # 지문과 예문 데이터도 함께 조회
        answer_passages = db.query(AnswerPassage).filter(
            AnswerPassage.worksheet_id == result.worksheet_id
        ).all()
        
        answer_examples = db.query(AnswerExample).filter(
            AnswerExample.worksheet_id == result.worksheet_id
        ).all()
        
        # 백엔드에서 미리 그룹핑 (grading_service와 동일한 로직)
        passage_groups = []
        example_groups = []
        standalone_questions = []
        
        # 문제별 결과를 딕셔너리로 변환 (그룹핑용)
        question_results = []
        processed_questions = set()
        
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
                "created_at": question_result.created_at,
                "passage_id": getattr(question_result, 'passage_id', None),
                "example_id": getattr(question_result, 'example_id', None)
            }
            question_results.append(question_data)
        
        # 지문별 문제 그룹핑 (related_questions 기준)
        for answer_passage in answer_passages:
            if answer_passage.related_questions:
                related_questions = []
                for question_id in answer_passage.related_questions:
                    matching_question = next((q for q in question_results if q["question_id"] == str(question_id)), None)
                    if matching_question:
                        related_questions.append(matching_question)
                        processed_questions.add(matching_question["question_id"])
                
                if related_questions:
                    passage_groups.append({
                        "passage": {
                            "passage_id": answer_passage.passage_id,
                            "original_content": answer_passage.original_content,
                            "text_type": getattr(answer_passage, 'text_type', None)
                        },
                        "questions": related_questions
                    })
        
        # 예문별 문제 그룹핑 (지문에 속하지 않은 것만)
        for answer_example in answer_examples:
            if answer_example.related_questions:
                related_questions = []
                
                # related_questions가 문자열인 경우 리스트로 변환
                if isinstance(answer_example.related_questions, str):
                    question_ids = [answer_example.related_questions]
                else:
                    question_ids = answer_example.related_questions
                    
                for question_id in question_ids:
                    if str(question_id) not in processed_questions:
                        matching_question = next((q for q in question_results if q["question_id"] == str(question_id)), None)
                        if matching_question:
                            related_questions.append(matching_question)
                            processed_questions.add(matching_question["question_id"])
                
                if related_questions:
                    example_groups.append({
                        "example": {
                            "example_id": answer_example.example_id,
                            "original_content": answer_example.original_content
                        },
                        "questions": related_questions
                    })
        
        # 독립 문제들
        standalone_questions = [q for q in question_results if q["question_id"] not in processed_questions]
        
        # 디버깅 로그
        print(f"🔍 API 디버깅 - result_id: {result.result_id}")
        print(f"📄 passage_groups 개수: {len(passage_groups)}")
        print(f"📝 example_groups 개수: {len(example_groups)}")
        print(f"📋 standalone_questions 개수: {len(standalone_questions)}")
        print(f"🗂️ answer_passages 개수: {len(answer_passages)}")
        print(f"🗂️ answer_examples 개수: {len(answer_examples)}")
        
        # 결과 객체 구성
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
            "question_results": question_results,  # 호환성을 위해 유지
            "passage_groups": passage_groups,      # 지문별 그룹
            "example_groups": example_groups,      # 예문별 그룹  
            "standalone_questions": standalone_questions  # 독립 문제들
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
    """채점 결과의 검수를 업데이트합니다."""
    try:
        # 채점 결과 조회
        grading_result = db.query(GradingResult).filter(GradingResult.result_id == result_id).first()
        if not grading_result:
            raise HTTPException(status_code=404, detail="채점 결과를 찾을 수 없습니다.")
        
        # 문제별 검수 결과 업데이트
        total_score = 0
        max_score = 0
        
        for question_result in grading_result.question_results:
            question_id = question_result.question_id
            max_score += question_result.max_score
            
            if question_id in review_data.question_results:
                review_info = review_data.question_results[question_id]
                
                # 검수된 점수와 피드백 업데이트
                if "score" in review_info:
                    question_result.reviewed_score = review_info["score"]
                    total_score += review_info["score"]
                else:
                    total_score += question_result.score
                
                if "feedback" in review_info:
                    question_result.reviewed_feedback = review_info["feedback"]
                
                question_result.is_reviewed = True
            else:
                total_score += question_result.score
        
        # 전체 채점 결과 업데이트
        grading_result.total_score = total_score
        grading_result.percentage = round((total_score / max_score * 100) if max_score > 0 else 0, 1)
        grading_result.is_reviewed = True
        grading_result.reviewed_at = datetime.now()
        grading_result.reviewed_by = review_data.reviewed_by
        grading_result.needs_review = False
        
        db.commit()
        
        return {
            "status": "success",
            "message": "검수가 완료되었습니다.",
            "result": {
                "result_id": result_id,
                "total_score": total_score,
                "max_score": max_score,
                "percentage": grading_result.percentage
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검수 업데이트 중 오류: {str(e)}")
