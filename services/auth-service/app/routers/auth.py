from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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

@router.post("/check-username")
async def check_username(username_data: dict, db: Session = Depends(get_db)):
    """아이디 중복 체크 전용 API"""
    username = username_data.get("username", "").strip()

    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required"
        )

    # Teacher와 Student 테이블 모두에서 중복 체크
    existing_teacher = db.query(Teacher).filter(Teacher.username == username).first()
    existing_student = db.query(Student).filter(Student.username == username).first()

    is_available = not (existing_teacher or existing_student)

    return {
        "available": is_available,
        "message": "Username is available" if is_available else "Username already exists"
    }

@router.post("/teacher/signup", response_model=TeacherResponse)
async def teacher_signup(teacher_data: TeacherSignup, db: Session = Depends(get_db)):
    existing_teacher = db.query(Teacher).filter(
        (Teacher.username == teacher_data.username) | (Teacher.email == teacher_data.email)
    ).first()

    if existing_teacher:
        if existing_teacher.username == teacher_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

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
    existing_student = db.query(Student).filter(
        (Student.username == student_data.username) | (Student.email == student_data.email)
    ).first()

    if existing_student:
        if existing_student.username == student_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

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

@router.get("/teachers/all")
async def get_all_teachers(db: Session = Depends(get_db)):
    """모든 활성 선생님 목록 조회 (마켓 알림용)"""
    teachers = db.query(Teacher).all()
    return [{"id": t.id, "name": t.name, "email": t.email} for t in teachers]

@router.post("/verify-token")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """다른 마이크로서비스에서 JWT 토큰 검증용"""
    try:
        teacher = await get_current_user(credentials.credentials, db, "teacher")
        return {
            "valid": True,
            "user_id": teacher.id,
            "user_type": "teacher",
            "username": teacher.username,
            "name": teacher.name,
            "email": teacher.email
        }
    except Exception:
        try:
            student = await get_current_user(credentials.credentials, db, "student")
            return {
                "valid": True,
                "user_id": student.id,
                "user_type": "student",
                "username": student.username,
                "name": student.name,
                "email": student.email,
                "school_level": student.school_level.value,
                "grade": student.grade
            }
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )