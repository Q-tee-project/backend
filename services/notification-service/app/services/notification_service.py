from typing import Dict, Any, List
from .redis_client import redis_client
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:

    def send_message_notification(self, message_data: Dict[str, Any]) -> bool:
        """쪽지 알림 전송"""
        try:
            notification = {
                "type": "new_message",
                "id": f"msg_{message_data['message_id']}_{int(datetime.now().timestamp())}",
                "data": {
                    "message_id": message_data['message_id'],
                    "sender_id": message_data['sender_id'],
                    "sender_name": message_data['sender_name'],
                    "sender_type": message_data['sender_type'],
                    "subject": message_data['subject'],
                    "preview": message_data.get('preview', ''),
                    "classroom_id": message_data.get('classroom_id')
                },
                "timestamp": datetime.now().isoformat(),
                "read": False
            }

            receiver_type = message_data['receiver_type']
            receiver_id = message_data['receiver_id']

            # 실시간 알림 발송
            publish_success = redis_client.publish_notification(receiver_type, receiver_id, notification)

            # 알림 저장 (연결이 끊어진 경우 대비)
            store_success = redis_client.store_notification(receiver_type, receiver_id, notification)

            if publish_success or store_success:
                logger.info(f"Notification sent to {receiver_type}:{receiver_id} for message {message_data['message_id']}")
                return True
            else:
                logger.warning(f"Failed to send notification to {receiver_type}:{receiver_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    def send_bulk_notifications(self, notifications_data: List[Dict[str, Any]]) -> int:
        """대량 알림 전송"""
        success_count = 0
        for notif_data in notifications_data:
            if self.send_message_notification(notif_data):
                success_count += 1

        logger.info(f"Sent {success_count}/{len(notifications_data)} notifications")
        return success_count

    def get_stored_notifications(self, user_type: str, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """저장된 알림 조회"""
        try:
            notifications = redis_client.get_stored_notifications(user_type, user_id, limit)
            logger.info(f"Retrieved {len(notifications)} stored notifications for {user_type}:{user_id}")
            return notifications
        except Exception as e:
            logger.error(f"Failed to get stored notifications: {e}")
            return []

notification_service = NotificationService()