from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.sql import func
from ..database import Base


class KoreanGradingSession(Base):
    """국어 채점 세션 모델"""
    __tablename__ = "grading_sessions"
    __table_args__ = {"schema": "korean_service"}

    id = Column(Integer, primary_key=True, index=True)
    worksheet_id = Column(Integer, nullable=False)
    student_id = Column(Integer, nullable=False)  # 학생 ID
    graded_by = Column(Integer, nullable=False)  # 채점한 사용자 ID

    # 채점 정보
    total_problems = Column(Integer, nullable=False)
    correct_count = Column(Integer, default=0)
    total_score = Column(Float, default=0.0)
    max_possible_score = Column(Float, nullable=False)
    points_per_problem = Column(Float, nullable=False)

    # 입력 방식
    input_method = Column(String, nullable=False)  # "ocr", "manual", "mixed"

    # OCR 관련
    ocr_text = Column(Text, nullable=True)
    ocr_results = Column(JSON, nullable=True)

    # 객관식 답안 (직접 입력)
    multiple_choice_answers = Column(JSON, nullable=True)

    # 비동기 처리
    celery_task_id = Column(String, nullable=True)

    # 상태
    status = Column(String, default="pending_approval") # pending_approval, approved, rejected

    # 승인 정보
    teacher_id = Column(Integer, nullable=True)  # 승인한 선생님 ID
    approved_at = Column(DateTime(timezone=True), nullable=True) # 승인 시간

    # 시간 관리
    graded_at = Column(DateTime(timezone=True), server_default=func.now())


class KoreanProblemGradingResult(Base):
    """국어 문제별 채점 결과 모델"""
    __tablename__ = "problem_grading_results"
    __table_args__ = {"schema": "korean_service"}

    id = Column(Integer, primary_key=True, index=True)
    grading_session_id = Column(Integer, ForeignKey("korean_service.grading_sessions.id"), nullable=False)
    problem_id = Column(Integer, nullable=False)

    # 답안 정보
    user_answer = Column(Text, nullable=True)  # 사용자가 입력한 답안
    actual_user_answer = Column(Text, nullable=True)  # OCR로 인식된 실제 답안
    correct_answer = Column(Text, nullable=False)

    # 채점 결과
    is_correct = Column(Boolean, nullable=False)
    score = Column(Float, nullable=False)
    points_per_problem = Column(Float, nullable=False)

    # 문제 정보
    problem_type = Column(String, nullable=False)  # "객관식", "서술형", "단답형"
    input_method = Column(String, nullable=False)  # "ocr", "manual"

    # AI 채점 결과 (서술형의 경우)
    ai_score = Column(Float, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    keyword_score_ratio = Column(Float, nullable=True)

    # 해설
    explanation = Column(Text, nullable=True)