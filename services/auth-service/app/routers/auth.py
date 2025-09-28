from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Teacher, Student
from app.schemas.auth import (
    TeacherSignup, StudentSignup, UserLogin, Token, 
    TeacherResponse, StudentResponse
)
from app.services.auth_service import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()
security = HTTPBearer()

@router.post("/teacher/signup", response_model=TeacherResponse)
async def teacher_signup(teacher_data: TeacherSignup, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_teacher = db.query(Teacher).filter(
        (Teacher.username == teacher_data.username) | (Teacher.email == teacher_data.email)
    ).first()
    
    if existing_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new teacher
    hashed_password = get_password_hash(teacher_data.password)
    teacher = Teacher(
        username=teacher_data.username,
        email=teacher_data.email,
        name=teacher_data.name,
        phone=teacher_data.phone,
        hashed_password=hashed_password
    )
    
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    
    return teacher

@router.post("/student/signup", response_model=StudentResponse)
async def student_signup(student_data: StudentSignup, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_student = db.query(Student).filter(
        (Student.username == student_data.username) | (Student.email == student_data.email)
    ).first()
    
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new student
    hashed_password = get_password_hash(student_data.password)
    student = Student(
        username=student_data.username,
        email=student_data.email,
        name=student_data.name,
        phone=student_data.phone,
        parent_phone=student_data.parent_phone,
        school_level=student_data.school_level,
        grade=student_data.grade,
        hashed_password=hashed_password
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    return student

@router.post("/teacher/login", response_model=Token)
async def teacher_login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.username, login_data.password, "teacher")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "type": "teacher"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/student/login", response_model=Token)
async def student_login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.username, login_data.password, "student")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "type": "student"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_teacher(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    return await get_current_user(credentials.credentials, db, "teacher")

async def get_current_student(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    return await get_current_user(credentials.credentials, db, "student")

@router.get("/teacher/me", response_model=TeacherResponse)
async def get_teacher_profile(current_teacher: Teacher = Depends(get_current_teacher)):
    return current_teacher

@router.get("/student/me", response_model=StudentResponse)
async def get_student_profile(current_student: Student = Depends(get_current_student)):
    return current_student

@router.get("/students/{student_id}", response_model=StudentResponse)
async def get_student_by_id(
    student_id: int,
    db: Session = Depends(get_db)
):
    """특정 학생 정보 조회 (과제 결과 표시용)"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )
    return student