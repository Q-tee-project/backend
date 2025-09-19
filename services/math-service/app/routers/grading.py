from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..core.auth import get_current_user
from ..tasks import grade_problems_mixed_task

router = APIRouter()

@router.post("/worksheets/{worksheet_id}/grade")
async def grade_worksheet(
    worksheet_id: int,
    answer_sheet: UploadFile = File(..., description="답안지 이미지 파일"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from ..models.worksheet import Worksheet
    if not db.query(Worksheet).filter(Worksheet.id == worksheet_id).first():
        raise HTTPException(status_code=404, detail="워크시트를 찾을 수 없습니다.")
    
    image_data = await answer_sheet.read()
    task = grade_problems_mixed_task.delay(
        worksheet_id=worksheet_id,
        multiple_choice_answers={},
        canvas_answers={"sheet": image_data},
        user_id=current_user["id"]
    )
    return {"task_id": task.id, "status": "PENDING"}

@router.post("/worksheets/{worksheet_id}/grade-canvas")
async def grade_worksheet_canvas(
    worksheet_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from ..models.worksheet import Worksheet
    if not db.query(Worksheet).filter(Worksheet.id == worksheet_id).first():
        raise HTTPException(status_code=404, detail="워크시트를 찾을 수 없습니다.")

    task = grade_problems_mixed_task.delay(
        worksheet_id=worksheet_id,
        multiple_choice_answers=request.get("multiple_choice_answers", {}),
        canvas_answers=request.get("canvas_answers", {}),
        user_id=current_user["id"]
    )
    return {"task_id": task.id, "status": "PENDING"}
