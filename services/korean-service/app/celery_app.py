from celery import Celery
import os

# Redis 연결 URL (모든 서비스가 같은 DB 사용)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery 앱 생성 (korean-service 전용)
celery_app = Celery(
    "korean_service",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.tasks",
    ]
)

# Celery 설정
celery_app.conf.update(
    result_expires=3600,
    timezone='Asia/Seoul',
    enable_utc=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # 국어 서비스 전용 큐 설정
    task_routes={
        'app.tasks.generate_korean_problems_task': {'queue': 'korean_queue'},
    },
)