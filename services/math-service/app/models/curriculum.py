from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from ..database import Base


class Curriculum(Base):
    """교육과정 데이터 모델"""
    __tablename__ = "curriculum"
    __table_args__ = {"schema": "math_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    grade = Column(String, nullable=False)  # "중1"
    subject = Column(String, nullable=False)  # "수학" 
    semester = Column(String, nullable=False)  # "1학기"
    unit_number = Column(String, nullable=False)  # "I"
    unit_name = Column(String, nullable=False)  # "소인수분해"
    chapter_number = Column(String, nullable=False)  # "01"
    chapter_name = Column(String, nullable=False)  # "소인수분해"
    learning_objectives = Column(Text)  # 학습 목표
    keywords = Column(Text)  # 핵심 키워드
    difficulty_levels = Column(JSON)  # 난이도별 설명
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())