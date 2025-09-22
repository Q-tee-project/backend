from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from ..database import get_db
from ..models.grading_result import KoreanGradingSession
from ..models.korean_generation import Assignment
from ..schemas.grading_result import KoreanGradingSessionResponse, GradingApprovalRequest
from ..core.auth import get_current_teacher

router = APIRouter()

@router.get(
    "/grading-sessions/pending",
    response_model=List[KoreanGradingSessionResponse],
    summary="Get all grading sessions pending teacher approval",
    description="Retrieves a list of all Korean grading sessions that are awaiting teacher approval."
)
async def get_pending_grading_sessions(db: Session = Depends(get_db)):
    pending_sessions = db.query(KoreanGradingSession).filter(KoreanGradingSession.status == "pending_approval").all()
    return pending_sessions


@router.get(
    "/grading-sessions/{session_id}",
    response_model=KoreanGradingSessionResponse,
    summary="Get details of a specific grading session",
    description="Retrieves the detailed results of a specific Korean grading session by its ID."
)
async def get_grading_session_details(session_id: int, db: Session = Depends(get_db)):
    session = db.query(KoreanGradingSession).filter(KoreanGradingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading session not found")
    return session


@router.post(
    "/grading-sessions/{session_id}/approve",
    response_model=KoreanGradingSessionResponse,
    summary="Approve a grading session",
    description="Approves a Korean grading session, setting its status to 'approved' and recording the teacher's ID and approval timestamp."
)
async def approve_grading_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_teacher: Dict[str, Any] = Depends(get_current_teacher)
):
    session = db.query(KoreanGradingSession).filter(KoreanGradingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading session not found")

    if session.status != "pending_approval":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grading session is not pending approval")

    session.status = "approved"
    session.teacher_id = current_teacher["id"]
    session.approved_at = datetime.now()
    db.commit()
    db.refresh(session)
    return session


@router.get("/assignments/{assignment_id}/results")
async def get_assignment_results(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    grading_sessions = db.query(KoreanGradingSession).filter(KoreanGradingSession.worksheet_id == assignment.worksheet_id).all()
    return grading_sessions
