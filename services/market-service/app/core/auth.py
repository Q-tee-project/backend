from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
import httpx

from .database import get_db
from ..services.external_service import ExternalService

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "qt_project_super_secret_key_for_jwt_tokens_change_in_production")
ALGORITHM = "HS256"

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """JWT 토큰에서 현재 사용자 정보를 추출"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        print(f"[DEBUG] Received token: {token[:50]}...")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"[DEBUG] JWT payload: {payload}")

        username: str = payload.get("sub")
        user_type: str = payload.get("type")

        print(f"[DEBUG] Extracted - username: {username}, user_type: {user_type}")

        if username is None or user_type is None:
            print("[DEBUG] Missing username or user_type")
            raise credentials_exception

    except JWTError as e:
        print(f"[DEBUG] JWT Error: {e}")
        raise credentials_exception

    # Auth service에서 사용자 정보 가져오기
    try:
        auth_url = f"http://auth-service:8000/api/auth/{user_type}/me"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                auth_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                user_info = response.json()
                return {
                    "id": user_info["id"],
                    "username": user_info["username"],
                    "name": user_info["name"],
                    "user_type": user_type
                }
            else:
                print(f"[DEBUG] Auth service returned {response.status_code}")
                raise credentials_exception

    except Exception as e:
        print(f"[DEBUG] Error fetching user info: {e}")
        raise credentials_exception


def verify_teacher_permission(current_user: Dict[str, Any]) -> Dict[str, Any]:
    """선생님 권한 확인"""
    print(f"[DEBUG] Checking teacher permission for user: {current_user}")
    if current_user.get("user_type") != "teacher":
        print(f"[DEBUG] Access denied - user_type: {current_user.get('user_type')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"선생님만 접근할 수 있습니다. 현재 사용자 타입: {current_user.get('user_type')}, 사용자: {current_user.get('name')}"
        )
    return current_user


async def get_current_teacher(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """현재 로그인한 선생님 정보 가져오기"""
    return verify_teacher_permission(current_user)