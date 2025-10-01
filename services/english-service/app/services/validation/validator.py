"""
문제 검증 로직
AI Judge를 사용하여 생성된 문제의 품질을 검증하고 필요시 재생성합니다.
"""

import logging
from typing import Dict, Any, Tuple, Callable, Awaitable
from datetime import datetime

from app.schemas.validation import QuestionValidationResult, ValidationMetrics
from app.services.validation.judge import QuestionJudge

logger = logging.getLogger(__name__)


class QuestionValidator:
    """문제 품질 검증 및 재생성 관리"""

    def __init__(
        self,
        max_retries: int = 3,
        pass_threshold: int = 85,
        fail_threshold: int = 60
    ):
        """
        Args:
            max_retries: 최대 재생성 시도 횟수
            pass_threshold: Pass 판정 기준 점수 (이상)
            fail_threshold: Fail 판정 기준 점수 (미만)
        """
        self.max_retries = max_retries
        self.pass_threshold = pass_threshold
        self.fail_threshold = fail_threshold
        self.judge = QuestionJudge()

    async def validate_and_regenerate(
        self,
        generate_fn: Callable[[], Awaitable[Dict[str, Any]]],
        validate_fn: Callable[[str], Awaitable[QuestionValidationResult]],
        metadata: Dict[str, Any],
        question_id: str
    ) -> Tuple[Dict[str, Any], QuestionValidationResult, ValidationMetrics]:
        """
        문제를 생성하고 검증하며, 필요시 재생성합니다.

        Args:
            generate_fn: 문제 생성 함수 (비동기)
            validate_fn: 검증 프롬프트를 Gemini에 전송하는 함수 (비동기)
            metadata: 문제 메타데이터 (학년, 난이도 등)
            question_id: 문제 ID

        Returns:
            (최종 생성된 문제, 검증 결과, 검증 메트릭)
        """

        question_data = None
        validation_result = None
        attempt = 0

        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Question {question_id} generation attempt {attempt}/{self.max_retries}")

            try:
                # 1. 문제 생성
                question_data = await generate_fn()

                # 2. 검증 프롬프트 생성
                judge_prompt = self.judge.create_judge_prompt(question_data, metadata)

                # 3. AI Judge로 검증
                validation_result = await validate_fn(judge_prompt)

                # 4. 검증 결과 로깅
                logger.info(
                    f"Question {question_id} validation result (attempt {attempt}): "
                    f"{validation_result.final_judgment} - Score: {validation_result.total_score}/100"
                )

                # 5. Pass 여부 확인
                if validation_result.final_judgment == "Pass":
                    logger.info(f"Question {question_id} passed validation on attempt {attempt}")
                    break
                elif validation_result.final_judgment == "Needs Revision":
                    logger.warning(
                        f"Question {question_id} needs revision (attempt {attempt}): "
                        f"Score {validation_result.total_score}/100. "
                        f"Suggestions: {validation_result.suggestions_for_improvement}"
                    )
                else:  # Fail
                    logger.warning(
                        f"Question {question_id} failed validation (attempt {attempt}): "
                        f"Score {validation_result.total_score}/100. "
                        f"Suggestions: {validation_result.suggestions_for_improvement}"
                    )

                # 6. 마지막 시도가 아니면 재생성
                if attempt < self.max_retries:
                    logger.info(f"Regenerating question {question_id}...")
                    continue
                else:
                    logger.warning(
                        f"Question {question_id} reached max retries. "
                        f"Using last generated version with score {validation_result.total_score}/100"
                    )

            except Exception as e:
                logger.error(f"Error during validation attempt {attempt} for question {question_id}: {e}", exc_info=True)
                if attempt >= self.max_retries:
                    raise
                continue

        # 7. 검증 메트릭 생성
        metrics = ValidationMetrics(
            question_id=question_id,
            attempt_number=attempt,
            validation_result=validation_result,
            regeneration_needed=(validation_result.final_judgment != "Pass"),
            timestamp=datetime.utcnow().isoformat()
        )

        return question_data, validation_result, metrics

    def should_regenerate(self, validation_result: QuestionValidationResult) -> bool:
        """재생성 필요 여부 판단"""
        return validation_result.final_judgment != "Pass"

    def get_quality_summary(self, validation_result: QuestionValidationResult) -> Dict[str, Any]:
        """검증 결과 요약 정보 추출"""
        return {
            "judgment": validation_result.final_judgment,
            "total_score": validation_result.total_score,
            "alignment_score": validation_result.alignment.total_score,
            "content_quality_score": validation_result.content_quality.total_score,
            "explanation_quality_score": validation_result.explanation_quality.total_score,
            "needs_improvement": len(validation_result.suggestions_for_improvement) > 0,
            "suggestions_count": len(validation_result.suggestions_for_improvement)
        }
