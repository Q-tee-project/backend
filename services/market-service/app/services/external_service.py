import httpx
import asyncio
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
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
                "english": settings.ENGLISH_SERVICE_URL,
            }

            if service not in service_urls:
                return None

            # 수학 서비스는 다른 URL 패턴 사용
            if service == "math":
                url = f"{service_urls[service]}/api/market-integration/market/worksheets/{worksheet_id}"
            else:
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
                "english": settings.ENGLISH_SERVICE_URL,
            }

            if service not in service_urls:
                return None

            # 수학 서비스는 다른 URL 패턴 사용
            if service == "math":
                url = f"{service_urls[service]}/api/market-integration/market/worksheets/{worksheet_id}/problems"
            else:
                url = f"{service_urls[service]}/market/worksheets/{worksheet_id}/problems"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15.0)

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception as e:
            print(f"Error fetching worksheet details from {service}: {str(e)}")
            return None

    @staticmethod
    async def get_problems_by_ids(service: str, problem_ids: List[int]) -> List[Dict[str, Any]]:
        """문제 ID 목록으로 문제 상세 조회"""
        try:
            service_urls = {
                "korean": settings.KOREAN_SERVICE_URL,
                "math": settings.MATH_SERVICE_URL,
                "english": settings.ENGLISH_SERVICE_URL,
            }

            if service not in service_urls:
                return []

            url = f"{service_urls[service]}/problems/batch"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={"problem_ids": problem_ids},
                    timeout=15.0
                )

                if response.status_code == 200:
                    return response.json()
                return []

        except Exception as e:
            print(f"Error fetching problems from {service}: {str(e)}")
            return []

    @staticmethod
    async def copy_worksheet_to_user(service: str, worksheet_id: int,
                                    target_user_id: int, new_title: str) -> Optional[int]:
        """워크시트를 구매자의 계정으로 복사"""
        try:
            service_urls = {
                "korean": settings.KOREAN_SERVICE_URL,
                "math": settings.MATH_SERVICE_URL,
                "english": settings.ENGLISH_SERVICE_URL,
            }

            if service not in service_urls:
                return None

            copy_data = {
                "source_worksheet_id": worksheet_id,
                "target_user_id": target_user_id,
                "new_title": new_title,
                "copy_type": "purchase"  # 구매로 인한 복사임을 명시
            }

            base_url = service_urls[service]
            if service == "math":
                url = f"{base_url}/api/worksheets/copy"
            elif service == "korean":
                url = f"{base_url}/api/korean-generation/copy"
            else:
                url = f"{base_url}/worksheets/copy"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=copy_data,
                    timeout=20.0
                )

                if response.status_code == 201:
                    result = response.json()
                    return result.get("new_worksheet_id")
                return None

        except Exception as e:
            print(f"Error copying worksheet from {service}: {str(e)}")
            return None

    @staticmethod
    async def check_user_access(service: str, user_id: int, worksheet_id: int) -> bool:
        """사용자가 해당 워크시트에 접근 권한이 있는지 확인"""
        try:
            service_urls = {
                "korean": settings.KOREAN_SERVICE_URL,
                "math": settings.MATH_SERVICE_URL,
                "english": settings.ENGLISH_SERVICE_URL,
            }

            if service not in service_urls:
                return False

            url = f"{service_urls[service]}/worksheets/{worksheet_id}/access"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params={"user_id": user_id},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("has_access", False)

        except Exception:
            pass

        return False

    @staticmethod
    def get_service_display_name(service: str) -> str:
        """서비스 이름을 한국어로 변환"""
        service_names = {
            "korean": "국어",
            "math": "수학",
            "english": "영어"
        }
        return service_names.get(service, service)

    @staticmethod
    async def notify_purchase(service: str, worksheet_id: int,
                             seller_id: int, buyer_id: int, purchase_id: int) -> bool:
        """구매 완료 알림 (선택사항)"""
        try:
            service_urls = {
                "korean": settings.KOREAN_SERVICE_URL,
                "math": settings.MATH_SERVICE_URL,
                "english": settings.ENGLISH_SERVICE_URL,
            }

            if service not in service_urls:
                return True  # 알림 실패해도 구매 자체는 성공

            notification_data = {
                "worksheet_id": worksheet_id,
                "seller_id": seller_id,
                "buyer_id": buyer_id,
                "purchase_id": purchase_id,
                "event_type": "worksheet_purchased"
            }

            url = f"{service_urls[service]}/notifications/purchase"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=notification_data,
                    timeout=10.0
                )

                return response.status_code == 200

        except Exception:
            # 알림 실패해도 구매 프로세스에는 영향 없음
            return True