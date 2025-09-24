from fastapi import APIRouter, Depends, HTTPException
from celery.result import AsyncResult
from ..celery_app import celery_app

router = APIRouter()

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    try:
        result = AsyncResult(task_id, app=celery_app)

        if result.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": "PENDING",
                "message": "태스크가 대기 중입니다."
            }
        elif result.state == 'PROGRESS':
            return {
                "task_id": task_id,
                "status": "PROGRESS",
                "current": result.info.get('current', 0),
                "total": result.info.get('total', 100),
                "message": result.info.get('status', '처리 중...')
            }
        elif result.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": result.result
            }
        elif result.state == 'FAILURE':
            return {
                "task_id": task_id,
                "status": "FAILURE",
                "error": str(result.info) if result.info else "알 수 없는 오류가 발생했습니다."
            }
        else:
            return {
                "task_id": task_id,
                "status": result.state,
                "info": result.info
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"태스크 상태 조회 중 오류: {str(e)}"
        )

@router.get("/{task_id}/status")
async def get_task_status_alias(task_id: str):
    """작업 상태 조회 - 호환성을 위한 별칭"""
    return await get_task_status(task_id)
