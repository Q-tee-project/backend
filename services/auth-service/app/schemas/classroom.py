from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .auth import SchoolLevel, TeacherResponse, StudentResponse

class ClassroomCreate(BaseModel):
    name: str
    school_level: SchoolLevel
    grade: int

class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    school_level: Optional[SchoolLevel] = None
    grade: Optional[int] = None

class ClassroomResponse(BaseModel):
    id: int
    name: str
    school_level: SchoolLevel
    grade: int
    class_code: str
    teacher_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class StudentJoinRequestCreate(BaseModel):
    class_code: str

class StudentJoinRequestResponse(BaseModel):
    id: int
    student_id: int
    classroom_id: int
    status: str
    requested_at: datetime
    processed_at: Optional[datetime]
    student: StudentResponse
    classroom: ClassroomResponse
    
    class Config:
        from_attributes = True

class StudentDirectRegister(BaseModel):
    name: str
    email: str
    phone: str
    parent_phone: str

class JoinRequestApproval(BaseModel):
    status: str  # "approved" or "rejected"

class ClassroomWithTeacherResponse(BaseModel):
    """학생용 클래스룸 정보 (교사 정보 포함)"""
    id: int
    name: str
    school_level: SchoolLevel
    grade: int
    class_code: str
    is_active: bool
    created_at: datetime
    teacher: TeacherResponse

    class Config:
        from_attributes = True