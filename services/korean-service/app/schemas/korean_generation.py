from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

class SchoolLevel(str, Enum):
    MIDDLE = "중학교"
    HIGH = "고등학교"

class KoreanType(str, Enum):
    POEM = "시"
    NOVEL = "소설"
    NON_FICTION = "수필/비문학"
    GRAMMAR = "문법"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "객관식"

class Difficulty(str, Enum):
    HIGH = "상"
    MEDIUM = "중"
    LOW = "하"

class KoreanProblemGenerationRequest(BaseModel):
    school_level: SchoolLevel
    grade: int = Field(..., ge=1, le=3, description="학년 (1-3)")
    korean_type: KoreanType = Field(..., description="국어 문제 유형 (단일 도메인)")
    question_type: QuestionType = Field(..., description="문제 형식")
    difficulty: Difficulty = Field(..., description="난이도")
    problem_count: int = Field(..., ge=1, le=20, description="문제 수")
    user_text: Optional[str] = Field(None, max_length=500, description="사용자 요구사항")

    # 비율 설정 (단일 도메인 내에서만)
    # question_type_ratio: 국어는 객관식만 지원하므로 제거
    difficulty_ratio: Optional[Dict[str, int]] = Field(None, description="난이도별 비율")

class KoreanWorksheetCreate(BaseModel):
    title: str = Field(..., max_length=200, description="워크시트 제목")
    school_level: SchoolLevel
    grade: int = Field(..., ge=1, le=3)
    korean_type: KoreanType
    question_type: QuestionType
    difficulty: Difficulty
    problem_count: int
    user_text: Optional[str] = None
    # question_type_ratio: 국어는 객관식만 지원하므로 제거
    difficulty_ratio: Optional[Dict[str, int]] = None

class KoreanWorksheetResponse(BaseModel):
    id: int
    title: str
    school_level: str
    grade: int
    korean_type: str
    question_type: str
    difficulty: str
    problem_count: int
    user_text: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

class KoreanProblemResponse(BaseModel):
    id: int
    sequence_order: int
    korean_type: str
    question_type: str
    difficulty: str
    question: str
    choices: Optional[List[str]]
    correct_answer: str
    explanation: str
    source_text: Optional[str] = Field(None, description="출처 텍스트 (시, 소설 등)")
    source_title: Optional[str] = Field(None, description="출처 제목")
    source_author: Optional[str] = Field(None, description="출처 작가")

class AssignmentCreate(BaseModel):
    title: str
    worksheet_id: int
    classroom_id: int
    due_date: Optional[datetime] = None

class AssignmentResponse(BaseModel):
    id: int
    title: str
    worksheet_id: int
    classroom_id: int
    teacher_id: int
    korean_type: str
    question_type: str
    problem_count: int
    is_deployed: str
    created_at: datetime

class AssignmentDeployRequest(BaseModel):
    assignment_id: int
    classroom_id: int
    student_ids: List[int]

class AssignmentDeploymentResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    classroom_id: int
    status: str
    deployed_at: str

class StudentAssignmentResponse(BaseModel):
    id: int
    title: str
    korean_type: str
    question_type: str
    problem_count: int
    status: str
    deployed_at: str
    assignment_id: int