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
      "questions": [EnglishQuestion[]],
      "passage": EnglishPassage,
      "formData": {
        "feedback": "사용자 피드백",
        "worksheet_context": {
          "school_level": "중학교",
          "grade": 1
        }
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
        print(f"\n📥 재생성 요청 받음:")
        print(f"Questions 개수: {len(request.questions)}")
        print(f"Passage 있음: {request.passage is not None}")
        print(f"FormData: {request.formData}")

        regenerator = QuestionRegenerator()

        # 재생성 실행
        success, message, regenerated_questions, regenerated_passage = regenerator.regenerate_from_data(
            questions=request.questions,
            passage=request.passage,
            form_data=request.formData
        )

        if success:
            print(f"✅ 재생성 성공: {len(regenerated_questions) if regenerated_questions else 0}개 문제")
            return RegenerationResponse(
                success=True,
                message=message,
                regenerated_questions=regenerated_questions,
                regenerated_passage=regenerated_passage
            )
        else:
            print(f"❌ 재생성 실패: {message}")
            return RegenerationResponse(
                success=False,
                message=message,
                error_details=message
            )

    except ValueError as e:
        print(f"🚨 Validation Error: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"요청 데이터 검증 실패: {str(e)}"
        )
    except Exception as e:
        print(f"💥 Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"재생성 중 오류가 발생했습니다: {str(e)}"
        )


