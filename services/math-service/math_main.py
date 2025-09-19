from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import Base
from app.routers import curriculum, worksheet, grading, assignment, problem, task, market_integration

# Import all models to ensure they are registered with Base.metadata
import app.models.worksheet
import app.models.problem
import app.models.math_generation
import app.models.grading_result
import app.models.curriculum
import app.models.user

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Math Problem Generation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "file://", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])
app.include_router(worksheet.router, tags=["worksheets"])
app.include_router(grading.router, prefix="/grading", tags=["grading"])
app.include_router(assignment.router, prefix="/assignments", tags=["assignments"])
app.include_router(problem.router, prefix="/problems", tags=["problems"])
app.include_router(task.router, prefix="/tasks", tags=["tasks"])
app.include_router(market_integration.router, tags=["market-integration"])

@app.get("/")
async def root():
    return {"message": "Math Problem Generation API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)