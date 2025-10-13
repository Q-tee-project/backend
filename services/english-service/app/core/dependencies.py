"""
FastAPI 의존성 함수들
미들웨어에서 검증된 사용자 정보를 가져옵니다.
"""

from fastapi import Request, HTTPException, status
from typing import Dict, Any


def get_current_user_from_state(request: Request) -> Dict[str, Any]:
    """
    미들웨어에서 검증 후 request.state에 저장된 사용자 정보 가져오기

    사용 예시:
        @router.post("/example")
        async def example(current_user: dict = Depends(get_current_user_from_state)):
            user_id = current_user["user_id"]
            user_type = current_user["user_type"]
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user


def get_current_teacher(request: Request) -> Dict[str, Any]:
    """선생님 권한 확인"""
    user = get_current_user_from_state(request)
    if user.get("user_type") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="선생님만 접근할 수 있습니다."
        )
    return user


def get_current_student(request: Request) -> Dict[str, Any]:
    """학생 권한 확인"""
    user = get_current_user_from_state(request)
    if user.get("user_type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="학생만 접근할 수 있습니다."
        )
    return user
