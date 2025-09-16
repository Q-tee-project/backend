from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class ProblemType(str, enum.Enum):
    MULTIPLE_CHOICE = "객관식"
    ESSAY = "서술형"
    SHORT_ANSWER = "단답형"


class Difficulty(str, enum.Enum):
    HIGH = "상"
    MEDIUM = "중"
    LOW = "하"


class KoreanType(str, enum.Enum):
    POEM = "시"
    NOVEL = "소설"
    NON_FICTION = "수필/비문학"
    GRAMMAR = "문법"


class Problem(Base):
    """국어 문제 모델"""
    __tablename__ = "problems"
    __table_args__ = {"schema": "korean_service"}

    id = Column(Integer, primary_key=True, index=True)

    # 문제지 관계
    worksheet_id = Column(Integer, ForeignKey("korean_service.worksheets.id"), nullable=False)

    # 문제 순서
    sequence_order = Column(Integer, nullable=False)

    # 문제 분류
    korean_type = Column(Enum(KoreanType), nullable=False)  # 국어 문제 유형
    problem_type = Column(Enum(ProblemType), nullable=False)  # 문제 형식
    difficulty = Column(Enum(Difficulty), nullable=False)  # 난이도

    # 문제 내용
    question = Column(Text, nullable=False)  # 문제 텍스트
    choices = Column(JSON, nullable=True)  # 객관식 선택지 ["A", "B", "C", "D"]
    correct_answer = Column(Text, nullable=False)  # 정답
    explanation = Column(Text, nullable=False)  # 해설

    # 국어 특화 필드
    source_text = Column(Text, nullable=True)  # 출처 지문 (시, 소설 등)
    source_title = Column(String, nullable=True)  # 출처 제목
    source_author = Column(String, nullable=True)  # 출처 작가

    # AI 생성 관련
    ai_model_used = Column(String, nullable=True)  # 사용된 AI 모델
    generation_prompt = Column(Text, nullable=True)  # 생성에 사용된 프롬프트

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    worksheet = relationship("Worksheet", back_populates="problems")