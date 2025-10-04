"""
Notification Service 연동 헬퍼 함수
"""
import httpx
import os
from typing import Literal, Optional

NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8006")


async def send_class_join_request_notification(
    teacher_id: int,
    student_id: int,
    student_name: str,
    class_id: int,
    class_name: str,
    message: Optional[str] = None
) -> bool:
    """클래스 가입 요청 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/class/join-request",
                json={
                    "receiver_id": teacher_id,
                    "receiver_type": "teacher",
                    "student_id": student_id,
                    "student_name": student_name,
                    "class_id": class_id,
                    "class_name": class_name,
                    "message": message
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 클래스 가입 요청 알림 전송 성공: teacher_id={teacher_id}, class_id={class_id}")
                return True
            else:
                print(f"⚠️ 클래스 가입 요청 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 클래스 가입 요청 알림 전송 실패: {e}")
        return False


async def send_class_approved_notification(
    student_id: int,
    class_id: int,
    class_name: str,
    teacher_name: str
) -> bool:
    """클래스 승인 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/class/approved",
                json={
                    "receiver_id": student_id,
                    "receiver_type": "student",
                    "class_id": class_id,
                    "class_name": class_name,
                    "teacher_name": teacher_name
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 클래스 승인 알림 전송 성공: student_id={student_id}, class_id={class_id}")
                return True
            else:
                print(f"⚠️ 클래스 승인 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 클래스 승인 알림 전송 실패: {e}")
        return False
