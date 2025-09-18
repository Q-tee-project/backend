"""
Multiple problems generation template for Korean
"""

from typing import Dict, List
from .base_template import BaseKoreanPromptTemplate


class MultipleProblemTemplate(BaseKoreanPromptTemplate):
    """다중 문제 생성 템플릿"""

    def generate_prompt(self, source_text: str, source_info: Dict, korean_type: str,
                       count: int, question_types: List[str], difficulties: List[str],
                       user_prompt: str, korean_data: Dict) -> str:
        """다중 문제 생성 프롬프트 구성"""

        # 문제 유형별 분포 정보
        question_type_info = []
        for i, (q_type, difficulty) in enumerate(zip(question_types, difficulties)):
            question_type_info.append(f"- 문제 {i+1}: {q_type} ({difficulty} - {self.difficulty_descriptions.get(difficulty, '')})")

        prompt = f"""
다음 지문을 바탕으로 {korean_type} 영역의 객관식 문제 {count}개를 생성해주세요.

**지문 정보:**
- 제목: {source_info.get('title', '')}
- 작가: {source_info.get('author', '')}

**지문:**
{source_text}

**문제 요구사항:**
- 학교급: {korean_data.get('school_level', '중학교')}
- 학년: {korean_data.get('grade', 1)}학년
- 문제 유형: {korean_type}
- 문제 형식: 객관식 (모든 문제)

**문제별 세부 요구사항:**
{chr(10).join(question_type_info)}
"""

        if user_prompt:
            prompt += f"\n**추가 요구사항:** {user_prompt}\n"

        prompt += self.get_multiple_output_format(source_info)
        prompt += self.get_problem_generation_rules()
        prompt += self.get_korean_type_characteristics(korean_type)
        prompt += self.get_general_instructions()

        return prompt

    def get_multiple_output_format(self, source_info: Dict) -> str:
        """다중 문제 출력 형식 - 모든 문제는 객관식"""
        return f"""
**출력 형식 (JSON):**
```json
{{
    "source_info": {{
        "title": "{source_info.get('title', '')}",
        "author": "{source_info.get('author', '')}"
    }},
    "problems": [
        {{
            "question": "문제 내용",
            "choices": ["1번 선택지", "2번 선택지", "3번 선택지", "4번 선택지"],
            "correct_answer": "정답 선택지 내용",
            "explanation": "해설"
        }},
        {{
            "question": "문제 내용",
            "choices": ["1번 선택지", "2번 선택지", "3번 선택지", "4번 선택지"],
            "correct_answer": "정답 선택지 내용",
            "explanation": "해설"
        }}
    ]
}}
```

**주의사항:**
- 모든 문제는 객관식으로 출제됩니다.
- 각 문제마다 4개의 선택지를 제공해야 합니다.
"""

    def get_problem_generation_rules(self) -> str:
        """문제 생성 규칙"""
        return """
**문제 생성 규칙:**
1. **하나의 지문에 연결된 문제들**: 모든 문제가 주어진 지문을 바탕으로 출제되어야 함
2. **문제 간 연관성**: 문제들이 서로 다른 관점에서 같은 지문을 다루되, 중복되지 않아야 함
3. **난이도별 특성**:
   - 하: 지문의 표면적 내용 이해 (누가, 언제, 어디서, 무엇을)
   - 중: 지문의 의미와 의도 파악 (왜, 어떻게)
   - 상: 지문의 깊은 의미와 작가의 의도, 표현 기법 분석
4. **객관식 문제 특성**:
   - 명확한 정답이 있는 사실 확인 문제
   - 4개의 선택지 중 1개만 정답
   - 선택지는 서로 구별되고 논리적이어야 함
   - 오답 선택지는 그럴듯하지만 명백히 틀린 내용
"""

    def get_korean_type_characteristics(self, korean_type: str) -> str:
        """국어 영역별 특성 설명 (다중 문제용)"""
        characteristics = {
            '시': """
**시 영역 특성:**
- 화자, 상황, 정서, 표현 기법, 주제 의식 등을 중심으로 문제 출제
- 운율, 은유, 의인법, 대조법 등의 문학적 표현 기법 분석
- 시어의 함축적 의미, 화자의 정서와 상황 파악
- 문제 1-3: 표면적 이해 (화자, 상황, 정서)
- 문제 4-7: 표현 기법과 시어 분석
- 문제 8-10: 주제 의식과 깊은 의미
""",
            '소설': """
**소설 영역 특성:**
- 인물, 배경, 사건, 갈등, 주제 등을 중심으로 문제 출제
- 서술자, 시점, 구성, 문체 등의 소설 기법 분석
- 인물의 심리, 갈등 상황, 주제 의식 파악
- 문제 1-3: 인물과 사건 이해
- 문제 4-7: 갈등과 심리 분석
- 문제 8-10: 주제와 작가 의도
""",
            '수필/비문학': """
**수필/비문학 영역 특성:**
- 글의 구조, 논리 전개, 주장과 근거, 핵심 내용 등을 중심으로 문제 출제
- 글쓴이의 관점, 의도, 글의 성격 파악
- 정보의 이해, 추론, 적용 능력 평가
- 문제 1-3: 핵심 내용 파악
- 문제 4-7: 논리 구조와 근거 분석
- 문제 8-10: 추론과 적용
""",
            '문법': """
**문법 영역 특성:**
- 음운, 단어, 문장, 의미 등의 문법 요소를 중심으로 문제 출제
- 품사, 어휘, 문장 성분, 문법적 관계 분석
- 언어의 특성, 변화, 규칙 등에 대한 이해 평가
- 문제 1-3: 기본 문법 개념
- 문제 4-7: 문법 규칙 적용
- 문제 8-10: 복합 문법 분석
"""
        }

        characteristics_text = characteristics.get(korean_type, "")

        return f"""
{characteristics_text}

**주의사항:**
- 모든 문제가 주어진 지문과 직접적으로 연결되어야 함
- 문제들이 서로 다른 측면을 다루되 논리적으로 연결되어야 함
- 모든 문제는 객관식으로 출제하며, 명확한 정답이 있어야 함
- 각 문제마다 4개의 선택지를 제공하고, 오답은 그럴듯하지만 명백히 틀려야 함
"""