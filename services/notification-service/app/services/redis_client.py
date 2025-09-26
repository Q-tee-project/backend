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

redis_client = RedisClient()