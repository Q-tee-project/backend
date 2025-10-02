"""
AI Judge Validator for Korean Problems
AI Judge를 사용한 국어 문제 검증
"""

import os
import json
from typing import Dict, Tuple
from openai import OpenAI


class AIJudgeValidator:
    """OpenAI GPT-4o-mini를 사용한 AI Judge 검증"""

    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("⚠️ Warning: OPENAI_API_KEY not found. AI Judge validation will be disabled.")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=openai_api_key)

    def validate_problem(self, problem: Dict, korean_type: str) -> Tuple[bool, Dict, str]:
        """
        AI Judge로 국어 문제 내용 검증

        Args:
            problem: 검증할 문제
            korean_type: 국어 문제 유형 (시/소설/수필/비문학/문법)

        Returns:
            (is_valid: bool, scores: dict, feedback: str)
        """
        if not self.openai_client:
            print("⚠️ AI Judge disabled (no OpenAI API key)")
            return True, {"overall_score": 5.0}, "AI Judge not available"

        try:
            question = problem.get('question', '')
            correct_answer = problem.get('correct_answer', '')
            explanation = problem.get('explanation', '')
            choices = problem.get('choices', [])
            choices_text = '\n'.join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)]) if choices else 'None'

            # 국어 유형별 검증 기준 설정
            type_specific_criteria = self._get_validation_criteria(korean_type)

            # 기준 이름 추출
            criteria_lines = type_specific_criteria.strip().split('\n')
            criterion_names = []
            for line in criteria_lines:
                if line.strip() and '. ' in line:
                    # "1. literary_accuracy (1-5): ..." -> "literary_accuracy"
                    name = line.split('. ')[1].split(' ')[0]
                    criterion_names.append(name)

            # JSON 스키마 생성
            scores_schema = ', '.join([f'"{name}": <score>' for name in criterion_names])

            validation_prompt = f"""You are an expert Korean language teacher. Please validate the following Korean language problem.

The problem data is as follows:
- Question: {question}
- Choices:
{choices_text}
- Correct Answer: {correct_answer}
- Explanation: {explanation}
- Korean Type: {korean_type}

Evaluation criteria (score 1-5 for each):
{type_specific_criteria}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "scores": {{{scores_schema}}},
  "overall_score": <average of all scores>,
  "decision": "VALID" or "INVALID",
  "feedback": "<brief feedback in Korean>"
}}

Decision rule: All scores must be 3.5 or higher to be "VALID".
"""

            # OpenAI API 호출
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Korean language education expert who validates Korean language problems and returns structured JSON responses."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)

            is_valid = result.get('decision') == 'VALID'
            scores = result.get('scores', {})
            scores['overall_score'] = result.get('overall_score', 0)
            feedback = result.get('feedback', 'No feedback')

            return is_valid, scores, feedback

        except json.JSONDecodeError as e:
            print(f"❌ AI Judge 응답 JSON 파싱 실패: {str(e)}")
            raise Exception(f"AI Judge validation failed - invalid JSON response: {str(e)}")

        except Exception as e:
            print(f"❌ AI Judge 검증 오류: {str(e)}")
            raise Exception(f"AI Judge validation error: {str(e)}")

    def _get_validation_criteria(self, korean_type: str) -> str:
        """국어 유형별 AI Judge 검증 기준 반환"""

        criteria_map = {
            '시': """1. literary_accuracy (1-5): The question and explanation accurately interpret the poem's literary devices, imagery, and meaning
2. relevance (1-5): The question directly relates to the provided poem and tests genuine comprehension
3. figurative_language_analysis (1-5): The question requires understanding of metaphors, symbols, or poetic techniques
4. answer_clarity (1-5): The correct answer is clearly identifiable and well-explained""",

            '소설': """1. narrative_comprehension (1-5): The question tests understanding of plot, character development, or narrative structure
2. relevance (1-5): The question directly relates to the provided novel excerpt
3. textual_analysis (1-5): The question requires analysis of the text rather than just recall
4. answer_clarity (1-5): The correct answer is clearly identifiable and well-explained""",

            '수필/비문학': """1. argument_comprehension (1-5): The question tests understanding of the main argument or informational content
2. relevance (1-5): The question directly relates to the provided text
3. critical_thinking (1-5): The question requires analysis, inference, or evaluation
4. answer_clarity (1-5): The correct answer is clearly identifiable and well-explained""",

            '문법': """1. grammar_accuracy (1-5): The grammatical concept is correctly presented and tested
2. example_quality (1-5): Examples are clear, correct, and illustrative of the concept
3. explanation_clarity (1-5): The explanation is accurate and easy to understand
4. answer_clarity (1-5): The correct answer is clearly identifiable and well-explained"""
        }

        return criteria_map.get(korean_type, criteria_map['수필/비문학'])
