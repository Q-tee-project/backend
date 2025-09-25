"""
문제 재생성 서비스
"""
import json
from typing import Dict, Any, Optional, Tuple, List
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

    def regenerate_multiple_questions_from_data(
        self,
        questions_data: List[Dict[str, Any]],
        passage_data: Optional[Dict[str, Any]],
        request: QuestionRegenerationRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[List[str]], Optional[List[Dict[str, Any]]]]:
        """
        여러 문제를 재생성합니다. (DB 저장 없음)
        """
        if not questions_data:
            return False, "재생성할 문제 데이터가 없습니다.", None, None, None

        try:
            # 메인 문제 재생성 (첫 번째 문제)
            main_question = questions_data[0]
            success, message, regenerated_question, regenerated_passage = self.regenerate_question_from_data(
                main_question, passage_data, request
            )

            if not success:
                return False, f"메인 문제 재생성 실패: {message}", None, None, None

            # 결과 구성 - 새로운 형식에 맞게
            regenerated_data = {
                "regenerated_passage": regenerated_passage,
                "regenerated_questions": [regenerated_question]  # 메인 문제를 배열에 포함
            }

            return True, "문제가 성공적으로 재생성되었습니다.", regenerated_data, None, None

        except Exception as e:
            return False, f"재생성 중 오류가 발생했습니다: {str(e)}", None, None, None

    def regenerate_question_from_data(
        self,
        question_data: Dict[str, Any],
        passage_data: Optional[Dict[str, Any]],
        request: QuestionRegenerationRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        전달받은 데이터로 문제를 재생성합니다. (DB 저장 없음)

        Args:
            question_data: 원본 문제 데이터
            passage_data: 원본 지문 데이터 (선택적)
            request: 재생성 요청

        Returns:
            (success, message, regenerated_question, regenerated_passage)
        """
        try:
            # 1. 최종 조건 결정
            final_conditions = self._determine_final_conditions_from_data(question_data, request)

            # 2. AI 프롬프트 데이터 준비
            prompt_data = RegenerationPromptData(
                original_question=question_data,
                original_passage=passage_data,
                user_feedback=request.feedback,
                worksheet_context=request.worksheet_context,
                final_question_type=final_conditions["question_type"],
                final_subject=final_conditions["subject"],
                final_detail_type=final_conditions["detail_type"],
                final_difficulty=final_conditions["difficulty"],
                keep_passage=request.keep_passage,
                additional_requirements=request.additional_requirements
            )

            # 3. AI로 문제 재생성
            regenerated_data = self._generate_with_ai(prompt_data)
            if not regenerated_data:
                return False, "AI 문제 생성에 실패했습니다.", None, None

            # 4. 재생성된 데이터 반환 (DB 저장 없음)
            regenerated_question = regenerated_data.get("question", {})
            regenerated_passage = regenerated_data.get("passage") if passage_data else None

            # 5. question_id 포함
            if "question_id" in question_data:
                regenerated_question["question_id"] = question_data["question_id"]

            # 6. 최종 조건 적용
            regenerated_question.update({
                "question_type": final_conditions["question_type"].value if hasattr(final_conditions["question_type"], 'value') else final_conditions["question_type"],
                "question_subject": final_conditions["subject"].value if hasattr(final_conditions["subject"], 'value') else final_conditions["subject"],
                "question_detail_type": final_conditions["detail_type"],
                "question_difficulty": final_conditions["difficulty"].value if hasattr(final_conditions["difficulty"], 'value') else final_conditions["difficulty"]
            })

            return True, "문제가 성공적으로 재생성되었습니다.", regenerated_question, regenerated_passage

        except Exception as e:
            return False, f"재생성 중 오류가 발생했습니다: {str(e)}", None, None

    def regenerate_question(
        self,
        db: Session,
        worksheet_id: int,
        question_id: int,
        request: QuestionRegenerationRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        DB에서 문제를 조회하여 재생성하고 저장합니다.

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

            # 3. 데이터 기반 재생성 호출
            question_data = self._question_to_dict(original_question)
            passage_data = self._passage_to_dict(original_passage) if original_passage else None

            success, message, regenerated_question, regenerated_passage = self.regenerate_question_from_data(
                question_data, passage_data, request
            )

            if not success:
                return False, message, None, None

            # 4. 데이터베이스 업데이트
            success = self._update_question_in_db(db, original_question, {"question": regenerated_question}, self._determine_final_conditions(original_question, request))
            if not success:
                return False, "데이터베이스 업데이트에 실패했습니다.", None, None

            # 5. 지문도 재생성된 경우 업데이트
            if regenerated_passage and original_passage:
                success = self._update_passage_in_db(db, original_passage, regenerated_passage)

            # 6. 연계된 문제들도 재생성하는 경우
            regenerated_related_questions = []
            if request.regenerate_related_questions and original_passage and not request.keep_passage:
                regenerated_related_questions = self._regenerate_related_questions(
                    db, worksheet_id, original_passage, regenerated_passage, request
                )

            db.commit()

            result_data = {
                "regenerated_question": self._question_to_dict(original_question),
                "regenerated_passage": self._passage_to_dict(original_passage) if original_passage else None,
                "regenerated_related_questions": regenerated_related_questions
            }

            return True, "문제가 성공적으로 재생성되었습니다.", result_data, None

        except Exception as e:
            db.rollback()
            return False, f"재생성 중 오류가 발생했습니다: {str(e)}", None, None

    def _determine_final_conditions_from_data(
        self,
        question_data: Dict[str, Any],
        request: QuestionRegenerationRequest
    ) -> Dict[str, Any]:
        """데이터에서 최종 적용될 조건들을 결정합니다."""
        return {
            "question_type": request.target_question_type if not request.keep_question_type
                           else question_data.get("question_type", "객관식"),
            "subject": request.target_subject if not request.keep_subject
                      else question_data.get("question_subject", "독해"),
            "detail_type": request.target_detail_type if not request.keep_detail_type
                          else question_data.get("question_detail_type", ""),
            "difficulty": request.target_difficulty if not request.keep_difficulty
                         else question_data.get("question_difficulty", "중")
        }

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

        prompt = f"""# 역할 설정
당신은 **전문적인 영어 교육 문제 개발자**입니다.
- 15년 이상의 영어 교육 경험을 가진 전문가
- 학생 수준에 맞는 문제 설계 전문가
- 교육과정과 평가 기준에 정통한 교육학 박사

# 임무
기존 영어 문제를 사용자의 피드백과 요구사항에 따라 **체계적이고 교육적으로 개선된 문제로 재생성**하세요.

## 기존 문제 정보
{json.dumps(data.original_question, ensure_ascii=False, indent=2)}

## 사용자 피드백
{data.user_feedback}

## 문제지 컨텍스트
- 학교급: {data.worksheet_context.school_level}
- 학년: {data.worksheet_context.grade}학년
- 문제지 유형: {data.worksheet_context.worksheet_type}

## 재생성 조건 (필수 준수)
- 문제 유형: {data.final_question_type}
- 문제 영역: {data.final_subject}
- 세부 영역: {data.final_detail_type}
- 난이도: {data.final_difficulty}
- 지문 유지: {"예" if data.keep_passage else "아니오"}

"""

        if data.original_passage:
            prompt += f"""
## 기존 지문 정보
{json.dumps(data.original_passage, ensure_ascii=False, indent=2)}
"""

        if data.additional_requirements:
            prompt += f"""
## 추가 요구사항
{data.additional_requirements}
"""

        # 응답 형식 (통일된 형식)
        if data.original_passage:
            prompt += """
# ⚠️ 응답 형식 - 절대 준수 사항

**문제와 지문을 재생성합니다. 반드시 다음 JSON 형식으로만 응답하세요.**

```json
{
  "question": {
    "question_text": "재생성된 문제 텍스트",
    "question_choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": 0,
    "example_content": "예문 내용",
    "example_original_content": "예문 원본",
    "example_korean_translation": "예문 한글 번역",
    "explanation": "해설",
    "learning_point": "학습 포인트"
  },
  "passage": {
    "passage_type": "article",
    "passage_content": {
      "content": [
        {"type": "title", "value": "제목"},
        {"type": "paragraph", "value": "첫 번째 문단 (빈칸 [ A ] 포함 가능)"},
        {"type": "paragraph", "value": "두 번째 문단"}
      ]
    },
    "original_content": {
      "content": [
        {"type": "title", "value": "완전한 제목"},
        {"type": "paragraph", "value": "완전한 첫 번째 문단"},
        {"type": "paragraph", "value": "완전한 두 번째 문단"}
      ]
    },
    "korean_translation": {
      "content": [
        {"type": "title", "value": "한글 제목"},
        {"type": "paragraph", "value": "첫 번째 문단 한글 번역"},
        {"type": "paragraph", "value": "두 번째 문단 한글 번역"}
      ]
    }
  }
}
```
"""
        else:
            prompt += """
# ⚠️ 응답 형식 - 절대 준수 사항

**문제만 재생성합니다. 반드시 다음 JSON 형식으로만 응답하세요.**

```json
{
  "question": {
    "question_text": "재생성된 문제 텍스트",
    "question_choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "1" or "2" or "3" or "4",
    "example_content": "예문 내용",
    "example_original_content": "예문 원본",
    "example_korean_translation": "예문 한글 번역",
    "explanation": "해설",
    "learning_point": "학습 포인트"
  }
}
```
"""

        prompt += """
## 🔥 절대 준수 규칙
1. **JSON 형식만 출력** - 설명이나 추가 텍스트 절대 금지
2. **모든 필드 필수 포함** - 누락된 필드가 있으면 시스템 오류 발생
3. **객관식이 아닌 경우** - question_choices는 빈 배열 []로 설정
4. **따옴표와 쉼표** - JSON 문법 엄격히 준수
5. **중괄호 { } 정확히 매칭** - 문법 오류 시 파싱 실패

## 📋 지문 JSON 구조화 규칙 (지문 재생성 시)

**지문 유형을 정확히 식별하고 해당 형식에 맞게 JSON을 구성하세요:**

### 1. article (기사/에세이/스토리)
```json
"passage": {
  "passage_type": "article",
  "passage_content": {
    "content": [
      {"type": "title", "value": "제목"},
      {"type": "paragraph", "value": "첫 번째 문단 내용 (빈칸 [ A ] 포함 가능)"},
      {"type": "paragraph", "value": "두 번째 문단 내용"}
    ]
  },
  "original_content": {
    "content": [
      {"type": "title", "value": "제목"},
      {"type": "paragraph", "value": "완전한 첫 번째 문단 내용"},
      {"type": "paragraph", "value": "완전한 두 번째 문단 내용"}
    ]
  },
  "korean_translation": {
    "content": [
      {"type": "title", "value": "한글 제목"},
      {"type": "paragraph", "value": "첫 번째 문단 한글 번역"},
      {"type": "paragraph", "value": "두 번째 문단 한글 번역"}
    ]
  }
}
```

### 2. correspondence (편지/이메일/공문)
```json
"passage": {
  "passage_type": "correspondence",
  "passage_content": {
    "metadata": {
      "sender": "보내는 사람",
      "recipient": "받는 사람",
      "subject": "제목",
      "date": "날짜"
    },
    "content": [
      {"type": "paragraph", "value": "편지 내용 (빈칸 [ B ] 포함 가능)"}
    ]
  },
  "original_content": {
    "metadata": {
      "sender": "보내는 사람",
      "recipient": "받는 사람",
      "subject": "제목",
      "date": "날짜"
    },
    "content": [
      {"type": "paragraph", "value": "완전한 편지 내용"}
    ]
  },
  "korean_translation": {
    "metadata": {
      "sender": "한글 보내는 사람",
      "recipient": "한글 받는 사람",
      "subject": "한글 제목",
      "date": "날짜"
    },
    "content": [
      {"type": "paragraph", "value": "편지 내용 한글 번역"}
    ]
  }
}
```

### 3. dialogue (대화)
```json
"passage": {
  "passage_type": "dialogue",
  "passage_content": {
    "metadata": {
      "participants": ["화자1", "화자2"]
    },
    "content": [
      {"speaker": "화자1", "line": "대화 내용1"},
      {"speaker": "화자2", "line": "대화 내용2 (빈칸 [ C ] 포함 가능)"}
    ]
  },
  "original_content": {
    "metadata": {
      "participants": ["화자1", "화자2"]
    },
    "content": [
      {"speaker": "화자1", "line": "완전한 대화 내용1"},
      {"speaker": "화자2", "line": "완전한 대화 내용2"}
    ]
  },
  "korean_translation": {
    "metadata": {
      "participants": ["한글 화자1", "한글 화자2"]
    },
    "content": [
      {"speaker": "한글 화자1", "line": "대화 내용1 한글 번역"},
      {"speaker": "한글 화자2", "line": "대화 내용2 한글 번역"}
    ]
  }
}
```

### 4. informational (안내문/포스터)
```json
"passage": {
  "passage_type": "informational",
  "passage_content": {
    "content": [
      {"type": "title", "value": "제목"},
      {"type": "paragraph", "value": "설명 문단"},
      {"type": "list", "items": ["항목1", "항목2", "항목3"]},
      {"type": "key_value", "pairs": [
        {"key": "날짜", "value": "2025-01-01"},
        {"key": "장소", "value": "[ D ]"}
      ]}
    ]
  },
  "original_content": {
    "content": [
      {"type": "title", "value": "제목"},
      {"type": "paragraph", "value": "설명 문단"},
      {"type": "list", "items": ["항목1", "항목2", "항목3"]},
      {"type": "key_value", "pairs": [
        {"key": "날짜", "value": "2025-01-01"},
        {"key": "장소", "value": "완전한 장소명"}
      ]}
    ]
  },
  "korean_translation": {
    "content": [
      {"type": "title", "value": "한글 제목"},
      {"type": "paragraph", "value": "설명 문단 한글 번역"},
      {"type": "list", "items": ["한글 항목1", "한글 항목2", "한글 항목3"]},
      {"type": "key_value", "pairs": [
        {"key": "날짜", "value": "2025년 1월 1일"},
        {"key": "장소", "value": "한글 장소명"}
      ]}
    ]
  }
}
```

### 5. review (리뷰/후기)
```json
"passage": {
  "passage_type": "review",
  "passage_content": {
    "metadata": {
      "rating": 5,
      "product_name": "제품명",
      "reviewer": "리뷰어",
      "date": "2025-01-01"
    },
    "content": [
      {"type": "paragraph", "value": "리뷰 내용 (빈칸 [ E ] 포함 가능)"}
    ]
  },
  "original_content": {
    "metadata": {
      "rating": 5,
      "product_name": "제품명",
      "reviewer": "리뷰어",
      "date": "2025-01-01"
    },
    "content": [
      {"type": "paragraph", "value": "완전한 리뷰 내용"}
    ]
  },
  "korean_translation": {
    "metadata": {
      "rating": 5,
      "product_name": "한글 제품명",
      "reviewer": "한글 리뷰어",
      "date": "2025-01-01"
    },
    "content": [
      {"type": "paragraph", "value": "리뷰 내용 한글 번역"}
    ]
  }
}
```

**⚠️ 중요: 지문 내용을 보고 가장 적합한 유형을 선택하고, 해당 형식을 정확히 따르세요!**"""

        prompt += """
## 🔥 절대 준수 규칙
1. **JSON 형식만 출력** - 설명이나 추가 텍스트 절대 금지
2. **모든 필드 필수 포함** - 누락된 필드가 있으면 시스템 오류 발생
3. **객관식이 아닌 경우** - question_choices는 빈 배열 []로 설정
4. **따옴표와 쉼표** - JSON 문법 엄격히 준수
5. **중괄호 { } 정확히 매칭** - 문법 오류 시 파싱 실패
6. **지문 유형 정확성** - 위에서 명시한 passage_type에 맞는 정확한 구조 사용

## 📚 교육적 품질 기준
1. **학년 수준 적합성** - 어휘와 문법 난이도 정확히 맞춤
2. **피드백 완전 반영** - 사용자 요구사항 100% 적용
3. **교육 목표 명확** - 학습 포인트와 해설의 교육적 가치 극대화
4. **문제 유형 정확성** - 지정된 조건과 완벽 일치

**⚠️ 경고: JSON 형식을 벗어나거나 필드가 누락되거나 지문 구조가 틀리면 렌더링 오류가 발생합니다!**
"""

        return prompt

    def _regenerate_related_questions(
        self,
        db: Session,
        worksheet_id: int,
        original_passage: 'Passage',
        regenerated_passage_data: Dict[str, Any],
        request: QuestionRegenerationRequest
    ) -> List[Dict[str, Any]]:
        """지문과 연계된 다른 문제들을 재생성합니다."""
        try:
            regenerated_questions = []

            # 연계된 문제들 조회
            if hasattr(original_passage, 'related_questions') and original_passage.related_questions:
                related_question_ids = original_passage.related_questions

                for q_id in related_question_ids:
                    # 현재 재생성 중인 문제는 제외
                    if str(q_id) == str(request.current_question_id if hasattr(request, 'current_question_id') else ''):
                        continue

                    related_question = db.query(Question).filter(
                        Question.worksheet_id == worksheet_id,
                        Question.question_id == q_id
                    ).first()

                    if related_question:
                        # 연계 문제용 재생성 요청 생성
                        related_request = QuestionRegenerationRequest(
                            feedback=f"지문이 변경되어 연계된 문제를 자동 재생성합니다: {request.feedback}",
                            worksheet_context=request.worksheet_context,
                            current_question_type=related_question.question_type,
                            current_subject=related_question.question_subject,
                            current_detail_type=related_question.question_detail_type,
                            current_difficulty=related_question.question_difficulty,
                            keep_passage=True,  # 지문은 이미 변경됨
                            regenerate_related_questions=False,  # 무한 루프 방지
                            additional_requirements="새로운 지문 내용에 맞게 문제를 조정해주세요."
                        )

                        # 개별 문제 재생성
                        question_data = self._question_to_dict(related_question)
                        passage_data = regenerated_passage_data

                        success, message, regenerated_q, _ = self.regenerate_question_from_data(
                            question_data, passage_data, related_request
                        )

                        if success and regenerated_q:
                            # DB 업데이트
                            update_success = self._update_question_in_db(
                                db, related_question, {"question": regenerated_q},
                                self._determine_final_conditions(related_question, related_request)
                            )

                            if update_success:
                                regenerated_questions.append(self._question_to_dict(related_question))

            return regenerated_questions

        except Exception as e:
            print(f"연계 문제 재생성 중 오류: {e}")
            return []

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