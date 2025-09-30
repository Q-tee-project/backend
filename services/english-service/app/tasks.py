from celery import current_task
from sqlalchemy.orm import Session
import json
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def call_gemini_for_question(prompt_info: Dict[str, Any]) -> Dict[str, Any]:
    """문제 생성을 위한 Gemini API 호출 (독해는 지문 포함)"""
    try:
        question_id = prompt_info['question_id']
        needs_passage = prompt_info.get('needs_passage', False)
        prompt = prompt_info['prompt']

        if needs_passage:
            print(f"📚❓ 독해 문제 {question_id} (지문 포함) 생성 시작...")
        else:
            print(f"❓ 문제 {question_id} 생성 시작...")

        # Gemini API 키 설정
        genai.configure(api_key=settings.gemini_api_key)

        # Gemini 모델 생성 (2.5 Flash 사용)
        model = genai.GenerativeModel(settings.gemini_flash_model)

        # API 호출
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        # JSON 파싱
        result = json.loads(response.text)

        if needs_passage:
            print(f"✅ 독해 문제 {question_id} (지문 포함) 생성 완료!")
        else:
            print(f"✅ 문제 {question_id} 생성 완료!")

        return result

    except Exception as e:
        print(f"❌ 문제 {prompt_info['question_id']} 생성 실패: {str(e)}")
        raise Exception(f"문제 {prompt_info['question_id']} 생성 실패: {str(e)}")


def generate_questions_parallel(question_prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """문제들을 병렬로 생성 (독해는 지문 포함)"""

    print(f"🚀 문제 병렬 생성 시작 ({len(question_prompts)}개)...")

    results = []

    # ThreadPoolExecutor로 병렬 처리
    with ThreadPoolExecutor(max_workers=len(question_prompts)) as executor:
        future_to_prompt = {
            executor.submit(call_gemini_for_question, prompt): prompt
            for prompt in question_prompts
        }

        # 완료되는 순서대로 결과 수집
        for future in as_completed(future_to_prompt):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                prompt_info = future_to_prompt[future]
                print(f"❌ 문제 {prompt_info['question_id']} 처리 실패: {str(e)}")
                raise

    # question_id 순서로 정렬
    results.sort(key=lambda x: x.get('question', x).get('question_id'))

    # 독해 문제(passage 포함)와 일반 문제 분리
    passages = []
    questions = []

    for result in results:
        if 'passage' in result:
            # 독해 문제: passage와 question 분리
            passages.append(result['passage'])
            questions.append(result['question'])
        else:
            # 문법/어휘 문제: question만
            questions.append(result)

    print(f"✅ 모든 문제 생성 완료! (지문 {len(passages)}개, 문제 {len(questions)}개)")
    return {'passages': passages, 'questions': questions}


def assemble_worksheet(passages: List[Dict[str, Any]], questions: List[Dict[str, Any]], request_data: Dict[str, Any]) -> str:
    """워크시트 최종 조립"""

    print(f"🔧 워크시트 조립 시작...")

    school_level = request_data.get('school_level', '중학교')
    grade = request_data.get('grade', 1)
    total_questions = len(questions)

    # 영역 분포 계산
    subjects = set(q['question_subject'] for q in questions)
    if len(subjects) == 1:
        problem_type = list(subjects)[0]
    else:
        problem_type = '혼합형'

    # related_questions 업데이트
    for passage in passages:
        passage['related_questions'] = [
            q['question_id'] for q in questions
            if q.get('question_passage_id') == passage['passage_id']
        ]

    worksheet = {
        "worksheet_id": 1,
        "worksheet_name": "",
        "worksheet_date": datetime.now().strftime("%Y-%m-%d"),
        "worksheet_time": datetime.now().strftime("%H:%M"),
        "worksheet_duration": "60",
        "worksheet_subject": "english",
        "worksheet_level": school_level,
        "worksheet_grade": grade,
        "problem_type": problem_type,
        "total_questions": total_questions,
        "passages": passages,
        "questions": questions
    }

    print(f"✅ 워크시트 조립 완료! (총 {total_questions}문제, {len(passages)}지문)")

    return json.dumps(worksheet, ensure_ascii=False)


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

                # 문제 병렬 생성 (독해는 지문 포함)
                result = generate_questions_parallel(question_prompts)
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
            # 워크시트 조립
            llm_response = assemble_worksheet(passages, questions, request_dict)

            # JSON 파싱
            parsed_llm_response = json.loads(llm_response)
            print("✅ 워크시트 조립 및 파싱 완료!")

        except Exception as e:
            print(f"❌ 워크시트 조립 오류: {e}")
            db.close()
            raise Exception(f"워크시트 조립 실패: {str(e)}")

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