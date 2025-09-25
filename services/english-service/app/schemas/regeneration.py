from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Dict, Any, List
from enum import Enum


class QuestionType(str, Enum):
    """문제 유형"""
    MULTIPLE_CHOICE = "객관식"
    SHORT_ANSWER = "단답형"
    ESSAY = "서술형"


class QuestionSubject(str, Enum):
    """문제 영역"""
    READING = "독해"
    GRAMMAR = "문법"
    VOCABULARY = "어휘"


class Difficulty(str, Enum):
    """난이도"""
    HIGH = "상"
    MEDIUM = "중"
    LOW = "하"


class WorksheetType(str, Enum):
    """문제지 유형"""
    READING = "독해"
    GRAMMAR = "문법"
    VOCABULARY = "어휘"
    MIXED = "혼합형"


class WorksheetContext(BaseModel):
    """문제지 컨텍스트 정보"""
    school_level: str = Field(..., description="학교급 (중학교, 고등학교)")
    grade: int = Field(..., ge=1, le=3, description="학년 (1-3)")
    worksheet_type: WorksheetType = Field(..., description="문제지 유형")


class QuestionRegenerationRequest(BaseModel):
    """문제 재생성 요청"""

    # 사용자 피드백
    feedback: str = Field(..., min_length=1, description="문제 수정 요구사항")

    # 기본 제약조건
    keep_passage: bool = Field(default=True, description="지문 유지 여부")
    regenerate_related_questions: bool = Field(default=False, description="연계된 문제들도 함께 재생성 여부")
    keep_question_type: bool = Field(default=True, description="문제 유형(객관식/단답형/서술형) 유지 여부")
    keep_difficulty: bool = Field(default=True, description="난이도 유지 여부")
    keep_subject: bool = Field(default=True, description="문제 영역(독해/문법/어휘) 유지 여부")
    keep_detail_type: bool = Field(default=True, description="세부 영역 유지 여부")

    # 문제지 컨텍스트 (필수)
    worksheet_context: WorksheetContext = Field(..., description="문제지 전체 컨텍스트")

    # 현재 문제 정보 (유지할 값들)
    current_question_type: QuestionType = Field(..., description="현재 문제 유형")
    current_subject: QuestionSubject = Field(..., description="현재 문제 영역")
    current_detail_type: str = Field(..., description="현재 세부 영역")
    current_difficulty: Difficulty = Field(..., description="현재 난이도")

    # 변경 요청 사항 (선택적)
    target_question_type: Optional[QuestionType] = Field(default=None, description="변경하고 싶은 문제 유형")
    target_subject: Optional[QuestionSubject] = Field(default=None, description="변경하고 싶은 문제 영역")
    target_detail_type: Optional[str] = Field(default=None, description="변경하고 싶은 세부 영역")
    target_difficulty: Optional[Difficulty] = Field(default=None, description="변경하고 싶은 난이도")

    # 추가 요구사항
    additional_requirements: Optional[str] = Field(default=None, description="추가 요구사항")

    @validator('target_question_type')
    def validate_target_question_type(cls, v, values):
        if v is not None and values.get('keep_question_type', True):
            raise ValueError("keep_question_type이 True일 때는 target_question_type을 설정할 수 없습니다")
        return v

    @validator('target_subject')
    def validate_target_subject(cls, v, values):
        if v is not None and values.get('keep_subject', True):
            raise ValueError("keep_subject가 True일 때는 target_subject를 설정할 수 없습니다")
        return v

    @validator('target_detail_type')
    def validate_target_detail_type(cls, v, values):
        if v is not None and values.get('keep_detail_type', True):
            raise ValueError("keep_detail_type이 True일 때는 target_detail_type을 설정할 수 없습니다")
        return v

    @validator('target_difficulty')
    def validate_target_difficulty(cls, v, values):
        if v is not None and values.get('keep_difficulty', True):
            raise ValueError("keep_difficulty가 True일 때는 target_difficulty를 설정할 수 없습니다")
        return v


class RegenerationResponse(BaseModel):
    """재생성 응답"""
    status: Literal["success", "partial_success", "error"] = Field(..., description="처리 상태")
    message: str = Field(..., description="처리 결과 메시지")

    # 성공시 반환 정보
    regenerated_passage: Optional[Dict[str, Any]] = Field(default=None, description="재생성된 지문 정보")
    regenerated_questions: Optional[List[Dict[str, Any]]] = Field(default=None, description="재생성된 모든 문제들 (메인 + 연관)")

    # 부분 실패시 반환 정보
    warnings: Optional[List[str]] = Field(default=None, description="부분 실패시 경고 메시지들")
    failed_questions: Optional[List[Dict[str, Any]]] = Field(default=None, description="실패한 문제들의 정보")

    # 오류시 반환 정보
    error_details: Optional[str] = Field(default=None, description="오류 상세 정보")


class QuestionDataRegenerationRequest(BaseModel):
    """데이터 기반 문제 재생성 요청"""
    questions_data: List[Dict[str, Any]] = Field(..., description="원본 문제 데이터들 (메인 문제 + 연관 문제들)")
    passage_data: Optional[Dict[str, Any]] = Field(None, description="원본 지문 데이터")
    regeneration_request: QuestionRegenerationRequest = Field(..., description="재생성 조건")


class RegenerationPromptData(BaseModel):
    """AI 프롬프트 생성을 위한 데이터"""
    original_question: Dict[str, Any] = Field(..., description="원본 문제 데이터")
    original_passage: Optional[Dict[str, Any]] = Field(default=None, description="원본 지문 데이터")

    user_feedback: str = Field(..., description="사용자 피드백")
    worksheet_context: WorksheetContext = Field(..., description="문제지 컨텍스트")

    # 최종 적용될 문제 조건들
    final_question_type: QuestionType = Field(..., description="최종 문제 유형")
    final_subject: QuestionSubject = Field(..., description="최종 문제 영역")
    final_detail_type: str = Field(..., description="최종 세부 영역")
    final_difficulty: Difficulty = Field(..., description="최종 난이도")

    keep_passage: bool = Field(..., description="지문 유지 여부")
    additional_requirements: Optional[str] = Field(default=None, description="추가 요구사항")