from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


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