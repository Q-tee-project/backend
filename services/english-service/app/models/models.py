from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base

# Grammar Categories 테이블 모델
class GrammarCategory(Base):
    __tablename__ = "grammar_categories"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    topics = relationship("GrammarTopic", back_populates="category")

# Grammar Topics 테이블 모델
class GrammarTopic(Base):
    __tablename__ = "grammar_topics"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("english_service.grammar_categories.id"), nullable=False)
    name = Column(String(200), nullable=False)  # 길이가 200으로 변경됨
    learning_objective = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    category = relationship("GrammarCategory", back_populates="topics")
    achievements = relationship("GrammarAchievement", back_populates="topic")

# Grammar Achievements 테이블 모델
class GrammarAchievement(Base):
    __tablename__ = "grammar_achievements"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("english_service.grammar_topics.id"), nullable=False)
    level = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=True)  # created_at 추가됨
    
    # 관계 설정
    topic = relationship("GrammarTopic", back_populates="achievements")

# Vocabulary Categories 테이블 모델
class VocabularyCategory(Base):
    __tablename__ = "vocabulary_categories"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 길이 제한 없음
    learning_objective = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)

# Words 테이블 모델
class Word(Base):
    __tablename__ = "words"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=True)

# Reading Types 테이블 모델  
class ReadingType(Base):
    __tablename__ = "reading_types"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 길이 제한 없음
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)

# Text Types 테이블 모델 (지문 유형과 JSON 형식)
class TextType(Base):
    __tablename__ = "text_types"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(50), nullable=False, unique=True)  # article, correspondence, dialogue 등
    display_name = Column(String(100), nullable=False)  # 한국어 표시명
    description = Column(Text, nullable=True)  # 유형 설명
    json_format = Column(JSON, nullable=False)  # 각 유형별 JSON 형식 예시
    created_at = Column(DateTime, nullable=True)

# Worksheets 테이블 모델 (문제지 메타데이터)
class Worksheet(Base):
    __tablename__ = "worksheets"
    __table_args__ = {"schema": "english_service"}
    
    worksheet_id = Column(String(50), primary_key=True, index=True)
    worksheet_name = Column(String(200), nullable=False)  # 문제지 제목
    school_level = Column(String(20), nullable=False)  # 중학교, 고등학교 등
    grade = Column(String(10), nullable=False)  # 1, 2, 3 등
    subject = Column(String(50), nullable=False, default="영어")  # 과목
    total_questions = Column(Integer, nullable=False)  # 총 문제 수
    duration = Column(Integer, nullable=True)  # 시험 시간(분)
    created_at = Column(DateTime, nullable=False)
    
    # 관계 설정
    passages = relationship("Passage", back_populates="worksheet", cascade="all, delete-orphan")
    examples = relationship("Example", back_populates="worksheet", cascade="all, delete-orphan") 
    questions = relationship("Question", back_populates="worksheet", cascade="all, delete-orphan")

# Passages 테이블 모델 (지문)
class Passage(Base):
    __tablename__ = "passages"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    worksheet_id = Column(String(50), ForeignKey("english_service.worksheets.worksheet_id"), nullable=False)
    passage_id = Column(Integer, nullable=False)  # "1", "2" 등
    passage_type = Column(String(50), nullable=False)  # article, dialogue 등
    passage_content = Column(JSON, nullable=False)  # 지문 내용 (JSON 형태)
    original_content = Column(JSON, nullable=True)
    korean_translation = Column(JSON, nullable=True)
    related_questions = Column(JSON, nullable=False)  # 연관 문제 ID 배열
    created_at = Column(DateTime, nullable=False)
    
    # 관계 설정
    worksheet = relationship("Worksheet", back_populates="passages")

# Examples 테이블 모델 (예문)
class Example(Base):
    __tablename__ = "examples"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    worksheet_id = Column(String(50), ForeignKey("english_service.worksheets.worksheet_id"), nullable=False)
    example_id = Column(Integer, nullable=False)  # "1", "2" 등
    example_content = Column(Text, nullable=False)  # 예문 내용
    original_content = Column(Text, nullable=True)
    korean_translation = Column(Text, nullable=True)
    related_question = Column(Integer, nullable=True)  # 연관 문제 ID
    created_at = Column(DateTime, nullable=False)
    
    # 관계 설정
    worksheet = relationship("Worksheet", back_populates="examples")

# Questions 테이블 모델 (문제)
class Question(Base):
    __tablename__ = "questions"
    __table_args__ = {"schema": "english_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    worksheet_id = Column(String(50), ForeignKey("english_service.worksheets.worksheet_id"), nullable=False)
    question_id = Column(Integer, nullable=False)  # "1", "2" 등
    question_text = Column(Text, nullable=False)  # 문제 질문
    question_type = Column(String(20), nullable=False)  # 객관식, 주관식, 서술형
    question_subject = Column(String(20), nullable=False)  # 독해, 문법, 어휘
    question_difficulty = Column(String(10), nullable=False)  # 상, 중, 하
    question_detail_type = Column(String(100), nullable=True)  # 세부 유형
    question_choices = Column(JSON, nullable=True)  # 선택지 (객관식인 경우)
    passage_id = Column(Integer, nullable=True)  # 연관 지문 ID
    example_id = Column(Integer, nullable=True)  # 연관 예문 ID
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    learning_point = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    
    # 관계 설정
    worksheet = relationship("Worksheet", back_populates="questions")

# Grading Results 테이블 모델 (채점 결과)
class GradingResult(Base):
    __tablename__ = "grading_results"
    __table_args__ = {"schema": "english_service"}
    
    result_id = Column(String(50), primary_key=True, index=True)  # UUID 기본키
    worksheet_id = Column(String(50), ForeignKey("english_service.worksheets.worksheet_id"), nullable=False)
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