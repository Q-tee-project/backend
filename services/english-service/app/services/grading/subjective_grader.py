from typing import Dict, Any
from ..ai.ai_service import AIService


class SubjectiveGrader:
    """주관식/서술형 문제 채점 클래스"""

    def __init__(self):
        self.ai_service = AIService()

    async def grade_subjective(self, question_text: str, correct_answer: str, student_answer: str,
                             passage_content: str = None, example_content: str = None,
                             explanation: str = None, learning_point: str = None) -> Dict[str, Any]:
        """
        단답형/서술형 문제를 AI로 채점합니다.

        Args:
            question_text: 문제 텍스트
            correct_answer: 정답
            student_answer: 학생 답안
            passage_content: 관련 지문 (선택사항)
            example_content: 관련 예문 (선택사항)

        Returns:
            채점 결과 딕셔너리
        """
        result = await self.ai_service.grade_subjective_question(
            question_text=question_text,
            correct_answer=correct_answer,
            student_answer=student_answer,
            passage_content=passage_content,
            example_content=example_content,
            explanation=explanation,
            learning_point=learning_point
        )

        # grading_method 추가
        result["grading_method"] = "ai"

        return result

    async def grade_essay(self, question_text: str, correct_answer: str, student_answer: str,
                         passage_content: str = None, example_content: str = None) -> Dict[str, Any]:
        """
        서술형 문제를 AI로 채점합니다.

        Args:
            question_text: 문제 텍스트
            correct_answer: 정답/답안 예시
            student_answer: 학생 답안
            passage_content: 관련 지문 (선택사항)
            example_content: 관련 예문 (선택사항)

        Returns:
            채점 결과 딕셔너리
        """
        # 서술형은 주관식과 동일한 로직 사용
        return await self.grade_subjective(
            question_text=question_text,
            correct_answer=correct_answer,
            student_answer=student_answer,
            passage_content=passage_content,
            example_content=example_content
        )