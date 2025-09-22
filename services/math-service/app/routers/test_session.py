from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models.math_generation import TestSession, TestAnswer, Assignment
from ..models.problem import Problem
from ..schemas.math_generation import TestSubmissionResponse
from ..core.auth import get_current_user
import json

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
    if not session or session.student_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Test session not found")

    if session.status == 'submitted':
        raise HTTPException(status_code=400, detail="Test already submitted")

    # 1. 문제 정보 가져오기
    assignment = db.query(Assignment).filter(Assignment.id == session.assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    problems = db.query(Problem).filter(Problem.worksheet_id == assignment.worksheet_id).all()
    problem_map = {str(p.id): p for p in problems}

    # 2. 채점 로직
    total_problems = len(problems)
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
        elif problem.problem_type in ['short_answer', 'essay']:
            # 1차: DB 정답과 비교
            if student_answer == problem.correct_answer:
                is_correct = True
            # 2차: LLM 채점 (추후 구현)
            # 여기서는 일단 DB 정답과 같으면 맞는 것으로 처리

        if is_correct:
            correct_answers += 1

        # 답안 저장
        db_answer = TestAnswer(
            session_id=session_id,
            problem_id=int(problem_id_str),
            answer=student_answer
        )
        db.add(db_answer)

    # 3. 세션 업데이트
    session.status = 'submitted'
    session.submitted_at = datetime.utcnow()
    db.commit()

    score = correct_answers * points_per_problem

    # TODO: 채점 결과를 DB에 저장 (GradingSession, ProblemGradingResult 모델 사용)
    # TODO: 선생님 승인 전까지는 예비 점수로 처리

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
    if not session or session.student_id != current_user["id"]:
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
