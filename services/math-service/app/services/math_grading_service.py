from ..models.problem import Problem

class MathGradingService:
    """수학 문제 채점 서비스 - OCR 텍스트 추출 및 자동 채점"""

    def __init__(self):
        pass

    def _normalize_fraction_text(self, text: str) -> str:
        """OCR 텍스트 정규화 (분수 등)"""
        return text.replace(' / ', '/')

    def _extract_answer_from_ocr(self, ocr_text: str, problem_id: int, problem_number: int) -> str:
        """OCR 텍스트에서 문제 번호에 해당하는 답안 추출"""
        try:
            lines = ocr_text.split('\n')
            for line in lines:
                if line.startswith(f"{problem_number}."):
                    return line.split(f"{problem_number}.")[1].strip()
            return ""
        except Exception:
            return ""

    def _grade_objective_problem(self, problem: Problem, user_answer: str, points_per_problem: int) -> dict:
        """객관식/단답형 문제 자동 채점 (DB 정답과 비교)"""
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
