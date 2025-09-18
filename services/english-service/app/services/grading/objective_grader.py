from typing import Dict, Any


class ObjectiveGrader:
    """객관식 문제 채점 클래스"""

    @staticmethod
    def grade_multiple_choice(correct_answer: str, student_answer: str) -> Dict[str, Any]:
        """
        객관식 문제를 채점합니다.

        Args:
            correct_answer: 정답 (예: "1", "2", "3")
            student_answer: 학생 답안

        Returns:
            채점 결과 딕셔너리
        """
        # 답안 정규화 (공백 제거, 소문자 변환)
        normalized_correct = str(correct_answer).strip().lower()
        normalized_student = str(student_answer).strip().lower()

        is_correct = normalized_correct == normalized_student
        score = 1 if is_correct else 0

        return {
            "score": score,
            "is_correct": is_correct,
            "grading_method": "db",
            "feedback": "정답입니다!" if is_correct else f"정답은 '{correct_answer}'입니다."
        }

    @staticmethod
    def grade_short_answer(correct_answer: str, student_answer: str) -> Dict[str, Any]:
        """
        단답형 문제를 채점합니다.

        Args:
            correct_answer: 정답
            student_answer: 학생 답안

        Returns:
            채점 결과 딕셔너리
        """
        # 답안 정규화 (공백 제거, 대소문자 구분 없음)
        normalized_correct = correct_answer.strip().lower()
        normalized_student = student_answer.strip().lower()

        is_correct = normalized_correct == normalized_student
        score = 1 if is_correct else 0

        return {
            "score": score,
            "is_correct": is_correct,
            "grading_method": "db",
            "feedback": "정답입니다!" if is_correct else f"정답은 '{correct_answer}'입니다."
        }