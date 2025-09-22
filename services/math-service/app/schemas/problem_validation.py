"""
문제 검증 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class ValidationResultSchema(BaseModel):
    """단일 문제 검증 결과 스키마"""
    is_valid: bool = Field(..., description="전체 검증 통과 여부")
    math_accuracy: str = Field(..., description="수학적 정확성: 정확/오류/의심")
    answer_correctness: str = Field(..., description="정답 정확성: 정확/오류/의심")
    explanation_quality: str = Field(..., description="해설 품질: 우수/보통/부족")
    latex_syntax: str = Field(..., description="LaTeX 문법: 정확/오류/없음")
    difficulty_appropriateness: str = Field(..., description="난이도 적절성: 적절/쉬움/어려움")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="검증 신뢰도 (0.0-1.0)")
    auto_approve: bool = Field(..., description="자동 승인 가능 여부")
    issues: List[str] = Field(default_factory=list, description="발견된 문제점들")
    suggestions: List[str] = Field(default_factory=list, description="개선 제안사항들")

    @validator('math_accuracy', 'answer_correctness')
    def validate_accuracy_fields(cls, v):
        allowed_values = ['정확', '오류', '의심', '검증실패', '파싱오류']
        if v not in allowed_values:
            raise ValueError(f'값은 {allowed_values} 중 하나여야 합니다')
        return v

    @validator('explanation_quality')
    def validate_quality_field(cls, v):
        allowed_values = ['우수', '보통', '부족', '검증실패', '파싱오류']
        if v not in allowed_values:
            raise ValueError(f'값은 {allowed_values} 중 하나여야 합니다')
        return v

    @validator('latex_syntax')
    def validate_latex_field(cls, v):
        allowed_values = ['정확', '오류', '없음', '검증실패', '파싱오류']
        if v not in allowed_values:
            raise ValueError(f'값은 {allowed_values} 중 하나여야 합니다')
        return v

    @validator('difficulty_appropriateness')
    def validate_difficulty_field(cls, v):
        allowed_values = ['적절', '쉬움', '어려움', '검증실패', '파싱오류']
        if v not in allowed_values:
            raise ValueError(f'값은 {allowed_values} 중 하나여야 합니다')
        return v

class ProblemWithValidationSchema(BaseModel):
    """검증 결과가 포함된 문제 스키마"""
    # 기본 문제 정보
    question: str = Field(..., description="문제 내용")
    correct_answer: str = Field(..., description="정답")
    explanation: str = Field(..., description="해설")
    problem_type: str = Field(..., description="문제 유형")
    difficulty: str = Field(..., description="난이도")
    choices: Optional[List[str]] = Field(None, description="선택지 (객관식인 경우)")

    # 검증 정보
    validation_result: ValidationResultSchema = Field(..., description="검증 결과")
    validation_status: str = Field(..., description="검증 상태: auto_approved/manual_review_needed")

class ValidationSummarySchema(BaseModel):
    """검증 요약 스키마"""
    total_problems: int = Field(..., description="총 문제 수")
    valid_problems: int = Field(..., description="유효한 문제 수")
    invalid_problems: int = Field(..., description="무효한 문제 수")
    auto_approved: int = Field(..., description="자동 승인된 문제 수")
    manual_review_needed: int = Field(..., description="수동 검토 필요한 문제 수")
    validity_rate: float = Field(..., description="유효율 (%)")
    auto_approval_rate: float = Field(..., description="자동 승인율 (%)")
    common_issues: Dict[str, int] = Field(default_factory=dict, description="자주 발견되는 문제점들")

class GenerationWithValidationResponseSchema(BaseModel):
    """검증이 포함된 문제 생성 응답 스키마"""
    problems: List[ProblemWithValidationSchema] = Field(..., description="생성된 문제들 (검증 결과 포함)")
    validation_results: List[ValidationResultSchema] = Field(..., description="검증 결과들")
    summary: ValidationSummarySchema = Field(..., description="검증 요약")

class ValidationConfigSchema(BaseModel):
    """검증 설정 스키마"""
    config_name: str = Field(..., description="설정 이름")
    description: Optional[str] = Field(None, description="설정 설명")
    min_confidence_score: float = Field(0.8, ge=0.0, le=1.0, description="자동 승인 최소 신뢰도")
    enable_latex_validation: bool = Field(True, description="LaTeX 문법 검증 활성화")
    enable_difficulty_validation: bool = Field(True, description="난이도 적절성 검증 활성화")
    validator_model: str = Field("gemini-2.5-flash", description="검증 모델")
    validator_temperature: float = Field(0.1, ge=0.0, le=2.0, description="검증 모델 temperature")
    validator_max_tokens: int = Field(2048, ge=512, le=8192, description="검증 모델 최대 토큰")

class TeacherReviewSchema(BaseModel):
    """교사 검토 스키마"""
    problem_id: str = Field(..., description="문제 ID")
    review_status: str = Field(..., description="검토 상태: approved/rejected")
    comment: Optional[str] = Field(None, description="검토 의견")

    @validator('review_status')
    def validate_review_status(cls, v):
        allowed_values = ['approved', 'rejected']
        if v not in allowed_values:
            raise ValueError(f'검토 상태는 {allowed_values} 중 하나여야 합니다')
        return v

class ValidationRequestSchema(BaseModel):
    """검증 요청 스키마"""
    problems: List[Dict[str, Any]] = Field(..., description="검증할 문제들")
    config_name: Optional[str] = Field("default", description="사용할 검증 설정")
    enable_auto_approval: bool = Field(True, description="자동 승인 활성화 여부")

class ValidationBatchResponseSchema(BaseModel):
    """일괄 검증 응답 스키마"""
    validation_results: List[ValidationResultSchema] = Field(..., description="검증 결과들")
    summary: ValidationSummarySchema = Field(..., description="검증 요약")
    session_id: str = Field(..., description="검증 세션 ID")
    created_at: datetime = Field(..., description="검증 수행 시간")

# Request/Response schemas for API endpoints
class ProblemGenerationRequestSchema(BaseModel):
    """문제 생성 요청 스키마 (검증 포함)"""
    curriculum_data: Dict[str, Any] = Field(..., description="교과과정 데이터")
    user_prompt: str = Field(..., description="사용자 요구사항")
    problem_count: int = Field(1, ge=1, le=50, description="생성할 문제 수")
    difficulty_ratio: Optional[Dict[str, int]] = Field(None, description="난이도 비율")
    enable_validation: bool = Field(True, description="검증 활성화 여부")
    validation_config: Optional[str] = Field("default", description="검증 설정")

class SingleProblemValidationRequestSchema(BaseModel):
    """단일 문제 검증 요청 스키마"""
    problem: Dict[str, Any] = Field(..., description="검증할 문제")
    config_name: Optional[str] = Field("default", description="검증 설정")

class SingleProblemValidationResponseSchema(BaseModel):
    """단일 문제 검증 응답 스키마"""
    validation_result: ValidationResultSchema = Field(..., description="검증 결과")
    validated_at: datetime = Field(..., description="검증 수행 시간")