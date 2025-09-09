"""
공통 설정 관리
각 서비스에서 사용할 수 있는 공통 설정들을 관리합니다.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class BaseServiceSettings(BaseSettings):
    """모든 서비스가 공통으로 사용하는 기본 설정"""
    
    # Database settings
    database_url: str = Field(..., env="DATABASE_URL")
    
    # API Keys
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # CORS settings
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class MathServiceSettings(BaseServiceSettings):
    """수학 서비스 전용 설정"""
    
    # Redis settings for Celery
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Math service specific settings
    max_problems_per_worksheet: int = Field(default=50, env="MAX_PROBLEMS_PER_WORKSHEET")
    default_difficulty: str = Field(default="medium", env="DEFAULT_DIFFICULTY")


class EnglishServiceSettings(BaseServiceSettings):
    """영어 서비스 전용 설정"""
    
    # English service specific settings
    max_questions_per_test: int = Field(default=30, env="MAX_QUESTIONS_PER_TEST")
    default_test_type: str = Field(default="reading", env="DEFAULT_TEST_TYPE")


def get_math_service_settings() -> MathServiceSettings:
    """수학 서비스 설정 반환"""
    return MathServiceSettings()


def get_english_service_settings() -> EnglishServiceSettings:
    """영어 서비스 설정 반환"""
    return EnglishServiceSettings()