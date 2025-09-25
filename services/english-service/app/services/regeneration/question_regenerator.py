"""
영어 문제 재생성 서비스
"""
import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from app.schemas.regeneration import (
    EnglishQuestion,
    EnglishPassage,
    EnglishRegenerationRequest
)
from app.core.config import get_settings

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

settings = get_settings()


class QuestionRegenerator:
    """영어 문제 재생성 클래스"""

    def __init__(self):
        if GEMINI_AVAILABLE and settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_flash_model)
        else:
            self.model = None

    def regenerate_from_data(
        self,
        questions: List[EnglishQuestion],
        passage: Optional[EnglishPassage],
        form_data: EnglishRegenerationRequest
    ) -> Tuple[bool, str, Optional[List[EnglishQuestion]], Optional[EnglishPassage]]:
        """
        프론트엔드에서 전달받은 데이터로 문제를 재생성합니다.

        Args:
            questions: 재생성할 문제들
            passage: 연관 지문 (있을 경우)
            form_data: 사용자 요청사항

        Returns:
            (성공여부, 메시지, 재생성된 문제들, 재생성된 지문)
        """
        if not questions:
            return False, "재생성할 문제가 없습니다.", None, None

        try:
            # AI 모델이 없으면 실패
            if not self.model:
                return False, "AI 모델을 사용할 수 없습니다.", None, None

            # 프롬프트 생성
            prompt = self._create_regeneration_prompt(questions, passage, form_data)

            print(f"\n🤖 재생성 프롬프트:")
            print("="*100)
            print(prompt)
            print("="*100)

            # AI 호출
            response = self.model.generate_content(prompt)

            if not response.text:
                return False, "AI 응답이 비어있습니다.", None, None

            print(f"\n📝 AI 응답:")
            print("="*100)
            print(response.text)
            print("="*100)

            # 응답 파싱
            regenerated_data = self._parse_ai_response(response.text)

            if not regenerated_data:
                return False, "AI 응답 파싱에 실패했습니다.", None, None

            # 결과 추출
            regenerated_questions = regenerated_data.get("questions", [])
            regenerated_passage = regenerated_data.get("passage")

            # EnglishQuestion 객체로 변환
            parsed_questions = []
            for q_data in regenerated_questions:
                try:
                    question = EnglishQuestion(**q_data)
                    parsed_questions.append(question)
                except Exception as e:
                    print(f"문제 파싱 오류: {e}")
                    continue

            # EnglishPassage 객체로 변환 (있을 경우)
            parsed_passage = None
            if regenerated_passage:
                try:
                    parsed_passage = EnglishPassage(**regenerated_passage)
                except Exception as e:
                    print(f"지문 파싱 오류: {e}")

            if not parsed_questions:
                return False, "재생성된 문제를 파싱할 수 없습니다.", None, None

            return True, "문제가 성공적으로 재생성되었습니다.", parsed_questions, parsed_passage

        except Exception as e:
            print(f"재생성 오류: {e}")
            return False, f"재생성 중 오류가 발생했습니다: {str(e)}", None, None

    def _create_regeneration_prompt(
        self,
        questions: List[EnglishQuestion],
        passage: Optional[EnglishPassage],
        form_data: EnglishRegenerationRequest
    ) -> str:
        """재생성 프롬프트를 생성합니다."""

        # 기본 지시사항
        prompt = f"""당신은 영어 문제 재생성 전문가입니다.

사용자 요청사항: {form_data.feedback}

"""

        # 워크시트 컨텍스트가 있으면 추가
        if form_data.worksheet_context and (form_data.worksheet_context.school_level or form_data.worksheet_context.grade):
            prompt += "문제지 컨텍스트:\n"
            if form_data.worksheet_context.school_level:
                prompt += f"- 학교급: {form_data.worksheet_context.school_level}\n"
            if form_data.worksheet_context.grade:
                prompt += f"- 학년: {form_data.worksheet_context.grade}학년\n"
            prompt += "\n"

        prompt += """아래 조건에 따라 문제를 재생성해주세요:

"""

        # 지문 재생성 여부
        if passage and form_data.regenerate_passage:
            prompt += f"""
## 지문 재생성 요청
기존 지문을 수정해서 새로운 지문을 만들어주세요.

기존 지문:
```json
{json.dumps(passage.dict(), ensure_ascii=False, indent=2)}
```

"""

        # 문제들
        prompt += f"""
## 재생성할 문제들:
"""
        for i, question in enumerate(questions):
            prompt += f"""
### 문제 {i+1}:
```json
{json.dumps(question.dict(), ensure_ascii=False, indent=2)}
```
"""

        # 추가 지시사항
        if form_data.new_difficulty:
            prompt += f"\n- 난이도를 '{form_data.new_difficulty}'로 조정해주세요."

        if form_data.additional_instructions:
            prompt += f"\n- 추가 요청: {form_data.additional_instructions}"

        # 응답 형식 지정
        prompt += f"""

## 응답 형식
다음 JSON 형식으로 응답해주세요:

```json
{{
  "questions": [
    {{
      "question_id": 문제ID,
      "question_text": "재생성된 문제 텍스트",
      "question_type": "객관식|단답형|서술형",
      "question_subject": "문제 영역",
      "question_difficulty": "상|중|하",
      "question_detail_type": "세부 유형",
      "question_passage_id": 지문ID또는null,
      "example_content": "예문 내용",
      "example_original_content": "원문 예문",
      "example_korean_translation": "한글 번역",
      "question_choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
      "correct_answer": 정답인덱스또는텍스트,
      "explanation": "해설",
      "learning_point": "학습 포인트"
    }}
  ]"""

        if passage and form_data.regenerate_passage:
            prompt += f""",
  "passage": {{
    "passage_id": {passage.passage_id},
    "passage_type": "article|correspondence|dialogue|informational|review",
    "passage_content": {{내용구조}},
    "original_content": {{원문구조}},
    "korean_translation": {{번역구조}},
    "related_questions": [문제ID배열]
  }}"""

        prompt += """
}
```

# 문제에 사용될 지문과 예문의 정의
- 지문은 120~150단어 이상의 긴 글을 의미 난이도와 상관없이 길이를 준수하여 생성
- 지문에는 2개 이상 3개 이하의 문제를 연계하여 출제
- 예문은 40단어 이하의 짧은 글을 의미(1~3줄) 난이도와 상관없이 길이를 준수하여 생성
- 지문은 반드시 유형별 json형식을 참고하여 생성
- 예문의 소재는 글의 소재를 참고하여 생성
- 지문 글의 유형은 글의 소재, 영역별 문제 출제 유형을 고려하여 자유롭게 선정해서 사용

# 문제 질문과 예문 분리 규칙 (절대 위반 금지)

## 핵심 원칙
- **example_content에는 절대 지시문을 포함하지 마세요!**
- **example_content는 순수한 영어 예문, 보기, 문제만 포함해야 합니다!**
- **모든 지시문과 한국어 설명은 question_text에만 들어가야 합니다!**

## 세부 규칙
- **문제의 질문(question_text)**: 순수한 한국어 지시문만 (예: "다음과 같이 소유격을 사용하여 쓰시오")
- **예문 내용(example_content)**: 순수한 영어 예문만 (예: "<보기> The book of Tom → Tom's book\\n<문제> The car of my father")
- **영어 문장, 대화문, 긴 예시는 반드시 별도의 예문(examples)으로 분리하세요**
- **예문이 없이 문제 질문과 선택지만 필요한 문제는 예문을 생성하지 않고 선택지에 내용이 포함되어야 합니다.**

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

**⚠️ 중요: 지문 내용을 보고 가장 적합한 유형을 선택하고, 해당 형식을 정확히 따르세요!**

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

    def _parse_ai_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """AI 응답을 파싱합니다."""
        try:
            # JSON 블록 추출
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    json_text = response_text[start:end].strip()
                else:
                    json_text = response_text[start:].strip()
            else:
                # JSON 블록이 없으면 전체 텍스트에서 JSON 찾기
                json_text = response_text.strip()

            # JSON 파싱
            parsed_data = json.loads(json_text)

            return parsed_data

        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            print(f"응답 텍스트: {response_text}")
            return None
        except Exception as e:
            print(f"응답 파싱 오류: {e}")
            return None