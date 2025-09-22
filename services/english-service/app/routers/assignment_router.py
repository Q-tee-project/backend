from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.worksheet import Worksheet, Question
from app.models.assignment import Assignment, AssignmentDeployment
from app.schemas.assignment import (
    AssignmentDeployRequest,
    AssignmentDeploymentResponse,
    StudentAssignmentResponse,
)

router = APIRouter()

@router.post("/assignments/deploy", response_model=List[AssignmentDeploymentResponse])
async def deploy_assignment(
    deploy_request: AssignmentDeployRequest,
    db: Session = Depends(get_db)
):
    """과제를 학생들에게 배포"""
    try:
        # 워크시트 존재 확인
        worksheet = db.query(Worksheet).filter(
            Worksheet.worksheet_id == deploy_request.worksheet_id
        ).first()
        
        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다"
            )
        
        # 기존 Assignment 확인 (같은 워크시트, 같은 클래스룸)
        assignment = db.query(Assignment).filter(
            Assignment.worksheet_id == worksheet.worksheet_id,
            Assignment.classroom_id == deploy_request.classroom_id
        ).first()
        
        # Assignment가 없으면 새로 생성
        if not assignment:
            assignment = Assignment(
                title=worksheet.worksheet_name,
                worksheet_id=worksheet.worksheet_id,
                classroom_id=deploy_request.classroom_id,
                teacher_id=worksheet.teacher_id,
                problem_type=worksheet.problem_type,
                total_questions=worksheet.total_questions,
                is_deployed="deployed"
            )
            db.add(assignment)
            db.flush()  # ID를 얻기 위해 flush
        else:
            # 기존 Assignment의 배포 상태 업데이트
            assignment.is_deployed = "deployed"
        
        # 배포 정보 생성 (중복 배포 방지)
        deployments = []
        for student_id in deploy_request.student_ids:
            # 기존 배포 정보 확인
            existing_deployment = db.query(AssignmentDeployment).filter(
                AssignmentDeployment.assignment_id == assignment.id,
                AssignmentDeployment.student_id == student_id
            ).first()
            
            if not existing_deployment:
                deployment = AssignmentDeployment(
                    assignment_id=assignment.id,
                    student_id=student_id,
                    classroom_id=deploy_request.classroom_id,
                    status="assigned"
                )
                db.add(deployment)
                deployments.append(deployment)
            else:
                deployments.append(existing_deployment)
        
        db.commit()
        
        # 응답 데이터 생성
        response_data = []
        for deployment in deployments:
            db.refresh(deployment)
            response_data.append(AssignmentDeploymentResponse(
                id=deployment.id,
                assignment_id=deployment.assignment_id,
                student_id=deployment.student_id,
                classroom_id=deployment.classroom_id,
                status=deployment.status,
                deployed_at=deployment.deployed_at
            ))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"과제 배포 중 오류 발생: {str(e)}"
        )

@router.get("/assignments/student/{student_id}", response_model=List[StudentAssignmentResponse])
async def get_student_assignments(
    student_id: int,
    db: Session = Depends(get_db)
):
    """학생의 과제 목록 조회"""
    try:
        # 학생이 속한 클래스룸 확인 (auth_service 스키마의 테이블 직접 접근)
        from sqlalchemy import text
        query = text("""
            SELECT classroom_id
            FROM auth_service.student_join_requests
            WHERE student_id = :student_id AND status = 'approved'
        """)
        result = db.execute(query, {"student_id": student_id})
        student_classrooms = result.fetchall()

        # classroom_id 목록 추출
        classroom_ids = [row[0] for row in student_classrooms]
        
        if not classroom_ids:
            return []
        
        deployments = db.query(AssignmentDeployment).join(Assignment).filter(
            AssignmentDeployment.student_id == student_id,
            AssignmentDeployment.classroom_id.in_(classroom_ids)
        ).all()
        
        response_data = []
        for deployment in deployments:
            assignment = deployment.assignment
            response_data.append(StudentAssignmentResponse(
                id=deployment.id,
                title=assignment.title,
                problem_type=assignment.problem_type,
                total_questions=assignment.total_questions,
                status=deployment.status,
                deployed_at=deployment.deployed_at,
                assignment_id=assignment.id
            ))
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"학생 과제 목록 조회 중 오류 발생: {str(e)}"
        )

@router.get("/assignments/{assignment_id}/student/{student_id}", response_model=dict)
async def get_assignment_detail_for_student(
    assignment_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    """학생용 과제 상세 정보 조회 (문제 포함)"""
    try:
        # 배포 정보 확인
        deployment = db.query(AssignmentDeployment).filter(
            AssignmentDeployment.assignment_id == assignment_id,
            AssignmentDeployment.student_id == student_id
        ).first()
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="배포된 과제를 찾을 수 없습니다"
            )
        
        assignment = deployment.assignment
        
        # 워크시트의 문제들 가져오기
        questions = db.query(Question).filter(
            Question.worksheet_id == assignment.worksheet_id
        ).order_by(Question.question_id).all()
        
        return {
            "assignment": {
                "id": assignment.id,
                "title": assignment.title,
                "problem_type": assignment.problem_type,
                "total_questions": assignment.total_questions
            },
            "deployment": {
                "id": deployment.id,
                "status": deployment.status,
                "deployed_at": deployment.deployed_at
            },
            "questions": questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"과제 상세 정보 조회 중 오류 발생: {str(e)}"
        )
