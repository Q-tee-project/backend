"""
애플리케이션 설정 관리

pydantic-settings를 사용하여 환경변수와 애플리케이션 설정을 중앙에서 관리합니다.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 전역 설정"""
    
    # === 애플리케이션 기본 설정 ===
    app_name: str = "English Question Generator"
    app_version: str = "2.0.0"
    app_description: str = "FastAPI와 PostgreSQL을 사용한 영어 문제 생성기 서버입니다."
    
    # === 서버 설정 ===
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    reload: bool = True
    
    # === 데이터베이스 설정 ===
    database_url: str = Field(
        default="postgresql://username:password@localhost:5432/testdb",
        env="DATABASE_URL",
        description="데이터베이스 연결 URL"
    )
    
    # === AI 서비스 설정 ===
    gemini_api_key: Optional[str] = Field(
        default=None,
        env="GEMINI_API_KEY", 
        description="Google Gemini API 키"
    )
    gemini_model: str = "gemini-2.5-pro"
    gemini_flash_model: str = "gemini-2.5-flash"
    
    # === 문제 생성 설정 ===
    max_questions_per_worksheet: int = 100
    default_question_score: int = 1
    max_worksheet_duration: int = 180  # 분
    
    # === CORS 설정 ===
    allowed_origins: List[str] = ["*"]  # 프로덕션에서는 특정 도메인만 허용
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]
    allow_credentials: bool = True
    
    # === 로깅 설정 ===
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # === 보안 설정 ===
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        env="SECRET_KEY",
        description="JWT 토큰 서명용 비밀 키"
    )
    
    # === 캐싱 설정 ===
    redis_url: Optional[str] = Field(
        default=None,
        env="REDIS_URL",
        description="Redis 캐시 서버 URL (선택사항)"
    )
    cache_ttl: int = 300  # 5분
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_masked_database_url(self) -> str:
        """데이터베이스 URL에서 비밀번호 부분을 마스킹하여 반환"""
        try:
            if '@' in self.database_url and ':' in self.database_url:
                parts = self.database_url.split('@')
                if len(parts) == 2:
                    user_pass = parts[0].split(':')
                    if len(user_pass) >= 3:
                        # postgresql://user:password@host... 형태
                        masked_url = f"{user_pass[0]}:{user_pass[1]}:****@{parts[1]}"
                        return masked_url
            return self.database_url
        except Exception:
            return "DATABASE_URL (parsing error)"
    
    def get_masked_api_key(self) -> str:
        """API 키를 마스킹하여 반환"""
        if not self.gemini_api_key:
            return "Not Set"
        
        if self.gemini_api_key == "your_gemini_api_key_here":
            return "Example Key (Please Replace)"
        
        if len(self.gemini_api_key) >= 8:
            return f"{self.gemini_api_key[:4]}{'*' * (len(self.gemini_api_key) - 8)}{self.gemini_api_key[-4:]}"
        else:
            return "****"
    
    def is_production(self) -> bool:
        """프로덕션 환경인지 확인"""
        return not self.debug
    
    def validate_required_settings(self) -> dict:
        """필수 설정들이 올바르게 설정되었는지 검증"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 데이터베이스 URL 검증
        if not self.database_url or self.database_url == "postgresql://username:password@localhost:5432/testdb":
            validation_result["errors"].append("DATABASE_URL이 설정되지 않았거나 기본값입니다.")
            validation_result["valid"] = False
        
        # Gemini API 키 검증
        if not self.gemini_api_key:
            validation_result["warnings"].append("GEMINI_API_KEY가 설정되지 않았습니다. 문제지 생성 기능이 작동하지 않습니다.")
        elif self.gemini_api_key == "your_gemini_api_key_here":
            validation_result["warnings"].append("GEMINI_API_KEY가 예시 키입니다. 실제 키로 교체하세요.")
        
        # 시크릿 키 검증 (프로덕션 환경)
        if self.is_production() and self.secret_key == "your-secret-key-change-this-in-production":
            validation_result["errors"].append("프로덕션 환경에서는 SECRET_KEY를 반드시 변경해야 합니다.")
            validation_result["valid"] = False
        
        return validation_result


# 전역 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스를 반환하는 의존성 함수"""
    return settings


def print_settings_summary():
    """설정 요약을 출력"""
    validation = settings.validate_required_settings()
    
    print("\n" + "="*80)
    print("🔧 애플리케이션 설정 요약")
    print("="*80)
    
    print(f"📱 애플리케이션: {settings.app_name} v{settings.app_version}")
    print(f"🌐 서버: {settings.host}:{settings.port}")
    print(f"🗄️  데이터베이스: {settings.get_masked_database_url()}")
    print(f"🤖 Gemini API: {settings.get_masked_api_key()}")
    print(f"📊 최대 문제 수: {settings.max_questions_per_worksheet}")
    print(f"⏰ 최대 시험 시간: {settings.max_worksheet_duration}분")
    print(f"🔒 환경: {'Production' if settings.is_production() else 'Development'}")
    
    if validation["errors"]:
        print("\n❌ 오류:")
        for error in validation["errors"]:
            print(f"   • {error}")
    
    if validation["warnings"]:
        print("\n⚠️  경고:")
        for warning in validation["warnings"]:
            print(f"   • {warning}")
    
    if validation["valid"] and not validation["warnings"]:
        print("\n✅ 모든 설정이 올바르게 구성되었습니다!")
    
    print("="*80 + "\n")
    
    return validation
