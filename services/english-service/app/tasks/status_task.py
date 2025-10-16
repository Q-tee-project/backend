"""
태스크 상태 조회 Celery 태스크
"""
from app.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.get_task_status")
def get_task_status(self, task_id: str):
    """태스크 상태 조회"""
    try:
        result = celery_app.AsyncResult(task_id)

        if result.state == 'PENDING':
            response = {
                'state': result.state,
                'status': '대기 중...'
            }
        elif result.state == 'PROGRESS':
            response = {
                'state': result.state,
                'current': result.info.get('current', 0),
                'total': result.info.get('total', 100),
                'status': result.info.get('status', '')
            }
        elif result.state == 'SUCCESS':
            response = {
                'state': result.state,
                'result': result.info
            }
        else:  # FAILURE
            response = {
                'state': result.state,
                'error': str(result.info)
            }

        return response

    except Exception as e:
        return {
            'state': 'FAILURE',
            'error': f'태스크 상태 조회 실패: {str(e)}'
        }

