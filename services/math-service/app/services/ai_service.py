import os
import json
import google.generativeai as genai
from typing import Dict, List
from dotenv import load_dotenv
from .problem_generator import ProblemGenerator
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
        """단일 문제 빠른 재생성 - AI Judge 검증 포함"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # 그래프가 필요한지 확인 (tikz_code가 있거나 has_diagram이 true인 경우)
                has_tikz = bool(current_problem.get('tikz_code'))
                has_diagram = current_problem.get('has_diagram', 'false')

                # has_diagram이 문자열인 경우 처리
                if isinstance(has_diagram, str):
                    has_diagram = has_diagram.lower() == 'true'

                needs_graph = has_tikz or has_diagram

                tikz_instruction = ""
                if needs_graph:
                    tikz_instruction = """

**TikZ Graph Requirements**:
- This problem requires a graph visualization. Generate appropriate TikZ code.
- Axis ranges: Minimize empty space, keep data points well-proportioned
- Typical good ranges: -5 to 5, -1 to 10, 0 to 20 (avoid extremes)
- Use ONLY English and math symbols in TikZ code, NO Korean text
- For coordinate plane problems, include appropriate points, lines, and shapes

**CRITICAL - Answer Point Hiding Rule**:
  * If the question asks to find a specific point (e.g., "Find the coordinate of point D"), that point is the ANSWER
  * **DO NOT draw or label the answer point on the graph** (NO \\coordinate or \\filldraw for answer point)
  * Only show GIVEN points on the graph
  * Example: Question asks "Find point D" and gives "A(1,2), B(5,2), C(6,5)" → Only draw A, B, C. DO NOT draw D.
"""

                prompt = f"""You are an expert math problem regenerator. Improve the following math problem based on user requirements.

**Current Problem**:
- Question: {current_problem.get('question', '')}
- Correct Answer: {current_problem.get('correct_answer', '')}
- Explanation: {current_problem.get('explanation', '')}
- Choices: {current_problem.get('choices', [])}
- Needs Graph: {needs_graph}
{f"- Existing TikZ Code: {current_problem.get('tikz_code', '')}" if has_tikz else ""}

**User Requirements**: {requirements}
{tikz_instruction}

**IMPORTANT**: All content fields (question, choices, correct_answer, explanation) MUST be in Korean.

Return ONLY valid JSON in this format:
{{
    "question": "Improved question content (in Korean)",
    "choices": ["Choice 1 (Korean)", "Choice 2 (Korean)", "Choice 3 (Korean)", "Choice 4 (Korean)"],
    "correct_answer": "Correct answer (Korean)",
    "explanation": "Explanation (in Korean)"{', "tikz_code": "TikZ LaTeX code"' if needs_graph else ''}
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

                # AI Judge 검증 (problem_generator의 검증 로직 활용)
                is_valid, scores, feedback = self.problem_generator._validate_with_ai_judge(result)

                if is_valid:
                    print(f"✅ 재생성 문제 검증 통과 - 평균 {scores['overall_score']:.1f}점")
                    return result
                else:
                    if attempt < max_retries - 1:
                        print(f"⚠️ 재생성 문제 검증 실패 (시도 {attempt + 1}/{max_retries}) - {scores['overall_score']:.1f}점")
                        print(f"   피드백: {feedback}")
                        # 재시도 시 피드백을 프롬프트에 추가
                        requirements = f"{requirements}\n\n**Previous issue**: {feedback}"
                        continue
                    else:
                        print(f"❌ 최종 검증 실패 - 기존 문제 반환")
                        return current_problem

            except Exception as e:
                print(f"❌ 문제 재생성 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    continue
                # 실패 시 기존 문제 반환
                return current_problem

        return current_problem

    def ocr_handwriting(self, image_data: bytes) -> str:
        """OCR 처리 - 분리된 서비스 사용"""
        return self.ocr_service.extract_text_from_image(image_data)


