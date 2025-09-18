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

        prompt = f"""
다음 지문을 바탕으로 {korean_type} 영역의 객관식 문제를 생성해주세요.

**지문:**
{source_text}
"""

        prompt += self.get_base_requirements(korean_data, difficulty, user_prompt)
        prompt += self.get_output_format("객관식")
        prompt += self.get_korean_type_characteristics(korean_type)
        prompt += self.get_general_instructions()

        return prompt

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