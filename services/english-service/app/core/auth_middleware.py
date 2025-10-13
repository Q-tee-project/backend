"""
인증 미들웨어
모든 요청에 대해 토큰 검증을 수행하되, 예외 경로는 건너뜁니다.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import httpx
import os
from typing import List

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

# 인증이 필요 없는 경로들
PUBLIC_PATHS: List[str] = [
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/openapi.json",
    "/api/english/health",
    "/api/english/health/db",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """모든 요청에 대해 JWT 토큰 검증을 수행하는 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        # CORS preflight 요청은 인증을 건너뛰어야 합니다.
        if request.method == "OPTIONS":
            return await call_next(request)

        # 공개 경로는 인증 건너뛰기
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing"}
            )

        # Bearer 토큰 추출
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authorization header format"}
            )

        token = auth_header.replace("Bearer ", "")

        # Auth Service로 토큰 검증
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{AUTH_SERVICE_URL}/api/auth/verify-token",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0
                )
                response.raise_for_status()
                user_data = response.json()

                # request.state에 사용자 정보 저장 (라우터에서 사용 가능)
                request.state.user = user_data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"}
                )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Authentication service unavailable"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": f"Authentication service error: {str(e)}"}
            )

        # 검증 통과 후 다음 처리
        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        """공개 경로인지 확인"""
        # 정확히 일치하는 경로
        if path in PUBLIC_PATHS:
            return True

        # prefix로 시작하는 경로 (예: /static/)
        public_prefixes = ["/static/"]
        for prefix in public_prefixes:
            if path.startswith(prefix):
                return True

        return False
