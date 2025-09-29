"""
지문 수정 서비스
기존 구조를 유지하면서 내용만 수정할 수 있는 서비스
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.worksheet import Passage


class PassageService:
    """지문 수정을 담당하는 서비스 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def update_passage(self, worksheet_id: int, passage_id: int, update_data: Dict[str, Any]) -> Passage:
        """지문 정보를 업데이트합니다 (구조 유지, 내용만 수정)"""
        passage = self._get_passage_or_404(worksheet_id, passage_id)

        # 수정 가능한 필드들
        updatable_fields = [
            "passage_content", "original_content",
            "korean_translation", "related_questions"
        ]

        for field in updatable_fields:
            if field in update_data:
                new_value = update_data.get(field)

                # passage_type 변경 시도 시 에러
                if field == "passage_type":
                    raise ValueError("지문 유형은 변경할 수 없습니다.")

                # JSON 구조 검증 (내용 변경 시)
                if field in ["passage_content", "original_content", "korean_translation"]:
                    self._validate_structure_preserved(getattr(passage, field), new_value)

                setattr(passage, field, new_value)

        self.db.commit()
        self.db.refresh(passage)
        return passage

    def _get_passage_or_404(self, worksheet_id: int, passage_id: int) -> Passage:
        """지문을 조회하거나 404 에러 발생"""
        passage = self.db.query(Passage).filter(
            Passage.worksheet_id == worksheet_id,
            Passage.passage_id == passage_id
        ).first()

        if not passage:
            raise ValueError("지문을 찾을 수 없습니다.")

        return passage

    def _validate_structure_preserved(self, existing_content: dict, new_content: dict) -> None:
        """기존 JSON 구조가 유지되는지 검증"""
        if not isinstance(new_content, dict):
            raise ValueError("지문 내용은 JSON 객체여야 합니다.")

        # 기존 구조의 최상위 키들이 유지되는지 확인
        if set(existing_content.keys()) != set(new_content.keys()):
            raise ValueError("기존 JSON 구조를 유지해야 합니다.")

        # metadata가 있는 경우 구조 확인
        if "metadata" in existing_content:
            if not isinstance(new_content.get("metadata"), dict):
                raise ValueError("metadata는 객체 형태를 유지해야 합니다.")

            # metadata 키 구조 유지 확인
            existing_meta_keys = set(existing_content["metadata"].keys())
            new_meta_keys = set(new_content["metadata"].keys())
            if existing_meta_keys != new_meta_keys:
                raise ValueError("metadata 구조를 유지해야 합니다.")

        # content 배열 구조 확인
        if "content" in existing_content:
            if not isinstance(new_content.get("content"), list):
                raise ValueError("content는 배열 형태를 유지해야 합니다.")

            # content 항목의 type 구조 확인 (길이는 가변 허용)
            existing_content_list = existing_content["content"]
            new_content_list = new_content["content"]

            # 각 항목의 type과 구조만 검증 (길이 검증 제거)
            min_length = min(len(existing_content_list), len(new_content_list))

            for i in range(min_length):
                existing_item = existing_content_list[i]
                new_item = new_content_list[i]
                if existing_item.get("type") != new_item.get("type"):
                    raise ValueError(f"content[{i}]의 type을 변경할 수 없습니다.")

                # 구조적 키들 확인
                if set(existing_item.keys()) != set(new_item.keys()):
                    raise ValueError(f"content[{i}]의 구조를 유지해야 합니다.")