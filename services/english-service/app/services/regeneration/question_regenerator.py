"""
문제 재생성 서비스
"""
import json
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Question, Passage, Worksheet
from app.schemas.regeneration import (
    QuestionRegenerationRequest,
    RegenerationPromptData,
    QuestionType,
    QuestionSubject,
    Difficulty
)
from app.core.config import get_settings

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

settings = get_settings()


class QuestionRegenerator:
    """문제 재생성 클래스"""

    def __init__(self):
        if GEMINI_AVAILABLE and settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_flash_model)
        else:
            self.model = None

    def regenerate_question(
        self,
        db: Session,
        worksheet_id: str,
        question_id: int,
        request: QuestionRegenerationRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        문제를 재생성합니다.

        Returns:
            (success, message, regenerated_question, regenerated_passage)
        """
        try:
            # 1. 기존 문제 조회
            original_question = db.query(Question).filter(
                Question.worksheet_id == worksheet_id,
                Question.question_id == question_id
            ).first()

            if not original_question:
                return False, "문제를 찾을 수 없습니다.", None, None

            # 2. 지문 정보 조회 (있는 경우)
            original_passage = None
            if original_question.passage_id:
                original_passage = db.query(Passage).filter(
                    Passage.worksheet_id == worksheet_id,
                    Passage.passage_id == original_question.passage_id
                ).first()

            # 3. 최종 조건 결정
            final_conditions = self._determine_final_conditions(original_question, request)

            # 4. AI 프롬프트 데이터 준비
            prompt_data = RegenerationPromptData(
                original_question=self._question_to_dict(original_question),
                original_passage=self._passage_to_dict(original_passage) if original_passage else None,
                user_feedback=request.feedback,
                worksheet_context=request.worksheet_context,
                final_question_type=final_conditions["question_type"],
                final_subject=final_conditions["subject"],
                final_detail_type=final_conditions["detail_type"],
                final_difficulty=final_conditions["difficulty"],
                keep_passage=request.keep_passage,
                additional_requirements=request.additional_requirements
            )

            # 5. AI로 문제 재생성
            regenerated_data = self._generate_with_ai(prompt_data)
            if not regenerated_data:
                return False, "AI 문제 생성에 실패했습니다.", None, None

            # 6. 데이터베이스 업데이트
            success = self._update_question_in_db(db, original_question, regenerated_data, final_conditions)
            if not success:
                return False, "데이터베이스 업데이트에 실패했습니다.", None, None

            # 7. 지문도 재생성된 경우 업데이트
            regenerated_passage_data = None
            if not request.keep_passage and original_passage and "passage" in regenerated_data:
                success = self._update_passage_in_db(db, original_passage, regenerated_data["passage"])
                if success:
                    regenerated_passage_data = self._passage_to_dict(original_passage)

            db.commit()

            return True, "문제가 성공적으로 재생성되었습니다.", \
                   self._question_to_dict(original_question), regenerated_passage_data

        except Exception as e:
            db.rollback()
            return False, f"재생성 중 오류가 발생했습니다: {str(e)}", None, None

    def _determine_final_conditions(
        self,
        original_question: Question,
        request: QuestionRegenerationRequest
    ) -> Dict[str, Any]:
        """최종 적용될 조건들을 결정합니다."""
        return {
            "question_type": request.target_question_type if not request.keep_question_type
                           else QuestionType(original_question.question_type),
            "subject": request.target_subject if not request.keep_subject
                      else QuestionSubject(original_question.question_subject),
            "detail_type": request.target_detail_type if not request.keep_detail_type
                          else original_question.question_detail_type,
            "difficulty": request.target_difficulty if not request.keep_difficulty
                         else Difficulty(original_question.question_difficulty)
        }

    def _generate_with_ai(self, prompt_data: RegenerationPromptData) -> Optional[Dict[str, Any]]:
        """AI를 사용하여 문제를 재생성합니다."""
        if not self.model:
            return None

        try:
            prompt = self._build_regeneration_prompt(prompt_data)
            response = self.model.generate_content(prompt)

            # JSON 파싱
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]

            return json.loads(response_text)

        except Exception as e:
            print(f"AI 생성 중 오류: {e}")
            return None

    def _build_regeneration_prompt(self, data: RegenerationPromptData) -> str:
        """재생성을 위한 AI 프롬프트를 구성합니다."""

        prompt = f"""영어 문제 재생성 요청입니다.

## 기존 문제 정보
{json.dumps(data.original_question, ensure_ascii=False, indent=2)}

## 사용자 피드백
{data.user_feedback}

## 문제지 컨텍스트
- 학교급: {data.worksheet_context.school_level}
- 학년: {data.worksheet_context.grade}학년
- 문제지 유형: {data.worksheet_context.worksheet_type}

## 재생성 조건
- 문제 유형: {data.final_question_type}
- 문제 영역: {data.final_subject}
- 세부 영역: {data.final_detail_type}
- 난이도: {data.final_difficulty}
- 지문 유지: {"예" if data.keep_passage else "아니오"}

"""

        if data.original_passage and not data.keep_passage:
            prompt += f"""
## 기존 지문 정보
{json.dumps(data.original_passage, ensure_ascii=False, indent=2)}
"""

        if data.additional_requirements:
            prompt += f"""
## 추가 요구사항
{data.additional_requirements}
"""

        prompt += """
## 응답 형식
다음 JSON 형식으로 응답해주세요:

```json
{
  "question": {
    "question_text": "재생성된 문제 텍스트",
    "question_choices": ["선택지1", "선택지2", "선택지3", "선택지4"], // 객관식인 경우만
    "correct_answer": "정답",
    "example_content": "예문 내용",
    "example_original_content": "예문 원본",
    "example_korean_translation": "예문 한글 번역",
    "explanation": "해설",
    "learning_point": "학습 포인트"
  }
  // 지문도 재생성하는 경우에만 추가
  "passage": {
    "passage_content": {...},
    "original_content": {...},
    "korean_translation": {...}
  }
}
```

중요한 점:
1. 기존 문제의 구조와 형식을 유지하세요
2. 사용자 피드백을 반영하여 개선하세요
3. 지정된 학년 수준에 맞는 어휘와 문법을 사용하세요
4. 문제 유형과 영역 조건을 정확히 따르세요
"""

        return prompt

    def _update_question_in_db(
        self,
        db: Session,
        question: Question,
        regenerated_data: Dict[str, Any],
        final_conditions: Dict[str, Any]
    ) -> bool:
        """데이터베이스의 문제를 업데이트합니다."""
        try:
            question_data = regenerated_data.get("question", {})

            # 기본 필드 업데이트
            question.question_text = question_data.get("question_text", question.question_text)
            question.question_type = final_conditions["question_type"]
            question.question_subject = final_conditions["subject"]
            question.question_detail_type = final_conditions["detail_type"]
            question.question_difficulty = final_conditions["difficulty"]

            # 선택적 필드 업데이트
            if "question_choices" in question_data:
                question.question_choices = question_data["question_choices"]
            if "correct_answer" in question_data:
                question.correct_answer = question_data["correct_answer"]
            if "example_content" in question_data:
                question.example_content = question_data["example_content"]
            if "example_original_content" in question_data:
                question.example_original_content = question_data["example_original_content"]
            if "example_korean_translation" in question_data:
                question.example_korean_translation = question_data["example_korean_translation"]
            if "explanation" in question_data:
                question.explanation = question_data["explanation"]
            if "learning_point" in question_data:
                question.learning_point = question_data["learning_point"]

            return True

        except Exception as e:
            print(f"문제 업데이트 중 오류: {e}")
            return False

    def _update_passage_in_db(
        self,
        db: Session,
        passage: Passage,
        passage_data: Dict[str, Any]
    ) -> bool:
        """데이터베이스의 지문을 업데이트합니다."""
        try:
            if "passage_content" in passage_data:
                passage.passage_content = passage_data["passage_content"]
            if "original_content" in passage_data:
                passage.original_content = passage_data["original_content"]
            if "korean_translation" in passage_data:
                passage.korean_translation = passage_data["korean_translation"]

            return True

        except Exception as e:
            print(f"지문 업데이트 중 오류: {e}")
            return False

    def _question_to_dict(self, question: Question) -> Dict[str, Any]:
        """Question 객체를 딕셔너리로 변환합니다."""
        return {
            "id": question.id,
            "worksheet_id": question.worksheet_id,
            "question_id": question.question_id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "question_subject": question.question_subject,
            "question_detail_type": question.question_detail_type,
            "question_difficulty": question.question_difficulty,
            "question_choices": question.question_choices,
            "passage_id": question.passage_id,
            "correct_answer": question.correct_answer,
            "example_content": question.example_content,
            "example_original_content": question.example_original_content,
            "example_korean_translation": question.example_korean_translation,
            "explanation": question.explanation,
            "learning_point": question.learning_point,
            "created_at": question.created_at.isoformat() if question.created_at else None
        }

    def _passage_to_dict(self, passage: Optional[Passage]) -> Optional[Dict[str, Any]]:
        """Passage 객체를 딕셔너리로 변환합니다."""
        if not passage:
            return None

        return {
            "id": passage.id,
            "worksheet_id": passage.worksheet_id,
            "passage_id": passage.passage_id,
            "passage_type": passage.passage_type,
            "passage_content": passage.passage_content,
            "original_content": passage.original_content,
            "korean_translation": passage.korean_translation,
            "related_questions": passage.related_questions,
            "created_at": passage.created_at.isoformat() if passage.created_at else None
        }