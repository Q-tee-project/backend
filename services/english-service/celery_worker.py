#!/usr/bin/env python3

from app.celery_app import celery_app

if __name__ == "__main__":
    # Celery worker 시작
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=english_queue'
    ])