from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# 카테고리 정보 응답 스키마들
class GrammarCategoryResponse(BaseModel):
    id: int
    name: str
    topics: List[Dict[str, Any]] = []


class VocabularyCategoryResponse(BaseModel):
    id: int
    name: str


class ReadingTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    level: str


class CategoriesResponse(BaseModel):
    grammar_categories: List[GrammarCategoryResponse]
    vocabulary_categories: List[VocabularyCategoryResponse]
    reading_types: List[ReadingTypeResponse]