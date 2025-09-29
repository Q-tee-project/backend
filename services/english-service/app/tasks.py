from celery import current_task
from sqlalchemy.orm import Session
import json
from datetime import datetime
from typing import Dict, Any

from .celery_app import celery_app
from .database import SessionLocal
from .core.config import get_settings
from .schemas.generation import WorksheetGenerationRequest
from .schemas.regeneration import RegenerateEnglishQuestionRequest
from .services.generation.question_generator import PromptGenerator
from .services.regeneration.question_regenerator import QuestionRegenerator

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

        # 프롬프트 생성
        try:
            print("🔍 프롬프트 생성 시도 중...")
            prompt = generator.generate_prompt(request_dict, db=db)
            print("✅ 프롬프트 생성 성공!")
        except Exception as prompt_error:
            print(f"❌ 프롬프트 생성 오류: {prompt_error}")
            db.close()
            raise Exception(f"프롬프트 생성 실패: {str(prompt_error)}")

        # 진행 상황 업데이트 - AI 호출 (60%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 60, 'total': 100, 'status': 'AI 문제 생성 중...'}
        )

        # LLM에 프롬프트 전송 및 응답 받기
        llm_response = None
        llm_error = None

        if GEMINI_AVAILABLE:
            try:
                print("🤖 Gemini API 호출 시작...")

                # Gemini API 키 설정
                if not settings.gemini_api_key:
                    raise Exception("GEMINI_API_KEY가 설정되지 않았습니다.")

                genai.configure(api_key=settings.gemini_api_key)

                # Gemini 모델 생성
                model = genai.GenerativeModel(settings.gemini_model)

                # 통합 프롬프트로 API 한 번만 호출 (JSON 응답 요청)
                print("📝 통합 문제지/답안지 생성 중...")
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                llm_response = response.text
                print("✅ 통합 생성 완료!")

            except Exception as api_error:
                print(f"❌ Gemini API 호출 오류: {api_error}")
                llm_error = str(api_error)
                db.close()
                raise Exception(f"AI 문제 생성 실패: {str(api_error)}")
        else:
            llm_error = "Gemini 라이브러리가 설치되지 않았습니다."
            db.close()
            raise Exception(llm_error)

        # 진행 상황 업데이트 - JSON 파싱 (80%)
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'AI 응답 처리 중...'}
        )

        # JSON 파싱 처리
        parsed_llm_response = None

        if llm_response:
            try:
                # 통합 JSON 파싱
                parsed_llm_response = json.loads(llm_response)
                print("✅ 통합 JSON 파싱 완료!")
            except json.JSONDecodeError as e:
                print(f"⚠️ 통합 JSON 파싱 실패: {e}")
                db.close()
                raise Exception(f"AI 응답 파싱 실패: {str(e)}")

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
            print(f"📄 문제지 ID: {parsed_llm_response.get('worksheet_id', 'N/A')}")
            print(f"📝 문제지 제목: {parsed_llm_response.get('worksheet_name', 'N/A')}")
            print(f"📊 총 문제 수: {parsed_llm_response.get('total_questions', 'N/A')}개")
            print(f"🔍 문제 유형: {parsed_llm_response.get('problem_type', 'N/A')}")
        print("=" * 80)

        db.close()

        # 기존과 동일한 형태로 반환 (DB 저장하지 않음)
        return {
            "message": "문제지와 답안지 생성이 완료되었습니다!",
            "status": "success",
            "llm_response": parsed_llm_response,  # 생성된 JSON을 프론트엔드로 전달
            "llm_error": llm_error,
        }

    except Exception as e:
        print(f"❌ 영어 워크시트 생성 실패: {str(e)}")

        # 태스크 실패 상태 업데이트
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': '문제 생성 실패'}
        )

        raise Exception(f"영어 워크시트 생성 중 오류: {str(e)}")


@celery_app.task(bind=True, name="app.tasks.get_task_status")
def get_task_status(self, task_id: str):
    """태스크 상태 조회"""
    try:
        result = celery_app.AsyncResult(task_id)

        if result.state == 'PENDING':
            response = {
                'state': result.state,
                'status': '대기 중...'
            }
        elif result.state == 'PROGRESS':
            response = {
                'state': result.state,
                'current': result.info.get('current', 0),
                'total': result.info.get('total', 100),
                'status': result.info.get('status', '')
            }
        elif result.state == 'SUCCESS':
            response = {
                'state': result.state,
                'result': result.info
            }
        else:  # FAILURE
            response = {
                'state': result.state,
                'error': str(result.info)
            }

        return response

    except Exception as e:
        return {
            'state': 'FAILURE',
            'error': f'태스크 상태 조회 실패: {str(e)}'
        }


@celery_app.task(bind=True, name="app.tasks.regenerate_english_question_task")
def regenerate_english_question_task(self, request_data: dict):
    """영어 문제 재생성 비동기 태스크"""

    task_id = self.request.id
    print(f"🔄 English question regeneration task started: {task_id}")

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

        # 태스크 실패 상태 업데이트
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': '문제 재생성 실패'}
        )

        raise Exception(f"영어 문제 재생성 중 오류: {str(e)}")