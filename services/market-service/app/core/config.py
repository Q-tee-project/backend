import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/qt_project_db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Server
    PORT: int = int(os.getenv("PORT", 8000))

    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads/market")

    # External Services (Docker 내부 포트 사용)
    KOREAN_SERVICE_URL: str = os.getenv("KOREAN_SERVICE_URL", "http://korean-service:8000")
    MATH_SERVICE_URL: str = os.getenv("MATH_SERVICE_URL", "http://math-service:8000")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

settings = Settings()