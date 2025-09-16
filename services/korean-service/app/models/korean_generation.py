from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base


class KoreanGeneration(Base):
    """국어 문제 생성 세션 모델"""
    __tablename__ = "generations"
    __table_args__ = {"schema": "korean_service"}

    id = Column(Integer, primary_key=True, index=True)
    generation_id = Column(String, unique=True, nullable=False, index=True)

    # 사용자 정보
    user_id = Column(Integer, nullable=False)

    # 교육과정 정보
    school_level = Column(String, nullable=False)  # "중학교", "고등학교"
    grade = Column(Integer, nullable=False)
    semester = Column(String, nullable=False)

    # 국어 과목 정보
    korean_type = Column(String, nullable=False)  # "시", "소설", "수필/비문학", "문법"
    question_type = Column(String, nullable=False)  # "객관식", "서술형", "단답형"
    difficulty = Column(String, nullable=False)  # "상", "중", "하"

    # 요청 설정
    problem_count = Column(Integer, nullable=False)
    korean_type_ratio = Column(JSON, nullable=True)  # {"시": 30, "소설": 40, "수필/비문학": 30}
    question_type_ratio = Column(JSON, nullable=True)  # {"객관식": 50, "서술형": 30, "단답형": 20}
    difficulty_ratio = Column(JSON, nullable=True)  # {"상": 30, "중": 40, "하": 30}
    user_text = Column(Text, nullable=True)

    # 생성 결과
    total_generated = Column(Integer, default=0)
    actual_korean_type_distribution = Column(JSON, nullable=True)
    actual_question_type_distribution = Column(JSON, nullable=True)
    actual_difficulty_distribution = Column(JSON, nullable=True)

    # 비동기 처리
    celery_task_id = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Assignment(Base):
    """국어 과제 모델"""
    __tablename__ = "korean_assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    worksheet_id = Column(Integer, nullable=False)
    classroom_id = Column(Integer, nullable=False)
    teacher_id = Column(Integer, nullable=False)

    # 국어 과목 정보
    korean_type = Column(String, nullable=False)
    question_type = Column(String, nullable=False)
    problem_count = Column(Integer, nullable=False)

    # 배포 상태
    is_deployed = Column(String, default="draft")  # draft, deployed

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AssignmentDeployment(Base):
    """국어 과제 배포 모델"""
    __tablename__ = "korean_assignment_deployments"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, nullable=False)
    student_id = Column(Integer, nullable=False)
    classroom_id = Column(Integer, nullable=False)

    # 상태
    status = Column(String, default="assigned")  # assigned, submitted, graded

    # 시간 관리
    deployed_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)