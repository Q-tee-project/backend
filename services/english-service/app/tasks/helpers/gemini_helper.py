"""
Gemini API 호출 관련 헬퍼 함수들
"""
import json
from typing import Dict, Any

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from app.core.config import get_settings
from app.schemas.validation import QuestionValidationResult

settings = get_settings()


def call_gemini_for_question(prompt_info: Dict[str, Any]) -> Dict[str, Any]:
    """문제 생성을 위한 Gemini API 호출 (독해는 지문 포함)"""
    try:
        question_id = prompt_info['question_id']
        needs_passage = prompt_info.get('needs_passage', False)
        prompt = prompt_info['prompt']

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

        # 생성 완료 로그
        passage_text = "+지문" if needs_passage else ""
        print(f"✅ 문제 {question_id}{passage_text} 생성 완료")

        return result

    except Exception as e:
        print(f"❌ 문제 {prompt_info['question_id']} 생성 실패: {str(e)}")
        raise Exception(f"문제 {prompt_info['question_id']} 생성 실패: {str(e)}")


def call_gemini_for_validation(prompt: str) -> QuestionValidationResult:
    """문제 검증을 위한 Gemini API 호출 (AI Judge)"""
    try:
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

        # 검증 결과 간략 출력
        print(f"✅ 검증 완료: {validation_result.final_judgment} ({validation_result.total_score}/100점) - A:{validation_result.alignment_total}/30 B:{validation_result.content_quality_total}/40 C:{validation_result.explanation_quality_total}/30")

        return validation_result

    except Exception as e:
        print(f"❌ AI Judge 검증 실패: {str(e)}")
        raise Exception(f"AI Judge 검증 실패: {str(e)}")
