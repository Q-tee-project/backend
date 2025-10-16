"""
문제 검증 및 재시도 로직 헬퍼 함수들
"""
import json
from typing import Dict, Any, Tuple, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.schemas.validation import QuestionValidationResult
from app.services.validation.validator import QuestionValidator
from app.services.validation.judge import QuestionJudge
from app.core.validation_config import VALIDATION_SETTINGS
from .gemini_helper import call_gemini_for_question, call_gemini_for_validation


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


def generate_with_validation(prompt_info: Dict[str, Any], enable_validation: bool = True) -> Tuple[Dict[str, Any], Optional[QuestionValidationResult]]:
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
                question_data = call_gemini_for_question(prompt_info)
            else:
                # 2회 이상: 기존 문제 + 검증 피드백으로 수정
                print(f"🔧 문제 {question_id}: 재시도 {attempt}")
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
                print(f"✅ 문제 {question_id}: Pass")
                return question_data, validation_result

            # 재시도 필요
            print(f"⚠️ 문제 {question_id}: {validation_result.final_judgment} - 재시도 예정")

        except Exception as e:
            print(f"❌ 문제 {question_id} 검증 오류: {str(e)}")
            if attempt >= VALIDATION_SETTINGS['max_retries']:
                # 최대 시도 도달 - 최고 점수 문제 사용
                if best_question:
                    print(f"⚠️ 문제 {question_id}: 최고 점수 버전 사용 ({best_score}점)")
                    return best_question, best_validation
                raise

    # 최대 시도 후 최고 점수 문제 사용
    print(f"⚠️ 문제 {question_id}: 최대 재시도 도달 - 최고 점수 버전 사용 ({best_score}점)")
    return best_question, best_validation


def generate_questions_parallel(question_prompts: List[Dict[str, Any]], enable_validation: bool = False) -> Dict[str, Any]:
    """
    문제들을 병렬로 생성 (독해는 지문 포함)

    Args:
        question_prompts: 문제 프롬프트 리스트
        enable_validation: AI Judge 검증 활성화 여부
    """

    print(f"🚀 문제 생성 시작 ({len(question_prompts)}개, 검증: {'ON' if enable_validation else 'OFF'})")

    results = []
    validation_results = []

    # ThreadPoolExecutor로 병렬 처리
    with ThreadPoolExecutor(max_workers=len(question_prompts)) as executor:
        future_to_prompt = {
            executor.submit(generate_with_validation, prompt, enable_validation): prompt
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
        print(f"📊 검증: Pass {pass_count}/{len(validation_results)} (평균 {avg_score:.1f}점)")

    print(f"✅ 생성 완료: 지문 {len(passages)}개, 문제 {len(questions)}개")
    return {
        'passages': passages,
        'questions': questions,
        'validation_results': validation_results if enable_validation else None
    }
