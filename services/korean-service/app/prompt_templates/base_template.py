"""
Base template for Korean problem generation prompts
"""

from typing import Dict, List, Optional


class BaseKoreanPromptTemplate:
    """베이스 국어 문제 생성 프롬프트 템플릿"""

    def __init__(self):
        self.difficulty_descriptions = {
            '상': '어려운 수준 (고차원적 사고, 복합적 이해 필요)',
            '중': '보통 수준 (기본 이해와 적용)',
            '하': '쉬운 수준 (기초 개념 확인)'
        }

    def get_base_requirements(self, korean_data: Dict, difficulty: str, user_prompt: str = "") -> str:
        """기본 문제 요구사항 생성"""
        requirements = f"""
**문제 요구사항:**
- 학교급: {korean_data.get('school_level', '중학교')}
- 학년: {korean_data.get('grade', 1)}학년
- 문제 유형: {korean_data.get('korean_type', '시')}
- 문제 형식: {korean_data.get('question_type', '객관식')}
- 난이도: {difficulty} ({self.difficulty_descriptions.get(difficulty, '')})
"""

        if user_prompt:
            requirements += f"\n**추가 요구사항:** {user_prompt}\n"

        return requirements

    def get_output_format(self, question_type: str = "객관식") -> str:
        """출력 형식 생성 - 국어는 모두 객관식"""
        return """
**출력 형식 (JSON):**
```json
{
    "question": "문제 내용",
    "choices": ["1번 선택지", "2번 선택지", "3번 선택지", "4번 선택지"],
    "correct_answer": "A",
    "explanation": "해설",
    "source_title": "지문 제목 (있는 경우)",
    "source_author": "지문 작가 (있는 경우)"
}
```

**주의사항:**
- 4개의 선택지를 제공해야 합니다.
- correct_answer는 반드시 A, B, C, D 중 하나여야 합니다.
- A는 첫 번째 선택지, B는 두 번째 선택지, C는 세 번째 선택지, D는 네 번째 선택지입니다.
- 선택지는 명확하고 구별되어야 합니다.
- 모든 문제는 객관식으로 출제됩니다.
"""

    def get_general_instructions(self) -> str:
        """일반적인 지시사항"""
        return """
반드시 JSON 형식으로만 응답하고, 추가적인 설명은 포함하지 마세요.
"""