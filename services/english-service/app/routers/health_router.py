from fastapi import APIRouter
from sqlalchemy import text
from app.database import SessionLocal

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """서버 및 데이터베이스 상태 확인"""
    try:
        # 데이터베이스 연결 테스트
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy", 
            "message": "서버와 데이터베이스가 정상적으로 작동 중입니다.", 
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "message": "데이터베이스 연결에 문제가 있습니다.", 
            "database": "disconnected", 
            "error": str(e)
        }
