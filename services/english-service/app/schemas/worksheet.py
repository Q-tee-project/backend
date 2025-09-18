from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


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