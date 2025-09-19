from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..core.auth import get_current_student
from ..schemas.math_generation import AssignmentDeployRequest, AssignmentDeploymentResponse, StudentAssignmentResponse
from ..services.math_generation_service import MathGenerationService

router = APIRouter()
math_service = MathGenerationService()

@router.post("/deploy", response_model=List[AssignmentDeploymentResponse])
async def deploy_assignment(
    deploy_request: AssignmentDeployRequest,
    db: Session = Depends(get_db)
):
    # This logic should be moved to a dedicated AssignmentService
    from ..models.worksheet import Worksheet
    from ..models.math_generation import Assignment, AssignmentDeployment

    worksheet = db.query(Worksheet).filter(Worksheet.id == deploy_request.assignment_id).first()
    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    assignment = db.query(Assignment).filter(
        Assignment.worksheet_id == worksheet.id, 
        Assignment.classroom_id == deploy_request.classroom_id
    ).first()

    if not assignment:
        assignment = Assignment(
            title=worksheet.title, worksheet_id=worksheet.id, classroom_id=deploy_request.classroom_id,
            teacher_id=worksheet.teacher_id, unit_name=worksheet.unit_name, chapter_name=worksheet.chapter_name,
            problem_count=worksheet.problem_count, is_deployed="deployed"
        )
        db.add(assignment)
        db.flush()
    else:
        assignment.is_deployed = "deployed"

    deployments = []
    for student_id in deploy_request.student_ids:
        existing_deployment = db.query(AssignmentDeployment).filter(
            AssignmentDeployment.assignment_id == assignment.id, 
            AssignmentDeployment.student_id == student_id
        ).first()
        if not existing_deployment:
            deployment = AssignmentDeployment(
                assignment_id=assignment.id, student_id=student_id, 
                classroom_id=deploy_request.classroom_id, status="assigned"
            )
            db.add(deployment)
            deployments.append(deployment)
        else:
            deployments.append(existing_deployment)
    
    db.commit()
    return [d for d in deployments]

@router.get("/student/{student_id}", response_model=List[StudentAssignmentResponse])
async def get_student_assignments(
    student_id: int,
    db: Session = Depends(get_db)
):
    # This logic should be moved to a dedicated AssignmentService
    from sqlalchemy import text
    from ..models.math_generation import Assignment, AssignmentDeployment

    query = text("SELECT classroom_id FROM auth_service.student_join_requests WHERE student_id = :student_id AND status = 'approved'")
    result = db.execute(query, {"student_id": student_id})
    classroom_ids = [row[0] for row in result.fetchall()]
    
    if not classroom_ids:
        return []

    deployments = db.query(AssignmentDeployment).join(Assignment).filter(
        AssignmentDeployment.student_id == student_id,
        AssignmentDeployment.classroom_id.in_(classroom_ids)
    ).all()
    
    return [StudentAssignmentResponse.from_orm(d) for d in deployments]
