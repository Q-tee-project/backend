from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app.schemas.regeneration import (
    QuestionRegenerationRequest,
    QuestionDataRegenerationRequest,
    RegenerationResponse
)
from app.services.regeneration.question_regenerator import QuestionRegenerator

router = APIRouter(tags=["Question Regeneration"])


@router.post(
    "/worksheets/{worksheet_id}/questions/{question_id}/regenerate",
    response_model=RegenerationResponse
)
async def regenerate_question(
    worksheet_id: str = Path(..., description="워크시트 ID"),
    question_id: int = Path(..., description="문제 ID"),
    request: QuestionRegenerationRequest = ...,
    db: Session = Depends(get_db)
):
    """
    개별 문제를 재생성합니다.

    - **worksheet_id**: 문제지 ID
    - **question_id**: 재생성할 문제 ID
    - **request**: 재생성 요청 데이터

    ## 사용 예시

    ### 1. 기본 재생성 (모든 조건 유지)
    ```json
    {
      "feedback": "문제를 더 쉽게 만들어주세요",
      "worksheet_context": {
        "school_level": "중학교",
        "grade": 1,
        "worksheet_type": "혼합형"
      },
      "current_question_type": "객관식",
      "current_subject": "독해",
      "current_detail_type": "제목 및 요지 추론",
      "current_difficulty": "상"
    }
    ```

    ### 2. 난이도 변경 재생성
    ```json
    {
      "feedback": "문제가 너무 어려워요",
      "keep_difficulty": false,
      "target_difficulty": "하",
      "worksheet_context": {
        "school_level": "중학교",
        "grade": 1,
        "worksheet_type": "혼합형"
      },
      "current_question_type": "객관식",
      "current_subject": "독해",
      "current_detail_type": "제목 및 요지 추론",
      "current_difficulty": "상"
    }
    ```

    ### 3. 지문과 함께 재생성
    ```json
    {
      "feedback": "지문이 너무 길어요",
      "keep_passage": false,
      "worksheet_context": {
        "school_level": "중학교",
        "grade": 1,
        "worksheet_type": "독해"
      },
      "current_question_type": "객관식",
      "current_subject": "독해",
      "current_detail_type": "내용 일치",
      "current_difficulty": "중"
    }
    ```

    ## 응답 형식

    성공시:
    ```json
    {
      "status": "success",
      "message": "문제가 성공적으로 재생성되었습니다.",
      "regenerated_question": {
        "id": 123,
        "question_text": "새로운 문제 텍스트",
        "question_type": "객관식",
        ...
      },
      "regenerated_passage": null  // 지문 변경시에만 데이터 포함
    }
    ```

    실패시:
    ```json
    {
      "status": "error",
      "message": "재생성에 실패했습니다.",
      "error_details": "구체적인 오류 내용"
    }
    ```
    """

    try:
        # 문제 재생성 서비스 인스턴스 생성
        regenerator = QuestionRegenerator()

        # 문제 재생성 실행
        success, message, regenerated_question, regenerated_passage = regenerator.regenerate_question(
            db=db,
            worksheet_id=worksheet_id,
            question_id=question_id,
            request=request
        )

        if success:
            return RegenerationResponse(
                status="success",
                message=message,
                regenerated_question=regenerated_question,
                regenerated_passage=regenerated_passage
            )
        else:
            return RegenerationResponse(
                status="error",
                message=message,
                error_details=message
            )

    except ValueError as e:
        # 유효성 검사 오류
        raise HTTPException(
            status_code=400,
            detail=f"요청 데이터가 유효하지 않습니다: {str(e)}"
        )

    except Exception as e:
        # 기타 서버 오류
        raise HTTPException(
            status_code=500,
            detail=f"서버 내부 오류가 발생했습니다: {str(e)}"
        )


