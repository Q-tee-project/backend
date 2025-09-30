from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.korean_generation import KoreanGeneration
from ..models.worksheet import Worksheet, WorksheetStatus
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

    @staticmethod
    def copy_worksheet(db: Session, source_worksheet_id: int, target_user_id: int, new_title: str) -> Optional[int]:
        """워크시트와 포함된 문제들을 복사"""
        try:
            # 1. 원본 워크시트 조회
            source_worksheet = db.query(Worksheet).filter(Worksheet.id == source_worksheet_id).first()
            if not source_worksheet:
                return None

            # 2. 새 워크시트 생성 (기본 정보 복사)
            new_worksheet = Worksheet(
                title=new_title,
                school_level=source_worksheet.school_level,
                grade=source_worksheet.grade,
                korean_type=source_worksheet.korean_type,
                question_type=source_worksheet.question_type,
                difficulty=source_worksheet.difficulty,
                problem_count=source_worksheet.problem_count,
                status=WorksheetStatus.COMPLETED,
                teacher_id=target_user_id,
                generation_id=f"copy_{source_worksheet_id}_{target_user_id}"
            )
            db.add(new_worksheet)
            db.flush()

            # 3. 원본 문제들 조회
            source_problems = db.query(Problem).filter(Problem.worksheet_id == source_worksheet_id).all()

            # 4. 문제들을 새 워크시트에 복사
            for source_problem in source_problems:
                new_problem = Problem(
                    worksheet_id=new_worksheet.id,
                    sequence_order=source_problem.sequence_order,
                    korean_type=source_problem.korean_type,
                    problem_type=source_problem.problem_type,
                    difficulty=source_problem.difficulty,
                    question=source_problem.question,
                    choices=source_problem.choices,
                    correct_answer=source_problem.correct_answer,
                    explanation=source_problem.explanation,
                    source_text=source_problem.source_text,
                    source_title=source_problem.source_title,
                    source_author=source_problem.source_author
                )
                db.add(new_problem)
            
            db.commit()
            return new_worksheet.id

        except Exception as e:
            db.rollback()
            print(f"Error copying worksheet: {str(e)}")
            return None