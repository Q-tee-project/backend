"""
문제 수정 서비스
문제의 모든 필드를 수정할 수 있는 서비스
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.worksheet import Question


class QuestionService:
    """문제 수정을 담당하는 서비스 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def update_question(self, worksheet_id: str, question_id: int, update_data: Dict[str, Any]) -> Question:
        """문제 정보를 업데이트합니다"""
        question = self._get_question_or_404(worksheet_id, question_id)

        # 수정 가능한 필드들
        updatable_fields = [
            "question_text", "question_type", "question_subject",
            "question_difficulty", "question_detail_type", "question_choices",
            "passage_id", "correct_answer", "example_content",
            "example_original_content", "example_korean_translation",
            "explanation", "learning_point"
        ]

        for field in updatable_fields:
            if field in update_data:
                new_value = update_data.get(field)

                # 필드별 유효성 검사
                self._validate_field(field, new_value)

                setattr(question, field, new_value)

        self.db.commit()
        self.db.refresh(question)
        return question

    def _get_question_or_404(self, worksheet_id: str, question_id: int) -> Question:
        """문제를 조회하거나 404 에러 발생"""
        question = self.db.query(Question).filter(
            Question.worksheet_id == worksheet_id,
            Question.question_id == question_id
        ).first()

        if not question:
            raise ValueError("문제를 찾을 수 없습니다.")

        return question

    def _validate_field(self, field: str, value: Any) -> None:
        """필드별 유효성 검사"""
        if value is None:
            return

        # question_type 검증
        if field == "question_type":
            valid_types = ["객관식", "단답형", "서술형"]
            if value not in valid_types:
                raise ValueError(f"문제 유형은 {valid_types} 중 하나여야 합니다.")

        # question_subject 검증
        elif field == "question_subject":
            valid_subjects = ["독해", "문법", "어휘"]
            if value not in valid_subjects:
                raise ValueError(f"문제 영역은 {valid_subjects} 중 하나여야 합니다.")

        # question_difficulty 검증
        elif field == "question_difficulty":
            valid_difficulties = ["상", "중", "하"]
            if value not in valid_difficulties:
                raise ValueError(f"문제 난이도는 {valid_difficulties} 중 하나여야 합니다.")

        # question_choices 검증 (객관식인 경우)
        elif field == "question_choices":
            if value is not None and not isinstance(value, list):
                raise ValueError("선택지는 배열 형태여야 합니다.")

        # passage_id 검증
        elif field == "passage_id":
            if value is not None and not isinstance(value, int):
                raise ValueError("지문 ID는 숫자여야 합니다.")

        # 텍스트 필드 검증
        elif field in ["question_text", "example_content", "explanation", "learning_point"]:
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{field}는 문자열이어야 합니다.")

        # correct_answer 검증은 question_type에 따라 달라질 수 있으므로 별도 처리 가능