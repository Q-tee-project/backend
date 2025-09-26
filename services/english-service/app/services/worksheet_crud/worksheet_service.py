"""
워크시트 제목 수정 서비스
워크시트의 제목만 수정할 수 있는 서비스
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ....models.english_learning import Worksheet, Question, Passage

class WorksheetService:
    @staticmethod
    def create_worksheet(db: Session, worksheet_data: Dict[str, Any]) -> Worksheet:
        db_worksheet = Worksheet(**worksheet_data)
        db.add(db_worksheet)
        db.commit()
        db.refresh(db_worksheet)
        return db_worksheet

    @staticmethod
    def get_worksheet(db: Session, worksheet_id: int) -> Optional[Worksheet]:
        return db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()

    @staticmethod
    def get_worksheets_by_user(db: Session, user_id: int) -> List[Worksheet]:
        return db.query(Worksheet).filter(Worksheet.user_id == user_id).all()

    @staticmethod
    def update_worksheet(db: Session, worksheet_id: int, worksheet_data: Dict[str, Any]) -> Optional[Worksheet]:
        db_worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if db_worksheet:
            for key, value in worksheet_data.items():
                setattr(db_worksheet, key, value)
            db.commit()
            db.refresh(db_worksheet)
        return db_worksheet

    @staticmethod
    def delete_worksheet(db: Session, worksheet_id: int) -> bool:
        db_worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if db_worksheet:
            db.delete(db_worksheet)
            db.commit()
            return True
        return False

    @staticmethod
    def copy_worksheet(db: Session, source_worksheet_id: int, target_user_id: int, new_title: str) -> Optional[int]:
        """워크시트와 포함된 문제들을 복사"""
        try:
            # 1. 원본 워크시트 조회
            source_worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == source_worksheet_id).first()
            if not source_worksheet:
                return None

            # 2. 새 워크시트 생성 (기본 정보 복사)
            new_worksheet = Worksheet(
                user_id=target_user_id,
                worksheet_name=new_title,
                school_level=source_worksheet.school_level,
                grade=source_worksheet.grade,
                problem_type=source_worksheet.problem_type,
                total_questions=source_worksheet.total_questions,
                status="completed"
            )
            db.add(new_worksheet)
            db.flush()

            # 3. 원본 문제들 조회
            source_questions = db.query(Question).filter(Question.worksheet_id == source_worksheet_id).all()

            # 4. 문제들을 새 워크시트에 복사
            for source_question in source_questions:
                new_question = Question(
                    worksheet_id=new_worksheet.worksheet_id,
                    question_number=source_question.question_number,
                    question_text=source_question.question_text,
                    question_type=source_question.question_type,
                    passage_id=source_question.passage_id,
                    options=source_question.options,
                    answer=source_question.answer,
                    explanation=source_question.explanation,
                    score=source_question.score
                )
                db.add(new_question)
            
            db.commit()
            return new_worksheet.worksheet_id

        except Exception as e:
            db.rollback()
            print(f"Error copying worksheet: {str(e)}")
            return None