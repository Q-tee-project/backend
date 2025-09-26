from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_router, classroom_router, message_router
from app.database import engine
from app.models.base import Base

# Import all models to ensure they are registered with Base.metadata
from app.models.user import Teacher, Student, ClassRoom, StudentJoinRequest
from app.models.message import Message

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "file://", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(classroom_router, prefix="/api/classrooms", tags=["classrooms"])
app.include_router(message_router, prefix="/api/messages", tags=["messages"])

@app.get("/")
async def root():
    return {"message": "Auth Service API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)