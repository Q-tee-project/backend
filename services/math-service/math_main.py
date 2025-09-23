from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import Base
from app.routers import curriculum, worksheet, grading, assignment, problem, task, market_integration, problem_validation, test_session

# Import all models to ensure they are registered with Base.metadata
import app.models.worksheet
import app.models.problem
import app.models.math_generation
import app.models.grading_result
import app.models.curriculum
import app.models.user
import app.models.problem_validation

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Math Problem Generation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "file://", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Create API router with /api prefix to match Korean service structure
api_router = APIRouter(prefix="/api")

api_router.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])
api_router.include_router(worksheet.router, prefix="/worksheets", tags=["worksheets"])
api_router.include_router(grading.router, prefix="/grading", tags=["grading"])
api_router.include_router(assignment.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(problem.router, prefix="/problems", tags=["problems"])
api_router.include_router(task.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(market_integration.router, prefix="/market-integration", tags=["market-integration"])
api_router.include_router(problem_validation.router, prefix="/validation", tags=["validation"])
api_router.include_router(test_session.router, prefix="/test-sessions", tags=["test-sessions"])

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Math Problem Generation API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)