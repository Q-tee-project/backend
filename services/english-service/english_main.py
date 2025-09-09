from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv
from database import init_db
from routes import router

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="Test API Server",
    description="FastAPI와 PostgreSQL을 사용한 테스트 서버입니다.",
    version="1.0.0"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (HTML, CSS, JS 등)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록
app.include_router(router)

# 루트 경로에서 HTML 페이지 제공
@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse('static/index.html')

# 환경변수 로드 및 설정 확인
def check_environment():
    """환경변수 설정 상태를 확인하고 출력합니다."""
    load_dotenv()
    
    print("\n" + "="*80)
    print("🔧 환경변수 설정 확인")
    print("="*80)
    
    # 데이터베이스 URL 확인
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # 비밀번호 부분은 마스킹하여 출력
        masked_url = database_url.replace(database_url.split('@')[0].split(':')[-1], "****")
        print(f"✅ DATABASE_URL: {masked_url}")
    else:
        print("❌ DATABASE_URL: 설정되지 않음")
    
    # Gemini API 키 확인
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        if gemini_api_key == "your_gemini_api_key_here":
            print("⚠️  GEMINI_API_KEY: 예시 키가 설정됨 (실제 키로 교체 필요)")
        else:
            # API 키 앞 4자리와 뒤 4자리만 표시
            masked_key = f"{gemini_api_key[:4]}{'*' * (len(gemini_api_key) - 8)}{gemini_api_key[-4:]}"
            print(f"✅ GEMINI_API_KEY: {masked_key}")
    else:
        print("❌ GEMINI_API_KEY: 설정되지 않음")
    
    print("="*80 + "\n")
    
    return database_url, gemini_api_key

# 애플리케이션 시작 시 환경변수 확인 및 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    # 환경변수 확인
    database_url, gemini_api_key = check_environment()
    
    # 필수 환경변수 누락 시 경고
    if not database_url:
        print("⚠️  경고: DATABASE_URL이 설정되지 않았습니다. 데이터베이스 연결이 실패할 수 있습니다.")
    
    if not gemini_api_key:
        print("⚠️  경고: GEMINI_API_KEY가 설정되지 않았습니다. 문제지 생성 기능이 작동하지 않습니다.")
    
    # 데이터베이스 초기화
    try:
        init_db()
        print("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        print("⚠️  데이터베이스 설정을 확인해주세요.")

# 서버 실행 설정
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 모드에서 파일 변경 시 자동 재시작
    )
