from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
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