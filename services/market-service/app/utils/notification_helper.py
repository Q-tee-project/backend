"""
Notification Service 연동 헬퍼 함수
"""
import httpx
import os
from typing import Literal

NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")


async def send_market_sale_notification(
    seller_id: int,
    seller_type: Literal["teacher", "student"],
    buyer_id: int,
    buyer_name: str,
    product_id: int,
    product_title: str,
    amount: int
) -> bool:
    """마켓 판매 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/market/sale",
                json={
                    "receiver_id": seller_id,
                    "receiver_type": seller_type,
                    "buyer_id": buyer_id,
                    "buyer_name": buyer_name,
                    "product_id": product_id,
                    "product_title": product_title,
                    "amount": amount
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 마켓 판매 알림 전송 성공: seller_id={seller_id}, product_id={product_id}")
                return True
            else:
                print(f"⚠️ 마켓 판매 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 마켓 판매 알림 전송 실패: {e}")
        return False


async def send_market_new_product_notification(
    receiver_id: int,
    receiver_type: Literal["teacher", "student"],
    seller_id: int,
    seller_name: str,
    product_id: int,
    product_title: str,
    price: int
) -> bool:
    """마켓 신상품 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/market/new-product",
                json={
                    "receiver_id": receiver_id,
                    "receiver_type": receiver_type,
                    "seller_id": seller_id,
                    "seller_name": seller_name,
                    "product_id": product_id,
                    "product_title": product_title,
                    "price": price
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 마켓 신상품 알림 전송 성공: receiver_id={receiver_id}, product_id={product_id}")
                return True
            else:
                print(f"⚠️ 마켓 신상품 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 마켓 신상품 알림 전송 실패: {e}")
        return False
