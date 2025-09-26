from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from app.schemas.regeneration import (
    RegenerateEnglishQuestionRequest,
    RegenerationResponse,
    EnglishQuestion,
    EnglishPassage
)
from app.services.regeneration.question_regenerator import QuestionRegenerator

router = APIRouter(tags=["English Question Regeneration"])


@router.post("/questions/regenerate", response_model=RegenerationResponse)
async def regenerate_english_question(
    request: RegenerateEnglishQuestionRequest
):
    """
    영어 문제를 재생성합니다.

    ## 요청 형식
    ```json
    {
      "questions": [
        {
          "question_id": 1,
          "question_text": "다음 글의 주제로 가장 적절한 것은?",
          "question_type": "객관식",
          "question_subject": "독해",
          "question_difficulty": "상",
          "question_detail_type": "주제 추론",
          "question_passage_id": 1,
          "example_content": "예문 내용",
          "example_original_content": "원문 예문",
          "example_korean_translation": "한글 번역",
          "question_choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
          "correct_answer": 0,
          "explanation": "해설",
          "learning_point": "학습 포인트"
        }
      ],
      "passage": {
        "passage_id": 1,
        "passage_type": "article",
        "passage_content": {...},
        "original_content": {...},
        "korean_translation": {...},
        "related_questions": [1, 2]
      },
      "formData": {
        "user_feedback": "문제를 더 쉽게 만들어주세요",
        "regenerate_passage": false,
        "new_difficulty": "하"
      }
    }
    ```

    ## 응답 형식
    ```json
    {
      "success": true,
      "message": "문제가 성공적으로 재생성되었습니다.",
      "regenerated_questions": [...],
      "regenerated_passage": null
    }
    ```
    """

    try:
        regenerator = QuestionRegenerator()

        # 재생성 실행
        success, message, regenerated_questions, regenerated_passage = regenerator.regenerate_from_data(
            questions=request.questions,
            passage=request.passage,
            form_data=request.formData
        )

        if success:
            return RegenerationResponse(
                success=True,
                message=message,
                regenerated_questions=regenerated_questions,
                regenerated_passage=regenerated_passage
            )
        else:
            return RegenerationResponse(
                success=False,
                message=message,
                error_details=message
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"재생성 중 오류가 발생했습니다: {str(e)}"
        )


