from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Assignment(Base):
    """국어 과제 모델"""
    __tablename__ = "korean_assignments"
    __table_args__ = {"schema": "korean_service"}

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
    __table_args__ = {"schema": "korean_service"}

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("korean_service.korean_assignments.id"), nullable=False)
    student_id = Column(Integer, nullable=False)
    classroom_id = Column(Integer, nullable=False)

    # 상태
    status = Column(String, default="assigned")  # assigned, submitted, graded

    # 시간 관리
    deployed_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)

    # 관계
    assignment = relationship("Assignment", backref="deployments")