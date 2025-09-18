from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any


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
class WorksheetGenerationRequest(BaseModel):
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