from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.models import (
    GrammarCategory, VocabularyCategory, ReadingType
)

router = APIRouter(tags=["Categories"])

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """
    문법, 어휘, 독해 카테고리 정보를 조회하는 엔드포인트
    프론트엔드에서 선택 옵션을 만들 때 사용합니다.
    """
    try:
        # 문법 카테고리와 주제들 조회
        grammar_categories = db.query(GrammarCategory).all()
        grammar_data = []
        for category in grammar_categories:
            topics = [{"id": topic.id, "name": topic.name} for topic in category.topics]
            grammar_data.append({
                "id": category.id,
                "name": category.name,
                "topics": topics
            })
        
        # 어휘 카테고리 조회
        vocabulary_categories = db.query(VocabularyCategory).all()
        vocabulary_data = [{"id": cat.id, "name": cat.name} for cat in vocabulary_categories]
        
        # 독해 유형 조회
        reading_types = db.query(ReadingType).all()
        reading_data = [{"id": rt.id, "name": rt.name, "description": rt.description} for rt in reading_types]
        
        return {
            "grammar_categories": grammar_data,
            "vocabulary_categories": vocabulary_data,
            "reading_types": reading_data
        }
    except Exception as e:
        return {"error": f"카테고리 조회 중 오류 발생: {str(e)}"}
