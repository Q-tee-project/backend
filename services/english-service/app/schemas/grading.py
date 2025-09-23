from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


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
    result_id: int  # integer로 변경
    worksheet_id: int
    student_id: int
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
    worksheet_id: int
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
    assignment_id: int  # 과제 ID
    student_id: int  # 학생 ID
    answers: Dict[int, str]  # question_id -> answer
    user_id: int  # 사용자 ID (선택적)