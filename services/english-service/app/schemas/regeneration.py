from pydantic import BaseModel, Field
from typing import Optional, Union, Dict, Any, List, Literal


# 프론트엔드 데이터 구조에 맞춘 모델들
class EnglishQuestion(BaseModel):
    """영어 문제 데이터 (프론트엔드 sanitized 형태)"""
    question_id: int
    question_text: str
    question_type: Literal["객관식", "단답형", "서술형"]
    question_subject: str
    question_difficulty: Literal["상", "중", "하"]
    question_detail_type: str
    question_passage_id: Optional[int] = None
    example_content: str
    example_original_content: str
    example_korean_translation: str
    question_choices: List[str]
    correct_answer: Union[str, int]
    explanation: str
    learning_point: str


class EnglishPassage(BaseModel):
    """영어 지문 데이터 (프론트엔드 sanitized 형태)"""
    passage_id: int
    passage_type: Literal["article", "correspondence", "dialogue", "informational", "review"]
    passage_content: Dict[str, Any]  # EnglishPassageContent
    original_content: Dict[str, Any]  # EnglishPassageContent
    korean_translation: Dict[str, Any]  # EnglishPassageContent
    related_questions: List[int]


class WorksheetContext(BaseModel):
    """문제지 컨텍스트"""
    school_level: Optional[str] = Field(default=None, description="학교급")
    grade: Optional[int] = Field(default=None, description="학년")


class EnglishRegenerationRequest(BaseModel):
    """영어 재생성 요청 폼 데이터"""
    feedback: str = Field(..., description="사용자 피드백")
    worksheet_context: WorksheetContext = Field(..., description="문제지 컨텍스트")

    # 추가 옵션들 (선택사항)
    regenerate_passage: bool = Field(default=False, description="지문 재생성 여부")
    new_difficulty: Optional[str] = Field(default=None, description="변경할 난이도")
    additional_instructions: Optional[str] = Field(default=None, description="추가 지시사항")


# API 요청 모델
class RegenerateEnglishQuestionRequest(BaseModel):
    """영어 문제 재생성 API 요청"""
    questions: List[EnglishQuestion] = Field(..., description="재생성할 문제들")
    passage: Optional[EnglishPassage] = Field(default=None, description="연관 지문 (있을 경우)")
    formData: EnglishRegenerationRequest = Field(..., description="재생성 요청 옵션들")


# API 응답 모델
class RegenerationResponse(BaseModel):
    """재생성 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")

    # 성공시 데이터
    regenerated_questions: Optional[List[EnglishQuestion]] = Field(default=None, description="재생성된 문제들")
    regenerated_passage: Optional[EnglishPassage] = Field(default=None, description="재생성된 지문")

    # 실패시 정보
    error_details: Optional[str] = Field(default=None, description="오류 상세 정보")