from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EnglishAssignmentResultResponse(BaseModel):
    """영어 과제 결과 조회 응답 스키마"""
    id: int
    grading_session_id: int  # result_id를 grading_session_id로 매핑
    student_id: int
    student_name: Optional[str] = None
    status: str
    total_score: int
    max_possible_score: int
    correct_count: int
    total_problems: int
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    school: Optional[str] = None
    grade: Optional[str] = None
    school_level: Optional[str] = None

    class Config:
        from_attributes = True