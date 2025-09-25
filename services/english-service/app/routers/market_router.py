from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.worksheet import Worksheet, Question, Passage

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/worksheets/{worksheet_id}")
async def get_worksheet_for_market(
    worksheet_id: int,
    db: Session = Depends(get_db)
):
    """Market service용 워크시트 기본 정보 조회"""
    worksheet = db.query(Worksheet).filter(
        Worksheet.worksheet_id == worksheet_id
    ).first()

    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    # Market service가 기대하는 형식으로 변환
    return {
        "id": worksheet.worksheet_id,
        "title": worksheet.worksheet_name,
        "school_level": worksheet.school_level,
        "grade": int(worksheet.grade) if worksheet.grade.isdigit() else 1,  # String을 Integer로 변환
        "subject_type": "영어",  # 고정값
        "problem_type": worksheet.problem_type,
        "problem_count": worksheet.total_questions,
        "created_at": worksheet.created_at.isoformat(),
        "user_id": worksheet.teacher_id,
        "teacher_id": worksheet.teacher_id,
        "status": "completed"
    }


@router.get("/worksheets/{worksheet_id}/problems")
async def get_worksheet_problems_for_market(
    worksheet_id: int,
    db: Session = Depends(get_db)
):
    """Market service용 워크시트 + 문제 상세 정보 조회"""
    # 워크시트 정보 조회
    worksheet = db.query(Worksheet).filter(
        Worksheet.worksheet_id == worksheet_id
    ).first()

    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    # 문제 조회
    questions = db.query(Question).filter(
        Question.worksheet_id == worksheet_id
    ).order_by(Question.question_id).all()

    # 지문 조회 (필요한 경우)
    passages = db.query(Passage).filter(
        Passage.worksheet_id == worksheet_id
    ).all()

    # Passage를 딕셔너리로 변환 (passage_id를 키로)
    passage_dict = {p.passage_id: p for p in passages}

    # 워크시트 정보 (위와 동일한 형식)
    worksheet_info = {
        "id": worksheet.worksheet_id,
        "title": worksheet.worksheet_name,
        "school_level": worksheet.school_level,
        "grade": int(worksheet.grade) if worksheet.grade.isdigit() else 1,
        "subject_type": "영어",
        "problem_type": worksheet.problem_type,
        "problem_count": worksheet.total_questions,
        "created_at": worksheet.created_at.isoformat(),
        "status": "completed"
    }

    # 문제 정보 변환 (Market service 형식에 맞게)
    problems_list = []
    for question in questions:
        # 연관 지문 가져오기
        passage_content = ""
        if question.passage_id and question.passage_id in passage_dict:
            passage = passage_dict[question.passage_id]
            # passage_content가 JSON이면 적절히 처리
            if isinstance(passage.passage_content, dict):
                passage_content = passage.passage_content.get("content", "")
            else:
                passage_content = str(passage.passage_content)

        # 선택지 처리
        choices = None
        if question.question_choices:
            if isinstance(question.question_choices, list):
                choices = question.question_choices
            else:
                choices = question.question_choices

        problem_data = {
            "id": question.id,
            "sequence_order": question.question_id,
            "problem_type": question.question_type,
            "question_subject": question.question_subject,
            "difficulty": question.question_difficulty,
            "question": question.question_text,
            "choices": choices,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "learning_point": question.learning_point,
            "example_content": question.example_content,
            "passage_content": passage_content,
            # Market service가 필요로 할 수 있는 추가 필드들
            "source_text": passage_content,  # 호환성을 위해
            "source_title": f"{worksheet.worksheet_name} - 문제 {question.question_id}",
        }

        problems_list.append(problem_data)

    return {
        "worksheet": worksheet_info,
        "problems": problems_list
    }


@router.post("/worksheets/copy")
async def copy_worksheet_for_purchase(
    copy_request: dict,
    db: Session = Depends(get_db)
):
    """워크시트 복사 (Market service 구매 시 사용)"""
    source_worksheet_id = copy_request.get("source_worksheet_id")
    target_user_id = copy_request.get("target_user_id")
    new_title = copy_request.get("new_title")

    if not all([source_worksheet_id, target_user_id, new_title]):
        raise HTTPException(
            status_code=400,
            detail="source_worksheet_id, target_user_id, new_title are required"
        )

    # 원본 워크시트 조회
    source_worksheet = db.query(Worksheet).filter(
        Worksheet.worksheet_id == source_worksheet_id
    ).first()

    if not source_worksheet:
        raise HTTPException(status_code=404, detail="Source worksheet not found")

    try:
        # 새 워크시트 생성
        new_worksheet = Worksheet(
            teacher_id=target_user_id,
            worksheet_name=new_title,
            school_level=source_worksheet.school_level,
            grade=source_worksheet.grade,
            subject=source_worksheet.subject,
            problem_type=source_worksheet.problem_type,
            total_questions=source_worksheet.total_questions,
            duration=source_worksheet.duration,
            created_at=datetime.now()
        )

        db.add(new_worksheet)
        db.flush()  # ID 생성을 위해

        # 원본 문제들 복사
        source_questions = db.query(Question).filter(
            Question.worksheet_id == source_worksheet_id
        ).all()

        for question in source_questions:
            new_question = Question(
                worksheet_id=new_worksheet.worksheet_id,
                question_id=question.question_id,
                question_text=question.question_text,
                question_type=question.question_type,
                question_subject=question.question_subject,
                question_detail_type=question.question_detail_type,
                question_difficulty=question.question_difficulty,
                question_choices=question.question_choices,
                passage_id=question.passage_id,
                correct_answer=question.correct_answer,
                example_content=question.example_content,
                example_original_content=question.example_original_content,
                example_korean_translation=question.example_korean_translation,
                explanation=question.explanation,
                learning_point=question.learning_point,
                created_at=datetime.now()
            )
            db.add(new_question)

        # 원본 지문들 복사
        source_passages = db.query(Passage).filter(
            Passage.worksheet_id == source_worksheet_id
        ).all()

        for passage in source_passages:
            new_passage = Passage(
                worksheet_id=new_worksheet.worksheet_id,
                passage_id=passage.passage_id,
                passage_type=passage.passage_type,
                passage_content=passage.passage_content,
                original_content=passage.original_content,
                korean_translation=passage.korean_translation,
                related_questions=passage.related_questions,
                created_at=datetime.now()
            )
            db.add(new_passage)

        db.commit()

        return {
            "new_worksheet_id": new_worksheet.worksheet_id,
            "message": "Worksheet copied successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to copy worksheet: {str(e)}"
        )


@router.get("/worksheets/{worksheet_id}/access")
async def check_worksheet_access(
    worksheet_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """워크시트 접근 권한 확인"""
    worksheet = db.query(Worksheet).filter(
        Worksheet.worksheet_id == worksheet_id
    ).first()

    if not worksheet:
        return {"has_access": False}

    # 워크시트 소유자 확인
    has_access = worksheet.teacher_id == user_id

    return {"has_access": has_access}