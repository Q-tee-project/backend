from celery import current_task
from .celery_app import celery_app
from .database import SessionLocal
from .services.math_generation_service import MathGenerationService
from .schemas.math_generation import MathProblemGenerationRequest
from .models.worksheet import Worksheet, WorksheetStatus
from .models.problem import Problem
from .services.math_grading_service import MathGradingService
from .models.grading_result import GradingSession, ProblemGradingResult
from .models.math_generation import Assignment, TestSession, TestAnswer
from .services.ocr_service import OCRService
from .core.exceptions import AIResponseError, GradingError, GenerationError
import json
import uuid
import base64
from datetime import datetime, timezone
from sqlalchemy.orm import Session


@celery_app.task(bind=True, name="app.tasks.generate_math_problems_task")
def generate_math_problems_task(self, request_data: dict, user_id: int):
    """비동기 수학 문제 생성 태스크"""
    task_id = self.request.id
    generation_id = str(uuid.uuid4())
    print(f"🚀 Math problems generation task started: {task_id}")

    db = SessionLocal()
    worksheet = None
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': '요청 처리 중...'})
        request = MathProblemGenerationRequest.model_validate(request_data)

        worksheet_title = f"{request.chapter.chapter_name} - {request.problem_count.value}"
        worksheet = Worksheet(
            title=worksheet_title, school_level=request.school_level.value, grade=request.grade,
            semester=request.semester.value, unit_number=request.unit_number, unit_name=request.chapter.unit_name,
            chapter_number=request.chapter.chapter_number, chapter_name=request.chapter.chapter_name,
            problem_count=request.problem_count.value_int, difficulty_ratio=request.difficulty_ratio.model_dump(),
            problem_type_ratio=request.problem_type_ratio.model_dump(), user_prompt=request.user_text,
            generation_id=generation_id, status=WorksheetStatus.PROCESSING, teacher_id=user_id,
            created_by=user_id, celery_task_id=task_id
        )
        db.add(worksheet)
        db.commit()
        db.refresh(worksheet)

        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': 'AI 문제 생성 중...'})
        math_service = MathGenerationService()
        curriculum_data = math_service._get_curriculum_data(request)
        
        from .services.problem_generator import ProblemGenerator
        problem_generator = ProblemGenerator()
        generated_problems = problem_generator.generate_problems(
            curriculum_data=curriculum_data, user_prompt=request.user_text,
            problem_count=request.problem_count.value_int, difficulty_ratio=request.difficulty_ratio.model_dump()
        )

        if not isinstance(generated_problems, list):
            raise AIResponseError(f"AI 응답이 잘못된 형식입니다. 리스트가 아닌 {type(generated_problems)} 타입을 받았습니다.")

        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': '문제 저장 중...'})

        try:
            problems_to_save = []
            for i, problem_data in enumerate(generated_problems):
                if not isinstance(problem_data, dict):
                    print(f"⚠️ 경고: 생성된 문제 목록에 잘못된 항목이 있습니다. {type(problem_data)} 타입.")
                    continue
                
                problem = Problem(
                    worksheet_id=worksheet.id, sequence_order=i + 1,
                    problem_type=problem_data.get("problem_type", "multiple_choice"),
                    difficulty=problem_data.get("difficulty", "B"),
                    question=problem_data.get("question", ""),
                    choices=json.dumps(problem_data.get("choices")) if problem_data.get("choices") else None,
                    correct_answer=problem_data.get("correct_answer", ""),
                    explanation=problem_data.get("explanation", ""),
                    latex_content=problem_data.get("latex_content"),
                    has_diagram=str(problem_data.get("has_diagram", False)).lower(),
                    diagram_type=problem_data.get("diagram_type"),
                    diagram_elements=json.dumps(problem_data.get("diagram_elements")) if problem_data.get("diagram_elements") else None
                )
                problems_to_save.append(problem)

            if not problems_to_save:
                raise GenerationError("AI가 유효한 문제를 생성하지 못했습니다.")

            db.add_all(problems_to_save)

            worksheet.status = WorksheetStatus.COMPLETED
            worksheet.completed_at = datetime.now()
            worksheet.actual_difficulty_distribution = math_service._calculate_difficulty_distribution(generated_problems)
            worksheet.actual_type_distribution = math_service._calculate_type_distribution(generated_problems)
            
            db.commit()
            print(f"✅ 워크시트 {worksheet.id}와 문제 {len(problems_to_save)}개 저장 완료.")

        except Exception as e:
            db.rollback()
            worksheet.status = WorksheetStatus.FAILED
            worksheet.error_message = f"문제 저장 중 오류 발생: {str(e)}"
            db.commit()
            raise

        problem_responses = [{"id": p.id, "sequence_order": p.sequence_order, "question": p.question} for p in problems_to_save]
        return {"generation_id": generation_id, "worksheet_id": worksheet.id, "total_generated": len(problems_to_save), "problems": problem_responses}

    except Exception as e:
        print(f"❌ 태스크 실패: {e}")
        db.rollback()
        if worksheet and worksheet.id and worksheet.status != WorksheetStatus.FAILED:
            try:
                worksheet.status = WorksheetStatus.FAILED
                worksheet.error_message = str(e)
                db.commit()
            except Exception as update_err:
                print(f"❌ 실패 상태 업데이트 중 추가 오류: {update_err}")
        
        self.update_state(state='FAILURE', meta={'error': str(e), 'status': '문제 생성 실패'})
        raise

    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.grade_problems_mixed_task")
