from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging
import uuid
import json
from datetime import datetime

from ..database import get_db
from ..core.auth import get_current_student
from ..schemas.math_generation import AssignmentDeployRequest, AssignmentDeploymentResponse, StudentAssignmentResponse, TestSessionResponse
from ..services.math_generation_service import MathGenerationService
from ..models.math_generation import TestSession

router = APIRouter()
math_service = MathGenerationService()

@router.post("/create")
async def create_assignment(
    assignment_data: dict,
    db: Session = Depends(get_db)
):
    """과제 생성 (배포하지 않음)"""
    worksheet_id = assignment_data.get("worksheet_id")
    classroom_id = assignment_data.get("classroom_id")

    if not worksheet_id or not classroom_id:
        raise HTTPException(status_code=400, detail="worksheet_id and classroom_id are required")

    from ..models.worksheet import Worksheet
    from ..models.math_generation import Assignment

    worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    # 기존 과제가 있는지 확인
    existing_assignment = db.query(Assignment).filter(
        Assignment.worksheet_id == worksheet_id,
        Assignment.classroom_id == classroom_id
    ).first()

    if existing_assignment:
        return {"message": "Assignment already exists", "assignment_id": existing_assignment.id}

    # 새 과제 생성 (배포하지 않음)
    assignment = Assignment(
        title=worksheet.title,
        worksheet_id=worksheet_id,
        classroom_id=classroom_id,
        teacher_id=worksheet.teacher_id,
        unit_name=worksheet.unit_name,
        chapter_name=worksheet.chapter_name,
        problem_count=worksheet.problem_count,
        is_deployed="draft"  # 초안 상태로 생성
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {"message": "Assignment created successfully", "assignment_id": assignment.id}

logger = logging.getLogger(__name__)


@router.post("/deploy", response_model=List[AssignmentDeploymentResponse])
async def deploy_assignment(
    deploy_request: AssignmentDeployRequest,
    db: Session = Depends(get_db)
):
    # This logic should be moved to a dedicated AssignmentService
    from ..models.worksheet import Worksheet
    from ..models.math_generation import Assignment, AssignmentDeployment

    # 먼저 assignment_id로 Assignment를 찾기
    assignment = db.query(Assignment).filter(Assignment.id == deploy_request.assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # assignment에서 worksheet_id로 Worksheet 찾기
    worksheet = db.query(Worksheet).filter(Worksheet.id == assignment.worksheet_id).first()
    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    # assignment 상태를 deployed로 변경
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
    
    # 과제 배포 알림 전송
    from ..utils.notification_helper import send_assignment_deployed_notification
    for student_id in deploy_request.student_ids:
        try:
            await send_assignment_deployed_notification(
                student_id=student_id,
                class_id=deploy_request.classroom_id,
                class_name=f"클래스 {deploy_request.classroom_id}",  # TODO: 실제 클래스명 조회
                assignment_id=assignment.id,
                assignment_title=assignment.title,
                due_date=assignment.due_date.isoformat() if hasattr(assignment, 'due_date') and assignment.due_date else None
            )
        except Exception as e:
            print(f"⚠️ 알림 전송 실패 (주요 로직 계속 진행): {e}")
    
    return [AssignmentDeploymentResponse.from_orm(d) for d in deployments]

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

@router.get("/{assignment_id}/details")
async def get_assignment_details(
    assignment_id: int,
    student_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """학생용 과제 상세 정보 조회 (query param 버전)"""
    return await get_assignment_detail(assignment_id, student_id, db)

@router.get("/{assignment_id}/student/{student_id}")
async def get_assignment_detail(
    assignment_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    """학생용 과제 상세 정보 조회"""
    logger.info(f"[MATH_SERVICE] get_assignment_detail 호출됨. assignment_id: {assignment_id}, student_id: {student_id}")

    from ..models.math_generation import Assignment, AssignmentDeployment
    from ..models.worksheet import Worksheet
    from ..models.problem import Problem

    # 배포 정보 확인
    deployment = db.query(AssignmentDeployment).join(Assignment).filter(
        Assignment.id == assignment_id,
        AssignmentDeployment.student_id == student_id
    ).first()
    logger.info(f"[MATH_SERVICE] DB 쿼리 결과 (deployment): {deployment}")

    if not deployment:
        logger.warning(f"[MATH_SERVICE] 배포 정보를 찾을 수 없음. assignment_id: {assignment_id}, student_id: {student_id}")
        raise HTTPException(status_code=404, detail="Assignment not found or not assigned to student")

    assignment = deployment.assignment
    worksheet = db.query(Worksheet).filter(Worksheet.id == assignment.worksheet_id).first()

    if not worksheet:
        logger.warning(f"[MATH_SERVICE] 워크시트를 찾을 수 없음. worksheet_id: {assignment.worksheet_id}")
        raise HTTPException(status_code=404, detail="Worksheet not found")

    # 문제들 조회
    problems = db.query(Problem).filter(Problem.worksheet_id == worksheet.id).all()
    logger.info(f"[MATH_SERVICE] {len(problems)}개의 문제를 찾음.")

    # 응답 구성
    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "unit_name": assignment.unit_name,
            "chapter_name": assignment.chapter_name,
            "problem_count": assignment.problem_count,
            "status": assignment.is_deployed
        },
        "deployment": {
            "id": deployment.id,
            "status": deployment.status,
            "deployed_at": deployment.deployed_at.isoformat() if deployment.deployed_at else None
        },
        "problems": [
            {
                "id": problem.id,
                "sequence_order": problem.sequence_order,
                "problem_type": problem.problem_type,
                "difficulty": problem.difficulty,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else [],
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "latex_content": problem.latex_content,
                "image_url": problem.image_url,
                "has_diagram": problem.has_diagram,
                "diagram_type": problem.diagram_type,
                "diagram_elements": problem.diagram_elements,
                "tikz_code": problem.tikz_code
            }
            for problem in problems
        ]
    }

@router.post("/{assignment_id}/start", response_model=TestSessionResponse)
async def start_test_session(
    assignment_id: int,
    request_body: dict, # { "student_id": int }
    db: Session = Depends(get_db)
):
    """테스트 세션 시작"""
    student_id = request_body.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id is required")

    logger.info(f"[MATH_SERVICE] start_test_session 호출됨. assignment_id: {assignment_id}, student_id: {student_id}")

    # 기존에 진행중인 세션이 있는지 확인
    existing_session = db.query(TestSession).filter(
        TestSession.assignment_id == assignment_id,
        TestSession.student_id == student_id,
        TestSession.status == 'started'
    ).first()

    if existing_session:
        logger.info(f"[MATH_SERVICE] 기존 세션을 반환합니다: {existing_session.session_id}")
        return TestSessionResponse(
            session_id=existing_session.session_id,
            assignment_id=existing_session.assignment_id,
            student_id=existing_session.student_id,
            started_at=existing_session.started_at.isoformat(),
            status=existing_session.status
        )

    # 새 세션 생성
    new_session = TestSession(
        session_id=str(uuid.uuid4()),
        assignment_id=assignment_id,
        student_id=student_id,
        status="started",
        started_at=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    logger.info(f"[MATH_SERVICE] 새 세션을 생성했습니다: {new_session.session_id}")

    return TestSessionResponse(
        session_id=new_session.session_id,
        assignment_id=new_session.assignment_id,
        student_id=new_session.student_id,
        started_at=new_session.started_at.isoformat(),
        status=new_session.status
    )

@router.get("/classrooms/{class_id}/assignments")
async def get_assignments_for_classroom(class_id: int, db: Session = Depends(get_db)):
    """클래스룸별 모든 과제 목록 조회 (draft + deployed)"""
    from ..models.math_generation import Assignment

    # draft와 deployed 모든 과제를 반환
    assignments = db.query(Assignment).filter(Assignment.classroom_id == class_id).all()
    return assignments
