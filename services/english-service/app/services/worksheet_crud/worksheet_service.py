"""
워크시트 제목 수정 서비스
워크시트의 제목만 수정할 수 있는 서비스
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.worksheet import Worksheet, Question, Passage
from app.models.grading import GradingResult, QuestionResult
from app.models.assignment import Assignment, AssignmentDeployment

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
    def update_worksheet_title(db: Session, worksheet_id: int, new_title: str) -> Optional[Worksheet]:
        """워크시트 제목만 수정합니다."""
        db_worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not db_worksheet:
            raise ValueError(f"워크시트 ID {worksheet_id}를 찾을 수 없습니다.")

        db_worksheet.worksheet_name = new_title
        db.commit()
        db.refresh(db_worksheet)
        return db_worksheet

    @staticmethod
    def batch_delete_worksheets(db: Session, worksheet_ids: List[int], user_id: int) -> int:
        """여러 워크시트를 일괄 삭제합니다."""
        try:
            deleted_count = 0

            for worksheet_id in worksheet_ids:
                # 워크시트 존재 및 소유권 확인
                db_worksheet = db.query(Worksheet).filter(
                    Worksheet.worksheet_id == worksheet_id,
                    Worksheet.teacher_id == user_id  # 소유권 확인
                ).first()

                if not db_worksheet:
                    print(f"워크시트 ID {worksheet_id}를 찾을 수 없거나 권한이 없습니다.")
                    continue

                # 외래키 제약 조건 순서에 맞게 삭제

                # 1. 먼저 question_results 삭제 (grading_results를 참조)
                question_results = db.query(QuestionResult).join(GradingResult).filter(
                    GradingResult.worksheet_id == worksheet_id
                ).all()
                for qr in question_results:
                    db.delete(qr)

                # 2. grading_results 삭제 (worksheets를 참조)
                grading_results = db.query(GradingResult).filter(GradingResult.worksheet_id == worksheet_id).all()
                for gr in grading_results:
                    db.delete(gr)

                # 3. assignment_deployments 삭제 (assignments를 참조)
                assignments = db.query(Assignment).filter(Assignment.worksheet_id == worksheet_id).all()
                assignment_ids = [assignment.id for assignment in assignments]

                # 먼저 모든 assignment_deployments 삭제
                if assignment_ids:
                    db.query(AssignmentDeployment).filter(AssignmentDeployment.assignment_id.in_(assignment_ids)).delete(synchronize_session=False)

                # 4. assignments 삭제 (worksheets를 참조)
                if assignment_ids:
                    db.query(Assignment).filter(Assignment.id.in_(assignment_ids)).delete(synchronize_session=False)

                # 5. questions 삭제 (worksheets를 참조)
                related_questions = db.query(Question).filter(Question.worksheet_id == worksheet_id).all()
                for question in related_questions:
                    db.delete(question)

                # 6. passages 삭제 (worksheets를 참조, 필요시)
                related_passages = db.query(Passage).filter(Passage.worksheet_id == worksheet_id).all()
                for passage in related_passages:
                    db.delete(passage)

                # 7. 마지막으로 worksheet 삭제
                db.delete(db_worksheet)
                deleted_count += 1

                print(f"워크시트 ID {worksheet_id} 삭제 완료")

            db.commit()
            return deleted_count

        except Exception as e:
            db.rollback()
            print(f"일괄 삭제 중 오류 발생: {str(e)}")
            raise e

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