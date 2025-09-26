from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class KoreanGradingSessionBase(BaseModel):
    worksheet_id: int
    graded_by: int
    total_problems: int
    correct_count: int
    total_score: float
    max_possible_score: float
    points_per_problem: float
    input_method: str
    ocr_text: Optional[str] = None
    ocr_results: Optional[dict] = None
    celery_task_id: Optional[str] = None
    status: str = "pending_approval"
    teacher_id: Optional[int] = None
    approved_at: Optional[datetime] = None


class KoreanGradingSessionCreate(KoreanGradingSessionBase):
    pass


class KoreanGradingSessionResponse(KoreanGradingSessionBase):
    id: int
    graded_at: datetime

    class Config:
        from_attributes = True


class KoreanProblemGradingResultBase(BaseModel):
    grading_session_id: int
    problem_id: int
    user_answer: Optional[str] = None
    actual_user_answer: Optional[str] = None
    correct_answer: str
    is_correct: bool
    score: float
    points_per_problem: float
    problem_type: str
    input_method: str
    ai_score: Optional[float] = None
    ai_feedback: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    keyword_score_ratio: Optional[float] = None
    explanation: Optional[str] = None


class KoreanProblemGradingResultCreate(KoreanProblemGradingResultBase):
    pass


class KoreanProblemGradingResultResponse(KoreanProblemGradingResultBase):
    id: int

    class Config:
        from_attributes = True


class GradingApprovalRequest(BaseModel):
    pass
    # Optionally, add a field for status if rejection is also an option
    # status: str = "approved" # e.g., "approved", "rejected"