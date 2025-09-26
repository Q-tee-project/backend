from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List
from ..schemas.notification import (
    MessageNotificationRequest,
    BulkNotificationRequest,
    StoredNotificationsResponse
)
from ..services.sse_service import sse_service
from ..services.notification_service import notification_service
from ..services.redis_client import redis_client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stream/{user_type}/{user_id}")
async def stream_notifications(user_type: str, user_id: int):
    """SSE 스트림 엔드포인트"""
    if user_type not in ["teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    try:
        return StreamingResponse(
            sse_service.stream_notifications(user_type, user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"Error creating SSE stream: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification stream")

@router.post("/message")
async def send_message_notification(request: MessageNotificationRequest):
    """쪽지 알림 전송"""
    try:
        success = notification_service.send_message_notification(request.dict())

        if success:
            return {"success": True, "message": "Notification sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk")
async def send_bulk_notifications(request: BulkNotificationRequest):
    """대량 알림 전송"""
    try:
        notifications_data = [notif.dict() for notif in request.notifications]
        success_count = notification_service.send_bulk_notifications(notifications_data)

        return {
            "success": True,
            "message": f"Sent {success_count}/{len(notifications_data)} notifications",
            "sent_count": success_count,
            "total_count": len(notifications_data)
        }

    except Exception as e:
        logger.error(f"Error sending bulk notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stored/{user_type}/{user_id}", response_model=StoredNotificationsResponse)
async def get_stored_notifications(
    user_type: str,
    user_id: int,
    limit: int = Query(10, ge=1, le=50)
):
    """저장된 알림 조회"""
    if user_type not in ["teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    try:
        notifications = notification_service.get_stored_notifications(user_type, user_id, limit)
        return StoredNotificationsResponse(notifications=notifications)

    except Exception as e:
        logger.error(f"Error getting stored notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/stored/{user_type}/{user_id}")
async def clear_stored_notifications(user_type: str, user_id: int):
    """저장된 알림 삭제"""
    if user_type not in ["teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    try:
        success = redis_client.clear_stored_notifications(user_type, user_id)

        if success:
            return {"success": True, "message": "Stored notifications cleared"}
        else:
            return {"success": False, "message": "No notifications to clear"}

    except Exception as e:
        logger.error(f"Error clearing stored notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/{user_type}/{user_id}")
async def send_test_notification(user_type: str, user_id: int):
    """테스트 알림 전송"""
    if user_type not in ["teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    test_notification = {
        "message_id": 999999,
        "sender_id": 1,
        "sender_name": "테스트 발신자",
        "sender_type": "teacher" if user_type == "student" else "student",
        "receiver_id": user_id,
        "receiver_type": user_type,
        "subject": "테스트 쪽지입니다",
        "preview": "이것은 테스트 쪽지 내용입니다.",
        "classroom_id": 1
    }

    try:
        success = notification_service.send_message_notification(test_notification)

        if success:
            return {"success": True, "message": "Test notification sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test notification")

    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))