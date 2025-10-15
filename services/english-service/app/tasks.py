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
from .schemas.validation import QuestionValidationResult
from .services.generation.question_generator import PromptGenerator
from .services.regeneration.question_regenerator import QuestionRegenerator
from .services.validation.validator import QuestionValidator
from .services.validation.judge import QuestionJudge
from .core.validation_config import VALIDATION_SETTINGS

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

        # Gemini 모델 생성 (Pro 사용 - 문제 생성은 품질 중요)
        model = genai.GenerativeModel(settings.gemini_model)

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


def call_gemini_for_validation(prompt: str) -> QuestionValidationResult:
    """문제 검증을 위한 Gemini API 호출 (AI Judge)"""
    try:
        print(f"🔍 AI Judge 검증 시작...")

        # Gemini API 키 설정
        genai.configure(api_key=settings.gemini_api_key)

        # Gemini 모델 생성 (Pro 사용 - 검증도 정확성 중요)
        model = genai.GenerativeModel(settings.gemini_model)

        # API 호출 (response_schema 없이 프롬프트만 사용)
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json"
            }
        )

        # JSON 파싱 및 Pydantic 변환
        result_dict = json.loads(response.text)
        validation_result = QuestionValidationResult.model_validate(result_dict)

        # 검증 결과 전체 출력
        print("=" * 80)
        print(f"📊 AI Judge 검증 결과 상세")
        print("=" * 80)
        print(f"총점: {validation_result.total_score}/100")
        print(f"최종 판정: {validation_result.final_judgment}")
        print("-" * 80)

        # A. Alignment (정렬성) - 30점
        print(f"\n📌 A. Alignment (정렬성): {validation_result.alignment_total}/30")
        print(f"   • 교육과정 연관성: {validation_result.curriculum_relevance}/10")
        print(f"   • 난이도 일관성: {validation_result.difficulty_consistency}/10")
        print(f"   • 주제 적절성: {validation_result.topic_appropriateness}/10")
        print(f"   💬 평가: {validation_result.alignment_rationale}")

        # B. Content Quality (내용 품질) - 40점
        print(f"\n📌 B. Content Quality (내용 품질): {validation_result.content_quality_total}/40")
        print(f"   • 지문 품질: {validation_result.passage_quality}/10")
        print(f"   • 지시문 명확성: {validation_result.instruction_clarity}/10")
        print(f"   • 정답 정확성: {validation_result.answer_accuracy}/10")
        print(f"   • 오답 품질: {validation_result.distractor_quality}/10")
        print(f"   💬 평가: {validation_result.content_quality_rationale}")

        # C. Explanation Quality (해설 품질) - 30점
        print(f"\n📌 C. Explanation Quality (해설 품질): {validation_result.explanation_quality_total}/30")
        print(f"   • 논리적 설명: {validation_result.logical_explanation}/10")
        print(f"   • 오답 분석: {validation_result.incorrect_answer_analysis}/10")
        print(f"   • 추가 정보: {validation_result.additional_information}/10")
        print(f"   💬 평가: {validation_result.explanation_quality_rationale}")

        # 개선 제안
        if validation_result.suggestions_for_improvement:
            print(f"\n💡 개선 제안:")
            for i, suggestion in enumerate(validation_result.suggestions_for_improvement, 1):
                print(f"   {i}. {suggestion}")

        print("\n" + "=" * 80)

        return validation_result

    except Exception as e:
        print(f"❌ AI Judge 검증 실패: {str(e)}")
        raise Exception(f"AI Judge 검증 실패: {str(e)}")


