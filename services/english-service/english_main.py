from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from app.database import init_db
from app.core.config import get_settings, print_settings_summary
from app.api.v1.health_router import router as health_router
from app.api.v1.category_router import router as category_router
from app.api.v1.worksheet_router import router as worksheet_router
from app.api.v1.grading_router import router as grading_router

# 설정 인스턴스 가져오기
settings = get_settings()

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# 정적 파일 서빙 (HTML, CSS, JS 등)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록 (v1 API)
app.include_router(health_router, prefix="/api/v1")
app.include_router(category_router, prefix="/api/v1")
app.include_router(worksheet_router, prefix="/api/v1")
app.include_router(grading_router, prefix="/api/v1")

# 기존 호환성을 위한 라우터 등록 (prefix 없이)
app.include_router(health_router)
app.include_router(category_router)  
app.include_router(worksheet_router)
app.include_router(grading_router)

# 루트 경로에서 HTML 페이지 제공
@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse('static/index.html')

# 애플리케이션 시작 시 설정 확인 및 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    # 설정 요약 출력 및 검증
    validation_result = print_settings_summary()
    
    # 치명적인 오류가 있으면 종료
    if not validation_result["valid"]:
        print("❌ 애플리케이션을 시작할 수 없습니다. 설정을 확인해주세요.")
        import sys
        sys.exit(1)
    
    # 데이터베이스 초기화
    try:
        init_db()
        print("✅ 데이터베이스 초기화 완료")
        
        # 초기 데이터 import
        from init_all_data import init_all_data
        init_all_data()
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        print("⚠️  데이터베이스 설정을 확인해주세요.")

# 서버 실행 설정
if __name__ == "__main__":
    uvicorn.run(
        "english_main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload  # 개발 모드에서 파일 변경 시 자동 재시작
    )
