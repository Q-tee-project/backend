"""
로컬 개발용 실행 스크립트 (정리된 API 문서 버전)
"""
import uvicorn
import os
from pathlib import Path

# .env 파일 경로 확인
env_file = Path(__file__).parent / ".env"
if not env_file.exists():
    print("⚠️  .env 파일이 없습니다.")
    print("📝 다음 내용으로 .env 파일을 생성해주세요:")
    print()
    print("DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/english_service")
    print("GEMINI_API_KEY=your_actual_gemini_api_key_here")
    print("HOST=127.0.0.1")
    print("PORT=8000")
    print("DEBUG=true")
    print("RELOAD=true")
    print("SECRET_KEY=local-dev-english-service-key")
    print()
    exit(1)

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    print("🚀 영어 서비스 로컬 개발 서버 시작...")
    print("📂 현재 디렉토리:", os.getcwd())
    print("🌐 서버 주소: http://127.0.0.1:8000")
    print("📚 API 문서 (정리된 버전): http://127.0.0.1:8000/docs")
    print("📖 ReDoc 문서: http://127.0.0.1:8000/redoc")
    print("🔄 핫 리로드: 활성화")
    print("🐛 디버그 모드: 활성화")
    print("─" * 50)
    print("🎯 정리 완료:")
    print("  • 중복 라우터 제거")
    print("  • API 문서 깔끔하게 정리")
    print("  • 18개 필수 엔드포인트만 유지")
    print("  • 모든 엔드포인트 /api/v1/* 통일")
    print("─" * 50)
    
    uvicorn.run(
        "english_main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # 파일 변경시 자동 재시작
        reload_dirs=["./"],  # 현재 디렉토리 감시
        debug=True,  # 디버그 모드
        log_level="debug",  # 상세 로그
    )