def grade_problems_mixed_task(self, worksheet_id: int, multiple_choice_answers: dict, canvas_answers: dict, user_id: int):
    """혼합형 채점 태스크 (객관식 + 주관식 OCR)"""
    task_id = self.request.id
    db = SessionLocal()
    grading_service = MathGradingService()
    
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': '채점 준비 중...'})
        
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
        if not worksheet:
            raise GradingError("채점할 워크시트를 찾을 수 없습니다.")
        
        problems = db.query(Problem).filter(Problem.worksheet_id == worksheet_id).all()
        total_count = len(problems)
        points_per_problem = 100 // total_count if total_count > 0 else 0
        
        self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': '손글씨 답안 추출 중...'})
        
        ocr_results = grading_service.extract_answers_from_canvas(canvas_answers)
        
        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': '답안 채점 중...'})
        
        grading_results, correct_count, total_score = grading_service.grade_problems(
            problems=problems, 
            multiple_choice_answers=multiple_choice_answers, 
            ocr_results=ocr_results,
            points_per_problem=points_per_problem
        )
        
        self.update_state(state='PROGRESS', meta={'current': 95, 'total': 100, 'status': '결과 저장 중...'})
        
        grading_session = GradingSession(
            worksheet_id=worksheet_id, celery_task_id=task_id, total_problems=total_count, correct_count=correct_count,
            total_score=total_score, max_possible_score=total_count * points_per_problem, points_per_problem=points_per_problem,
            ocr_results=ocr_results, multiple_choice_answers=multiple_choice_answers, input_method="canvas", graded_by=user_id
        )
        db.add(grading_session)
        db.flush()
        
        for result_item in grading_results:
            db.add(ProblemGradingResult(**result_item, grading_session_id=grading_session.id))
        
        db.commit()
        
        return {
            "grading_session_id": grading_session.id, "worksheet_id": worksheet_id, "total_problems": total_count,
            "correct_count": correct_count, "total_score": total_score, "grading_results": grading_results
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e), 'status': '채점 실패'})
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.get_task_status")
def get_task_status(self, task_id: str):
    """태스크 상태 조회"""
    from celery.result import AsyncResult
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id, "status": result.status,
        "result": result.result if result.successful() else None, "info": result.info
    }


