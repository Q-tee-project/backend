from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List
import httpx

from ..database import get_db
from ..core.auth import get_current_user
from ..tasks import grade_problems_mixed_task, process_assignment_ai_grading_task
from ..models.grading_result import GradingSession, ProblemGradingResult
from ..models.math_generation import Assignment

router = APIRouter()

async def get_student_info(student_id: int) -> dict:
    """auth-service에서 학생 정보 조회"""
    try:
        async with httpx.AsyncClient() as client:
            # Docker 내부 통신은 8000 포트 사용
            response = await client.get(f"http://auth-service:8000/api/auth/students/{student_id}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 학생 정보 조회 실패: {student_id}, 상태코드: {response.status_code}")
                return {
                    "student_id": student_id,
                    "name": f"학생{student_id}",
                    "school": "정보없음",
                    "grade": "정보없음"
                }
    except Exception as e:
        print(f"❌ 학생 정보 조회 오류: {student_id}, 오류: {e}")
        return {
            "student_id": student_id,
            "name": f"학생{student_id}",
            "school": "정보없음",
            "grade": "정보없음"
        }

@router.post("/worksheets/{worksheet_id}/grade")
async def grade_worksheet(
    worksheet_id: int,
    answer_sheet: UploadFile = File(..., description="답안지 이미지 파일"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from ..models.worksheet import Worksheet
    if not db.query(Worksheet).filter(Worksheet.id == worksheet_id).first():
        raise HTTPException(status_code=404, detail="워크시트를 찾을 수 없습니다.")
    
    image_data = await answer_sheet.read()
    task = grade_problems_mixed_task.delay(
        worksheet_id=worksheet_id,
        multiple_choice_answers={},
        canvas_answers={"sheet": image_data},
        user_id=current_user["id"]
    )
    return {"task_id": task.id, "status": "PENDING"}

@router.post("/worksheets/{worksheet_id}/grade-canvas")
async def grade_worksheet_canvas(
    worksheet_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from ..models.worksheet import Worksheet
    if not db.query(Worksheet).filter(Worksheet.id == worksheet_id).first():
        raise HTTPException(status_code=404, detail="워크시트를 찾을 수 없습니다.")

    task = grade_problems_mixed_task.delay(
        worksheet_id=worksheet_id,
        multiple_choice_answers=request.get("multiple_choice_answers", {}),
        canvas_answers=request.get("canvas_answers", {}),
        user_id=current_user["id"]
    )
    return {"task_id": task.id, "status": "PENDING"}

@router.get("/assignments/{assignment_id}/results")
async def get_assignment_results(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """과제의 채점 결과를 조회 (선생님용) - 학생별 구분 포함"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 해당 과제에 배포된 모든 학생들 조회
    from ..models.math_generation import TestSession, AssignmentDeployment

    # 배포된 학생들과 제출 현황 조회
    deployed_students = db.query(AssignmentDeployment).filter(
        AssignmentDeployment.assignment_id == assignment_id
    ).all()

    results = []
    for deployment in deployed_students:
        student_id = deployment.student_id

        # 학생 정보 조회 (auth-service에서)
        student_info = await get_student_info(student_id)

        # 해당 학생의 테스트 세션 조회
        test_session = db.query(TestSession).filter(
            TestSession.assignment_id == assignment_id,
            TestSession.student_id == student_id
        ).first()

        # 해당 학생의 채점 결과 조회
        grading_session = db.query(GradingSession).filter(
            GradingSession.worksheet_id == assignment.worksheet_id,
            GradingSession.graded_by == student_id
        ).first()

        # 상태 결정
        if not test_session:
            status = "미시작"
            completed_at = None
        elif test_session.status == "submitted":
            status = "완료" if grading_session else "제출완료"
            completed_at = test_session.submitted_at.isoformat() if test_session.submitted_at else None
        elif test_session.status == "started":
            status = "진행중"
            completed_at = None
        else:
            status = "미완료"
            completed_at = None

        # 문제별 결과 조회 (채점된 경우만)
        problem_results = []
        if grading_session:
            problem_results = db.query(ProblemGradingResult).filter(
                ProblemGradingResult.grading_session_id == grading_session.id
            ).all()

        student_result = {
            "student_id": student_id,
            "student_name": student_info.get("name", f"학생{student_id}"),
            "school": student_info.get("school", "정보없음"),
            "grade": student_info.get("grade", "정보없음"),
            "status": status,
            "score": grading_session.total_score if grading_session else 0,
            "max_possible_score": grading_session.max_possible_score if grading_session else assignment.problem_count * 10,
            "completed_at": completed_at,
            "grading_session_id": grading_session.id if grading_session else None,
            "total_problems": grading_session.total_problems if grading_session else assignment.problem_count,
            "correct_count": grading_session.correct_count if grading_session else 0,
            "graded_at": grading_session.graded_at.isoformat() if grading_session and grading_session.graded_at else None,
            "problem_results": [
                {
                    "problem_id": pr.problem_id,
                    "user_answer": pr.user_answer,
                    "correct_answer": pr.correct_answer,
                    "is_correct": pr.is_correct,
                    "score": pr.score,
                    "problem_type": pr.problem_type,
                    "difficulty": pr.difficulty,
                    "input_method": pr.input_method,
                    "explanation": pr.explanation
                }
                for pr in problem_results
            ]
        }

        results.append(student_result)

    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "worksheet_id": assignment.worksheet_id,
        "total_students": len(results),
        "completed_count": len([r for r in results if r["status"] == "완료"]),
        "results": results
    }

@router.post("/assignments/{assignment_id}/start-ai-grading")
async def start_ai_grading(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """과제의 손글씨 답안에 대해 OCR + AI 채점을 비동기로 시작"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 해당 과제의 모든 제출된 세션들을 찾기
    from ..models.math_generation import TestSession
    submitted_sessions = db.query(TestSession).filter(
        TestSession.assignment_id == assignment_id,
        TestSession.status == 'submitted'
    ).all()

    if not submitted_sessions:
        return {"message": "제출된 세션이 없습니다.", "task_id": None}

    # Celery 태스크로 비동기 처리 시작
    task = process_assignment_ai_grading_task.delay(
        assignment_id=assignment_id,
        user_id=current_user["id"]
    )

    return {
        "message": "OCR + AI 채점이 시작되었습니다.",
        "task_id": task.id,
        "status": "PENDING",
        "assignment_id": assignment_id
    }

@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Celery 태스크 상태 조회"""
    from celery.result import AsyncResult
    from ..celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
        "info": result.info,
        "ready": result.ready()
    }

@router.get("/grading-sessions/{session_id}")
async def get_grading_session_details(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """채점 세션 상세 정보 조회 (선생님 편집용)"""
    try:
        grading_session = db.query(GradingSession).filter(GradingSession.id == session_id).first()
        if not grading_session:
            raise HTTPException(status_code=404, detail="Grading session not found")

        # 문제별 채점 결과 조회
        problem_results = db.query(ProblemGradingResult).filter(
            ProblemGradingResult.grading_session_id == session_id
        ).all()

        print(f"=== LOADING SESSION {session_id} DETAILS ===")
        for pr in problem_results:
            print(f"Problem {pr.problem_id}: user_answer='{pr.user_answer}', score={pr.score}, is_correct={pr.is_correct}")

        # 학생 정보 조회 (에러 처리 추가)
        try:
            student_info = await get_student_info(grading_session.graded_by)
            student_name = student_info.get("name", f"학생{grading_session.graded_by}")
        except Exception as e:
            print(f"학생 정보 조회 실패: {e}")
            student_name = f"학생{grading_session.graded_by}"

        return {
            "id": grading_session.id,
            "worksheet_id": grading_session.worksheet_id,
            "graded_by": grading_session.graded_by,
            "student_name": student_name,
            "total_problems": grading_session.total_problems or 0,
            "correct_count": grading_session.correct_count or 0,
            "total_score": grading_session.total_score or 0,
            "max_possible_score": grading_session.max_possible_score or 100,
            "input_method": grading_session.input_method or "unknown",
            "status": "completed",  # 기본값 설정
            "graded_at": grading_session.graded_at.isoformat() if grading_session.graded_at else None,
            "teacher_id": None,  # 현재 모델에 없음
            "approved_at": None,  # 현재 모델에 없음
            "problem_results": [
                {
                    "problem_id": pr.problem_id,
                    "user_answer": pr.user_answer or "",
                    "correct_answer": pr.correct_answer or "",
                    "is_correct": pr.is_correct or False,
                    "score": pr.score or 0,
                    "problem_type": pr.problem_type or "unknown",
                    "difficulty": pr.difficulty or "A",
                    "input_method": pr.input_method or "unknown",
                    "explanation": pr.explanation or "",
                    "question": getattr(pr, 'question', "") or ""  # 안전한 접근
                }
                for pr in problem_results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"채점 세션 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/grading-sessions/{session_id}/update")
async def update_grading_session(
    session_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """채점 결과 업데이트 (선생님 편집)"""
    print(f"=== UPDATE GRADING SESSION {session_id} ===")
    print(f"Received update_data: {update_data}")

    grading_session = db.query(GradingSession).filter(GradingSession.id == session_id).first()
    if not grading_session:
        raise HTTPException(status_code=404, detail="Grading session not found")

    try:
        # 세션 정보 업데이트 (존재하는 필드만)
        if "total_score" in update_data:
            grading_session.total_score = update_data["total_score"]
        if "correct_count" in update_data:
            grading_session.correct_count = update_data["correct_count"]

        # status와 teacher_id는 현재 모델에 없으므로 주석 처리
        # if "status" in update_data:
        #     grading_session.status = update_data["status"]
        # grading_session.teacher_id = current_user["id"]

        # 문제별 결과 업데이트 (점수와 정답 여부만)
        if "problem_results" in update_data:
            print(f"Updating {len(update_data['problem_results'])} problem results...")
            for problem_data in update_data["problem_results"]:
                problem_id = problem_data["problem_id"]
                print(f"Problem {problem_id}: {problem_data}")

                problem_result = db.query(ProblemGradingResult).filter(
                    ProblemGradingResult.grading_session_id == session_id,
                    ProblemGradingResult.problem_id == problem_id
                ).first()

                if problem_result:
                    old_score = problem_result.score
                    old_correct = problem_result.is_correct
                    old_user_answer = problem_result.user_answer

                    # 점수와 정답 여부만 업데이트 (다른 필드는 보존)
                    if "score" in problem_data:
                        problem_result.score = problem_data["score"]
                        print(f"  Score: {old_score} -> {problem_result.score}")
                    if "is_correct" in problem_data:
                        problem_result.is_correct = problem_data["is_correct"]
                        print(f"  Correct: {old_correct} -> {problem_result.is_correct}")

                    print(f"  User answer preserved: {old_user_answer}")
                else:
                    print(f"  Problem result not found for problem_id: {problem_id}")

        db.commit()

        # 명시적으로 세션을 새로고침하여 최신 데이터 확인
        db.refresh(grading_session)

        # 업데이트 후 문제별 결과 재조회하여 확인
        updated_problem_results = db.query(ProblemGradingResult).filter(
            ProblemGradingResult.grading_session_id == session_id
        ).all()

        print(f"=== AFTER UPDATE VERIFICATION ===")
        for pr in updated_problem_results:
            print(f"Problem {pr.problem_id}: user_answer='{pr.user_answer}', score={pr.score}, is_correct={pr.is_correct}")

        return {
            "message": "Grading session updated successfully",
            "session_id": session_id,
            "total_score": grading_session.total_score,
            "correct_count": grading_session.correct_count,
            "status": "completed"  # 고정값
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update grading session: {str(e)}")

@router.post("/grading-sessions/{session_id}/approve")
async def approve_grading_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """채점 결과 승인"""
    grading_session = db.query(GradingSession).filter(GradingSession.id == session_id).first()
    if not grading_session:
        raise HTTPException(status_code=404, detail="Grading session not found")

    try:
        from datetime import datetime

        # 현재 모델에 없는 필드들은 주석 처리
        # grading_session.status = "approved"
        # grading_session.teacher_id = current_user["id"]
        # grading_session.approved_at = datetime.utcnow()

        # 현재는 별도의 승인 처리 없이 완료 상태로 간주
        db.commit()

        return {
            "message": "Grading session approved successfully",
            "session_id": session_id,
            "status": "approved",  # 고정값
            "approved_at": datetime.utcnow().isoformat(),
            "approved_by": current_user["id"]
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to approve grading session: {str(e)}")

@router.get("/assignments/{assignment_id}/students/{student_id}/result")
async def get_student_grading_result(
    assignment_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """특정 학생의 과제 채점 결과 조회 (학생 상세보기용)"""
    try:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # 해당 학생의 채점 결과 찾기
        grading_session = db.query(GradingSession).filter(
            GradingSession.worksheet_id == assignment.worksheet_id,
            GradingSession.graded_by == student_id
        ).first()

        if not grading_session:
            raise HTTPException(status_code=404, detail="No grading result found for this student")

        # 문제별 채점 결과 조회
        problem_results = db.query(ProblemGradingResult).filter(
            ProblemGradingResult.grading_session_id == grading_session.id
        ).all()

        # 학생 정보 조회 (에러 처리 추가)
        try:
            student_info = await get_student_info(student_id)
            student_name = student_info.get("name", f"학생{student_id}")
        except Exception as e:
            print(f"학생 정보 조회 실패: {e}")
            student_name = f"학생{student_id}"

        return {
            "assignment_id": assignment_id,
            "student_id": student_id,
            "student_name": student_name,
            "total_score": grading_session.total_score or 0,
            "max_possible_score": grading_session.max_possible_score or 100,
            "correct_count": grading_session.correct_count or 0,
            "total_problems": grading_session.total_problems or 0,
            "status": "completed",  # 고정값
            "graded_at": grading_session.graded_at.isoformat() if grading_session.graded_at else None,
            "problem_results": [
                {
                    "problem_id": pr.problem_id,
                    "user_answer": pr.user_answer or "",
                    "correct_answer": pr.correct_answer or "",
                    "is_correct": pr.is_correct or False,
                    "score": pr.score or 0,
                    "problem_type": pr.problem_type or "unknown",
                    "difficulty": pr.difficulty or "A",
                    "input_method": pr.input_method or "unknown",
                    "explanation": pr.explanation or "",
                    "question": getattr(pr, 'question', "") or ""  # 안전한 접근
                }
                for pr in problem_results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"학생 채점 결과 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
