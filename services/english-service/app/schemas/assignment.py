from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AssignmentDeployRequest(BaseModel):
    """과제 배포 요청"""
    worksheet_id: int = Field(..., description="배포할 문제지 ID")
    classroom_id: int = Field(..., description="배포할 클래스룸 ID")
    student_ids: List[int] = Field(..., description="배포할 학생 ID 목록")

class AssignmentDeploymentResponse(BaseModel):
    """과제 배포 응답"""
    id: int
    assignment_id: int
    student_id: int
    classroom_id: int
    status: str
    deployed_at: datetime

    class Config:
        orm_mode = True

class StudentAssignmentResponse(BaseModel):
    """학생의 과제 목록 응답"""
    id: int
    title: str
    problem_type: str
    total_questions: int
    status: str
    deployed_at: datetime
    assignment_id: int

    class Config:
        orm_mode = True
