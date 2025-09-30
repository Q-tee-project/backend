from celery import Celery
from celery.signals import after_setup_logger
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Redis URL 설정
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery 앱 생성
celery_app = Celery(
    "english_problem_generator",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    """Celery 로거 설정"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=False,
    task_track_started=True,
    task_always_eager=False,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    # 로깅 설정
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    # 영어 서비스 전용 큐 설정
    task_default_queue='english_queue',
    task_routes={
        'app.tasks.*': {'queue': 'english_queue'},
    },
)

# 태스크 발견을 위한 autodiscover
celery_app.autodiscover_tasks(["app"])

if __name__ == "__main__":
    celery_app.start()