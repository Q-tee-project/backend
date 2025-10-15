from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class SchoolLevel(str, Enum):
    MIDDLE = "middle"
    HIGH = "high"

class TeacherSignup(BaseModel):
    username: str
    email: str
    name: str
    phone: str
    password: str

class StudentSignup(BaseModel):
    username: str
    email: str
    name: str
    phone: str
    parent_phone: str
    school_level: SchoolLevel
    grade: int
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TeacherResponse(BaseModel):
    id: int
    username: str
    email: str
    name: str
    phone: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class StudentResponse(BaseModel):
    id: int
    username: str
    email: str
    name: str
    phone: str
    parent_phone: str
    school_level: SchoolLevel
    grade: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Activity Statistics Schemas
class TeacherStatistics(BaseModel):
    created_worksheets: int
    total_classrooms: int
    total_students: int

class StudentStatistics(BaseModel):
    completed_assignments: int
    joined_classrooms: int
    average_score: float

# Recent Activity Schemas
class RecentActivity(BaseModel):
    id: int
    description: str
    timestamp: datetime
    activity_type: str  # "worksheet", "grading", "classroom", etc.

    class Config:
        from_attributes = True