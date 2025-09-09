from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

# 열거형 정의
class SchoolLevel(str, Enum):
    MIDDLE = "중학교"
    HIGH = "고등학교"

class Grade(int, Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3

class Subject(str, Enum):
    ALL = "전체"
    READING = "독해"
    GRAMMAR = "문법"
    VOCABULARY = "어휘"

class QuestionFormat(str, Enum):
    ALL = "전체"
    MULTIPLE_CHOICE = "객관식"
    SHORT_ANSWER = "주관식"
    ESSAY = "서술형"

class Difficulty(str, Enum):
    HIGH = "상"
    MEDIUM = "중"
    LOW = "하"

# 세부영역 선택 스키마 (직접 내용 입력)
class SubjectDetails(BaseModel):
    reading_types: Optional[List[str]] = Field(default=[], description="선택된 독해 유형들 (예: ['일반 글', '서신/소통', '대화문'])")
    grammar_categories: Optional[List[str]] = Field(default=[], description="선택된 문법 카테고리들 (예: ['시제', '조동사', '관계사'])")
    grammar_topics: Optional[List[str]] = Field(default=[], description="선택된 문법 토픽들 (예: ['현재완료', '과거완료', '미래완료'])")
    vocabulary_categories: Optional[List[str]] = Field(default=[], description="선택된 어휘 카테고리들 (예: ['일상생활', '학교생활', '취미활동'])")

# 문제 비율 스키마
class SubjectRatio(BaseModel):
    subject: str = Field(..., description="영역명 (독해, 문법, 어휘)")
    ratio: int = Field(..., ge=0, le=100, description="해당 영역의 비율 (0-100%)")

# 문제 형식별 비율 스키마
class FormatRatio(BaseModel):
    format: str = Field(..., description="문제 형식 (객관식, 주관식, 서술형)")
    ratio: int = Field(..., ge=0, le=100, description="해당 형식의 비율 (0-100%)")

# 난이도 분배 스키마
class DifficultyDistribution(BaseModel):
    difficulty: str = Field(..., description="난이도 (상, 중, 하)")
    ratio: int = Field(..., ge=0, le=100, description="해당 난이도의 비율 (0-100%)")

# 메인 문제 생성 요청 스키마
class QuestionGenerationRequest(BaseModel):
    # 기본 정보
    school_level: str = Field(..., description="학교급")
    grade: int = Field(..., ge=1, le=3, description="학년")
    total_questions: int = Field(..., ge=1, le=100, description="총 문제 수 (1-100)")
    
    # 영역 선택 (복수 선택 가능)
    subjects: List[str] = Field(..., description="선택된 영역들 (독해, 문법, 어휘)")
    subject_details: SubjectDetails = Field(default=SubjectDetails(), description="영역별 세부영역 선택")
    
    # 문제 비율
    subject_ratios: List[SubjectRatio] = Field(..., description="영역별 문제 비율")
    
    # 문제 형식
    question_format: str = Field(..., description="문제 형식")
    format_ratios: List[FormatRatio] = Field(default=[], description="형식별 비율")
    
    # 난이도 분배
    difficulty_distribution: List[DifficultyDistribution] = Field(..., description="난이도별 분배")
    
    # 추가 요구사항
    additional_requirements: Optional[str] = Field(None, description="추가 요구사항 (선택사항)")
    
    @validator('subject_ratios')
    def validate_subject_ratios(cls, v):
        if v:  # 비어있지 않을 때만 검증
            total_ratio = sum(ratio.ratio for ratio in v)
            if total_ratio != 100:
                raise ValueError('영역별 비율의 합계는 100%여야 합니다')
        return v
    
    @validator('format_ratios')
    def validate_format_ratios(cls, v):
        if v:  # 비어있지 않을 때만 검증
            total_ratio = sum(fr.ratio for fr in v)
            if total_ratio != 100:
                raise ValueError('형식별 비율의 합계는 100%여야 합니다')
        return v
    
    @validator('difficulty_distribution')
    def validate_difficulty_distribution(cls, v):
        if v:  # 비어있지 않을 때만 검증
            total_ratio = sum(dd.ratio for dd in v)
            if total_ratio != 100:
                raise ValueError('난이도별 분배의 합계는 100%여야 합니다')
        return v

# 응답 스키마 (간소화)
class QuestionGenerationResponse(BaseModel):
    message: str
    status: str = "received"
    request_data: Optional[Dict[str, Any]] = None

# 카테고리 정보 응답 스키마들
class GrammarCategoryResponse(BaseModel):
    id: int
    name: str
    topics: List[Dict[str, Any]] = []

class VocabularyCategoryResponse(BaseModel):
    id: int
    name: str

class ReadingTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    level: str

class CategoriesResponse(BaseModel):
    grammar_categories: List[GrammarCategoryResponse]
    vocabulary_categories: List[VocabularyCategoryResponse]
    reading_types: List[ReadingTypeResponse]

# ===========================================
# 지문 유형 관련 스키마들 (간단 버전)
# ===========================================

# 지문 유형 생성 요청 스키마
class TextTypeCreate(BaseModel):
    type_name: str = Field(..., description="지문 유형 이름 (영문, 예: article, correspondence)")
    display_name: str = Field(..., description="지문 유형 표시명 (한글)")
    description: Optional[str] = Field(None, description="유형 설명")
    json_format: Dict[str, Any] = Field(..., description="JSON 형식 예시")

# 지문 유형 수정 요청 스키마
class TextTypeUpdate(BaseModel):
    display_name: Optional[str] = Field(None, description="지문 유형 표시명 (한글)")
    description: Optional[str] = Field(None, description="유형 설명")
    json_format: Optional[Dict[str, Any]] = Field(None, description="JSON 형식 예시")

# 지문 유형 응답 스키마
class TextTypeResponse(BaseModel):
    id: int
    type_name: str
    display_name: str
    description: Optional[str]
    json_format: Dict[str, Any]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True
