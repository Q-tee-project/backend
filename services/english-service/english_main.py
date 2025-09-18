from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from app.database import init_db
from app.core.config import get_settings, print_settings_summary
from app.routers.health_router import router as health_router
from app.routers.category_router import router as category_router
from app.routers.worksheet_router import router as worksheet_router
from app.routers.grading_router import router as grading_router

# 설정 인스턴스 가져오기
settings = get_settings()

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",  # Swagger UI 경로
    redoc_url="/redoc",  # ReDoc 경로
    openapi_url="/api/v1/openapi.json",  # OpenAPI JSON 경로
    openapi_tags=[
        {
            "name": "Health",
            "description": "서버 및 데이터베이스 상태 확인"
        },
        {
            "name": "Categories", 
            "description": "문법, 어휘, 독해 카테고리 조회"
        },
        {
            "name": "Worksheets",
            "description": "문제지 생성, 관리 및 편집 기능"
        },
        {
            "name": "Grading",
            "description": "답안 제출, 채점 및 결과 관리"
        }
    ]
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

# API v1 라우터 등록 (깔끔한 단일 버전)
app.include_router(health_router, prefix="/api/v1")
app.include_router(category_router, prefix="/api/v1")
app.include_router(worksheet_router, prefix="/api/v1")
app.include_router(grading_router, prefix="/api/v1")

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
