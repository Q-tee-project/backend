from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base


# Grading Results 테이블 모델 (채점 결과)
class GradingResult(Base):
    __tablename__ = "grading_results"
    __table_args__ = {"schema": "english_service"}

    result_id = Column(String(50), primary_key=True, index=True)  # UUID 기본키
    worksheet_id = Column(Integer, ForeignKey("english_service.worksheets.worksheet_id"), nullable=False)
    student_name = Column(String(100), nullable=False)
    completion_time = Column(Integer, nullable=False)  # 소요 시간 (초)
    total_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    needs_review = Column(Boolean, default=False)
    is_reviewed = Column(Boolean, default=False)  # 검수 완료 여부
    reviewed_at = Column(DateTime, nullable=True)  # 검수 완료 시간
    reviewed_by = Column(String(100), nullable=True)  # 검수자
    created_at = Column(DateTime, nullable=False)

    # 관계 설정
    worksheet = relationship("Worksheet")
    question_results = relationship("QuestionResult", back_populates="grading_result", cascade="all, delete-orphan")


# Question Results 테이블 모델 (문제별 채점 결과)
class QuestionResult(Base):
    __tablename__ = "question_results"
    __table_args__ = {"schema": "english_service"}

    id = Column(Integer, primary_key=True, index=True)
    grading_result_id = Column(String(50), ForeignKey("english_service.grading_results.result_id"), nullable=False)
    question_id = Column(Integer, nullable=False)
    question_type = Column(String(20), nullable=False)
    student_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    grading_method = Column(String(10), nullable=False)  # "db" | "ai"
    ai_feedback = Column(Text, nullable=True)
    needs_review = Column(Boolean, default=False)

    # 검수 관련 필드
    reviewed_score = Column(Integer, nullable=True)  # 검수 후 점수
    reviewed_feedback = Column(Text, nullable=True)  # 검수 후 피드백
    is_reviewed = Column(Boolean, default=False)  # 개별 문제 검수 여부
    created_at = Column(DateTime, nullable=False)

    # 관계 설정
    grading_result = relationship("GradingResult", back_populates="question_results")