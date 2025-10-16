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
    worksheet_id: int,
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
            # student_id로 student 이름 조회 (auth_service 스키마에서)
            from sqlalchemy import text
            student_query = text("""
                SELECT name
                FROM auth_service.students
                WHERE id = :student_id
            """)
            student_result = db.execute(student_query, {"student_id": result.student_id})
            student_name = student_result.scalar() or f"Student {result.student_id}"

            result_summaries.append(GradingResultSummary(
                id=result.result_id,  # int 그대로 사용
                result_id=result.result_id,  # int 그대로 사용
                worksheet_id=result.worksheet_id,
                student_name=student_name,
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
async def get_grading_result(result_id: int, db: Session = Depends(get_db)):
    """특정 채점 결과의 상세 정보를 조회합니다."""
    try:
        print(f"📊 채점 결과 상세 조회: result_id={result_id} (type: {type(result_id)})")
        # result_id (Integer)로 검색
        result = db.query(GradingResult).filter(
            GradingResult.result_id == result_id
        ).first()
        print(f"📋 채점 결과 조회: {result}")

        if not result:
            raise HTTPException(status_code=404, detail="채점 결과를 찾을 수 없습니다.")
        
        # 문제별 결과를 딕셔너리로 변환 (깔끔한 구조)
        print(f"🔍 문제별 결과 처리 시작: {len(result.question_results)}개")
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
        print("📝 문제지 데이터 조회 시작")
        from app.models import Worksheet, Passage, Question
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == result.worksheet_id).first()
        print(f"📄 Worksheet 조회 결과: {worksheet}")

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
        
        # 예문 데이터는 Question 모델의 example_* 필드에서 처리됨 (별도 테이블 없음)
        
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
                "example_content": question.example_content,
                "example_original_content": question.example_original_content,
                "example_korean_translation": question.example_korean_translation,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "learning_point": question.learning_point
            })
        
        # 학생 이름 조회
        print("👤 학생 정보 조회 시작")
        try:
            from sqlalchemy import text
            student_query = text("""
                SELECT name
                FROM auth_service.students
                WHERE id = :student_id
            """)
            student_result = db.execute(student_query, {"student_id": result.student_id})
            student_info = student_result.fetchone()
            student_name = student_info[0] if student_info else f"학생{result.student_id}"
        except Exception as e:
            print(f"학생 정보 조회 실패: {e}")
            student_name = f"학생{result.student_id}"

        # 결과 객체 구성 (문제지 데이터 포함)
        result_dict = {
            "result_id": result.result_id,
            "worksheet_id": result.worksheet_id,
            "student_id": result.student_id,
            "student_name": student_name,
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
        print(f"❌ 채점 결과 조회 에러: {str(e)}")
        import traceback
        print(f"❌ 전체 스택트레이스: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"채점 결과 조회 중 오류: {str(e)}")

@router.put("/grading-results/{result_id}/update")
async def update_grading_result(
    result_id: int,
    update_data: dict,
    db: Session = Depends(get_db)
):
    """영어 채점 결과를 업데이트합니다."""
    try:
        # 채점 결과 조회
        grading_result = db.query(GradingResult).filter(
            GradingResult.result_id == result_id
        ).first()

        if not grading_result:
            raise HTTPException(status_code=404, detail="채점 결과를 찾을 수 없습니다.")

        print(f"📊 영어 채점 결과 업데이트: result_id={result_id}")
        print(f"📊 업데이트 데이터: {update_data}")

        # 문제별 정답/오답 처리
        if "answers" in update_data:
            answers = update_data["answers"]

            for answer in answers:
                question_id = answer.get("question_id")
                is_correct = answer.get("is_correct", False)
                score = answer.get("score", 0)

                # 해당 문제 결과 찾기
                question_result = db.query(QuestionResult).filter(
                    QuestionResult.grading_result_id == result_id,
                    QuestionResult.question_id == question_id
                ).first()

                if question_result:
                    # 기존 결과 업데이트
                    question_result.is_correct = is_correct
                    question_result.score = score

                    # 업데이트된 정답이 있으면 반영
                    if "correct_answer" in answer:
                        question_result.correct_answer = answer["correct_answer"]
                        print(f"🔄 문제 {question_id}의 정답을 '{answer['correct_answer']}'로 업데이트")

                    print(f"📝 문제 {question_id} 업데이트: 정답={is_correct}, 점수={score}")

        # 업데이트된 정답들 처리 (선생님이 정답처리한 경우 학생 답안을 정답으로 설정)
        if "updated_correct_answers" in update_data:
            updated_answers = update_data["updated_correct_answers"]

            for question_id_str, new_correct_answer in updated_answers.items():
                question_id = int(question_id_str)
                question_result = db.query(QuestionResult).filter(
                    QuestionResult.grading_result_id == result_id,
                    QuestionResult.question_id == question_id
                ).first()

                if question_result:
                    question_result.correct_answer = new_correct_answer
                    print(f"🔄 영어 문제 {question_id}의 정답을 '{new_correct_answer}'로 업데이트")

        # 전체 점수 재계산
        if "answers" in update_data:
            all_question_results = db.query(QuestionResult).filter(
                QuestionResult.grading_result_id == result_id
            ).all()

            correct_count = sum(1 for qr in all_question_results if qr.is_correct)
            total_score = sum(qr.score for qr in all_question_results)
            max_score = sum(qr.max_score for qr in all_question_results)
            percentage = (total_score / max_score * 100) if max_score > 0 else 0

            grading_result.total_score = total_score
            grading_result.percentage = percentage

            print(f"📊 점수 재계산: 총점={total_score}, 정답수={correct_count}, 퍼센트={percentage}")

        # 검수 상태 업데이트
        if "is_reviewed" in update_data:
            grading_result.is_reviewed = update_data["is_reviewed"]

        db.commit()
        db.refresh(grading_result)

        # 채점 수정 알림 전송 (선생님 → 학생)
        from app.models.assignment import Assignment, AssignmentDeployment
        from app.utils.notification_helper import send_grading_updated_notification

        # worksheet_id로 assignment 찾기
        assignment = db.query(Assignment).filter(
            Assignment.worksheet_id == grading_result.worksheet_id
        ).first()

        if assignment:
            try:
                await send_grading_updated_notification(
                    student_id=grading_result.student_id,
                    assignment_id=assignment.id,
                    assignment_title=assignment.title,
                    score=grading_result.total_score,
                    feedback=update_data.get("feedback")
                )
            except Exception as e:
                print(f"⚠️ 채점 수정 알림 전송 실패 (주요 로직 계속 진행): {e}")

        return {
            "result_id": result_id,
            "status": "success",
            "total_score": grading_result.total_score,
            "percentage": grading_result.percentage,
            "message": "채점 결과가 성공적으로 업데이트되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 채점 결과 업데이트 에러: {str(e)}")
        import traceback
        print(f"❌ 전체 스택트레이스: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"채점 결과 업데이트 중 오류: {str(e)}")

@router.put("/grading-results/{result_id}/review")
async def update_grading_review(
    result_id: int,
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

