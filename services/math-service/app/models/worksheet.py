from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class WorksheetStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PUBLISHED = "published"


class Worksheet(Base):
    """문제지 모델 - 10개 또는 20개 문제를 포함하는 세트"""
    __tablename__ = "worksheets"
    __table_args__ = {"schema": "math_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # 문제지 제목
    
    # 교육과정 정보
    school_level = Column(String, nullable=False)  # "초등학교", "중학교", "고등학교"
    grade = Column(Integer, nullable=False)
    semester = Column(String, nullable=False)
    unit_number = Column(String, nullable=False)
    unit_name = Column(String, nullable=False)
    chapter_number = Column(String, nullable=False)
    chapter_name = Column(String, nullable=False)
    
    # 문제지 설정
    problem_count = Column(Integer, nullable=False)  # 10 or 20
    difficulty_ratio = Column(JSON, nullable=False)  # {"A": 30, "B": 40, "C": 30}
    problem_type_ratio = Column(JSON, nullable=False)  # {"multiple_choice": 50, "essay": 30, "short_answer": 20}
    
    # 생성 정보
    user_prompt = Column(Text, nullable=False)  # 사용자가 입력한 세부사항
    generation_id = Column(String, unique=True, nullable=False, index=True)  # 생성 세션 ID
    
    # 실제 결과
    actual_difficulty_distribution = Column(JSON)  # 실제 생성된 난이도 분포
    actual_type_distribution = Column(JSON)  # 실제 생성된 유형 분포
    
    # 상태 관리
    status = Column(Enum(WorksheetStatus), default=WorksheetStatus.COMPLETED)
    
    # 비동기 처리 관련
    celery_task_id = Column(String, nullable=True, index=True)  # Celery 태스크 ID
    error_message = Column(Text, nullable=True)  # 오류 메시지
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 완료 시간
    
    # 메타데이터
    teacher_id = Column(Integer, ForeignKey("public.teachers.id"), nullable=False, index=True)
    created_by = Column(Integer)  # 호환성을 위해 유지
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    problems = relationship("Problem", back_populates="worksheet", order_by="Problem.sequence_order")
    # teacher = relationship("Teacher")  # 다른 스키마의 테이블이므로 직접 관계 설정하지 않음


# WorksheetProblem 모델 제거됨 - Problem 모델로 통합