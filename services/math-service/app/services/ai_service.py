import os
import json
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

    def generate_math_problem(self, curriculum_data: Dict, user_prompt: str, problem_count: int = 1, difficulty_ratio: Dict = None) -> Dict:
        """수학 문제 생성"""
        try:
            # 문제 생성
            print(f"📝 {problem_count}개 문제 생성 중...")
            generated_problems = self.problem_generator.generate_problems(
                curriculum_data=curriculum_data,
                user_prompt=user_prompt,
                problem_count=problem_count,
                difficulty_ratio=difficulty_ratio
            )

            return {
                "problems": generated_problems,
                "summary": {"total_problems": len(generated_problems)}
            }

        except Exception as e:
            print(f"❌ 문제 생성 및 검증 오류: {str(e)}")
            return {
                "problems": [],
                "validation_results": [],
                "summary": {"error": str(e)}
            }

    def regenerate_single_problem(self, current_problem: Dict, requirements: str, curriculum_info: Dict = None) -> Dict:
        """단일 문제 빠른 재생성 - 복잡한 파이프라인 없이 직접 AI 호출"""
        try:
            # 간단한 재생성 프롬프트 구성
            prompt = f"""
다음 수학 문제를 사용자 요구사항에 맞게 개선해주세요.

기존 문제:
- 문제: {current_problem.get('question', '')}
- 정답: {current_problem.get('correct_answer', '')}
- 해설: {current_problem.get('explanation', '')}
- 선택지: {current_problem.get('choices', [])}

사용자 요구사항: {requirements}

아래 JSON 형식으로만 응답해주세요:
{{
    "question": "개선된 문제 내용",
    "choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "정답",
    "explanation": "해설"
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
            print(f"❌ 문제 재생성 오류: {str(e)}")
            # 실패 시 기존 문제 반환
            return current_problem

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



