from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.worksheet import Worksheet
from ..models.problem import Problem

router = APIRouter(prefix="/market", tags=["market-integration"])


@router.get("/worksheets/{worksheet_id}")
async def get_worksheet_info(worksheet_id: int, db: Session = Depends(get_db)):
    """마켓에서 문제지 기본 정보 조회용"""
    worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()

    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    return {
        "id": worksheet.id,
        "title": worksheet.title,
        "school_level": worksheet.school_level,
        "grade": worksheet.grade,
        "korean_type": worksheet.korean_type,
        "problem_count": worksheet.problem_count,
        "created_at": worksheet.created_at,
        "user_id": worksheet.teacher_id,  # 소유자 ID
        "status": worksheet.status
    }


@router.get("/worksheets/{worksheet_id}/problems")
async def get_worksheet_with_problems(worksheet_id: int, db: Session = Depends(get_db)):
    """구매자를 위한 문제지 상세 내용 (문제 포함)"""
    worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()

    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    problems = db.query(Problem).filter(
        Problem.worksheet_id == worksheet_id
    ).order_by(Problem.sequence_order).all()

    return {
        "worksheet": {
            "id": worksheet.id,
            "title": worksheet.title,
            "school_level": worksheet.school_level,
            "grade": worksheet.grade,
            "korean_type": worksheet.korean_type,
            "problem_count": worksheet.problem_count,
            "created_at": worksheet.created_at,
            "status": worksheet.status
        },
        "problems": [
            {
                "id": problem.id,
                "sequence_order": problem.sequence_order,
                "korean_type": problem.korean_type,
                "problem_type": problem.problem_type,
                "difficulty": problem.difficulty,
                "question": problem.question,
                "choices": problem.choices,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "source_text": problem.source_text,
                "source_title": problem.source_title,
                "source_author": problem.source_author
            }
            for problem in problems
        ]
    }


@router.get("/worksheets")
async def get_user_worksheets(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """사용자의 문제지 목록 조회 (마켓 등록을 위한)"""
    worksheets = db.query(Worksheet).filter(
        Worksheet.teacher_id == user_id,
        Worksheet.status == "completed"
    ).order_by(Worksheet.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": worksheet.id,
            "title": worksheet.title,
            "school_level": worksheet.school_level,
            "grade": worksheet.grade,
            "korean_type": worksheet.korean_type,
            "problem_count": worksheet.problem_count,
            "created_at": worksheet.created_at
        }
        for worksheet in worksheets
    ]