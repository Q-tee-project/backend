from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..schemas.math_generation import SchoolLevel
from ..services.math_generation_service import MathGenerationService

router = APIRouter()
math_service = MathGenerationService()

@router.get("/structure")
async def get_curriculum_structure(
    school_level: Optional[SchoolLevel] = Query(None, description="학교급 필터"),
    db: Session = Depends(get_db)
):
    try:
        structure = math_service.get_curriculum_structure(
            db, 
            school_level.value if school_level else None
        )
        return {"structure": structure}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"교육과정 구조 조회 중 오류: {str(e)}"
        )

@router.get("/units")
async def get_units():
    try:
        units = math_service.get_units()
        return {"units": units}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대단원 목록 조회 중 오류: {str(e)}"
        )

@router.get("/chapters")
async def get_chapters_by_unit(unit_name: str = Query(..., description="대단원명")):
    try:
        chapters = math_service.get_chapters_by_unit(unit_name)
        return {"chapters": chapters}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"소단원 목록 조회 중 오류: {str(e)}"
        )