def create_revision_prompt(original_question: Dict[str, Any], validation_result: QuestionValidationResult, metadata: Dict[str, Any]) -> str:
    """검증 결과를 바탕으로 문제 수정 프롬프트 생성"""

    # 검증 피드백 정리
    feedback_sections = []

    # A. Alignment 피드백
    if validation_result.alignment_total < 25:  # 30점 만점 중 25점 미만이면 문제 있음
        feedback_sections.append(f"\n**A. Alignment (정렬성) - {validation_result.alignment_total}/30:**")
        feedback_sections.append(f"  교육과정 연관성: {validation_result.curriculum_relevance}/10")
        feedback_sections.append(f"  난이도 일관성: {validation_result.difficulty_consistency}/10")
        feedback_sections.append(f"  주제 적절성: {validation_result.topic_appropriateness}/10")
        feedback_sections.append(f"  평가: {validation_result.alignment_rationale}")

    # B. Content Quality 피드백
    if validation_result.content_quality_total < 32:  # 40점 만점 중 32점 미만이면 문제 있음
        feedback_sections.append(f"\n**B. Content Quality (내용 품질) - {validation_result.content_quality_total}/40:**")
        feedback_sections.append(f"  지문 품질: {validation_result.passage_quality}/10")
        feedback_sections.append(f"  지시문 명확성: {validation_result.instruction_clarity}/10")
        feedback_sections.append(f"  정답 정확성: {validation_result.answer_accuracy}/10")
        feedback_sections.append(f"  오답 품질: {validation_result.distractor_quality}/10")
        feedback_sections.append(f"  평가: {validation_result.content_quality_rationale}")

    # C. Explanation Quality 피드백
    if validation_result.explanation_quality_total < 24:  # 30점 만점 중 24점 미만이면 문제 있음
        feedback_sections.append(f"\n**C. Explanation Quality (해설 품질) - {validation_result.explanation_quality_total}/30:**")
        feedback_sections.append(f"  논리적 설명: {validation_result.logical_explanation}/10")
        feedback_sections.append(f"  오답 분석: {validation_result.incorrect_answer_analysis}/10")
        feedback_sections.append(f"  추가 정보: {validation_result.additional_information}/10")
        feedback_sections.append(f"  평가: {validation_result.explanation_quality_rationale}")

    # 개선 제안
    if validation_result.suggestions_for_improvement:
        feedback_sections.append(f"\n**개선 제안:**")
        for suggestion in validation_result.suggestions_for_improvement:
            feedback_sections.append(f"- {suggestion}")

    feedback_text = "\n".join(feedback_sections) if feedback_sections else "일반적인 품질 개선 필요"

    # 문제 유형에 따라 다른 프롬프트 생성
    needs_passage = 'passage' in original_question

    if needs_passage:
        # 독해 문제 수정 프롬프트
        prompt = f"""You are a Korean English education expert. You need to REVISE an existing reading comprehension question based on validation feedback.

# Original Question and Passage (JSON format):
```json
{json.dumps(original_question, ensure_ascii=False, indent=2)}
```

# Validation Score: {validation_result.total_score}/100
# Judgment: {validation_result.final_judgment}

# Issues Found:
{feedback_text}

# Required Metadata:
- School Level: {metadata.get('school_level', '중학교')}
- Grade: {metadata.get('grade', 1)}
- CEFR Level: {metadata.get('cefr_level', 'B1')}
- Difficulty: {metadata.get('difficulty', '중')}
- Subject: {metadata.get('subject', '독해')}
- Format: {metadata.get('format_type', '객관식')}

# Your Task:
REVISE the question and passage to fix the issues mentioned above. DO NOT create a completely new question - instead, IMPROVE the existing one by:

1. Adjusting vocabulary and sentence complexity to match the grade level
2. Fixing any format or structural errors
3. Improving clarity and quality while maintaining the original topic/theme
4. Ensuring the difficulty matches the required level
5. Correcting any language errors

# IMPORTANT:
- Keep the same general topic and theme
- Maintain the original question type (주제 파악, 세부 정보 등)
- Preserve the passage type (article, dialogue, etc.)
- Only modify what needs to be fixed based on the feedback
- Return the COMPLETE revised question in the EXACT SAME JSON format as the original

# Response Format (JSON):
Return the complete revised question with both passage and question in the same JSON structure as the original.
```json
{{
    "passage": {{...}},
    "question": {{...}}
}}
```

Return ONLY the JSON, no other text."""

    else:
        # 문법/어휘 문제 수정 프롬프트
        prompt = f"""You are a Korean English education expert. You need to REVISE an existing {metadata.get('subject', '문법')} question based on validation feedback.

# Original Question (JSON format):
```json
{json.dumps(original_question, ensure_ascii=False, indent=2)}
```

# Validation Score: {validation_result.total_score}/100
# Judgment: {validation_result.final_judgment}

# Issues Found:
{feedback_text}

# Required Metadata:
- School Level: {metadata.get('school_level', '중학교')}
- Grade: {metadata.get('grade', 1)}
- CEFR Level: {metadata.get('cefr_level', 'B1')}
- Difficulty: {metadata.get('difficulty', '중')}
- Subject: {metadata.get('subject', '문법')}
- Format: {metadata.get('format_type', '객관식')}

# Your Task:
REVISE the question to fix the issues mentioned above. DO NOT create a completely new question - instead, IMPROVE the existing one by:

1. Adjusting vocabulary and sentence complexity to match the grade level
2. Fixing any format or structural errors
3. Improving clarity and quality while maintaining the original grammar/vocabulary point
4. Ensuring the difficulty matches the required level
5. Correcting any language errors

# IMPORTANT:
- Keep the same grammar/vocabulary concept being tested
- Maintain the original question type
- Only modify what needs to be fixed based on the feedback
- Return the COMPLETE revised question in the EXACT SAME JSON format as the original

# Response Format (JSON):
Return the complete revised question in the same JSON structure as the original.
```json
{{
    "question_id": ...,
    "question_type": "...",
    ...
}}
```

Return ONLY the JSON, no other text."""

    return prompt


