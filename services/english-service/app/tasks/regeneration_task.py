"""
문제 재생성 Celery 태스크
"""
from celery import current_task

from app.celery_app import celery_app
from app.database import SessionLocal
from app.schemas.regeneration import RegenerateEnglishQuestionRequest
from app.services.regeneration.question_regenerator import QuestionRegenerator


@celery_app.task(bind=True, name="app.tasks.regenerate_english_question_task")
def regenerate_english_question_task(self, request_data: dict):
    """영어 문제 재생성 비동기 태스크"""

    task_id = self.request.id
    print(f"🔄 English question regeneration task started: {task_id}")

    # teacher_id 추출 (토큰에서 전달받음)
    teacher_id = request_data.get('teacher_id')

    try:
        # 요청 데이터 검증
        request = RegenerateEnglishQuestionRequest.model_validate(request_data)

        # 진행 상황 업데이트 - 시작 (10%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '재생성 옵션 처리 중...'}
        )

        print("🔄 문제 재생성 옵션 처리:")
        print(f" 대상 문제 수: {len(request.questions)}개")
        print(f" 지문 재생성: {'있음' if request.passage else '없음'}")
        print(f" 사용자 피드백: {request.formData.feedback}")

        # 진행 상황 업데이트 - 재생성 시작 (30%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': '문제 재생성 중...'}
        )

        # 문제 재생성기 초기화 및 실행
        print("🎯 문제 재생성 시작...")
        regenerator = QuestionRegenerator()

        # 진행 상황 업데이트 - AI 처리 (60%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 60, 'total': 100, 'status': 'AI 재생성 처리 중...'}
        )

        # 재생성 실행
        success, message, regenerated_questions, regenerated_passage = regenerator.regenerate_from_data(
            questions=request.questions,
            passage=request.passage,
            form_data=request.formData
        )

        # 진행 상황 업데이트 - 결과 처리 (80%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': '재생성 결과 처리 중...'}
        )

        if success:
            # 진행 상황 업데이트 - 완료 (100%)
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': '재생성 완료!'}
            )

            # 백엔드에서 결과 출력
            print("=" * 80)
            print("🎉 문제 재생성 완료!")
            print("=" * 80)
            print(f"📝 재생성된 문제 수: {len(regenerated_questions) if regenerated_questions else 0}개")
            print(f"📄 재생성된 지문: {'있음' if regenerated_passage else '없음'}")
            print("=" * 80)

            # 문제 재생성 완료 알림 전송
            if regenerated_questions and len(regenerated_questions) > 0 and teacher_id:
                try:
                    from app.models.worksheet import Worksheet, Question as DBQuestion

                    db = SessionLocal()
                    first_question = regenerated_questions[0]
                    question_id = first_question.question_id if hasattr(first_question, 'question_id') else first_question.get('question_id')

                    # DB에서 question으로 worksheet 조회 (worksheet_id와 title만 필요)
                    db_question = db.query(DBQuestion).filter(DBQuestion.question_id == question_id).first()

                    if db_question and db_question.worksheet_id:
                        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == db_question.worksheet_id).first()

                        if worksheet:
                            from app.utils.notification_helper import safe_send_notification, send_problem_regeneration_notification

                            # 재생성된 문제 ID 목록
                            problem_indices = [
                                q.question_id if hasattr(q, 'question_id') else q.get('question_id')
                                for q in regenerated_questions
                            ]

                            safe_send_notification(
                                send_problem_regeneration_notification,
                                teacher_id=teacher_id,  # 토큰에서 전달받은 teacher_id 사용
                                task_id=task_id,
                                subject="english",
                                worksheet_id=worksheet.worksheet_id,
                                worksheet_title=worksheet.worksheet_name,
                                problem_indices=problem_indices,
                                success=True
                            )

                    db.close()
                except Exception as notif_error:
                    print(f"⚠️ 재생성 알림 전송 중 오류 (무시): {notif_error}")

            # Pydantic 객체를 딕셔너리로 변환
            serialized_questions = None
            if regenerated_questions:
                serialized_questions = [q.model_dump() if hasattr(q, 'model_dump') else q for q in regenerated_questions]

            serialized_passage = None
            if regenerated_passage:
                serialized_passage = regenerated_passage.model_dump() if hasattr(regenerated_passage, 'model_dump') else regenerated_passage

            return {
                "status": "success",
                "message": message,
                "regenerated_questions": serialized_questions,
                "regenerated_passage": serialized_passage
            }
        else:
            # 재생성 실패
            current_task.update_state(
                state='FAILURE',
                meta={'error': message, 'status': '재생성 실패'}
            )
            raise Exception(message)

    except Exception as e:
        print(f"❌ 영어 문제 재생성 실패: {str(e)}")

        # 문제 재생성 실패 알림 전송
        if 'request' in locals() and request.questions and len(request.questions) > 0 and teacher_id:
            try:
                from app.models.worksheet import Worksheet, Question as DBQuestion

                db = SessionLocal()
                first_question = request.questions[0]
                question_id = first_question.question_id if hasattr(first_question, 'question_id') else first_question.get('question_id')

                # DB에서 question으로 worksheet 조회 (worksheet_id와 title만 필요)
                db_question = db.query(DBQuestion).filter(DBQuestion.question_id == question_id).first()

                if db_question and db_question.worksheet_id:
                    worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == db_question.worksheet_id).first()

                    if worksheet:
                        from app.utils.notification_helper import safe_send_notification, send_problem_regeneration_notification

                        # 재생성 시도한 문제 ID 목록
                        problem_indices = [
                            q.question_id if hasattr(q, 'question_id') else q.get('question_id')
                            for q in request.questions
                        ]

                        safe_send_notification(
                            send_problem_regeneration_notification,
                            teacher_id=teacher_id,  # 토큰에서 전달받은 teacher_id 사용
                            task_id=task_id,
                            subject="english",
                            worksheet_id=worksheet.worksheet_id,
                            worksheet_title=worksheet.worksheet_name,
                            problem_indices=problem_indices,
                            success=False,
                            error_message=str(e)
                        )

                db.close()
            except Exception as notif_error:
                print(f"⚠️ 재생성 실패 알림 전송 중 오류 (무시): {notif_error}")

        # 태스크 실패 상태 업데이트
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': '문제 재생성 실패'}
        )

        raise Exception(f"영어 문제 재생성 중 오류: {str(e)}")