"""
검증 관련 Pydantic 스키마
AI-as-a-Judge 방식으로 생성된 문제를 평가하기 위한 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class QuestionValidationResult(BaseModel):
    """개별 문항 검증 결과 (총 100점) - Gemini API 호환 평탄한 구조"""

    # 최종 판정
    final_judgment: str = Field(..., description="Pass, Needs Revision, or Fail")
    total_score: int = Field(..., description="Total score 0-100")

    # A. Alignment (30점)
    curriculum_relevance: int = Field(..., description="Curriculum alignment score 0-10")
    difficulty_consistency: int = Field(..., description="Difficulty consistency score 0-10")
    topic_appropriateness: int = Field(..., description="Topic appropriateness score 0-10")
    alignment_total: int = Field(..., description="Alignment total score 0-30")
    alignment_rationale: str = Field(..., description="Alignment evaluation rationale")

    # B. Content Quality (40점)
    passage_quality: int = Field(..., description="Passage quality score 0-10")
    instruction_clarity: int = Field(..., description="Instruction clarity score 0-10")
    answer_accuracy: int = Field(..., description="Answer accuracy score 0-10")
    distractor_quality: int = Field(..., description="Distractor quality score 0-10")
    content_quality_total: int = Field(..., description="Content quality total score 0-40")
    content_quality_rationale: str = Field(..., description="Content quality rationale")

    # C. Explanation Quality (30점)
    logical_explanation: int = Field(..., description="Explanation logic score 0-10")
    incorrect_answer_analysis: int = Field(..., description="Incorrect answer analysis score 0-10")
    additional_information: int = Field(..., description="Additional information score 0-10")
    explanation_quality_total: int = Field(..., description="Explanation quality total score 0-30")
    explanation_quality_rationale: str = Field(..., description="Explanation quality rationale")

    # 개선 제안
    suggestions_for_improvement: List[str] = Field(
        default_factory=list,
        description="Specific actionable suggestions for improvement"
    )


# 호환성을 위한 중첩 구조 (내부 사용, API에는 전달 안함)
class AlignmentEvaluation(BaseModel):
    """문항-콘텐츠 정합성 평가 (30점)"""
    curriculum_relevance: int
    difficulty_consistency: int
    topic_appropriateness: int
    total_score: int
    rationale: str


class ContentQualityEvaluation(BaseModel):
    """내용 및 문제 품질 평가 (40점)"""
    passage_quality: int
    instruction_clarity: int
    answer_accuracy: int
    distractor_quality: int
    total_score: int
    rationale: str


class ExplanationQualityEvaluation(BaseModel):
    """해설 품질 평가 (30점)"""
    logical_explanation: int
    incorrect_answer_analysis: int
    additional_information: int
    total_score: int
    rationale: str


class ValidationMetrics(BaseModel):
    """검증 메트릭 (로깅 및 분석용)"""
    question_id: str
    attempt_number: int  # 몇 번째 생성 시도인지
    validation_result: QuestionValidationResult
    regeneration_needed: bool
    timestamp: str
