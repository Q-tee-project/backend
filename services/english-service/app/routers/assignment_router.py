from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.worksheet import Worksheet, Question
from app.models.assignment import Assignment, AssignmentDeployment
from app.schemas.assignment import (
    AssignmentDeployRequest,
    SimpleAssignmentDeployRequest,
    AssignmentDeploymentResponse,
    StudentAssignmentResponse,
)
from app.schemas import SubmissionRequest

router = APIRouter()

@router.post("/assignments/deploy", response_model=dict)
async def deploy_assignment_simple(
    deploy_request: SimpleAssignmentDeployRequest,
    db: Session = Depends(get_db)
):
    """과제를 학생들에게 배포 (프론트엔드용)"""
    try:
        # assignment_id를 worksheet_id로 사용
        worksheet_id = deploy_request.assignment_id

        # 워크시트 존재 확인
        worksheet = db.query(Worksheet).filter(
            Worksheet.worksheet_id == worksheet_id
        ).first()

        if not worksheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="워크시트를 찾을 수 없습니다"
            )

        # 기존 Assignment 확인 (같은 워크시트, 같은 클래스룸)
        assignment = db.query(Assignment).filter(
            Assignment.worksheet_id == worksheet_id,
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
        deployed_count = 0
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
                deployed_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"과제가 {deployed_count}명의 학생에게 배포되었습니다.",
            "assignment_id": assignment.id,
            "worksheet_id": worksheet_id,
            "deployed_count": deployed_count,
            "total_students": len(deploy_request.student_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"과제 배포 중 오류 발생: {str(e)}"
        )

@router.post("/assignments/deploy-detailed", response_model=List[AssignmentDeploymentResponse])
async def deploy_assignment_detailed(
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

@router.get("/assignments/deployed")
async def get_deployed_assignments(
    classroom_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """특정 클래스룸의 배포된 과제 목록 조회"""
    try:
        # 클래스룸에 배포된 과제들 조회
        assignments = db.query(Assignment).filter(
            Assignment.classroom_id == classroom_id,
            Assignment.is_deployed == "deployed"
        ).all()

        response_data = []
        for assignment in assignments:
            # 각 과제에 대한 배포 정보도 함께 조회
            deployment = db.query(AssignmentDeployment).filter(
                AssignmentDeployment.assignment_id == assignment.id,
                AssignmentDeployment.student_id == user_id
            ).first()

            assignment_data = {
                "id": assignment.id,
                "title": assignment.title,
                "worksheet_id": assignment.worksheet_id,
                "problem_type": assignment.problem_type,
                "total_questions": assignment.total_questions,
                "is_deployed": assignment.is_deployed,
                "created_at": assignment.created_at
            }

            # 해당 학생에게 배포되었는지 확인
            if deployment:
                assignment_data["deployment_status"] = deployment.status
                assignment_data["deployed_at"] = deployment.deployed_at
            else:
                assignment_data["deployment_status"] = "not_assigned"
                assignment_data["deployed_at"] = None

            response_data.append(assignment_data)

        return {
            "assignments": response_data,
            "total_count": len(response_data)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"배포된 과제 목록 조회 중 오류 발생: {str(e)}"
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

        # 워크시트의 지문들 가져오기
        from app.models.worksheet import Passage
        passages = db.query(Passage).filter(
            Passage.worksheet_id == assignment.worksheet_id
        ).order_by(Passage.passage_id).all()

        # 지문 데이터를 딕셔너리로 변환
        passages_data = []
        for passage in passages:
            passages_data.append({
                "id": passage.id,
                "worksheet_id": passage.worksheet_id,
                "passage_id": passage.passage_id,
                "passage_type": passage.passage_type,
                "passage_content": passage.passage_content,
                "original_content": passage.original_content,
                "korean_translation": passage.korean_translation,
                "related_questions": passage.related_questions,
                "created_at": passage.created_at
            })

        # 문제 데이터를 딕셔너리로 변환
        questions_data = []
        for question in questions:
            questions_data.append({
                "id": question.id,
                "worksheet_id": question.worksheet_id,
                "question_id": question.question_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "question_subject": question.question_subject,
                "question_difficulty": question.question_difficulty,
                "question_detail_type": question.question_detail_type,
                "question_choices": question.question_choices,
                "passage_id": question.passage_id,
                "correct_answer": question.correct_answer,
                "example_content": question.example_content,
                "example_original_content": question.example_original_content,
                "example_korean_translation": question.example_korean_translation,
                "explanation": question.explanation,
                "learning_point": question.learning_point,
                "created_at": question.created_at
            })

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
            "passages": passages_data,
            "questions": questions_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"과제 상세 정보 조회 중 오류 발생: {str(e)}"
        )

@router.post("/assignments/submit")
async def submit_assignment(
    submission_data: SubmissionRequest,
    db: Session = Depends(get_db)
):
    """과제 답안을 제출하고 자동 채점을 수행합니다."""
    try:
        # assignment_id로 워크시트 ID 찾기
        assignment_id = submission_data.assignment_id if hasattr(submission_data, 'assignment_id') else None
        print(f"answers: {submission_data.answers}")
        if assignment_id:
            # Assignment에서 worksheet_id 찾기
            assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
            if not assignment:
                raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
            worksheet_id = assignment.worksheet_id
        else:
            # 기존 방식: worksheet_id 직접 사용
            worksheet_id = submission_data.worksheet_id

        # 문제지 조회
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")

        # 기존 채점 서비스 사용
        from app.services.grading.grading_service import GradingService
        grading_service = GradingService(db)

        # 채점 수행
        result = await grading_service.grade_worksheet(
            worksheet_id=worksheet_id,
            student_id=submission_data.student_id,
            answers=submission_data.answers,
            completion_time=0  # 기본값
        )

        # Assignment 배포 상태 업데이트 (제출됨으로 변경)
        if assignment_id:
            deployment = db.query(AssignmentDeployment).filter(
                AssignmentDeployment.assignment_id == assignment_id,
                AssignmentDeployment.student_id == submission_data.student_id
            ).first()

            if deployment:
                deployment.status = "submitted"
                db.commit()

        return {
            "message": "과제가 성공적으로 제출되었습니다.",
            "grading_result": result,
            "worksheet_id": worksheet_id,
            "assignment_id": assignment_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"과제 제출 중 오류 발생: {str(e)}"
        )
