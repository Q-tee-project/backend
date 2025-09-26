from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Assignment(Base):
    """과제 정보"""
    __tablename__ = "assignments"
    __table_args__ = {"schema": "english_service"}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    worksheet_id = Column(Integer, ForeignKey("english_service.worksheets.worksheet_id"), nullable=False)
    classroom_id = Column(Integer, nullable=False)
    teacher_id = Column(Integer, nullable=False)

    # 과제 메타데이터
    problem_type = Column(String(20), nullable=False)
    total_questions = Column(Integer, nullable=False)

    # 배포 상태
    is_deployed = Column(String, default="draft")  # draft, deployed, completed

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    worksheet = relationship("Worksheet")


class AssignmentDeployment(Base):
    """과제 배포 정보"""
    __tablename__ = "assignment_deployments"
    __table_args__ = {"schema": "english_service"}

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("english_service.assignments.id"), nullable=False)
    student_id = Column(Integer, nullable=False)
    classroom_id = Column(Integer, nullable=False)

    # 배포 상태
    status = Column(String, default="assigned")  # assigned, started, completed

    # 배포 시간
    deployed_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    # 관계
    assignment = relationship("Assignment", backref="deployments")
