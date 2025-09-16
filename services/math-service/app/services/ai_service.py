import os
import google.generativeai as genai
from typing import Dict, List
from dotenv import load_dotenv
from .problem_generator import ProblemGenerator
from .grading_service import GradingService
from .ocr_service import OCRService

load_dotenv()

class AIService:
    def __init__(self):
        # Gemini API 키 설정 - 환경변수에서만 가져오기
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        
        # 서비스 인스턴스 초기화
        self.problem_generator = ProblemGenerator()
        self.grading_service = GradingService()
        self.ocr_service = OCRService()

    def generate_math_problem(self, curriculum_data: Dict, user_prompt: str, problem_count: int = 1, difficulty_ratio: Dict = None) -> List[Dict]:
        """수학 문제 생성 - 분리된 서비스 사용"""
        return self.problem_generator.generate_problems(
            curriculum_data=curriculum_data,
            user_prompt=user_prompt,
            problem_count=problem_count,
            difficulty_ratio=difficulty_ratio
        )

    def ocr_handwriting(self, image_data: bytes) -> str:
        """OCR 처리 - 분리된 서비스 사용"""
        return self.ocr_service.extract_text_from_image(image_data)

    def grade_math_answer(self, question: str, correct_answer: str, student_answer: str, explanation: str, problem_type: str = "essay") -> Dict:
        """수학 답안 채점 - 분리된 서비스 사용"""
        if problem_type.lower() == "essay":
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



