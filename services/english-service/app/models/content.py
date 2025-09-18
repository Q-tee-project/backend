from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.database import Base


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