from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from app.schemas.regeneration import (
    RegenerateEnglishQuestionRequest,
    RegenerationResponse,
    EnglishQuestion,
    EnglishPassage
)
from app.services.regeneration.question_regenerator import QuestionRegenerator
from app.tasks import regenerate_english_question_task
from app.celery_app import celery_app

router = APIRouter(tags=["English Question Regeneration"])


@router.post("/questions/regenerate")
async def regenerate_english_question(
    request: RegenerateEnglishQuestionRequest
):
    """
    영어 문제를 비동기로 재생성합니다.

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

    ## 응답 형식 (비동기)
    ```json
    {
      "task_id": "celery-task-uuid",
      "status": "started",
      "message": "문제 재생성 작업이 시작되었습니다."
    }
    ```
    """

    try:
        print("🚨 비동기 문제 재생성 요청 시작!")

        # 요청 데이터를 딕셔너리로 변환
        request_data = request.model_dump()

        # 비동기 재생성 태스크 시작
        task = regenerate_english_question_task.delay(request_data)

        print(f"🎯 재생성 태스크 ID: {task.id}")

        return {
            "task_id": task.id,
            "status": "started",
            "message": "문제 재생성 작업이 시작되었습니다."
        }

    except Exception as e:
        print(f"❌ 비동기 문제 재생성 시작 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"재생성 작업 시작 실패: {str(e)}"
        )


