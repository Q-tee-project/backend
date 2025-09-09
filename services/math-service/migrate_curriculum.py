import json
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base
from app.models.curriculum import Curriculum

def migrate_curriculum_data():
    """JSON 교육과정 데이터를 데이터베이스로 마이그레이션"""
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # JSON 파일 읽기
    curriculum_file_path = os.path.join(os.path.dirname(__file__), "data/middle1_math_curriculum.json")
    
    try:
        with open(curriculum_file_path, 'r', encoding='utf-8') as f:
            curriculum_data = json.load(f)
    except FileNotFoundError:
        print("교육과정 데이터 파일을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError:
        print("교육과정 데이터 파일 형식이 올바르지 않습니다.")
        return
    
    db = SessionLocal()
    
    try:
        # 기존 데이터 삭제 (선택사항)
        db.query(Curriculum).delete()
        
        # 새 데이터 삽입
        for item in curriculum_data:
            curriculum = Curriculum(
                grade=item["grade"],
                subject=item["subject"],
                semester=item["semester"],
                unit_number=item["unit_number"],
                unit_name=item["unit_name"],
                chapter_number=item["chapter_number"],
                chapter_name=item["chapter_name"],
                learning_objectives=item["learning_objectives"],
                keywords=item["keywords"],
                difficulty_levels=json.loads(item["difficulty_levels"]) if isinstance(item["difficulty_levels"], str) else item["difficulty_levels"]
            )
            db.add(curriculum)
        
        db.commit()
        print(f"교육과정 데이터 {len(curriculum_data)}개 항목을 성공적으로 마이그레이션했습니다.")
        
    except Exception as e:
        db.rollback()
        print(f"마이그레이션 중 오류 발생: {str(e)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    migrate_curriculum_data()