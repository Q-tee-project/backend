from ..services.ai_service import AIService
from ..models.problem import Problem

class MathGradingService:
    def __init__(self):
        self.ai_service = AIService()

    def grade_mixed_problems(self, problems: list[Problem], multiple_choice_answers: dict, canvas_answers: dict) -> list[dict]:
        """혼합형 문제(객관식+주관식 OCR) 채점"""
        # Implementation will be moved from tasks.py
        pass

    def grade_ocr_problems(self, problems: list[Problem], image_data: bytes) -> list[dict]:
        """이미지 OCR 기반 문제 채점"""
        # Implementation will be moved from tasks.py
        pass

    def _normalize_fraction_text(self, text: str) -> str:
        """OCR 텍스트 정규화 (분수 등)"""
        # This is a simplified placeholder. Actual logic might be more complex.
        return text.replace(' / ', '/')

    def _extract_answer_from_ocr(self, ocr_text: str, problem_id: int, problem_number: int) -> str:
        """OCR 텍스트에서 문제 번호에 해당하는 답안 추출"""
        # This is a simplified placeholder. Actual logic would be more robust.
        try:
            lines = ocr_text.split('\n')
            for line in lines:
                if line.startswith(f"{problem_number}."):
                    return line.split(f"{problem_number}.")[1].strip()
            return ""
        except Exception:
            return ""

    def _grade_essay_problem(self, problem: Problem, user_answer: str, points_per_problem: int) -> dict:
        """서술형 문제 채점"""
        ai_result = self.ai_service.grade_math_answer(
            question=problem.question,
            correct_answer=problem.correct_answer,
            student_answer=user_answer,
            explanation=problem.explanation,
            problem_type="essay"
        )
        ai_score_ratio = ai_result.get("score", 0) / 100
        final_score = points_per_problem * ai_score_ratio
        return {
            "problem_id": problem.id,
            "problem_type": "essay",
            "user_answer": user_answer,
            "correct_answer": problem.correct_answer,
            "is_correct": final_score >= (points_per_problem * 0.6),
            "score": final_score,
            "points_per_problem": points_per_problem,
            "ai_score": ai_result.get("score", 0),
            "ai_feedback": ai_result.get("feedback", ""),
            "strengths": ai_result.get("strengths", ""),
            "improvements": ai_result.get("improvements", ""),
            "explanation": problem.explanation
        }

    def _grade_objective_problem(self, problem: Problem, user_answer: str, points_per_problem: int) -> dict:
        """객관식/단답형 문제 채점"""
        # Simple comparison logic
        is_correct = str(user_answer).strip() == str(problem.correct_answer).strip()
        score = points_per_problem if is_correct else 0
        return {
            "problem_id": problem.id,
            "problem_type": problem.problem_type,
            "user_answer": user_answer,
            "correct_answer": problem.correct_answer,
            "is_correct": is_correct,
            "score": score,
            "points_per_problem": points_per_problem,
            "explanation": problem.explanation
        }
