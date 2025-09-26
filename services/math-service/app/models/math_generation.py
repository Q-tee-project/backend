from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class MathProblemGeneration(Base):
    """수학 문제 생성 세션 기록"""
    __tablename__ = "math_problem_generations"
    __table_args__ = {"schema": "math_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    generation_id = Column(String, unique=True, nullable=False, index=True)
    
    # 교육과정 정보
    school_level = Column(String, nullable=False)  # "초등학교", "중학교", "고등학교"
    grade = Column(Integer, nullable=False)
    semester = Column(String, nullable=False)
    unit_number = Column(String, nullable=False)
    unit_name = Column(String, nullable=False)
    chapter_number = Column(String, nullable=False)
    chapter_name = Column(String, nullable=False)
    
    # 생성 설정
    problem_count = Column(Integer, nullable=False)  # 10 or 20
    difficulty_ratio = Column(JSON, nullable=False)  # {"A": 30, "B": 40, "C": 30}
    problem_type_ratio = Column(JSON, nullable=False)  # {"multiple_choice": 50, "essay": 30, "short_answer": 20}
    
    # 사용자 입력
    user_text = Column(Text, nullable=False)
    
    # 생성 결과 요약
    actual_difficulty_distribution = Column(JSON)  # 실제 생성된 난이도 분포
    actual_type_distribution = Column(JSON)  # 실제 생성된 유형 분포
    total_generated = Column(Integer)  # 실제 생성된 문제 수
    
    # 메타데이터
    created_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    # problems relationship removed since Problem model no longer exists


class Assignment(Base):
    """과제 정보"""
    __tablename__ = "assignments"
    __table_args__ = {"schema": "math_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    worksheet_id = Column(Integer, nullable=False)  # 워크시트 ID 참조
    classroom_id = Column(Integer, nullable=False)  # 클래스룸 ID
    teacher_id = Column(Integer, nullable=False)  # 교사 ID
    
    # 과제 메타데이터
    unit_name = Column(String, nullable=False)
    chapter_name = Column(String, nullable=False)
    problem_count = Column(Integer, nullable=False)
    
    # 배포 상태
    is_deployed = Column(String, default="draft")  # draft, deployed, completed
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AssignmentDeployment(Base):
    """과제 배포 정보"""
    __tablename__ = "assignment_deployments"
    __table_args__ = {"schema": "math_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("math_service.assignments.id"), nullable=False)
    student_id = Column(Integer, nullable=False)  # 학생 ID
    classroom_id = Column(Integer, nullable=False)  # 클래스룸 ID
    
    # 배포 상태
    status = Column(String, default="assigned")  # assigned, started, completed
    
    # 배포 시간
    deployed_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # 관계
    assignment = relationship("Assignment", backref="deployments")


# ===== 테스트 세션 관련 모델 =====

class TestSession(Base):
    """테스트 세션 모델"""
    __tablename__ = "test_sessions"
    __table_args__ = {"schema": "math_service"}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)  # UUID
    assignment_id = Column(Integer, ForeignKey("math_service.assignments.id"), nullable=False)
    student_id = Column(Integer, nullable=False)  # 학생 ID

    # 세션 상태
    status = Column(String, default="started")  # started, completed, submitted

    # 시간 정보
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))

    # 관계
    assignment = relationship("Assignment", backref="test_sessions")
    test_answers = relationship("TestAnswer", back_populates="test_session")


class TestAnswer(Base):
    """테스트 답안 모델"""
    __tablename__ = "test_answers"
    __table_args__ = {"schema": "math_service"}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("math_service.test_sessions.session_id"), nullable=False)
    problem_id = Column(Integer, nullable=False)  # 문제 ID
    answer = Column(Text)  # 학생 답안

    # 시간 정보
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    test_session = relationship("TestSession", back_populates="test_answers")


# GeneratedProblemSet 모델 제거됨 - Problem 테이블의 sequence_order와 worksheet_id로 대체