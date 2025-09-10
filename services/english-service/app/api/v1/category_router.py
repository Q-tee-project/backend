from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.schemas.schemas import TextTypeCreate, TextTypeUpdate, TextTypeResponse
from app.models.models import (
    GrammarCategory, VocabularyCategory, ReadingType, TextType
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

# ===========================================
# 지문 유형 관리 엔드포인트들
# ===========================================

@router.get("/text-types", response_model=List[TextTypeResponse])
async def get_text_types(db: Session = Depends(get_db)):
    """모든 지문 유형을 조회합니다."""
    try:
        text_types = db.query(TextType).all()
        return text_types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지문 유형 조회 중 오류: {str(e)}")

@router.get("/text-types/{text_type_id}", response_model=TextTypeResponse)
async def get_text_type(text_type_id: int, db: Session = Depends(get_db)):
    """특정 지문 유형을 조회합니다."""
    try:
        text_type = db.query(TextType).filter(TextType.id == text_type_id).first()
        if not text_type:
            raise HTTPException(status_code=404, detail="지문 유형을 찾을 수 없습니다.")
        return text_type
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지문 유형 조회 중 오류: {str(e)}")

@router.post("/text-types", response_model=TextTypeResponse)
async def create_text_type(text_type: TextTypeCreate, db: Session = Depends(get_db)):
    """새로운 지문 유형을 생성합니다."""
    try:
        # 중복 이름 확인
        existing = db.query(TextType).filter(TextType.type_name == text_type.type_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 지문 유형 이름입니다.")
        
        db_text_type = TextType(
            type_name=text_type.type_name,
            display_name=text_type.display_name,
            description=text_type.description,
            json_format=text_type.json_format,
            created_at=datetime.now()
        )
        db.add(db_text_type)
        db.commit()
        db.refresh(db_text_type)
        return db_text_type
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"지문 유형 생성 중 오류: {str(e)}")

@router.put("/text-types/{text_type_id}", response_model=TextTypeResponse)
async def update_text_type(text_type_id: int, text_type: TextTypeUpdate, db: Session = Depends(get_db)):
    """지문 유형을 수정합니다."""
    try:
        db_text_type = db.query(TextType).filter(TextType.id == text_type_id).first()
        if not db_text_type:
            raise HTTPException(status_code=404, detail="지문 유형을 찾을 수 없습니다.")
        
        # 수정할 필드들 업데이트
        if text_type.display_name is not None:
            db_text_type.display_name = text_type.display_name
        if text_type.description is not None:
            db_text_type.description = text_type.description
        if text_type.json_format is not None:
            db_text_type.json_format = text_type.json_format
        
        db.commit()
        db.refresh(db_text_type)
        return db_text_type
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"지문 유형 수정 중 오류: {str(e)}")

@router.delete("/text-types/{text_type_id}")
async def delete_text_type(text_type_id: int, db: Session = Depends(get_db)):
    """지문 유형을 삭제합니다."""
    try:
        db_text_type = db.query(TextType).filter(TextType.id == text_type_id).first()
        if not db_text_type:
            raise HTTPException(status_code=404, detail="지문 유형을 찾을 수 없습니다.")
        
        db.delete(db_text_type)
        db.commit()
        return {"message": "지문 유형이 성공적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"지문 유형 삭제 중 오류: {str(e)}")
