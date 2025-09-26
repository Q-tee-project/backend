import redis
import json
from typing import Optional, Dict, Any, List
import os
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )

        try:
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")

    def publish_notification(self, user_type: str, user_id: int, notification: Dict[Any, Any]):
        """사용자별 알림 발행"""
        try:
            channel = f"notifications:{user_type}:{user_id}"
            result = self.redis_client.publish(channel, json.dumps(notification))
            logger.info(f"Published notification to channel {channel}, subscribers: {result}")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to publish notification: {e}")
            return False

    def store_notification(self, user_type: str, user_id: int, notification: Dict[Any, Any]):
        """알림을 임시 저장 (SSE 연결이 끊어진 경우 대비)"""
        try:
            key = f"stored_notifications:{user_type}:{user_id}"
            self.redis_client.lpush(key, json.dumps(notification))
            # 최대 100개까지만 저장
            self.redis_client.ltrim(key, 0, 99)
            # 24시간 후 만료
            self.redis_client.expire(key, 86400)
            logger.debug(f"Stored notification for {user_type}:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")
            return False

    def get_stored_notifications(self, user_type: str, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """저장된 알림들 조회"""
        try:
            key = f"stored_notifications:{user_type}:{user_id}"
            notifications = self.redis_client.lrange(key, 0, limit - 1)
            return [json.loads(notif) for notif in notifications]
        except Exception as e:
            logger.error(f"Failed to get stored notifications: {e}")
            return []

    def clear_stored_notifications(self, user_type: str, user_id: int):
        """저장된 알림들 삭제"""
        try:
            key = f"stored_notifications:{user_type}:{user_id}"
            result = self.redis_client.delete(key)
            logger.debug(f"Cleared stored notifications for {user_type}:{user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to clear stored notifications: {e}")
            return False

    def mark_notification_as_read(self, user_type: str, user_id: int, notification_id: str) -> bool:
        """특정 알림을 읽음 처리"""
        try:
            key = f"stored_notifications:{user_type}:{user_id}"
            notifications = self.redis_client.lrange(key, 0, -1)

            if not notifications:
                logger.warning(f"No notifications found for {user_type}:{user_id}")
                return False

            updated = False
            for i, notif_str in enumerate(notifications):
                notif_json = json.loads(notif_str)
                if notif_json.get("id") == notification_id:
                    notif_json["read"] = True
                    updated_notif_str = json.dumps(notif_json)

                    # Redis에서 기존 항목 삭제하고 새 항목 추가
                    self.redis_client.lset(key, i, updated_notif_str)
                    updated = True
                    logger.info(f"Marked notification {notification_id} as read for {user_type}:{user_id}")
                    break

            return updated
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    def mark_all_notifications_as_read(self, user_type: str, user_id: int) -> bool:
        """모든 알림을 읽음 처리"""
        try:
            key = f"stored_notifications:{user_type}:{user_id}"
            notifications = self.redis_client.lrange(key, 0, -1)

            if not notifications:
                return True

            updated_notifications = []
            for notif_str in notifications:
                notif_json = json.loads(notif_str)
                notif_json["read"] = True
                updated_notifications.append(json.dumps(notif_json))

            # 기존 리스트 삭제하고 새 리스트로 교체
            self.redis_client.delete(key)
            if updated_notifications:
                self.redis_client.lpush(key, *updated_notifications)
                self.redis_client.expire(key, 86400)  # 24시간 TTL 재설정

            logger.info(f"Marked all notifications as read for {user_type}:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            return False

    def delete_notifications_by_type(self, user_type: str, user_id: int, notification_type: str) -> bool:
        """특정 타입의 모든 알림 삭제"""
        try:
            key = f"stored_notifications:{user_type}:{user_id}"
            notifications = self.redis_client.lrange(key, 0, -1)

            if not notifications:
                return True

            filtered_notifications = []
            for notif_str in notifications:
                notif_json = json.loads(notif_str)
                if notif_json.get("type") != notification_type:
                    filtered_notifications.append(notif_str)

            # 기존 리스트 삭제하고 필터된 리스트로 교체
            self.redis_client.delete(key)
            if filtered_notifications:
                self.redis_client.lpush(key, *filtered_notifications)
                self.redis_client.expire(key, 86400)

            logger.info(f"Deleted all {notification_type} notifications for {user_type}:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete notifications by type: {e}")
            return False

    def delete_notification_by_id(self, user_type: str, user_id: int, notification_id: str, notification_type: str) -> bool:
        """ID와 Type으로 특정 알림 하나를 삭제"""
        try:
            logger.info(f"[DEBUG] Attempting to delete notification. Target ID: {notification_id}, Target Type: {notification_type}")
            key = f"stored_notifications:{user_type}:{user_id}"
            notifications = self.redis_client.lrange(key, 0, -1)

            if not notifications:
                logger.warning(f"[DEBUG] No notifications found in Redis for key: {key}")
                return False

            notification_to_delete = None
            logger.info("[DEBUG] Checking notifications in Redis...")
            for i, notif_str in enumerate(notifications):
                notif_json = json.loads(notif_str)
                redis_id = notif_json.get("id")
                redis_type = notif_json.get("type")
                logger.info(f"[DEBUG] Item {i} -> ID: {redis_id}, Type: {redis_type}")

                if redis_id == notification_id and redis_type == notification_type:
                    logger.info(f"[DEBUG] Match found at index {i}. Preparing to delete.")
                    notification_to_delete = notif_str
                    break

            if notification_to_delete:
                result = self.redis_client.lrem(key, 1, notification_to_delete)
                if result > 0:
                    logger.info(f"Successfully deleted notification {notification_id} ({notification_type}) for {user_type}:{user_id}")
                    return True
                else:
                    logger.error(f"[DEBUG] LREM command failed for notification: {notification_to_delete}")
                    return False

            logger.warning(f"[DEBUG] No match found for Target ID: {notification_id}, Target Type: {notification_type}")
            return False
        except Exception as e:
            logger.error(f"Exception in delete_notification_by_id: {e}")
            return False

redis_client = RedisClient()