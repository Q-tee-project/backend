import os
import json
import google.generativeai as genai
from typing import Dict, List
from dotenv import load_dotenv
from .korean_problem_generator import KoreanProblemGenerator
from .grading_service import GradingService
from .ocr_service import OCRService

load_dotenv()

class AIService:
    def __init__(self):
        # Gemini API 키 설정 - 환경변수에서만 가져오기 (Korean 전용 키 우선, 없으면 일반 키 사용)
        gemini_api_key = os.getenv("KOREAN_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("KOREAN_GEMINI_API_KEY or GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

        # 서비스 인스턴스 초기화
        self.problem_generator = KoreanProblemGenerator()
        self.grading_service = GradingService()
        self.ocr_service = OCRService()

    def generate_korean_problem(self, korean_data: Dict, user_prompt: str, problem_count: int = 1,
                               korean_type_ratio: Dict = None, question_type_ratio: Dict = None,
                               difficulty_ratio: Dict = None) -> List[Dict]:
        """국어 문제 생성 - 분리된 서비스 사용"""
        return self.problem_generator.generate_problems(
            korean_data=korean_data,
            user_prompt=user_prompt,
            problem_count=problem_count,
            korean_type_ratio=korean_type_ratio,
            question_type_ratio=question_type_ratio,
            difficulty_ratio=difficulty_ratio
        )

    def regenerate_single_problem(self, current_problem: Dict, requirements: str, korean_info: Dict = None) -> Dict:
        """단일 문제 빠른 재생성 - 영어 프롬프트 사용"""
        try:
            # 영어 기반 재생성 프롬프트 구성
            prompt = f"""You are an expert Korean language teacher. Please improve the following Korean language problem according to the user's requirements.

**Current Problem:**
- Question: {current_problem.get('question', '')}
- Choices: {current_problem.get('choices', [])}
- Correct Answer: {current_problem.get('correct_answer', '')}
- Explanation: {current_problem.get('explanation', '')}

**User Requirements:** {requirements}

**CRITICAL:** Output MUST be in KOREAN language (except JSON keys).

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "question": "<개선된 문제 내용 (Korean)>",
    "choices": ["<선택지 1 (Korean)>", "<선택지 2 (Korean)>", "<선택지 3 (Korean)>", "<선택지 4 (Korean)>"],
    "correct_answer": "<A/B/C/D>",
    "explanation": "<상세한 해설 (Korean)>"
}}
"""

            # AI 모델 호출
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # JSON 응답 파싱
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            result = json.loads(response_text.strip())
            return result

        except Exception as e:
            print(f"❌ 국어 문제 재생성 오류: {str(e)}")
            # 실패 시 기존 문제 반환
            return current_problem

    def ocr_handwriting(self, image_data: bytes) -> str:
        """OCR 처리 - 분리된 서비스 사용"""
        return self.ocr_service.extract_text_from_image(image_data)

    def grade_korean_answer(self, question: str, correct_answer: str, student_answer: str,
                           explanation: str, question_type: str = "essay") -> Dict:
        """국어 답안 채점 - 분리된 서비스 사용"""
        if question_type.lower() == "essay" or question_type == "서술형":
            return self.grading_service.grade_essay_problem(
                question=question,
                correct_answer=correct_answer,
                student_answer=student_answer,
                explanation=explanation
            )
        else:
            return self.grading_service.grade_objective_problem(
                question=question,
                correct_answer=correct_answer,
                student_answer=student_answer,
                explanation=explanation
            )