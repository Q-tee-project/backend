from typing import Dict, Any
from fastapi import Depends, HTTPException, status, Request

async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    미들웨어에서 검증하고 request.state에 저장한 사용자 정보를 반환합니다.
    (네트워크 호출을 다시 하지 않음)
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials from middleware",
        )
    return request.state.user


def verify_teacher_permission(current_user: Dict[str, Any]) -> Dict[str, Any]:
    """선생님 권한 확인"""
    if current_user.get("user_type") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="선생님만 접근할 수 있습니다."
        )
    return current_user


async def get_current_teacher(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """현재 로그인한 선생님 정보 가져오기"""
    return verify_teacher_permission(current_user)


async def get_current_student(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """현재 로그인한 학생 정보 가져오기"""
    if current_user.get("user_type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="학생만 접근할 수 있습니다."
        )
    return current_user
