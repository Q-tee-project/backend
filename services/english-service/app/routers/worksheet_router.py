from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.core.config import get_settings
from app.schemas.generation import WorksheetGenerationRequest
from app.schemas.worksheet import (
    WorksheetSaveRequest, WorksheetSummary
)
from app.models import (
    GradingResult, QuestionResult, Worksheet, Passage, Question
)
from app.tasks import generate_english_worksheet_task
from app.celery_app import celery_app

router = APIRouter(tags=["Worksheets"])
settings = get_settings()

@router.post("/worksheet-generate")
async def worksheet_generate(request: WorksheetGenerationRequest, db: Session = Depends(get_db)):
    """비동기 영어 문제 생성을 시작합니다. (AI Judge 검증 항상 활성화)"""
    print("🚨 비동기 문제 생성 요청 시작!")

    try:
        print("\n" + "="*80)
        print("🎯 문제 생성 옵션 입력 받음!")

        print(f" 학교급: {request.school_level}")
        print(f" 학년: {request.grade}학년")
        print(f" 총 문제 수: {request.total_questions}개")
        print(f" 선택된 영역: {', '.join(request.subjects)}")
        print(f" AI Judge 검증: 활성화 (항상)")

        # 세부 영역 정보 출력
        if request.subject_details:
            print("\n📋 세부 영역 선택:")
            if request.subject_details.reading_types:
                print(f"  📖 독해 유형: {', '.join(map(str, request.subject_details.reading_types))}")
            if request.subject_details.grammar_categories:
                print(f"  📝 문법 카테고리: {', '.join(map(str, request.subject_details.grammar_categories))}")
            if request.subject_details.vocabulary_categories:
                print(f"  📚 어휘 카테고리: {', '.join(map(str, request.subject_details.vocabulary_categories))}")

        print("="*80)

        # 요청 데이터에 검증 항상 활성화
        request_data = request.model_dump()
        request_data['enable_validation'] = True

        # 비동기 태스크 시작
        task = generate_english_worksheet_task.delay(request_data)

        print(f"🚀 Celery 태스크 시작됨: {task.id}")

        return {
            "task_id": task.id,
            "status": "started",
            "message": "영어 문제 생성이 시작되었습니다. 태스크 ID로 진행 상황을 확인하세요."
        }

    except Exception as e:
        print(f"❌ 비동기 문제 생성 시작 실패: {str(e)}")
        return {
            "message": f"문제 생성 시작 중 오류가 발생했습니다: {str(e)}",
            "status": "error"
        }


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """태스크 진행 상황 조회"""
    try:
        print(f"🔍 태스크 상태 조회: {task_id}")

        # Celery AsyncResult로 태스크 상태 확인
        result = celery_app.AsyncResult(task_id)

        if result.state == 'PENDING':
            return {
                "task_id": task_id,
                "state": result.state,
                "status": "대기 중...",
                "current": 0,
                "total": 100
            }
        elif result.state == 'PROGRESS':
            info = result.info or {}
            return {
                "task_id": task_id,
                "state": result.state,
                "status": info.get('status', '처리 중...'),
                "current": info.get('current', 0),
                "total": info.get('total', 100)
            }
        elif result.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "state": result.state,
                "status": "완료",
                "current": 100,
                "total": 100,
                "result": result.info
            }
        else:  # FAILURE
            error_msg = str(result.info) if result.info else "알 수 없는 오류"
            return {
                "task_id": task_id,
                "state": result.state,
                "status": "실패",
                "current": 0,
                "total": 100,
                "error": error_msg
            }

    except Exception as e:
        print(f"❌ 태스크 상태 조회 실패 {task_id}: {str(e)}")
        return {
            "task_id": task_id,
            "state": "FAILURE",
            "status": "상태 조회 실패",
            "current": 0,
            "total": 100,
            "error": f"태스크 상태 조회 실패: {str(e)}"
        }


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """태스크 취소"""
    try:
        print(f"🛑 태스크 취소: {task_id}")

        # Celery 태스크 취소
        celery_app.control.revoke(task_id, terminate=True)

        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "태스크가 취소되었습니다."
        }

    except Exception as e:
        print(f"❌ 태스크 취소 실패 {task_id}: {str(e)}")
        return {
            "task_id": task_id,
            "status": "error",
            "message": f"태스크 취소 실패: {str(e)}"
        }


