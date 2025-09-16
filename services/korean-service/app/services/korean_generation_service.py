from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.korean_generation import KoreanGeneration
from ..models.worksheet import Worksheet
from ..models.problem import Problem


class KoreanGenerationService:
    def __init__(self):
        pass

    def get_generation_history(self, db: Session, user_id: int, skip: int = 0, limit: int = 10) -> List[KoreanGeneration]:
        """국어 문제 생성 이력 조회"""
        return db.query(KoreanGeneration)\
            .filter(KoreanGeneration.user_id == user_id)\
            .order_by(KoreanGeneration.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_generation_detail(self, db: Session, generation_id: str, user_id: int) -> Optional[KoreanGeneration]:
        """국어 문제 생성 세션 상세 조회"""
        return db.query(KoreanGeneration)\
            .filter(KoreanGeneration.generation_id == generation_id, KoreanGeneration.user_id == user_id)\
            .first()

    def get_worksheet_problems(self, db: Session, worksheet_id: int) -> List[Dict]:
        """워크시트의 문제들 조회"""
        problems = db.query(Problem)\
            .filter(Problem.worksheet_id == worksheet_id)\
            .order_by(Problem.sequence_order)\
            .all()

        result = []
        for problem in problems:
            import json
            problem_dict = {
                "id": problem.id,
                "sequence_order": problem.sequence_order,
                "korean_type": problem.korean_type.value if hasattr(problem.korean_type, 'value') else problem.korean_type,
                "problem_type": problem.problem_type.value if hasattr(problem.problem_type, 'value') else problem.problem_type,
                "difficulty": problem.difficulty.value if hasattr(problem.difficulty, 'value') else problem.difficulty,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else None,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "source_text": problem.source_text,
                "source_title": problem.source_title,
                "source_author": problem.source_author
            }
            result.append(problem_dict)

        return result