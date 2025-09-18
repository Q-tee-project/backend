"""
Text passage extraction template for Korean
"""

from typing import Dict
from .base_template import BaseKoreanPromptTemplate


class ExtractPassageTemplate(BaseKoreanPromptTemplate):
    """지문 발췌 템플릿"""

    def generate_prompt(self, source_text: str, korean_type: str) -> str:
        """지문 발췌 프롬프트 구성"""

        prompt = f"""
다음 {korean_type} 지문에서 중학교 1학년 학생들이 이해하기에 적합한 핵심 부분을 발췌해주세요.

**지문:**
{source_text}

**발췌 기준:**
- 전체 지문의 핵심 내용을 담고 있어야 함
- 800-1200자 정도의 적절한 길이
- 문맥이 완결된 부분
- 문제 출제에 적합한 내용

발췌된 부분만 텍스트로 출력해주세요. 추가 설명은 필요하지 않습니다.
"""

        return prompt