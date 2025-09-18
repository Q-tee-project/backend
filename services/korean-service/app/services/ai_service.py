import os
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