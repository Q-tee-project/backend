from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .core.database import engine, Base
from .routers.market import router as market_router
from .core.config import settings

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Market Service",
    description="Q-tee 마켓플레이스 서비스",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(market_router)


@app.get("/")
async def root():
    return {"message": "Market Service is running!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "market-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True
    )