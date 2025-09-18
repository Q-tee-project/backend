import httpx
import asyncio
from typing import Optional, Dict, Any
from ..core.config import settings


class ExternalService:
    """외부 서비스와의 통신을 담당하는 클래스"""

    @staticmethod
    async def get_worksheet_info(service: str, worksheet_id: int) -> Optional[Dict[Any, Any]]:
        """다른 서비스에서 문제지 정보를 가져오기"""
        try:
            service_urls = {
                "korean": settings.KOREAN_SERVICE_URL,
                "math": settings.MATH_SERVICE_URL,
            }

            if service not in service_urls:
                return None

            url = f"{service_urls[service]}/market/worksheets/{worksheet_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception as e:
            print(f"Error fetching worksheet from {service}: {str(e)}")
            return None

    @staticmethod
    async def verify_user(user_id: int) -> Optional[Dict[Any, Any]]:
        """auth-service에서 사용자 정보 확인"""
        try:
            url = f"{settings.AUTH_SERVICE_URL}/users/{user_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception as e:
            print(f"Error verifying user: {str(e)}")
            return None

    @staticmethod
    async def check_worksheet_ownership(service: str, worksheet_id: int, user_id: int) -> bool:
        """사용자가 해당 문제지의 소유자인지 확인"""
        try:
            worksheet_info = await ExternalService.get_worksheet_info(service, worksheet_id)

            if worksheet_info:
                # 문제지의 소유자 ID가 현재 사용자와 일치하는지 확인
                return worksheet_info.get("user_id") == user_id or worksheet_info.get("teacher_id") == user_id

            return False

        except Exception as e:
            print(f"Error checking worksheet ownership: {str(e)}")
            return False

    @staticmethod
    async def get_worksheet_details(service: str, worksheet_id: int) -> Optional[Dict[Any, Any]]:
        """문제지 상세 정보 (문제 포함) 가져오기"""
        try:
            service_urls = {
                "korean": settings.KOREAN_SERVICE_URL,
                "math": settings.MATH_SERVICE_URL,
            }

            if service not in service_urls:
                return None

            url = f"{service_urls[service]}/market/worksheets/{worksheet_id}/problems"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15.0)

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception as e:
            print(f"Error fetching worksheet details from {service}: {str(e)}")
            return None