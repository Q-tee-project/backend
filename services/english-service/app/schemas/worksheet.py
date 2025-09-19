from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# 지문 저장 스키마
class PassageSaveData(BaseModel):
    passage_id: int
    passage_type: str
    passage_content: Dict[str, Any]  # JSON 객체
    original_content: Dict[str, Any]  # JSON 객체
    korean_translation: Dict[str, Any]  # JSON 객체
    related_questions: List[int]


# 문제 저장 스키마
class QuestionSaveData(BaseModel):
    question_id: int
    question_type: str
    question_subject: str
    question_detail_type: str
    question_difficulty: str
    question_text: str
    example_content: Optional[str] = None
    example_original_content: Optional[str] = None
    example_korean_translation: Optional[str] = None
    related_question: Optional[int] = None
    question_passage_id: Optional[int] = None
    question_choices: Optional[List[str]] = None
    correct_answer: Any  # int for 객관식, str for others
    explanation: str
    learning_point: str


# 문제지 저장 요청 스키마 (프론트 형식에 맞춤)
class WorksheetSaveRequest(BaseModel):
    worksheet_id: str
    teacher_id: int
    worksheet_name: str
    worksheet_date: str
    worksheet_time: str
    worksheet_duration: str
    worksheet_subject: str
    worksheet_level: str
    worksheet_grade: int
    problem_type: Optional[str] = "혼합형"
    total_questions: int
    passages: List[PassageSaveData]
    questions: List[QuestionSaveData]


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
    worksheet_id: str  # worksheet_id와 동일한 값
    teacher_id: int
    worksheet_name: str
    school_level: str
    grade: str
    subject: str
    problem_type: str
    total_questions: int
    duration: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True