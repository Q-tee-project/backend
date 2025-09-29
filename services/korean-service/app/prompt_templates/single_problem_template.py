"""
Single problem generation template for Korean
"""

from typing import Dict
from .base_template import BaseKoreanPromptTemplate


class SingleProblemTemplate(BaseKoreanPromptTemplate):
    """단일 문제 생성 템플릿"""

    def generate_prompt(self, source_text: str, korean_type: str, question_type: str,
                       difficulty: str, user_prompt: str, korean_data: Dict) -> str:
        """단일 문제 생성 프롬프트 구성 - 모든 문제는 객관식"""

        # 문법 문제인 경우 특별 처리
        if korean_type == '문법':
            prompt = f"""
다음 문법 참고 자료를 활용하여 {korean_type} 영역의 객관식 문제를 생성해주세요.

**참고 자료:**
{source_text}

**중요한 지침:**
1. 참고 자료의 내용을 직접 언급하지 마세요 (예: "지문의 [01. 단어의 발음과 표기]를 바탕으로" 금지)
2. 필요한 경우 문제 안에 새로운 예시 문장이나 상황을 만들어 사용하세요
3. 문법 개념을 묻는 독립적인 문제로 구성하세요
"""
        else:
            prompt = f"""
다음 지문을 바탕으로 {korean_type} 영역의 객관식 문제를 생성해주세요.

**지문:**
{source_text}
"""

        prompt += self.get_base_requirements(korean_data, difficulty, user_prompt)
        if korean_type == '문법':
            prompt += self.get_grammar_output_format()
        else:
            prompt += self.get_output_format("객관식")
        prompt += self.get_korean_type_characteristics(korean_type)
        prompt += self.get_general_instructions()

        return prompt

    def get_grammar_output_format(self) -> str:
        """문법 문제 전용 출력 형식"""
        return """
**출력 형식 (JSON):**
```json
{
    "question": "문제 내용",
    "choices": ["1번 선택지", "2번 선택지", "3번 선택지", "4번 선택지"],
    "correct_answer": "A",
    "explanation": "해설",
    "source_text": "문제에 사용된 예시 지문 (있는 경우만)",
    "source_title": "예시 제목 (있는 경우만)",
    "source_author": "예시 작성자 (있는 경우만)"
}
```

**주의사항:**
- 4개의 선택지를 제공해야 합니다.
- correct_answer는 반드시 A, B, C, D 중 하나여야 합니다.
- A는 첫 번째 선택지, B는 두 번째 선택지, C는 세 번째 선택지, D는 네 번째 선택지입니다.
- source_text, source_title, source_author는 문제에 예시 지문이 필요한 경우에만 포함하세요.
- 예시 지문은 참고 자료와 별개의 새로운 내용이어야 합니다.
"""

    def get_korean_type_characteristics(self, korean_type: str) -> str:
        """국어 영역별 특성 설명"""
        characteristics = {
            '시': """
**시 영역 특성:**
- 화자, 상황, 정서, 표현 기법, 주제 의식 등을 중심으로 문제 출제
- 운율, 은유, 의인법, 대조법 등의 문학적 표현 기법 분석
- 시어의 함축적 의미, 화자의 정서와 상황 파악
""",
            '소설': """
**소설 영역 특성:**
- 인물, 배경, 사건, 갈등, 주제 등을 중심으로 문제 출제
- 서술자, 시점, 구성, 문체 등의 소설 기법 분석
- 인물의 심리, 갈등 상황, 주제 의식 파악
""",
            '수필/비문학': """
**수필/비문학 영역 특성:**
- 글의 구조, 논리 전개, 주장과 근거, 핵심 내용 등을 중심으로 문제 출제
- 글쓴이의 관점, 의도, 글의 성격 파악
- 정보의 이해, 추론, 적용 능력 평가
""",
            '문법': """
**문법 영역 특성:**
- 음운, 단어, 문장, 의미 등의 문법 요소를 중심으로 문제 출제
- 품사, 어휘, 문장 성분, 문법적 관계 분석
- 언어의 특성, 변화, 규칙 등에 대한 이해 평가
"""
        }

        return characteristics.get(korean_type, "")