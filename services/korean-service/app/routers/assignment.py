from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime

from ..database import get_db
from ..schemas.korean_generation import AssignmentDeployRequest, AssignmentDeploymentResponse, StudentAssignmentResponse
from ..models.worksheet import Worksheet
from ..models.problem import Problem
from ..models.korean_generation import Assignment, AssignmentDeployment
from ..models.grading_result import KoreanGradingSession, KoreanProblemGradingResult

router = APIRouter()

@router.post("/deploy", response_model=List[AssignmentDeploymentResponse])
async def deploy_assignment(
    deploy_request: AssignmentDeployRequest,
    db: Session = Depends(get_db)
):
    worksheet = db.query(Worksheet).filter(Worksheet.id == deploy_request.assignment_id).first()
    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    assignment = db.query(Assignment).filter(
        Assignment.worksheet_id == worksheet.id,
        Assignment.classroom_id == deploy_request.classroom_id
    ).first()

    if not assignment:
        assignment = Assignment(
            title=worksheet.title,
            worksheet_id=worksheet.id,
            classroom_id=deploy_request.classroom_id,
            teacher_id=worksheet.teacher_id,
            korean_type=worksheet.korean_type or "소설",
            question_type=worksheet.question_type or "객관식",
            problem_count=worksheet.problem_count,
            is_deployed="deployed"
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
    return [AssignmentDeploymentResponse.from_orm(d) for d in deployments]

@router.get("/student/{student_id}", response_model=List[StudentAssignmentResponse])
async def get_student_assignments(
    student_id: int,
    db: Session = Depends(get_db)
):
    from sqlalchemy import text

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

@router.get("/{assignment_id}/student/{student_id}")
async def get_assignment_detail(
    assignment_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    """학생용 과제 상세 정보 조회"""
    deployment = db.query(AssignmentDeployment).join(Assignment).filter(
        Assignment.id == assignment_id,
        AssignmentDeployment.student_id == student_id
    ).first()

    if not deployment:
        raise HTTPException(status_code=404, detail="Assignment not found or not assigned to student")

    assignment = deployment.assignment
    worksheet = db.query(Worksheet).filter(Worksheet.id == assignment.worksheet_id).first()

    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    problems = db.query(Problem).filter(Problem.worksheet_id == worksheet.id).all()

    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "korean_type": assignment.korean_type,
            "question_type": assignment.question_type,
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
                "korean_type": problem.korean_type,
                "question_type": problem.problem_type,
                "difficulty": problem.difficulty,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else [],
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "source_text": problem.source_text,
                "source_title": problem.source_title,
                "source_author": problem.source_author
            }
            for problem in problems
        ]
    }

@router.post("/{assignment_id}/submit")
async def submit_korean_assignment(
    assignment_id: int,
    submission: Dict[str, Any] = Body(...), # { "student_id": int, "answers": { "problem_id": "answer" } }
    db: Session = Depends(get_db)
):
    student_id = submission.get("student_id")
    answers = submission.get("answers")

    if not student_id or not answers:
        raise HTTPException(status_code=400, detail="student_id and answers are required")

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    problems = db.query(Problem).filter(Problem.worksheet_id == assignment.worksheet_id).all()
    problem_map = {str(p.id): p for p in problems}

    total_problems = len(problems)
    if total_problems == 0:
        raise HTTPException(status_code=400, detail="No problems in this assignment")

    points_per_problem = 10 if total_problems <= 10 else 5
    correct_count = 0

    grading_session = KoreanGradingSession(
        worksheet_id=assignment.worksheet_id,
        graded_by=student_id,
        total_problems=total_problems,
        max_possible_score=total_problems * points_per_problem,
        points_per_problem=points_per_problem,
        input_method="manual",
        multiple_choice_answers=answers
    )
    db.add(grading_session)
    db.flush()

    for problem_id_str, student_answer in answers.items():
        problem = problem_map.get(problem_id_str)
        if not problem:
            continue

        is_correct = student_answer == problem.correct_answer
        if is_correct:
            correct_count += 1

        problem_result = KoreanProblemGradingResult(
            grading_session_id=grading_session.id,
            problem_id=int(problem_id_str),
            user_answer=student_answer,
            correct_answer=problem.correct_answer,
            is_correct=is_correct,
            score=points_per_problem if is_correct else 0,
            points_per_problem=points_per_problem,
            problem_type=problem.problem_type,
            input_method="manual",
            explanation=problem.explanation
        )
        db.add(problem_result)

    grading_session.correct_count = correct_count
    grading_session.total_score = correct_count * points_per_problem
    
    # Update deployment status
    deployment = db.query(AssignmentDeployment).filter(
        AssignmentDeployment.assignment_id == assignment_id,
        AssignmentDeployment.student_id == student_id
    ).first()
    if deployment:
        deployment.status = "completed"
        deployment.completed_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Assignment submitted successfully.",
        "grading_session_id": grading_session.id,
        "score": grading_session.total_score,
        "total_problems": total_problems,
        "correct_answers": correct_count,
        "submitted_at": datetime.utcnow().isoformat()
    }

@router.get("/classrooms/{class_id}/assignments")
async def get_assignments_for_classroom(class_id: int, db: Session = Depends(get_db)):
    assignments = db.query(Assignment).filter(Assignment.classroom_id == class_id, Assignment.is_deployed == "deployed").all()
    return assignments
