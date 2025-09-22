from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


# Worksheets 테이블 모델 (문제지 메타데이터)
class Worksheet(Base):
    __tablename__ = "worksheets"
    __table_args__ = {"schema": "english_service"}

    worksheet_id = Column(Integer, primary_key=True, index=True)  # 문제지 ID
    teacher_id = Column(Integer, nullable=False)    # 선생님 ID
    worksheet_name = Column(String(200), nullable=False)  # 문제지 제목
    school_level = Column(String(20), nullable=False)  # 중학교, 고등학교 등
    grade = Column(String(10), nullable=False)  # 1, 2, 3 등
    subject = Column(String(50), nullable=False, default="영어")  # 과목
    problem_type = Column(String(20), nullable=False, default="혼합형")  # 문제 유형: 독해, 문법, 어휘, 혼합형
    total_questions = Column(Integer, nullable=False)  # 총 문제 수
    duration = Column(Integer, nullable=True)  # 시험 시간(분)
    created_at = Column(DateTime, nullable=False)  # 생성 시간

    # 관계 설정
    passages = relationship("Passage", back_populates="worksheet", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="worksheet", cascade="all, delete-orphan")


# Passages 테이블 모델 (지문)
class Passage(Base):
    __tablename__ = "passages"
    __table_args__ = {"schema": "english_service"}

    id = Column(Integer, primary_key=True, index=True)
    worksheet_id = Column(Integer, ForeignKey("english_service.worksheets.worksheet_id"), nullable=False)  # 문제지 ID
    passage_id = Column(Integer, nullable=False)  # "1", "2" 등
    passage_type = Column(String(50), nullable=False)  # article, dialogue 등
    passage_content = Column(JSON, nullable=False)  # 지문 내용 (JSON 형태)
    original_content = Column(JSON, nullable=True)  # 원본 지문 내용
    korean_translation = Column(JSON, nullable=True)  # 한글 번역 지문 내용
    related_questions = Column(JSON, nullable=False)  # 연관 문제 ID 배열
    created_at = Column(DateTime, nullable=False)

    # 관계 설정
    worksheet = relationship("Worksheet", back_populates="passages")



# Questions 테이블 모델 (문제)
class Question(Base):
    __tablename__ = "questions"
    __table_args__ = {"schema": "english_service"}

    id = Column(Integer, primary_key=True, index=True)
    worksheet_id = Column(Integer, ForeignKey("english_service.worksheets.worksheet_id"), nullable=False)  # 문제지 ID
    question_id = Column(Integer, nullable=False)  # "1", "2" 등
    question_text = Column(Text, nullable=False)  # 문제 질문
    question_type = Column(String(20), nullable=False)  # 객관식, 단답형, 서술형
    question_subject = Column(String(20), nullable=False)  # 독해, 문법, 어휘
    question_detail_type = Column(String(100), nullable=True)  # 세부 유형
    question_difficulty = Column(String(10), nullable=False)  # 상, 중, 하
    question_choices = Column(JSON, nullable=True)  # 선택지 (객관식인 경우)
    passage_id = Column(Integer, nullable=True)  # 연관 지문 ID
    correct_answer = Column(Text, nullable=True) # 정답
    example_content = Column(Text, nullable=False)  # 예문 내용
    example_original_content = Column(Text, nullable=True) # 예문 원본 내용
    example_korean_translation = Column(Text, nullable=True) # 예문 한글 번역
    explanation = Column(Text, nullable=True) # 해설
    learning_point = Column(Text, nullable=True) # 학습 포인트
    created_at = Column(DateTime, nullable=False)

    # 관계 설정
    worksheet = relationship("Worksheet", back_populates="questions")