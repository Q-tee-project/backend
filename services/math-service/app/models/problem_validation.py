"""
문제 검증 결과 모델
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ProblemValidation(Base):
    """문제 검증 결과 모델"""
    __tablename__ = 'problem_validations'

    id = Column(Integer, primary_key=True, index=True)

    # 연관 관계
    problem_id = Column(String, index=True, nullable=True, comment="생성된 문제 ID (임시)")
    generation_session_id = Column(String, index=True, nullable=True, comment="문제 생성 세션 ID")

    # 검증 결과
    is_valid = Column(Boolean, nullable=False, default=False, comment="전체 검증 통과 여부")
    math_accuracy = Column(String(50), nullable=False, comment="수학적 정확성: 정확/오류/의심")
    answer_correctness = Column(String(50), nullable=False, comment="정답 정확성: 정확/오류/의심")
    explanation_quality = Column(String(50), nullable=False, comment="해설 품질: 우수/보통/부족")
    latex_syntax = Column(String(50), nullable=False, comment="LaTeX 문법: 정확/오류/없음")
    difficulty_appropriateness = Column(String(50), nullable=False, comment="난이도 적절성: 적절/쉬움/어려움")

    # 검증 세부 정보
    confidence_score = Column(Float, nullable=False, default=0.0, comment="검증 신뢰도 (0.0-1.0)")
    auto_approve = Column(Boolean, nullable=False, default=False, comment="자동 승인 가능 여부")

    # 검증 내용 (JSON)
    issues = Column(JSON, nullable=True, comment="발견된 문제점들")
    suggestions = Column(JSON, nullable=True, comment="개선 제안사항들")

    # 원본 문제 정보 (검증 당시 스냅샷)
    original_problem = Column(JSON, nullable=False, comment="검증 대상 문제 원본")

    # 검증자 정보
    validator_model = Column(String(100), nullable=False, default="gemini-2.5-flash", comment="검증에 사용된 AI 모델")
    validation_prompt_version = Column(String(50), nullable=True, comment="검증 프롬프트 버전")

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, comment="검증 수행 시간")
    validation_duration_ms = Column(Integer, nullable=True, comment="검증 소요 시간 (밀리초)")

    # 사후 검토 (교사)
    teacher_review_status = Column(String(50), nullable=True, comment="교사 검토 상태: pending/approved/rejected")
    teacher_review_by = Column(String, nullable=True, comment="검토한 교사 ID")
    teacher_review_at = Column(DateTime, nullable=True, comment="교사 검토 시간")
    teacher_review_comment = Column(Text, nullable=True, comment="교사 검토 의견")

    def __repr__(self):
        return f"<ProblemValidation(id={self.id}, is_valid={self.is_valid}, confidence={self.confidence_score})>"

class ValidationSummary(Base):
    """검증 요약 모델 - 세션별 통계"""
    __tablename__ = 'validation_summaries'

    id = Column(Integer, primary_key=True, index=True)

    # 세션 정보
    generation_session_id = Column(String, unique=True, index=True, nullable=False, comment="문제 생성 세션 ID")
    user_id = Column(String, nullable=True, comment="요청 사용자 ID")

    # 통계 정보
    total_problems = Column(Integer, nullable=False, default=0, comment="총 문제 수")
    valid_problems = Column(Integer, nullable=False, default=0, comment="유효한 문제 수")
    invalid_problems = Column(Integer, nullable=False, default=0, comment="무효한 문제 수")
    auto_approved = Column(Integer, nullable=False, default=0, comment="자동 승인된 문제 수")
    manual_review_needed = Column(Integer, nullable=False, default=0, comment="수동 검토 필요한 문제 수")

    # 비율 (%)
    validity_rate = Column(Float, nullable=False, default=0.0, comment="유효율 (%)")
    auto_approval_rate = Column(Float, nullable=False, default=0.0, comment="자동 승인율 (%)")

    # 공통 문제점
    common_issues = Column(JSON, nullable=True, comment="자주 발견되는 문제점들")

    # 성능 정보
    total_validation_time_ms = Column(Integer, nullable=True, comment="총 검증 시간 (밀리초)")
    avg_validation_time_ms = Column(Float, nullable=True, comment="평균 검증 시간 (밀리초)")

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, comment="요약 생성 시간")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="마지막 업데이트 시간")

    def __repr__(self):
        return f"<ValidationSummary(session={self.generation_session_id}, validity_rate={self.validity_rate}%)>"

class ValidationConfig(Base):
    """검증 설정 모델"""
    __tablename__ = 'validation_configs'

    id = Column(Integer, primary_key=True, index=True)

    # 설정 정보
    config_name = Column(String(100), unique=True, nullable=False, comment="설정 이름")
    description = Column(Text, nullable=True, comment="설정 설명")

    # 검증 기준
    min_confidence_score = Column(Float, nullable=False, default=0.8, comment="자동 승인 최소 신뢰도")
    enable_latex_validation = Column(Boolean, nullable=False, default=True, comment="LaTeX 문법 검증 활성화")
    enable_difficulty_validation = Column(Boolean, nullable=False, default=True, comment="난이도 적절성 검증 활성화")

    # AI 모델 설정
    validator_model = Column(String(100), nullable=False, default="gemini-2.5-flash", comment="검증 모델")
    validator_temperature = Column(Float, nullable=False, default=0.1, comment="검증 모델 temperature")
    validator_max_tokens = Column(Integer, nullable=False, default=2048, comment="검증 모델 최대 토큰")

    # 활성화 상태
    is_active = Column(Boolean, nullable=False, default=True, comment="설정 활성화 여부")

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, comment="설정 생성 시간")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="마지막 업데이트 시간")
    created_by = Column(String, nullable=True, comment="설정 생성자")

    def __repr__(self):
        return f"<ValidationConfig(name={self.config_name}, active={self.is_active})>"