@router.get("/celery-health")
async def check_celery_health():
    """Celery 워커 상태 확인"""
    try:
        # Celery 워커들의 상태 확인
        inspect = celery_app.control.inspect()

        # 활성 워커 확인
        active_workers = inspect.active()
        registered_tasks = inspect.registered()

        if not active_workers:
            return {
                "status": "unhealthy",
                "message": "활성화된 Celery 워커가 없습니다.",
                "active_workers": 0,
                "workers": {}
            }

        return {
            "status": "healthy",
            "message": "Celery 워커가 정상 작동 중입니다.",
            "active_workers": len(active_workers),
            "workers": active_workers,
            "registered_tasks": registered_tasks
        }

    except Exception as e:
        print(f"❌ Celery 상태 확인 실패: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Celery 상태 확인 실패: {str(e)}",
            "active_workers": 0,
            "workers": {}
        }


@router.post("/worksheet-save", response_model=Dict[str, Any])
async def save_worksheet(request: WorksheetSaveRequest, db: Session = Depends(get_db)):
    """생성된 문제지를 데이터베이스에 저장합니다."""
    print("🚨 저장 요청 시작!")
    try:
        # 문제지 메타데이터는 이제 직접 접근 가능
        teacher_id = request.teacher_id
        worksheet_name = request.worksheet_name
        school_level = request.worksheet_level
        grade = str(request.worksheet_grade)
        subject = request.worksheet_subject
        problem_type = request.problem_type
        total_questions = request.total_questions
        duration = request.worksheet_duration

        print(f"🆔 워크시트 자동 ID 생성 예정")

        # 1. Worksheet 생성 (worksheet_id는 자동 증가)
        db_worksheet = Worksheet(
            teacher_id=teacher_id,
            worksheet_name=worksheet_name,
            school_level=school_level,
            grade=grade,
            subject=subject,
            problem_type=problem_type,
            total_questions=total_questions,
            duration=int(duration) if duration else None,
            created_at=datetime.now()
        )
        db.add(db_worksheet)
        db.flush()
        
        # 2. Passages 저장
        for passage_data in request.passages:
            db_passage = Passage(
                worksheet_id=db_worksheet.worksheet_id,
                passage_id=passage_data.passage_id,
                passage_type=passage_data.passage_type,
                passage_content=passage_data.passage_content,
                original_content=passage_data.original_content,
                korean_translation=passage_data.korean_translation,
                related_questions=passage_data.related_questions,
                created_at=datetime.now()
            )
            db.add(db_passage)
        
        # 3. Examples는 이제 Question 모델에 포함됨 (별도 저장 불필요)
        
        # 4. Questions 저장
        for question_data in request.questions:
            db_question = Question(
                worksheet_id=db_worksheet.worksheet_id,
                question_id=question_data.question_id,
                question_text=question_data.question_text,
                question_type=question_data.question_type,
                question_subject=question_data.question_subject,
                question_difficulty=question_data.question_difficulty,
                question_detail_type=question_data.question_detail_type,
                question_choices=question_data.question_choices,
                passage_id=question_data.question_passage_id,
                correct_answer=question_data.correct_answer,
                example_content=question_data.example_content,
                example_original_content=question_data.example_original_content,
                example_korean_translation=question_data.example_korean_translation,
                explanation=question_data.explanation,
                learning_point=question_data.learning_point,
                created_at=datetime.now()
            )
            db.add(db_question)
        
        # 커밋
        db.commit()
        db.refresh(db_worksheet)
        
        return {
            "message": "문제지가 성공적으로 저장되었습니다.",
            "worksheet_id": db_worksheet.worksheet_id,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 문제지 저장 오류 상세:")
        print(f"   오류 타입: {type(e).__name__}")
        print(f"   오류 메시지: {str(e)}")
        print(f"   오류 위치: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
        import traceback
        print(f"   전체 스택 트레이스:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"문제지 저장 중 오류: {str(e)}")

@router.get("/worksheets", response_model=List[WorksheetSummary])
async def get_worksheets(user_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """특정 교사의 저장된 문제지 목록을 조회합니다."""
    try:
        # limit 값을 100으로 제한
        actual_limit = min(limit, 100)

        worksheets = db.query(Worksheet).filter(
            Worksheet.teacher_id == user_id
        ).order_by(Worksheet.created_at.desc()).limit(actual_limit).all()

        return [
            WorksheetSummary(
                worksheet_id=worksheet.worksheet_id,
                teacher_id=worksheet.teacher_id,
                worksheet_name=worksheet.worksheet_name,
                school_level=worksheet.school_level,
                grade=worksheet.grade,
                subject=worksheet.subject,
                problem_type=worksheet.problem_type,
                total_questions=worksheet.total_questions,
                duration=worksheet.duration,
                created_at=worksheet.created_at
            )
            for worksheet in worksheets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제지 목록 조회 중 오류: {str(e)}")

@router.get("/worksheets/{worksheet_id}")
async def get_worksheet_for_editing(worksheet_id: int, user_id: int, db: Session = Depends(get_db)):
    """문제지 편집용 워크시트를 조회합니다"""
    try:
        worksheet = db.query(Worksheet).filter(
            Worksheet.worksheet_id == worksheet_id,
            Worksheet.teacher_id == user_id
        ).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        # 문제지 데이터를 딕셔너리로 변환
        worksheet_data = {
            "worksheet_id": worksheet.worksheet_id,
            "teacher_id": worksheet.teacher_id,
            "worksheet_name": worksheet.worksheet_name,
            "worksheet_level": worksheet.school_level,
            "worksheet_grade": worksheet.grade,
            "worksheet_subject": worksheet.subject,
            "problem_type": worksheet.problem_type,
            "total_questions": worksheet.total_questions,
            "worksheet_duration": worksheet.duration,
            "passages": [],
            "questions": []
        }
        
        # 지문 데이터 추가
        for passage in worksheet.passages:
            passage_data = {
                "passage_id": passage.passage_id,
                "passage_type": passage.passage_type,
                "passage_content": passage.passage_content,
                "original_content": passage.original_content,
                "korean_translation": passage.korean_translation,
                "related_questions": passage.related_questions
            }
            worksheet_data["passages"].append(passage_data)
        
        # 문제 데이터 추가 (정답/해설 포함)
        for question in worksheet.questions:
            question_data = {
                "question_id": question.question_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "question_subject": question.question_subject,
                "question_difficulty": question.question_difficulty,
                "question_detail_type": question.question_detail_type,
                "question_choices": question.question_choices,
                "question_passage_id": question.passage_id,
                "correct_answer": question.correct_answer,
                "example_content": question.example_content,
                "example_original_content": question.example_original_content,
                "example_korean_translation": question.example_korean_translation,
                "explanation": question.explanation,
                "learning_point": question.learning_point
            }
            worksheet_data["questions"].append(question_data)
        
        return {
            "status": "success",
            "message": "편집용 문제지를 성공적으로 조회했습니다.",
            "worksheet_data": worksheet_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"편집용 문제지 조회 중 오류: {str(e)}")

@router.get("/worksheets/{worksheet_id}/solve")
async def get_worksheet_for_solving(worksheet_id: int, db: Session = Depends(get_db)):
    """문제 풀이용 문제지를 조회합니다 (답안 제외)."""
    try:
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        # 문제지 데이터를 딕셔너리로 변환
        worksheet_data = {
            "worksheet_id": worksheet.worksheet_id,
            "worksheet_name": worksheet.worksheet_name,
            "worksheet_level": worksheet.school_level,
            "worksheet_grade": worksheet.grade,
            "worksheet_subject": worksheet.subject,
            "total_questions": worksheet.total_questions,
            "worksheet_duration": worksheet.duration,
            "passages": [],
            "examples": [],
            "questions": []
        }
        
        # 지문 데이터 추가 (한글 번역 포함)
        for passage in worksheet.passages:
            worksheet_data["passages"].append({
                "passage_id": passage.passage_id,
                "passage_type": passage.passage_type,
                "passage_content": passage.passage_content,
                "original_content": passage.original_content,
                "korean_translation": passage.korean_translation,
                "related_questions": passage.related_questions
            })
        
        # 문제 데이터 추가 (답안 제외)
        for question in worksheet.questions:
            worksheet_data["questions"].append({
                "question_id": question.question_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "question_subject": question.question_subject,
                "question_difficulty": question.question_difficulty,
                "question_detail_type": question.question_detail_type,
                "question_choices": question.question_choices,
                "question_passage_id": question.passage_id,
                "question_example_id": question.example_id
            })
        
        # 응답 데이터 구조 통일 (채점 결과 호환성)
        return {
            "worksheet_id": worksheet_data["worksheet_id"],
            "worksheet_name": worksheet_data["worksheet_name"],
            "worksheet_level": worksheet_data["worksheet_level"],
            "worksheet_grade": worksheet_data["worksheet_grade"],
            "worksheet_subject": worksheet_data["worksheet_subject"],
            "total_questions": worksheet_data["total_questions"],
            "worksheet_duration": worksheet_data["worksheet_duration"],
            "passages": worksheet_data["passages"],
            "examples": worksheet_data["examples"],
            "questions": worksheet_data["questions"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제지 조회 중 오류: {str(e)}")

# === CRUD 엔드포인트들 ===

@router.put("/worksheets/{worksheet_id}/questions/{question_id}")
async def update_question(
    worksheet_id: int,
    question_id: int,
    request: Dict[str, Any],
    user_id: int,
    db: Session = Depends(get_db)
):
    """문제를 수정합니다."""
    try:
        from app.services.worksheet_crud.question_service import QuestionService

        service = QuestionService(db)
        updated_question = service.update_question(worksheet_id, question_id, request)

        return {
            "status": "success",
            "message": "문제가 수정되었습니다.",
            "question": {
                "question_id": updated_question.question_id,
                "question_text": updated_question.question_text,
                "question_type": updated_question.question_type,
                "question_subject": updated_question.question_subject,
                "question_difficulty": updated_question.question_difficulty,
                "correct_answer": updated_question.correct_answer
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제 수정 중 오류: {str(e)}")

@router.put("/worksheets/{worksheet_id}/passages/{passage_id}")
async def update_passage(
    worksheet_id: int,
    passage_id: int,
    request: Dict[str, Any],
    user_id: int,
    db: Session = Depends(get_db)
):
    """지문을 수정합니다."""
    try:
        from app.services.worksheet_crud.passage_service import PassageService

        service = PassageService(db)
        updated_passage = service.update_passage(worksheet_id, passage_id, request)

        return {
            "status": "success",
            "message": "지문이 수정되었습니다.",
            "passage": {
                "passage_id": updated_passage.passage_id,
                "passage_type": updated_passage.passage_type
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지문 수정 중 오류: {str(e)}")

@router.put("/worksheets/{worksheet_id}/title")
async def update_worksheet_title(
    worksheet_id: int,
    request: Dict[str, str],
    user_id: int = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """워크시트 제목을 수정합니다."""
    try:
        from app.services.worksheet_crud.worksheet_service import WorksheetService

        new_title = request.get("worksheet_name")

        if not new_title:
            raise HTTPException(status_code=400, detail="worksheet_name이 필요합니다.")

        updated_worksheet = WorksheetService.update_worksheet_title(db, worksheet_id, new_title)

        return {
            "status": "success",
            "message": "제목이 수정되었습니다.",
            "worksheet": {
                "worksheet_id": updated_worksheet.worksheet_id,
                "worksheet_name": updated_worksheet.worksheet_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제목 수정 중 오류: {str(e)}")

@router.delete("/worksheets/batch")
async def batch_delete_worksheets(
    request: Dict[str, List[int]],
    user_id: int = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """여러 워크시트를 일괄 삭제합니다."""
    try:
        from app.services.worksheet_crud.worksheet_service import WorksheetService

        worksheet_ids = request.get("worksheet_ids", [])

        if not worksheet_ids:
            raise HTTPException(status_code=400, detail="worksheet_ids가 필요합니다.")

        deleted_count = WorksheetService.batch_delete_worksheets(db, worksheet_ids, user_id)

        return {
            "status": "success",
            "message": f"{deleted_count}개의 워크시트가 삭제되었습니다.",
            "deleted_count": deleted_count,
            "deleted_ids": worksheet_ids
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일괄 삭제 중 오류: {str(e)}")

@router.delete("/worksheets/{worksheet_id}", response_model=Dict[str, Any])
async def delete_worksheet(worksheet_id: int, db: Session = Depends(get_db)):
    """문제지와 관련된 모든 데이터를 삭제합니다."""
    try:
        # 문제지 존재 확인
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        worksheet_name = worksheet.worksheet_name
        
        # 관련된 채점 결과 삭제
        grading_results = db.query(GradingResult).filter(GradingResult.worksheet_id == worksheet_id).all()
        for result in grading_results:
            db.query(QuestionResult).filter(QuestionResult.grading_result_id == result.result_id).delete()
            db.delete(result)
        
        # 2. 문제 삭제
        db.query(Question).filter(Question.worksheet_id == worksheet_id).delete()
        
        # 3. 지문 삭제
        db.query(Passage).filter(Passage.worksheet_id == worksheet_id).delete()
        
        # 4. 예문은 Question 모델에 포함되어 있으므로 별도 삭제 불필요
        
        # 5. 문제지 삭제
        db.delete(worksheet)
        
        # 변경사항 커밋
        db.commit()
        
        return {
            "status": "success",
            "message": f"문제지 '{worksheet_name}'이 성공적으로 삭제되었습니다.",
            "deleted_worksheet_id": worksheet_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"문제지 삭제 중 오류: {str(e)}")


