from typing import Dict, Any


class ObjectiveGrader:
    """객관식 문제 채점 클래스"""

    @staticmethod
    def grade_multiple_choice(correct_answer: str, student_answer: str) -> Dict[str, Any]:
        """
        객관식 문제를 채점합니다.

        Args:
            correct_answer: 정답 (DB에 index+1 값으로 저장: "1", "2", "3", "4")
            student_answer: 학생 답안 (프론트에서 index+1 값 전송: "1", "2", "3", "4")

        Returns:
            채점 결과 딕셔너리
        """
        # 답안 정규화 (공백 제거)
        normalized_correct = str(correct_answer).strip()
        normalized_student = str(student_answer).strip()

        is_correct = normalized_correct == normalized_student
        score = 10 if is_correct else 0

        return {
            "score": score,
            "max_score": 10,
            "is_correct": is_correct,
            "grading_method": "db",
            "feedback": "정답입니다!" if is_correct else f"정답은 '{normalized_correct}번'입니다."
        }

