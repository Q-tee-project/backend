import os
import google.generativeai as genai
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class GradingService:
    def __init__(self):
        gemini_api_key = os.getenv("KOREAN_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("KOREAN_GEMINI_API_KEY or GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    def grade_essay_problem(self, question: str, correct_answer: str, student_answer: str, explanation: str) -> Dict:
        """서술형 문제 채점"""
        prompt = f"""
다음 국어 서술형 문제에 대한 학생의 답안을 채점해주세요.

**문제:** {question}

**모범답안:** {correct_answer}

**학생답안:** {student_answer}

**해설:** {explanation}

다음 기준으로 채점해주세요:
1. 핵심 내용 포함 여부 (60%)
2. 표현의 정확성 (25%)
3. 논리적 구성 (15%)

JSON 형식으로 응답해주세요:
{{
    "is_correct": true/false,
    "score": 0-100,
    "ai_feedback": "구체적인 피드백",
    "strengths": "잘한 점",
    "improvements": "개선점",
    "keyword_score_ratio": 0.0-1.0
}}
"""

        try:
            response = self.model.generate_content(prompt)
            result = response.text

            # JSON 파싱 시도
            import json
            if "```json" in result:
                json_start = result.find("```json") + 7
                json_end = result.find("```", json_start)
                json_text = result[json_start:json_end].strip()
            else:
                json_text = result.strip()

            grading_result = json.loads(json_text)
            return grading_result

        except Exception as e:
            print(f"채점 오류: {e}")
            return {
                "is_correct": False,
                "score": 0,
                "ai_feedback": "채점 중 오류가 발생했습니다.",
                "strengths": "",
                "improvements": "다시 시도해주세요.",
                "keyword_score_ratio": 0.0
            }

    def grade_objective_problem(self, question: str, correct_answer: str, student_answer: str, explanation: str) -> Dict:
        """객관식/단답형 문제 채점"""
        is_correct = student_answer.strip().lower() == correct_answer.strip().lower()

        return {
            "is_correct": is_correct,
            "score": 100 if is_correct else 0,
            "ai_feedback": "정답입니다." if is_correct else f"오답입니다. 정답은 '{correct_answer}'입니다.",
            "strengths": "정확한 답안을 작성했습니다." if is_correct else "",
            "improvements": "" if is_correct else f"정답: {correct_answer}. {explanation}",
            "keyword_score_ratio": 1.0 if is_correct else 0.0
        }