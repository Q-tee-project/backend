import asyncio
import json
import logging
from typing import AsyncGenerator
from fastapi import HTTPException
from .redis_client import redis_client
import redis.asyncio as aioredis
import os

logger = logging.getLogger(__name__)

class SSEService:
    def __init__(self):
        self.redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/0"

    async def stream_notifications(self, user_type: str, user_id: int) -> AsyncGenerator[str, None]:
        """SSE 스트림 생성"""
        redis_conn = None
        pubsub = None

        try:
            # Redis 연결
            redis_conn = aioredis.from_url(self.redis_url)
            pubsub = redis_conn.pubsub()

            # 채널 구독
            channel = f"notifications:{user_type}:{user_id}"
            await pubsub.subscribe(channel)

            logger.info(f"SSE connection established for {user_type}:{user_id}")

            # 연결 시 저장된 알림들 먼저 전송
            stored_notifications = redis_client.get_stored_notifications(user_type, user_id)
            for notification in stored_notifications:
                yield f"data: {json.dumps(notification)}\n\n"

            # 저장된 알림들 삭제
            if stored_notifications:
                redis_client.clear_stored_notifications(user_type, user_id)

            # 실시간 알림 스트리밍
            heartbeat_counter = 0
            while True:
                try:
                    # Redis에서 메시지 확인 (non-blocking)
                    message = await asyncio.wait_for(pubsub.get_message(), timeout=5.0)

                    if message and message['type'] == 'message':
                        notification_data = message['data']
                        logger.info(f"Raw notification data type: {type(notification_data)}")
                        logger.info(f"Raw notification data: {notification_data}")

                        # bytes를 string으로 디코딩
                        if isinstance(notification_data, bytes):
                            notification_data = notification_data.decode('utf-8')
                            logger.info(f"Decoded notification data: {notification_data}")

                        # JSON 형태인지 검증하고 재포맷
                        try:
                            parsed_data = json.loads(notification_data)
                            formatted_data = json.dumps(parsed_data)
                            logger.info(f"Formatted notification data: {formatted_data}")
                            yield f"data: {formatted_data}\n\n"
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON data: {notification_data}, error: {e}")
                            continue
                    else:
                        # Heartbeat 전송 (30초마다)
                        heartbeat_counter += 1
                        if heartbeat_counter >= 6:  # 5초 * 6 = 30초
                            yield f": heartbeat\n\n"
                            heartbeat_counter = 0

                except asyncio.TimeoutError:
                    # 타임아웃 시 heartbeat 전송
                    yield f": heartbeat\n\n"

                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    yield f"data: {json.dumps({'error': 'Connection error'})}\n\n"
                    break

        except Exception as e:
            logger.error(f"Failed to establish SSE connection: {e}")
            yield f"data: {json.dumps({'error': 'Failed to connect'})}\n\n"

        finally:
            try:
                if pubsub:
                    await pubsub.unsubscribe()
                    await pubsub.close()
                if redis_conn:
                    await redis_conn.close()
            except Exception as e:
                logger.error(f"Error closing Redis connections: {e}")
            logger.info(f"SSE connection closed for {user_type}:{user_id}")

sse_service = SSEService()