@router.post(
    "/questions/regenerate-data",
    response_model=RegenerationResponse
)
async def regenerate_question_from_data(
    request: QuestionDataRegenerationRequest
):
    """
    전달받은 데이터로 문제를 재생성합니다. (DB 저장 없음)

    생성 직후나 미리보기 상태에서 재생성할 때 사용합니다.

    ## 사용 예시
    ```json
    {
      "question_data": {
        "question_text": "다음 문장의 빈칸에 들어갈 말은?",
        "question_type": "객관식",
        "question_subject": "독해",
        "question_detail_type": "빈칸 추론",
        "question_difficulty": "상",
        "question_choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
        "correct_answer": 0
      },
      "passage_data": {
        "passage_content": "지문 내용...",
        "original_content": "원본 지문...",
        "korean_translation": "한글 번역..."
      },
      "regeneration_request": {
        "feedback": "문제를 더 쉽게 만들어주세요",
        "worksheet_context": {
          "school_level": "중학교",
          "grade": 1,
          "worksheet_type": "독해"
        },
        "current_question_type": "객관식",
        "current_subject": "독해",
        "current_detail_type": "빈칸 추론",
        "current_difficulty": "상"
      }
    }
    ```
    """
    try:
        regenerator = QuestionRegenerator()

        success, message, regenerated_question, regenerated_passage = regenerator.regenerate_question_from_data(
            request.question_data,
            request.passage_data,
            request.regeneration_request
        )

        if success:
            return RegenerationResponse(
                status="success",
                message=message,
                regenerated_question=regenerated_question,
                regenerated_passage=regenerated_passage
            )
        else:
            return RegenerationResponse(
                status="error",
                message=message,
                error_details=message
            )

    except Exception as e:
        return RegenerationResponse(
            status="error",
            message="재생성 중 오류가 발생했습니다.",
            error_details=str(e)
        )


@router.get("/worksheets/{worksheet_id}/questions/{question_id}/regeneration-info")
async def get_regeneration_info(
    worksheet_id: str = Path(..., description="워크시트 ID"),
    question_id: int = Path(..., description="문제 ID"),
    db: Session = Depends(get_db)
):
    """
    문제 재생성을 위한 현재 문제 정보를 조회합니다.
    프론트엔드에서 재생성 폼을 구성할 때 사용합니다.

    ## 응답 예시
    ```json
    {
      "question": {
        "id": 123,
        "question_type": "객관식",
        "question_subject": "독해",
        "question_detail_type": "제목 및 요지 추론",
        "question_difficulty": "상",
        "passage_id": 5
      },
      "worksheet": {
        "school_level": "중학교",
        "grade": 1,
        "problem_type": "혼합형"
      },
      "has_passage": true,
      "related_questions": [
        {"id": 124, "text": "다음 글의 내용과 일치하는 것은?"},
        {"id": 125, "text": "빈 칸에 들어갈 말로 가장 적절한 것은?"}
      ]
    }
    ```
    """

    try:
        from app.models import Question, Worksheet, Passage

        # 문제 정보 조회
        question = db.query(Question).filter(
            Question.worksheet_id == worksheet_id,
            Question.question_id == question_id
        ).first()

        if not question:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

        # 워크시트 정보 조회
        worksheet = db.query(Worksheet).filter(
            Worksheet.worksheet_id == worksheet_id
        ).first()

        if not worksheet:
            raise HTTPException(status_code=404, detail="워크시트를 찾을 수 없습니다.")

        # 지문 연계 정보 조회
        has_passage = question.passage_id is not None
        related_questions = []

        if has_passage:
            # 같은 지문에 연결된 다른 문제들 조회
            related_questions_query = db.query(Question).filter(
                Question.worksheet_id == worksheet_id,
                Question.passage_id == question.passage_id,
                Question.question_id != question_id
            ).all()

            related_questions = [
                {
                    "id": q.question_id,
                    "text": q.question_text[:50] + "..." if len(q.question_text) > 50 else q.question_text
                }
                for q in related_questions_query
            ]

        return {
            "question": {
                "id": question.question_id,
                "question_type": question.question_type,
                "question_subject": question.question_subject,
                "question_detail_type": question.question_detail_type,
                "question_difficulty": question.question_difficulty,
                "passage_id": question.passage_id
            },
            "worksheet": {
                "school_level": worksheet.school_level,
                "grade": worksheet.grade,
                "problem_type": worksheet.problem_type
            },
            "has_passage": has_passage,
            "related_questions": related_questions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"정보 조회 중 오류가 발생했습니다: {str(e)}"
        )