def generate_questions_parallel(question_prompts: List[Dict[str, Any]], enable_validation: bool = False) -> Dict[str, Any]:
    """
    문제들을 병렬로 생성 (독해는 지문 포함)

    Args:
        question_prompts: 문제 프롬프트 리스트
        enable_validation: AI Judge 검증 활성화 여부
    """

    print(f"🚀 문제 병렬 생성 시작 ({len(question_prompts)}개)...")
    if enable_validation:
        print(f"✅ AI Judge 검증 활성화됨 (최대 {VALIDATION_SETTINGS['max_retries']}회 재시도)")

    results = []
    validation_results = []

    def generate_with_validation(prompt_info: Dict[str, Any]) -> tuple:
        """단일 문제 생성 + 검증 (검증 실패 시 수정)"""
        question_id = prompt_info['question_id']
        metadata = prompt_info.get('metadata', {})

        if not enable_validation:
            # 검증 없이 바로 생성
            question_data = call_gemini_for_question(prompt_info)
            return question_data, None

        # 검증 포함 생성
        validator = QuestionValidator(
            max_retries=VALIDATION_SETTINGS['max_retries']
        )
        judge = QuestionJudge()

        best_question = None
        best_validation = None
        best_score = -1
        current_question = None

        for attempt in range(1, VALIDATION_SETTINGS['max_retries'] + 1):
            try:
                # 첫 시도: 새로 생성
                if attempt == 1:
                    print(f"📝 문제 {question_id}: 초기 생성 (attempt {attempt})")
                    question_data = call_gemini_for_question(prompt_info)
                else:
                    # 2회 이상: 기존 문제 + 검증 피드백으로 수정
                    print(f"🔧 문제 {question_id}: 검증 피드백 기반 수정 (attempt {attempt})")
                    revision_prompt_info = prompt_info.copy()
                    revision_prompt_info['prompt'] = create_revision_prompt(
                        current_question,
                        best_validation,
                        metadata
                    )
                    question_data = call_gemini_for_question(revision_prompt_info)

                # 현재 문제 저장
                current_question = question_data

                # 검증 프롬프트 생성
                judge_prompt = judge.create_judge_prompt(question_data, metadata)

                # AI Judge 검증
                validation_result = call_gemini_for_validation(judge_prompt)

                # 최고 점수 추적
                if validation_result.total_score > best_score:
                    best_score = validation_result.total_score
                    best_question = question_data
                    best_validation = validation_result

                # Pass 판정이면 바로 사용
                if validation_result.final_judgment == "Pass":
                    print(f"✅ 문제 {question_id}: Pass 판정 (attempt {attempt}, score {validation_result.total_score}/100)")
                    return question_data, validation_result

                # 재시도 필요
                print(f"⚠️ 문제 {question_id}: {validation_result.final_judgment} (attempt {attempt}, score {validation_result.total_score}/100)")
                if attempt < VALIDATION_SETTINGS['max_retries']:
                    print(f"   → 다음 시도에서 검증 피드백 기반으로 수정합니다...")

            except Exception as e:
                print(f"❌ 문제 {question_id} 검증 중 오류 (attempt {attempt}): {str(e)}")
                if attempt >= VALIDATION_SETTINGS['max_retries']:
                    # 최대 시도 도달 - 최고 점수 문제 사용
                    if best_question:
                        print(f"⚠️ 문제 {question_id}: 최고 점수 버전 사용 (score {best_score}/100)")
                        return best_question, best_validation
                    raise

        # 최대 시도 후 최고 점수 문제 사용
        print(f"⚠️ 문제 {question_id}: 최대 재시도 도달. 최고 점수 버전 사용 (score {best_score}/100)")
        return best_question, best_validation

    # ThreadPoolExecutor로 병렬 처리
    with ThreadPoolExecutor(max_workers=len(question_prompts)) as executor:
        future_to_prompt = {
            executor.submit(generate_with_validation, prompt): prompt
            for prompt in question_prompts
        }

        # 완료되는 순서대로 결과 수집
        for future in as_completed(future_to_prompt):
            try:
                question_data, validation_result = future.result()
                results.append(question_data)
                if validation_result:
                    validation_results.append(validation_result)
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

    # 검증 결과 요약
    if enable_validation and validation_results:
        pass_count = sum(1 for v in validation_results if v.final_judgment == "Pass")
        avg_score = sum(v.total_score for v in validation_results) / len(validation_results)
        print(f"📊 검증 결과 요약: Pass {pass_count}/{len(validation_results)}, 평균 점수 {avg_score:.1f}/100")

    print(f"✅ 모든 문제 생성 완료! (지문 {len(passages)}개, 문제 {len(questions)}개)")
    return {
        'passages': passages,
        'questions': questions,
        'validation_results': validation_results if enable_validation else None
    }


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

        worksheet_id = None
        teacher_id = request_data.get('teacher_id')

        # teacher_id가 있으면 DB에 자동 저장
        if teacher_id:
            try:
                from app.models.worksheet import Worksheet, Passage, Question

                print(f"💾 DB 자동 저장 시작 (teacher_id: {teacher_id})...")

                # 문제지 제목 생성 (없으면 자동 생성)
                worksheet_name = request_data.get('worksheet_name')
                if not worksheet_name:
                    worksheet_name = f"{request.school_level} {request.grade}학년 영어 문제지"

                # 1. Worksheet 저장
                db_worksheet = Worksheet(
                    teacher_id=teacher_id,
                    worksheet_name=worksheet_name,
                    school_level=request.school_level,
                    grade=str(request.grade),
                    subject="영어",
                    problem_type=parsed_llm_response.get('problem_type', '혼합형'),
                    total_questions=request.total_questions,
                    duration=request_data.get('duration', 60),
                    created_at=datetime.now()
                )
                db.add(db_worksheet)
                db.flush()
                worksheet_id = db_worksheet.worksheet_id

                print(f"  ✅ Worksheet 저장 완료 (ID: {worksheet_id})")

                # 2. Passages 저장
                for passage_data in passages:
                    db_passage = Passage(
                        worksheet_id=worksheet_id,
                        passage_id=passage_data['passage_id'],
                        passage_type=passage_data['passage_type'],
                        passage_content=passage_data['passage_content'],
                        original_content=passage_data.get('original_content'),
                        korean_translation=passage_data.get('korean_translation'),
                        related_questions=passage_data.get('related_questions', []),
                        created_at=datetime.now()
                    )
                    db.add(db_passage)

                print(f"  ✅ Passages 저장 완료 ({len(passages)}개)")

                # 3. Questions 저장
                for question_data in questions:
                    db_question = Question(
                        worksheet_id=worksheet_id,
                        question_id=question_data['question_id'],
                        question_text=question_data['question_text'],
                        question_type=question_data['question_type'],
                        question_subject=question_data['question_subject'],
                        question_difficulty=question_data['question_difficulty'],
                        question_detail_type=question_data.get('question_detail_type'),
                        question_choices=question_data.get('question_choices'),
                        passage_id=question_data.get('question_passage_id'),
                        correct_answer=str(question_data.get('correct_answer')) if question_data.get('correct_answer') else None,
                        example_content=question_data.get('example_content') or '',
                        example_original_content=question_data.get('example_original_content'),
                        example_korean_translation=question_data.get('example_korean_translation'),
                        explanation=question_data.get('explanation'),
                        learning_point=question_data.get('learning_point'),
                        created_at=datetime.now()
                    )
                    db.add(db_question)

                print(f"  ✅ Questions 저장 완료 ({len(questions)}개)")

                # 커밋
                db.commit()
                print(f"✅ DB 자동 저장 완료! worksheet_id: {worksheet_id}")

                # parsed_llm_response의 worksheet_id 업데이트
                if parsed_llm_response:
                    parsed_llm_response['worksheet_id'] = worksheet_id
                    print(f"  ✅ worksheet_id 업데이트 완료: {worksheet_id}")

                # 문제 생성 완료 알림 전송
                from app.utils.notification_helper import safe_send_notification, send_problem_generation_notification
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

            except Exception as save_error:
                db.rollback()
                print(f"⚠️ DB 자동 저장 실패: {save_error}")
                import traceback
                traceback.print_exc()
                # 저장 실패해도 생성 결과는 반환
        else:
            print("⚠️ teacher_id가 없어 DB 저장을 건너뜁니다.")

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
        if 'worksheet_id' in locals() and worksheet_id and 'teacher_id' in locals() and teacher_id:
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
                    from app.database import SessionLocal
                    from app.models.worksheet import Worksheet

                    db = SessionLocal()
                    first_question = regenerated_questions[0]
                    question_id = first_question.question_id if hasattr(first_question, 'question_id') else first_question.get('question_id')

                    # DB에서 question으로 worksheet 조회 (worksheet_id와 title만 필요)
                    from app.models.worksheet import Question as DBQuestion
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
                from app.database import SessionLocal
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