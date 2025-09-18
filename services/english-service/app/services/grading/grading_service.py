from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.models import (
    Worksheet, Question, Passage,
    GradingResult, QuestionResult
)
from .objective_grader import ObjectiveGrader
from .subjective_grader import SubjectiveGrader


class GradingService:
    """통합 채점 서비스 - 객관식은 DB 비교, 주관식/서술형은 AI 채점"""

    def __init__(self, db: Session):
        self.db = db
        self.objective_grader = ObjectiveGrader()
        self.subjective_grader = SubjectiveGrader()

    async def grade_worksheet(self, worksheet_id: str, student_name: str,
                            answers: Dict[int, str], completion_time: int) -> Dict[str, Any]:
        """문제지 전체 채점"""
        try:
            # 문제지 정보 조회
            worksheet = self.db.query(Worksheet).filter(
                Worksheet.worksheet_id == worksheet_id
            ).first()

            if not worksheet:
                raise Exception("문제지를 찾을 수 없습니다.")

            # 문제들 조회
            questions = self.db.query(Question).filter(
                Question.worksheet_id == worksheet_id
            ).all()

            if not questions:
                raise Exception("문제를 찾을 수 없습니다.")

            # 각 문제별 채점
            question_results = []
            total_score = 0
            max_score = 0

            for question in questions:
                student_answer = answers.get(question.question_id, "")

                # 문제별 채점
                result = await self._grade_single_question(
                    question, student_answer, worksheet_id
                )

                question_results.append(result)
                total_score += result["score"]
                max_score += result["max_score"]

            # 채점 결과 저장
            grading_result = await self._save_grading_result(
                worksheet_id, student_name, completion_time,
                total_score, max_score, question_results
            )

            # 결과 반환
            percentage = (total_score / max_score * 100) if max_score > 0 else 0

            return {
                "result_id": grading_result.result_id,
                "student_name": student_name,
                "worksheet_id": worksheet_id,
                "total_score": total_score,
                "max_score": max_score,
                "percentage": round(percentage, 2),
                "completion_time": completion_time,
                "question_results": question_results,
                "needs_review": any(qr.get("needs_review", False) for qr in question_results),
                "created_at": grading_result.created_at
            }

        except Exception as e:
            print(f"❌ 채점 오류: {str(e)}")
            raise e

    async def _grade_single_question(self, question: Question, student_answer: str,
                                   worksheet_id: str) -> Dict[str, Any]:
        """개별 문제 채점"""

        question_result = {
            "question_id": question.question_id,
            "question_type": question.question_type,
            "question_text": question.question_text,
            "student_answer": student_answer,
            "correct_answer": question.correct_answer,
            "max_score": 10,  # 기본 점수
            "score": 0,
            "is_correct": False,
            "grading_method": "db",
            "ai_feedback": None,
            "needs_review": False
        }

        if not student_answer.strip():
            # 답안이 없는 경우
            question_result["score"] = 0
            question_result["is_correct"] = False
            return question_result

        if question.question_type == "객관식":
            # 객관식: DB의 정답과 직접 비교
            grading_result = self.objective_grader.grade_multiple_choice(
                question.correct_answer, student_answer
            )
            question_result.update(grading_result)

        elif question.question_type == "단답형":
            # 단답형: DB의 정답과 직접 비교
            grading_result = self.objective_grader.grade_short_answer(
                question.correct_answer, student_answer
            )
            question_result.update(grading_result)

        elif question.question_type in ["주관식", "서술형"]:
            # 주관식/서술형: AI 채점
            # 관련 지문과 예문 조회
            passage_content = self._get_passage_content(worksheet_id, question.passage_id)
            example_content = question.example_content

            grading_result = await self.subjective_grader.grade_subjective(
                question_text=question.question_text,
                correct_answer=question.correct_answer,
                student_answer=student_answer,
                passage_content=passage_content,
                example_content=example_content
            )

            question_result.update(grading_result)
            question_result["needs_review"] = True  # AI 채점은 항상 검수 필요

        return question_result

    def _get_passage_content(self, worksheet_id: str, passage_id: Optional[int]) -> Optional[str]:
        """지문 내용을 조회합니다."""
        if not passage_id:
            return None

        passage = self.db.query(Passage).filter(
            Passage.worksheet_id == worksheet_id,
            Passage.passage_id == passage_id
        ).first()

        return str(passage.passage_content) if passage else None

    async def _save_grading_result(self, worksheet_id: str, student_name: str,
                                 completion_time: int, total_score: int, max_score: int,
                                 question_results: List[Dict[str, Any]]) -> GradingResult:
        """채점 결과를 데이터베이스에 저장합니다."""

        # 전체 채점 결과 저장
        result_id = str(uuid.uuid4())
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        needs_review = any(qr.get("needs_review", False) for qr in question_results)

        grading_result = GradingResult(
            result_id=result_id,
            worksheet_id=worksheet_id,
            student_name=student_name,
            completion_time=completion_time,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            needs_review=needs_review,
            created_at=datetime.now()
        )

        self.db.add(grading_result)
        self.db.flush()  # ID 생성을 위해 flush

        # 문제별 채점 결과 저장
        for qr in question_results:
            question_result = QuestionResult(
                grading_result_id=result_id,
                question_id=qr["question_id"],
                question_type=qr["question_type"],
                student_answer=qr["student_answer"],
                correct_answer=qr["correct_answer"],
                score=qr["score"],
                max_score=qr["max_score"],
                is_correct=qr["is_correct"],
                grading_method=qr["grading_method"],
                ai_feedback=qr.get("ai_feedback"),
                needs_review=qr.get("needs_review", False),
                created_at=datetime.now()
            )
            self.db.add(question_result)

        self.db.commit()
        return grading_result

    def get_grading_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """채점 결과를 조회합니다."""
        grading_result = self.db.query(GradingResult).filter(
            GradingResult.result_id == result_id
        ).first()

        if not grading_result:
            return None

        question_results = self.db.query(QuestionResult).filter(
            QuestionResult.grading_result_id == result_id
        ).all()

        return {
            "result_id": grading_result.result_id,
            "student_name": grading_result.student_name,
            "worksheet_id": grading_result.worksheet_id,
            "total_score": grading_result.total_score,
            "max_score": grading_result.max_score,
            "percentage": grading_result.percentage,
            "completion_time": grading_result.completion_time,
            "needs_review": grading_result.needs_review,
            "is_reviewed": grading_result.is_reviewed,
            "created_at": grading_result.created_at,
            "question_results": [
                {
                    "question_id": qr.question_id,
                    "question_type": qr.question_type,
                    "student_answer": qr.student_answer,
                    "correct_answer": qr.correct_answer,
                    "score": qr.score,
                    "max_score": qr.max_score,
                    "is_correct": qr.is_correct,
                    "grading_method": qr.grading_method,
                    "ai_feedback": qr.ai_feedback,
                    "needs_review": qr.needs_review,
                    "is_reviewed": qr.is_reviewed
                }
                for qr in question_results
            ]
        }