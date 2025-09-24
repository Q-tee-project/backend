"""
워크시트 제목 수정 서비스
워크시트의 제목만 수정할 수 있는 서비스
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.worksheet import Worksheet


class WorksheetService:
    """워크시트 제목 수정을 담당하는 서비스 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def update_worksheet_title(self, worksheet_id: int, new_title: str) -> Worksheet:
        """워크시트 제목을 업데이트합니다"""
        worksheet = self._get_worksheet_or_404(worksheet_id)

        # 제목 유효성 검사
        self._validate_title(new_title)

        worksheet.worksheet_name = new_title
        self.db.commit()
        self.db.refresh(worksheet)
        return worksheet

    def _get_worksheet_or_404(self, worksheet_id: int) -> Worksheet:
        """워크시트를 조회하거나 404 에러 발생"""
        worksheet = self.db.query(Worksheet).filter(
            Worksheet.worksheet_id == worksheet_id
        ).first()

        if not worksheet:
            raise ValueError("문제지를 찾을 수 없습니다.")

        return worksheet

    def _validate_title(self, title: str) -> None:
        """제목 유효성 검사"""
        if not title or not isinstance(title, str):
            raise ValueError("제목은 문자열이어야 합니다.")

        if not title.strip():
            raise ValueError("제목은 공백일 수 없습니다.")

        if len(title.strip()) > 200:
            raise ValueError("제목은 200자를 초과할 수 없습니다.")