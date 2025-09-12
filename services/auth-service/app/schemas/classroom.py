from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .auth import SchoolLevel, TeacherResponse, StudentResponse

class ClassroomCreate(BaseModel):
    name: str
    school_level: SchoolLevel
    grade: int

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