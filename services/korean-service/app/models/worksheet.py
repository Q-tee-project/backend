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
    """국어 문제지 모델 - 10개 또는 20개 문제를 포함하는 세트"""
    __tablename__ = "worksheets"
    __table_args__ = {"schema": "korean_service"}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # 문제지 제목

    # 교육과정 정보
    school_level = Column(String, nullable=False)  # "중학교", "고등학교"
    grade = Column(Integer, nullable=False)

    # 국어 과목 정보
    korean_type = Column(String, nullable=False)  # "시", "소설", "수필/비문학", "문법"
    question_type = Column(String, nullable=False)  # "객관식", "서술형", "단답형"
    difficulty = Column(String, nullable=False)  # "상", "중", "하"

    # 문제지 설정
    problem_count = Column(Integer, nullable=False)  # 10 or 20
    question_type_ratio = Column(JSON, nullable=True)  # {"객관식": 50, "서술형": 30, "단답형": 20}
    difficulty_ratio = Column(JSON, nullable=True)  # {"상": 30, "중": 40, "하": 30}

    # 생성 정보
    user_text = Column(Text, nullable=True)  # 사용자가 입력한 세부사항
    generation_id = Column(String, unique=True, nullable=False, index=True)  # 생성 세션 ID

    # 실제 결과
    actual_korean_type_distribution = Column(JSON)  # 실제 생성된 국어 유형 분포
    actual_question_type_distribution = Column(JSON)  # 실제 생성된 문제 유형 분포
    actual_difficulty_distribution = Column(JSON)  # 실제 생성된 난이도 분포

    # 상태 관리
    status = Column(Enum(WorksheetStatus), default=WorksheetStatus.COMPLETED)

    # 비동기 처리 관련
    celery_task_id = Column(String, nullable=True, index=True)  # Celery 태스크 ID

    # 사용자 관리
    teacher_id = Column(Integer, nullable=False)  # 생성한 선생님 ID

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    problems = relationship("Problem", back_populates="worksheet", cascade="all, delete-orphan")