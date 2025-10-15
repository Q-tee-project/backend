"""
문제 생성 Celery 태스크
"""
import json
from celery import current_task

from app.celery_app import celery_app
from app.database import SessionLocal
from app.core.config import get_settings
from app.schemas.generation import WorksheetGenerationRequest
from app.services.generation.question_generator import PromptGenerator
from app.core.validation_config import VALIDATION_SETTINGS
from .helpers.validation_helper import generate_questions_parallel
from .helpers.db_helper import assemble_worksheet, save_worksheet_to_db

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

settings = get_settings()


def get_session():
    """데이터베이스 세션 생성"""
    return SessionLocal()


@celery_app.task(bind=True, name="app.tasks.generate_english_worksheet_task")
def generate_english_worksheet_task(self, request_data: dict):
    """영어 워크시트 생성 비동기 태스크"""

    task_id = self.request.id
    print(f"🚀 English worksheet generation task started: {task_id}")

    try:
        # 요청 데이터 검증
        request = WorksheetGenerationRequest.model_validate(request_data)

        # 진행 상황 업데이트 - 시작 (10%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '문제 생성 옵션 처리 중...'}
        )

        print("🎯 문제 생성 옵션 처리:")
        print(f" 학교급: {request.school_level}")
        print(f" 학년: {request.grade}학년")
        print(f" 총 문제 수: {request.total_questions}개")
        print(f" 선택된 영역: {', '.join(request.subjects)}")

        # 데이터베이스 세션 생성
        db = get_session()

        # 진행 상황 업데이트 - 프롬프트 생성 (30%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': '프롬프트 생성 중...'}
        )

        # 프롬프트 생성기 초기화 및 실행
        print("🎯 프롬프트 생성 시작...")
        generator = PromptGenerator()

        # 요청 데이터를 딕셔너리로 변환
        request_dict = request.model_dump()

        # 분배 요약 생성
        distribution_summary = generator.get_distribution_summary(request_dict)

        print("📊 분배 결과:")
        print(f"  총 문제 수: {distribution_summary['total_questions']}")
        print("  영역별 분배:")
        for item in distribution_summary['subject_distribution']:
            print(f"    {item['subject']}: {item['count']}문제 ({item['ratio']}%)")

        # === 1단계: 문제 프롬프트 생성 (독해는 지문 생성 포함) ===
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': '문제 프롬프트 생성 중...'}
        )

        try:
            print("🔍 1단계: 문제 프롬프트 생성 시도 중 (독해는 지문 포함)...")
            question_prompts = generator.generate_question_prompts(request_dict, passages=None, db=db)
            print(f"✅ 문제 프롬프트 생성 성공! ({len(question_prompts)}개)")
        except Exception as prompt_error:
            print(f"❌ 문제 프롬프트 생성 오류: {prompt_error}")
            db.close()
            raise Exception(f"문제 프롬프트 생성 실패: {str(prompt_error)}")

        # === 2단계: 문제 병렬 생성 (독해는 지문 포함) ===
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 60, 'total': 100, 'status': '문제 및 지문 병렬 생성 중...'}
        )

        passages = []
        questions = []
        llm_error = None

        if GEMINI_AVAILABLE:
            try:
                # Gemini API 키 확인
                if not settings.gemini_api_key:
                    raise Exception("GEMINI_API_KEY가 설정되지 않았습니다.")

                # AI Judge 검증 활성화 여부 (기본값: 설정 파일 참조)
                enable_validation = request_data.get('enable_validation', VALIDATION_SETTINGS['enable_by_default'])

                # 문제 병렬 생성 (독해는 지문 포함, 검증 옵션)
                result = generate_questions_parallel(question_prompts, enable_validation=enable_validation)
                passages = result['passages']
                questions = result['questions']

            except Exception as api_error:
                print(f"❌ 문제 생성 오류: {api_error}")
                llm_error = str(api_error)
                db.close()
                raise Exception(f"문제 생성 실패: {str(api_error)}")
        else:
            llm_error = "Gemini 라이브러리가 설치되지 않았습니다."
            db.close()
            raise Exception(llm_error)

        # === 3단계: 워크시트 조립 ===
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': '워크시트 조립 중...'}
        )

        llm_response = None
        parsed_llm_response = None

        try:
            # 워크시트 조립 (worksheet_id는 나중에 DB 저장 후 업데이트)
            llm_response = assemble_worksheet(passages, questions, request_dict)

            # JSON 파싱
            parsed_llm_response = json.loads(llm_response)
            print("✅ 워크시트 조립 및 파싱 완료!")

        except Exception as e:
            print(f"❌ 워크시트 조립 오류: {e}")
            db.close()
            raise Exception(f"워크시트 조립 실패: {str(e)}")

        # === 4단계: DB 자동 저장 ===
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 95, 'total': 100, 'status': 'DB에 저장 중...'}
        )

        worksheet_id = save_worksheet_to_db(db, passages, questions, request_data, parsed_llm_response)

        # parsed_llm_response의 worksheet_id 업데이트
        if worksheet_id and parsed_llm_response:
            parsed_llm_response['worksheet_id'] = worksheet_id
            print(f"  ✅ worksheet_id 업데이트 완료: {worksheet_id}")

        # 문제 생성 완료 알림 전송
        teacher_id = request_data.get('teacher_id')
        if worksheet_id and teacher_id:
            from app.utils.notification_helper import safe_send_notification, send_problem_generation_notification
            worksheet_name = request_data.get('worksheet_name') or f"{request.school_level} {request.grade}학년 영어 문제지"
            safe_send_notification(
                send_problem_generation_notification,
                teacher_id=teacher_id,
                task_id=task_id,
                subject="english",
                worksheet_id=worksheet_id,
                worksheet_title=worksheet_name,
                problem_count=len(questions),
                success=True
            )

        # 진행 상황 업데이트 - 완료 (100%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': '완료!'}
        )

        # 백엔드에서 결과 출력
        print("=" * 80)
        print("🎉 문제지 및 답안지 생성 완료!")
        print("=" * 80)
        if parsed_llm_response:
            print(f"📄 문제지 ID: {worksheet_id if worksheet_id else 'N/A (저장 안 됨)'}")
            print(f"📝 문제지 제목: {parsed_llm_response.get('worksheet_name', 'N/A')}")
            print(f"📊 총 문제 수: {parsed_llm_response.get('total_questions', 'N/A')}개")
            print(f"🔍 문제 유형: {parsed_llm_response.get('problem_type', 'N/A')}")
        print("=" * 80)

        db.close()

        # DB 저장된 worksheet_id 포함하여 반환
        return {
            "message": "문제지와 답안지 생성이 완료되었습니다!",
            "status": "success",
            "worksheet_id": worksheet_id,  # DB에 저장된 ID (없으면 None)
            "llm_response": parsed_llm_response,  # 생성된 JSON을 프론트엔드로 전달
            "llm_error": llm_error,
        }

    except Exception as e:
        print(f"❌ 영어 워크시트 생성 실패: {str(e)}")

        # 문제 생성 실패 알림 전송
        teacher_id = request_data.get('teacher_id')
        if 'worksheet_id' in locals() and worksheet_id and teacher_id:
            from app.utils.notification_helper import safe_send_notification, send_problem_generation_notification
            safe_send_notification(
                send_problem_generation_notification,
                teacher_id=teacher_id,
                task_id=task_id,
                subject="english",
                worksheet_id=worksheet_id,
                worksheet_title=request_data.get('worksheet_name', '영어 문제지'),
                problem_count=0,
                success=False,
                error_message=str(e)
            )

        # 태스크 실패 상태 업데이트
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': '문제 생성 실패'}
        )

        raise Exception(f"영어 워크시트 생성 중 오류: {str(e)}")