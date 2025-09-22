"""
문제 검증 API 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
import uuid
from datetime import datetime

from ..services.problem_validation_service import ProblemValidationService
from ..schemas.problem_validation import (
    ValidationRequestSchema,
    ValidationBatchResponseSchema,
    SingleProblemValidationRequestSchema,
    SingleProblemValidationResponseSchema,
    ValidationConfigSchema,
    TeacherReviewSchema,
    ValidationResultSchema
)

router = APIRouter(prefix="/validation", tags=["Problem Validation"])

# 서비스 인스턴스 (의존성 주입 대신 직접 생성)
validation_service = ProblemValidationService()

@router.post("/validate-single", response_model=SingleProblemValidationResponseSchema)
async def validate_single_problem(request: SingleProblemValidationRequestSchema):
    """
    단일 문제 검증

    - **problem**: 검증할 문제 (question, correct_answer, explanation 등 포함)
    - **config_name**: 사용할 검증 설정 (기본: "default")
    """
    try:
        validation_result = validation_service.validate_problem(request.problem)

        return SingleProblemValidationResponseSchema(
            validation_result=ValidationResultSchema(**validation_result),
            validated_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제 검증 중 오류 발생: {str(e)}")

@router.post("/validate-batch", response_model=ValidationBatchResponseSchema)
async def validate_problem_batch(request: ValidationRequestSchema):
    """
    여러 문제 일괄 검증

    - **problems**: 검증할 문제들의 배열
    - **config_name**: 사용할 검증 설정
    - **enable_auto_approval**: 자동 승인 활성화 여부
    """
    try:
        # 세션 ID 생성
        session_id = str(uuid.uuid4())

        # 일괄 검증 수행
        validation_results = validation_service.validate_problem_batch(request.problems)

        # 검증 요약 생성
        summary = validation_service.get_validation_summary(validation_results)

        return ValidationBatchResponseSchema(
            validation_results=[ValidationResultSchema(**result) for result in validation_results],
            summary=summary,
            session_id=session_id,
            created_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일괄 검증 중 오류 발생: {str(e)}")

@router.get("/summary/{session_id}")
async def get_validation_summary(session_id: str):
    """
    특정 세션의 검증 요약 조회

    - **session_id**: 검증 세션 ID
    """
    # TODO: 데이터베이스에서 세션 정보 조회
    # 현재는 임시 응답
    return {
        "session_id": session_id,
        "message": "검증 요약 조회 기능은 데이터베이스 연동 후 구현됩니다"
    }

@router.post("/teacher-review")
async def submit_teacher_review(review: TeacherReviewSchema):
    """
    교사 검토 의견 제출

    - **problem_id**: 검토할 문제 ID
    - **review_status**: 승인(approved) 또는 거부(rejected)
    - **comment**: 검토 의견 (선택사항)
    """
    try:
        # TODO: 데이터베이스에 교사 검토 결과 저장
        # 현재는 임시 응답

        return {
            "message": "교사 검토가 성공적으로 제출되었습니다",
            "problem_id": review.problem_id,
            "status": review.review_status,
            "reviewed_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"교사 검토 제출 중 오류 발생: {str(e)}")

@router.get("/pending-reviews")
async def get_pending_reviews():
    """
    검토 대기 중인 문제들 조회

    자동 승인되지 않아 교사의 수동 검토가 필요한 문제들을 반환
    """
    try:
        # TODO: 데이터베이스에서 manual_review_needed 상태인 문제들 조회
        # 현재는 임시 응답

        return {
            "pending_problems": [],
            "total_count": 0,
            "message": "검토 대기 문제 조회 기능은 데이터베이스 연동 후 구현됩니다"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검토 대기 문제 조회 중 오류 발생: {str(e)}")

@router.get("/statistics")
async def get_validation_statistics():
    """
    전체 검증 통계 조회

    - 전체 검증 통과율
    - 자동 승인율
    - 자주 발견되는 문제점들
    - 시간대별 검증 성능 등
    """
    try:
        # TODO: 데이터베이스에서 통계 데이터 조회 및 계산
        # 현재는 임시 응답

        return {
            "total_validations": 0,
            "overall_validity_rate": 0.0,
            "overall_auto_approval_rate": 0.0,
            "most_common_issues": {},
            "avg_validation_time_ms": 0.0,
            "message": "검증 통계 기능은 데이터베이스 연동 후 구현됩니다"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검증 통계 조회 중 오류 발생: {str(e)}")

@router.post("/config", response_model=Dict[str, str])
async def create_validation_config(config: ValidationConfigSchema):
    """
    새로운 검증 설정 생성

    - **config_name**: 설정 이름 (고유해야 함)
    - **min_confidence_score**: 자동 승인 최소 신뢰도
    - **validator_model**: 검증에 사용할 AI 모델
    - 기타 검증 관련 설정들
    """
    try:
        # TODO: 데이터베이스에 검증 설정 저장
        # 현재는 임시 응답

        return {
            "message": f"검증 설정 '{config.config_name}'이 성공적으로 생성되었습니다",
            "config_name": config.config_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검증 설정 생성 중 오류 발생: {str(e)}")

@router.get("/config/{config_name}")
async def get_validation_config(config_name: str):
    """
    특정 검증 설정 조회

    - **config_name**: 조회할 설정 이름
    """
    try:
        # TODO: 데이터베이스에서 검증 설정 조회
        # 현재는 기본 설정 반환

        default_config = {
            "config_name": config_name,
            "min_confidence_score": 0.8,
            "enable_latex_validation": True,
            "enable_difficulty_validation": True,
            "validator_model": "gemini-2.5-flash",
            "validator_temperature": 0.1,
            "validator_max_tokens": 2048,
            "is_active": True
        }

        return default_config

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검증 설정 조회 중 오류 발생: {str(e)}")

@router.get("/health")
async def validation_health_check():
    """
    검증 서비스 상태 확인

    검증 서비스의 정상 작동 여부와 AI 모델 연결 상태를 확인
    """
    try:
        # 간단한 테스트 문제로 검증 서비스 테스트
        test_problem = {
            "question": "2 + 2 = ?",
            "correct_answer": "4",
            "explanation": "2에 2를 더하면 4입니다.",
            "problem_type": "short_answer",
            "difficulty": "A"
        }

        # 검증 수행
        result = validation_service.validate_problem(test_problem)

        return {
            "status": "healthy",
            "service": "problem_validation",
            "ai_model": "gemini-2.5-flash",
            "test_validation_success": result.get("is_valid", False),
            "test_confidence": result.get("confidence_score", 0.0),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "problem_validation",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }