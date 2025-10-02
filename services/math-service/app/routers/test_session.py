from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from ..database import get_db
from ..models.math_generation import TestSession, TestAnswer, Assignment, AssignmentDeployment
from ..models.problem import Problem
from ..models.grading_result import GradingSession, ProblemGradingResult
from ..schemas.math_generation import TestSubmissionResponse
from ..core.auth import get_current_user
from ..services.ocr_service import OCRService
import json
import base64

router = APIRouter()

@router.post("/test-sessions/{session_id}/submit", response_model=TestSubmissionResponse)
async def submit_test(
    session_id: str,
    answers: Dict[str, str] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """학생이 과제를 제출하고 채점을 시작하는 엔드포인트"""
    session = db.query(TestSession).filter(TestSession.session_id == session_id).first()
    if not session or session.student_id != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Test session not found")

    if session.status == 'submitted':
        raise HTTPException(status_code=400, detail="Test already submitted")

    # 1. 문제 정보 가져오기
    assignment = db.query(Assignment).filter(Assignment.id == session.assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    problems = db.query(Problem).filter(Problem.worksheet_id == assignment.worksheet_id).all()
    problem_map = {str(p.id): p for p in problems}

    # 2. 모든 문제에 대한 답안이 제출되었는지 확인
    total_problems = len(problems)
    answered_problems = len(answers)
    if answered_problems < total_problems:
        raise HTTPException(
            status_code=422,
            detail=f"모든 문제에 답안을 제출해야 합니다. 현재 {answered_problems}/{total_problems}개 문제에 답안이 제출되었습니다."
        )

    # 3. 채점 로직
    correct_answers = 0
    points_per_problem = 10 if total_problems == 10 else 5 if total_problems == 20 else 100 / total_problems

    for problem_id_str, student_answer in answers.items():
        problem = problem_map.get(problem_id_str)
        if not problem:
            continue

        is_correct = False
        if problem.problem_type == 'multiple_choice':
            if student_answer == problem.correct_answer:
                is_correct = True
        elif problem.problem_type == 'short_answer':
            # DB 정답과 비교 (OCR 추출 텍스트)
            if student_answer == problem.correct_answer:
                is_correct = True

        if is_correct:
            correct_answers += 1

        # 답안 저장
        db_answer = TestAnswer(
            session_id=session_id,
            problem_id=int(problem_id_str),
            answer=student_answer
        )
        db.add(db_answer)

    # 3. 세션 및 과제 배포 상태 업데이트
    session.status = 'completed'
    session.submitted_at = datetime.utcnow()

    # AssignmentDeployment 상태를 'completed'로 업데이트
    deployment = db.query(AssignmentDeployment).filter(
        AssignmentDeployment.assignment_id == assignment.id,
        AssignmentDeployment.student_id == current_user["user_id"]
    ).first()
    if deployment:
        deployment.status = 'completed'
        deployment.submitted_at = datetime.utcnow()

    db.commit()

    score = correct_answers * points_per_problem

    # 4. 채점 결과를 DB에 저장 (GradingSession, ProblemGradingResult 모델 사용)
    grading_session = GradingSession(
        worksheet_id=assignment.worksheet_id,
        total_problems=total_problems,
        correct_count=correct_answers,
        total_score=score,
        max_possible_score=total_problems * points_per_problem,
        points_per_problem=points_per_problem,
        input_method="mixed",  # 수학 과제는 객관식+손글씨 혼합
        graded_at=datetime.utcnow(),
        graded_by=current_user["user_id"]
    )
    db.add(grading_session)
    db.flush()  # ID를 얻기 위해 flush

    # 5. 문제별 채점 결과 저장
    for problem_id_str, student_answer in answers.items():
        problem = problem_map.get(problem_id_str)
        if not problem:
            continue

        is_correct = False
        if problem.problem_type == 'multiple_choice':
            if student_answer == problem.correct_answer:
                is_correct = True
        elif problem.problem_type == 'short_answer':
            if student_answer == problem.correct_answer:
                is_correct = True

        # 문제별 채점 결과 저장
        problem_result = ProblemGradingResult(
            grading_session_id=grading_session.id,
            problem_id=int(problem_id_str),
            user_answer=student_answer,
            actual_user_answer=student_answer if problem.problem_type == 'multiple_choice' else None,
            correct_answer=problem.correct_answer,
            is_correct=is_correct,
            score=points_per_problem if is_correct else 0,
            points_per_problem=points_per_problem,
            problem_type=problem.problem_type,
            difficulty=problem.difficulty,
            input_method="handwriting_ocr" if problem.problem_type == 'short_answer' else "checkbox",
            explanation=problem.explanation
        )
        db.add(problem_result)

    db.commit()

    return TestSubmissionResponse(
        session_id=session_id,
        submitted_at=session.submitted_at.isoformat(),
        total_problems=total_problems,
        answered_problems=len(answers)
    )

@router.post("/test-sessions/{session_id}/answers")
async def save_answer(
    session_id: str,
    answer_data: dict, # { "problem_id": int, "answer": str }
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """학생의 답안을 실시간으로 저장"""
    session = db.query(TestSession).filter(TestSession.session_id == session_id).first()
    if not session or session.student_id != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Test session not found")

    problem_id = answer_data.get("problem_id")
    answer = answer_data.get("answer")

    existing_answer = db.query(TestAnswer).filter(
        TestAnswer.session_id == session_id,
        TestAnswer.problem_id == problem_id
    ).first()

    if existing_answer:
        existing_answer.answer = answer
    else:
        new_answer = TestAnswer(
            session_id=session_id,
            problem_id=problem_id,
            answer=answer
        )
        db.add(new_answer)
    
    db.commit()
    return {"message": "Answer saved"}

@router.post("/test-sessions/{session_id}/answers/ocr")
async def save_answer_with_ocr(
    session_id: str,
    problem_id: int = Body(...),
    answer: str = Body(...),
    handwriting_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """OCR을 지원하는 답안 저장"""
    session = db.query(TestSession).filter(TestSession.session_id == session_id).first()
    if not session or session.student_id != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Test session not found")

    # 손글씨 이미지가 있으면 OCR 처리
    final_answer = answer
    if handwriting_image:
        try:
            # 이미지 데이터 읽기
            image_data = await handwriting_image.read()

            # OCR 서비스 사용
            ocr_service = OCRService()
            ocr_text = ocr_service.extract_text_from_image(image_data)

            if ocr_text and ocr_text.strip():
                # OCR이 성공한 경우 텍스트 사용
                final_answer = ocr_text.strip()
                print(f"OCR 성공: {final_answer}")
            else:
                # OCR 실패 시 이미지를 base64로 저장
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                final_answer = f"data:image/{handwriting_image.content_type.split('/')[-1]};base64,{image_base64}"
                print(f"OCR 실패, 이미지 저장")

        except Exception as e:
            print(f"OCR 처리 중 오류 발생: {e}")
            # OCR 처리 실패 시 원본 답안 사용
            final_answer = answer
    else:
        final_answer = answer

    # 기존 답안 업데이트 또는 새로 생성
    existing_answer = db.query(TestAnswer).filter(
        TestAnswer.session_id == session_id,
        TestAnswer.problem_id == problem_id
    ).first()

    if existing_answer:
        existing_answer.answer = final_answer
    else:
        new_answer = TestAnswer(
            session_id=session_id,
            problem_id=problem_id,
            answer=final_answer
        )
        db.add(new_answer)

    db.commit()
    return {"message": "Answer saved with OCR support"}