@celery_app.task(bind=True, name="app.tasks.regenerate_single_problem_task")
def regenerate_single_problem_task(self, problem_id: int, requirements: str, current_problem: dict):
    """비동기 개별 문제 재생성 태스크"""
    task_id = self.request.id
    print(f"🔄 Problem regeneration task started: {task_id}")
    db = SessionLocal()
    try:
        self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': '문제 정보 조회 중...'})
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem: raise GenerationError("문제를 찾을 수 없습니다.")
        worksheet = db.query(Worksheet).filter(Worksheet.id == problem.worksheet_id).first()
        if not worksheet: raise GenerationError("워크시트를 찾을 수 없습니다.")

        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'AI 문제 생성 중...'})
        
        from .services.ai_service import AIService
        ai_service = AIService()
        new_problem_data = ai_service.regenerate_single_problem(current_problem=current_problem, requirements=requirements)
        if not new_problem_data: raise AIResponseError("문제 재생성에 실패했습니다.")

        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': '문제 정보 업데이트 중...'})
        
        problem.question = new_problem_data.get("question", problem.question)
        problem.correct_answer = new_problem_data.get("correct_answer", problem.correct_answer)
        problem.explanation = new_problem_data.get("explanation", problem.explanation)
        if new_problem_data.get("choices"): problem.choices = json.dumps(new_problem_data["choices"], ensure_ascii=False)
        
        db.commit()
        db.refresh(problem)

        return {"message": f"{problem.sequence_order}번 문제가 성공적으로 재생성되었습니다.", "problem_id": problem_id, **new_problem_data}

    except Exception as e:
        print(f"❌ Problem regeneration failed: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e), 'status': '문제 재생성 실패'})
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.process_assignment_ai_grading_task")
def process_assignment_ai_grading_task(self, assignment_id: int, user_id: int):
    """과제의 손글씨 답안에 대해 OCR + AI 채점을 비동기로 처리하는 태스크"""
    task_id = self.request.id
    db = SessionLocal()

    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': '과제 정보 조회 중...'})

        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise GradingError("Assignment not found")

        self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': '제출된 세션 조회 중...'})

        # 해당 과제의 모든 제출된 세션들을 찾기
        submitted_sessions = db.query(TestSession).filter(
            TestSession.assignment_id == assignment_id,
            TestSession.status == 'submitted'
        ).all()

        if not submitted_sessions:
            return {"message": "제출된 세션이 없습니다.", "processed_count": 0}

        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': 'OCR 처리 중...'})

        processed_count = 0
        total_answers = 0

        # 모든 세션의 손글씨 답안 수 계산
        for session in submitted_sessions:
            handwriting_answers = db.query(TestAnswer).filter(
                TestAnswer.session_id == session.session_id,
                TestAnswer.answer.like('data:image/%')
            ).all()
            total_answers += len(handwriting_answers)

        current_answer = 0

        for session in submitted_sessions:
            # 손글씨 이미지 답안들을 찾기
            handwriting_answers = db.query(TestAnswer).filter(
                TestAnswer.session_id == session.session_id,
                TestAnswer.answer.like('data:image/%')
            ).all()

            for answer in handwriting_answers:
                current_answer += 1
                progress = 20 + (current_answer * 50 // total_answers) if total_answers > 0 else 70
                self.update_state(state='PROGRESS', meta={
                    'current': progress, 'total': 100,
                    'status': f'OCR 처리 중... ({current_answer}/{total_answers})'
                })

                try:
                    print(f"🔍 답안 디버그: 문제 {answer.problem_id}, 답안 길이: {len(answer.answer)}")
                    print(f"🔍 답안 디버그: 답안 시작: {answer.answer[:100]}...")

                    # base64 이미지에서 실제 데이터 추출
                    if ',' in answer.answer:
                        image_data = base64.b64decode(answer.answer.split(',')[1])
                        print(f"🔍 답안 디버그: 디코딩된 이미지 크기: {len(image_data)} bytes")

                        ocr_service = OCRService()
                        ocr_text = ocr_service.extract_text_from_image(image_data)

                        if ocr_text and ocr_text.strip():
                            # OCR 성공 시 텍스트로 업데이트
                            answer.answer = ocr_text.strip()
                            processed_count += 1
                            print(f"✅ OCR 처리 완료: 문제 {answer.problem_id} → {ocr_text[:50]}")
                        else:
                            print(f"❌ OCR 텍스트 인식 실패: 문제 {answer.problem_id}")
                    else:
                        print(f"❌ 잘못된 이미지 형식: 문제 {answer.problem_id}")

                except Exception as e:
                    print(f"❌ OCR 처리 실패: 문제 {answer.problem_id}, 오류: {e}")
                    continue

        db.commit()

        self.update_state(state='PROGRESS', meta={'current': 75, 'total': 100, 'status': '채점 세션 생성 중...'})

        # OCR 처리된 손글씨 답안에 대해서만 채점 세션 업데이트
        updated_sessions = []
        newly_graded_sessions = []
        from .models.problem import Problem

        for session in submitted_sessions:
            # 해당 세션에 손글씨 답안이 있는지 확인
            handwriting_answers = db.query(TestAnswer).filter(
                TestAnswer.session_id == session.session_id,
                TestAnswer.answer.like('data:image/%')
            ).all()

            # 손글씨 답안이 없으면 스킵 (이미 채점된 객관식만 있음)
            if not handwriting_answers:
                continue

            # 해당 세션의 기존 채점 결과가 있는지 확인
            existing_grading = db.query(GradingSession).filter(
                GradingSession.worksheet_id == assignment.worksheet_id,
                GradingSession.graded_by == session.student_id  # 학생별 구분
            ).first()

            problems = db.query(Problem).filter(Problem.worksheet_id == assignment.worksheet_id).all()
            answers = db.query(TestAnswer).filter(TestAnswer.session_id == session.session_id).all()

            problem_map = {p.id: p for p in problems}
            answer_map = {str(ans.problem_id): ans.answer for ans in answers}

            correct_count = 0
            points_per_problem = 10 if len(problems) == 10 else 5 if len(problems) == 20 else 100 / len(problems)

            if existing_grading:
                # 기존 채점 세션이 있으면 업데이트 (손글씨 답안만)
                # 기존 문제별 결과 중 손글씨였던 것만 삭제하고 다시 생성
                db.query(ProblemGradingResult).filter(
                    ProblemGradingResult.grading_session_id == existing_grading.id,
                    ProblemGradingResult.input_method.like('%ocr%')
                ).delete()

                # 모든 답안 다시 채점
                for problem in problems:
                    student_answer = answer_map.get(str(problem.id), '')
                    is_correct = student_answer == problem.correct_answer
                    if is_correct:
                        correct_count += 1

                    # 기존 결과가 있는지 확인
                    existing_result = db.query(ProblemGradingResult).filter(
                        ProblemGradingResult.grading_session_id == existing_grading.id,
                        ProblemGradingResult.problem_id == problem.id
                    ).first()

                    if not existing_result:
                        # 새로운 문제 결과 생성
                        input_method = "ai_grading_ocr" if student_answer.startswith('data:image/') else "multiple_choice"
                        problem_result = ProblemGradingResult(
                            grading_session_id=existing_grading.id,
                            problem_id=problem.id,
                            user_answer=student_answer,
                            correct_answer=problem.correct_answer,
                            is_correct=is_correct,
                            score=points_per_problem if is_correct else 0,
                            points_per_problem=points_per_problem,
                            problem_type=problem.problem_type,
                            difficulty=problem.difficulty,
                            input_method=input_method,
                            explanation=problem.explanation
                        )
                        db.add(problem_result)

                # 채점 세션 점수 업데이트
                existing_grading.correct_count = correct_count
                existing_grading.total_score = correct_count * points_per_problem
                existing_grading.graded_at = datetime.now(timezone.utc)
                updated_sessions.append(existing_grading.id)

            else:
                # 새로운 채점 세션 생성
                new_grading_session = GradingSession(
                    worksheet_id=assignment.worksheet_id,
                    celery_task_id=task_id,
                    total_problems=len(problems),
                    correct_count=0,  # 나중에 업데이트
                    total_score=0,    # 나중에 업데이트
                    max_possible_score=len(problems) * points_per_problem,
                    points_per_problem=points_per_problem,
                    input_method="ai_grading",
                    graded_at=datetime.now(timezone.utc),
                    graded_by=session.student_id  # 학생 ID로 구분
                )
                db.add(new_grading_session)
                db.flush()

                # 문제별 채점 결과 생성
                for problem in problems:
                    student_answer = answer_map.get(str(problem.id), '')
                    is_correct = student_answer == problem.correct_answer
                    if is_correct:
                        correct_count += 1

                    input_method = "ai_grading_ocr" if student_answer.startswith('data:image/') else "multiple_choice"
                    problem_result = ProblemGradingResult(
                        grading_session_id=new_grading_session.id,
                        problem_id=problem.id,
                        user_answer=student_answer,
                        correct_answer=problem.correct_answer,
                        is_correct=is_correct,
                        score=points_per_problem if is_correct else 0,
                        points_per_problem=points_per_problem,
                        problem_type=problem.problem_type,
                        difficulty=problem.difficulty,
                        input_method=input_method,
                        explanation=problem.explanation
                    )
                    db.add(problem_result)

                # 채점 세션 점수 업데이트
                new_grading_session.correct_count = correct_count
                new_grading_session.total_score = correct_count * points_per_problem
                newly_graded_sessions.append(new_grading_session.id)

        self.update_state(state='PROGRESS', meta={'current': 95, 'total': 100, 'status': '결과 저장 중...'})

        db.commit()

        return {
            "message": f"OCR + AI 채점 완료",
            "processed_count": processed_count,
            "updated_sessions": len(updated_sessions),
            "newly_graded_sessions": len(newly_graded_sessions),
            "assignment_id": assignment_id,
            "task_id": task_id
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_info = traceback.format_exc()
        print(f"❌ AI 채점 태스크 실패: {error_msg}")
        print(f"❌ 상세 오류: {traceback_info}")

        try:
            self.update_state(
                state='FAILURE',
                meta={
                    'error': error_msg,
                    'status': 'OCR + AI 채점 실패',
                    'assignment_id': assignment_id
                }
            )
        except Exception as update_error:
            print(f"❌ 상태 업데이트 실패: {str(update_error)}")

        raise GradingError(f"AI 채점 태스크 실패: {error_msg}")
    finally:
        db.close()