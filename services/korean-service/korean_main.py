from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import korean_generation
from app.database import engine
from app.models import Base
# Import all models to ensure they are registered with Base.metadata
import app.models.worksheet
import app.models.problem
import app.models.korean_generation
import app.models.grading_result

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Korean Problem Generation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "file://", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(korean_generation.router, prefix="/api/korean-generation", tags=["korean-generation"])

@app.get("/")
async def root():
    return {"message": "Korean Problem Generation API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)