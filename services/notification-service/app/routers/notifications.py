from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List
from ..schemas.notification import (
    MessageNotificationRequest,
    ProblemGenerationNotificationRequest,
    ProblemRegenerationNotificationRequest,
    AssignmentSubmittedNotificationRequest,
    AssignmentDeployedNotificationRequest,
    ClassJoinRequestNotificationRequest,
    ClassApprovedNotificationRequest,
    GradingUpdatedNotificationRequest,
    MarketSaleNotificationRequest,
    MarketNewProductNotificationRequest,
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


@router.patch("/stored/{user_type}/{user_id}/{notification_id}/read")
async def mark_notification_as_read(user_type: str, user_id: int, notification_id: str):
    """특정 알림을 읽음 처리"""
    if user_type not in ["teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    try:
        success = redis_client.mark_notification_as_read(user_type, user_id, notification_id)

        if success:
            return {"success": True, "message": f"Notification {notification_id} marked as read"}
        else:
            raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found")

    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/stored/{user_type}/{user_id}/read-all")
async def mark_all_notifications_as_read(user_type: str, user_id: int):
    """모든 알림을 읽음 처리"""
    if user_type not in ["teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    try:
        success = redis_client.mark_all_notifications_as_read(user_type, user_id)

        if success:
            return {"success": True, "message": "All notifications marked as read"}
        else:
            raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")

    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/stored/{user_type}/{user_id}/type/{notification_type}")
async def delete_notifications_by_type(user_type: str, user_id: int, notification_type: str):
    """특정 타입의 모든 알림 삭제"""
    if user_type not in ["teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    try:
        success = redis_client.delete_notifications_by_type(user_type, user_id, notification_type)

        if success:
            return {"success": True, "message": f"All {notification_type} notifications deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete notifications by type")

    except Exception as e:
        logger.error(f"Error deleting notifications by type: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/stored/{user_type}/{user_id}/{notification_type}/{notification_id}")
async def delete_single_notification(user_type: str, user_id: int, notification_type: str, notification_id: str):
    """ID와 Type으로 특정 알림 하나만 삭제"""
    if user_type not in ["teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    try:
        success = redis_client.delete_notification_by_id(user_type, user_id, notification_id, notification_type)

        if success:
            return {"success": True, "message": f"Notification {notification_id} deleted."}
        else:
            # 404 Not Found를 반환하는 것이 더 적절할 수 있습니다.
            raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found.")

    except Exception as e:
        logger.error(f"Error deleting single notification: {e}")
        # 이미 HTTPException인 경우 다시 감싸지 않도록 확인
        if isinstance(e, HTTPException):
            raise e
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
# 문제 생성/재생성 알림
@router.post("/problem/generation")
async def send_problem_generation_notification(request: ProblemGenerationNotificationRequest):
    """문제 생성 완료/실패 알림 전송"""
    try:
        success = notification_service.send_problem_generation_notification(request.dict())
        if success:
            return {"success": True, "message": "Problem generation notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending problem generation notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/problem/regeneration")
async def send_problem_regeneration_notification(request: ProblemRegenerationNotificationRequest):
    """문제 재생성 완료/실패 알림 전송"""
    try:
        success = notification_service.send_problem_regeneration_notification(request.dict())
        if success:
            return {"success": True, "message": "Problem regeneration notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending problem regeneration notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 과제 관련 알림
@router.post("/assignment/submitted")
async def send_assignment_submitted_notification(request: AssignmentSubmittedNotificationRequest):
    """과제 제출 알림 전송 (선생님이 받음)"""
    try:
        success = notification_service.send_assignment_submitted_notification(request.dict())
        if success:
            return {"success": True, "message": "Assignment submitted notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending assignment submitted notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assignment/deployed")
async def send_assignment_deployed_notification(request: AssignmentDeployedNotificationRequest):
    """과제 배포 알림 전송 (학생이 받음)"""
    try:
        success = notification_service.send_assignment_deployed_notification(request.dict())
        if success:
            return {"success": True, "message": "Assignment deployed notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending assignment deployed notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 클래스 관련 알림
@router.post("/class/join-request")
async def send_class_join_request_notification(request: ClassJoinRequestNotificationRequest):
    """클래스 가입 요청 알림 전송 (선생님이 받음)"""
    try:
        success = notification_service.send_class_join_request_notification(request.dict())
        if success:
            return {"success": True, "message": "Class join request notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending class join request notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/class/approved")
async def send_class_approved_notification(request: ClassApprovedNotificationRequest):
    """클래스 승인 알림 전송 (학생이 받음)"""
    try:
        success = notification_service.send_class_approved_notification(request.dict())
        if success:
            return {"success": True, "message": "Class approved notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending class approved notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 채점 관련 알림
@router.post("/grading/updated")
async def send_grading_updated_notification(request: GradingUpdatedNotificationRequest):
    """채점 수정 알림 전송 (학생이 받음)"""
    try:
        success = notification_service.send_grading_updated_notification(request.dict())
        if success:
            return {"success": True, "message": "Grading updated notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending grading updated notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 마켓 관련 알림
@router.post("/market/sale")
async def send_market_sale_notification(request: MarketSaleNotificationRequest):
    """마켓 판매 알림 전송 (판매자가 받음)"""
    try:
        success = notification_service.send_market_sale_notification(request.dict())
        if success:
            return {"success": True, "message": "Market sale notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending market sale notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market/new-product")
async def send_market_new_product_notification(request: MarketNewProductNotificationRequest):
    """마켓 신상품 알림 전송"""
    try:
        success = notification_service.send_market_new_product_notification(request.dict())
        if success:
            return {"success": True, "message": "Market new product notification sent"}
        raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Error sending market new product notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
