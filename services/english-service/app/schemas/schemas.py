from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
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

# 지문 유형 관련 스키마들 제거 (사용하지 않음)

# ====================================
# 문제지 저장 관련 스키마
# ====================================

# 문제지 저장 요청 스키마
class WorksheetSaveRequest(BaseModel):
    worksheet_data: Dict[str, Any] = Field(..., description="생성된 통합 문제지 JSON 데이터 (문제지+답안지)")

# 지문 스키마
class PassageResponse(BaseModel):
    id: int
    passage_id: int
    passage_type: str
    passage_content: Dict[str, Any]
    related_questions: List[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 예문 스키마
class ExampleResponse(BaseModel):
    id: int
    example_id: int
    example_content: str
    related_question: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 문제 스키마
class QuestionResponse(BaseModel):
    id: int
    question_id: int
    question_text: str
    question_type: str
    question_subject: str
    question_difficulty: str
    question_detail_type: Optional[str]
    question_choices: Optional[List[str]]
    passage_id: Optional[int]
    example_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 답안지 스키마
class AnswerSheetResponse(BaseModel):
    id: int
    answer_data: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 문제지 전체 응답 스키마
class WorksheetResponse(BaseModel):
    worksheet_id: str
    worksheet_name: str
    school_level: str
    grade: str
    subject: str
    total_questions: int
    duration: Optional[int]
    created_at: datetime
    passages: List[PassageResponse]
    examples: List[ExampleResponse]
    questions: List[QuestionResponse]
    
    class Config:
        from_attributes = True

# 문제지 목록 조회용 간단한 스키마
class WorksheetSummary(BaseModel):
    id: str  # worksheet_id와 동일한 값
    worksheet_id: str
    worksheet_name: str
    school_level: str
    grade: str
    subject: str
    total_questions: int
    duration: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 문제별 채점 결과 스키마 (간소화)
class QuestionResultResponse(BaseModel):
    question_id: int
    question_type: str
    student_answer: Optional[str]
    correct_answer: Optional[str]
    score: int
    max_score: int
    is_correct: bool
    grading_method: str
    ai_feedback: Optional[str]
    # 검수 관련 필드들 및 id, created_at 제거
    
    class Config:
        from_attributes = True

# 지문 원문 정보 스키마 (채점 결과용)
class PassageInfo(BaseModel):
    passage_id: int
    original_content: str
    korean_translation: Optional[str] = None
    text_type: Optional[str] = None

# 예문 원문 정보 스키마 (채점 결과용)  
class ExampleInfo(BaseModel):
    example_id: int
    original_content: str
    korean_translation: Optional[str] = None

# 채점 결과 전체 스키마 (문제지 데이터 포함)
class GradingResultResponse(BaseModel):
    result_id: str  # id 제거, result_id만 사용
    worksheet_id: str
    student_name: str
    completion_time: int
    total_score: int
    max_score: int
    percentage: float
    question_results: List[QuestionResultResponse] = []
    student_answers: Dict[int, str] = {}  # 학생 답안 딕셔너리
    created_at: datetime
    worksheet_data: Dict[str, Any] = {}  # 문제지 데이터 포함
    
    class Config:
        from_attributes = True

# 채점 결과 목록 조회용 간단한 스키마
class GradingResultSummary(BaseModel):
    id: str  # result_id가 UUID 문자열이므로 str로 변경
    result_id: str
    worksheet_id: str
    student_name: str
    completion_time: int
    total_score: int
    max_score: int
    percentage: float
    needs_review: bool
    is_reviewed: bool
    created_at: datetime
    worksheet_name: Optional[str]  # 조인으로 가져온 문제지 이름
    
    class Config:
        from_attributes = True

# 검수 요청 스키마
class ReviewRequest(BaseModel):
    question_results: Dict[int, Dict[str, Any]]  # question_id -> {score, feedback}
    reviewed_by: Optional[str] = "교사"
    
# 답안 제출 요청 스키마
class SubmissionRequest(BaseModel):
    student_name: str  # 학생 이름
    answers: Dict[int, str]  # question_id -> answer
    completion_time: int  # 소요 시간 (초)
