from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from app.database import get_db
from app.models.user import Teacher, Student
from app.schemas.auth import (
    TeacherSignup, StudentSignup, UserLogin, Token,
    TeacherResponse, StudentResponse, TeacherStatistics,
    StudentStatistics, RecentActivity
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

@router.post("/check-email")
async def check_email(email_data: dict, db: Session = Depends(get_db)):
    """이메일 중복 체크 전용 API"""
    email = email_data.get("email", "").strip()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )

    # Teacher와 Student 테이블 모두에서 중복 체크
    existing_teacher = db.query(Teacher).filter(Teacher.email == email).first()
    existing_student = db.query(Student).filter(Student.email == email).first()

    is_available = not (existing_teacher or existing_student)

    return {
        "available": is_available,
        "message": "Email is available" if is_available else "Email already exists"
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

@router.get("/teacher/statistics", response_model=TeacherStatistics)
async def get_teacher_statistics(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """선생님 활동 통계 조회"""
    teacher_id = current_teacher.id

    # 생성한 문제 수 (math, korean, english 서비스의 worksheets 테이블 합산)
    worksheet_count_query = text("""
        SELECT
            COALESCE((SELECT COUNT(*) FROM math_service.worksheets WHERE teacher_id = :teacher_id), 0) +
            COALESCE((SELECT COUNT(*) FROM korean_service.worksheets WHERE teacher_id = :teacher_id), 0) +
            COALESCE((SELECT COUNT(*) FROM english_service.worksheets WHERE teacher_id = :teacher_id), 0) as total
    """)
    worksheet_result = db.execute(worksheet_count_query, {"teacher_id": teacher_id}).fetchone()
    created_worksheets = worksheet_result[0] if worksheet_result else 0

    # 관리 중인 반 수
    total_classrooms = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    classroom_count = len(total_classrooms.classrooms) if total_classrooms and total_classrooms.classrooms else 0

    # 총 학생 수 (승인된 학생만)
    total_students_query = text("""
        SELECT COUNT(DISTINCT sjr.student_id)
        FROM auth_service.student_join_requests sjr
        JOIN auth_service.classrooms c ON sjr.classroom_id = c.id
        WHERE c.teacher_id = :teacher_id AND sjr.status = 'approved'
    """)
    students_result = db.execute(total_students_query, {"teacher_id": teacher_id}).fetchone()
    total_students = students_result[0] if students_result else 0

    return TeacherStatistics(
        created_worksheets=created_worksheets,
        total_classrooms=classroom_count,
        total_students=total_students
    )

@router.get("/student/statistics", response_model=StudentStatistics)
async def get_student_statistics(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """학생 활동 통계 조회"""
    student_id = current_student.id
    print(f"[DEBUG] Fetching statistics for student_id: {student_id}")

    # 완료한 과제 수 (grading_sessions/grading_results 테이블 합산)
    # Note: English service uses grading_results with student_id column instead of graded_by
    completed_query = text("""
        SELECT
            COALESCE((SELECT COUNT(*) FROM math_service.grading_sessions WHERE graded_by = :student_id), 0) +
            COALESCE((SELECT COUNT(*) FROM korean_service.grading_sessions WHERE graded_by = :student_id), 0) +
            COALESCE((SELECT COUNT(*) FROM english_service.grading_results WHERE student_id = :student_id), 0) as total
    """)
    completed_result = db.execute(completed_query, {"student_id": student_id}).fetchone()
    completed_assignments = completed_result[0] if completed_result else 0
    print(f"[DEBUG] Completed assignments: {completed_assignments}")

    # 참여 중인 반 수
    joined_classrooms_query = text("""
        SELECT COUNT(*)
        FROM auth_service.student_join_requests
        WHERE student_id = :student_id AND status = 'approved'
    """)
    classroom_result = db.execute(joined_classrooms_query, {"student_id": student_id}).fetchone()
    joined_classrooms = classroom_result[0] if classroom_result else 0
    print(f"[DEBUG] Joined classrooms: {joined_classrooms}")

    # 평균 정답률 계산
    # Note: English service uses grading_results with total_score/max_score columns
    average_score_query = text("""
        SELECT
            CASE
                WHEN COUNT(*) = 0 THEN 0
                ELSE ROUND(CAST(AVG(score_percent) AS NUMERIC), 1)
            END as avg_score
        FROM (
            SELECT (total_score::float / max_possible_score * 100) as score_percent
            FROM math_service.grading_sessions
            WHERE graded_by = :student_id AND max_possible_score > 0
            UNION ALL
            SELECT (total_score::float / max_possible_score * 100) as score_percent
            FROM korean_service.grading_sessions
            WHERE graded_by = :student_id AND max_possible_score > 0
            UNION ALL
            SELECT (total_score::float / max_score * 100) as score_percent
            FROM english_service.grading_results
            WHERE student_id = :student_id AND max_score > 0
        ) as all_sessions
    """)
    score_result = db.execute(average_score_query, {"student_id": student_id}).fetchone()
    average_score = float(score_result[0]) if score_result and score_result[0] is not None else 0.0
    print(f"[DEBUG] Average score: {average_score}")

    result = StudentStatistics(
        completed_assignments=completed_assignments,
        joined_classrooms=joined_classrooms,
        average_score=average_score
    )
    print(f"[DEBUG] Returning result: {result}")
    return result

@router.get("/teacher/recent-activities")
async def get_teacher_recent_activities(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """선생님 최근 활동 조회"""
    teacher_id = current_teacher.id

    # 최근 생성한 worksheets 조회
    # Note: English service has different table structure (worksheet_id, worksheet_name, no status column)
    recent_worksheets_query = text("""
        SELECT id, title, created_at, 'math' as service_type
        FROM math_service.worksheets
        WHERE teacher_id = :teacher_id AND status = 'COMPLETED'
        UNION ALL
        SELECT id, title, created_at, 'korean' as service_type
        FROM korean_service.worksheets
        WHERE teacher_id = :teacher_id AND status = 'COMPLETED'
        UNION ALL
        SELECT worksheet_id as id, worksheet_name as title, created_at, 'english' as service_type
        FROM english_service.worksheets
        WHERE teacher_id = :teacher_id
        ORDER BY created_at DESC
        LIMIT :limit
    """)

    results = db.execute(recent_worksheets_query, {"teacher_id": teacher_id, "limit": limit}).fetchall()

    activities = []
    for row in results:
        subject_map = {"math": "수학", "korean": "국어", "english": "영어"}
        subject = subject_map.get(row[3], row[3])
        activities.append({
            "id": row[0],
            "description": f"{subject} 문제 생성: {row[1]}",
            "timestamp": row[2],
            "activity_type": "worksheet"
        })

    return activities

@router.get("/student/recent-activities")
async def get_student_recent_activities(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """학생 최근 활동 조회"""
    student_id = current_student.id
    print(f"[DEBUG] Fetching recent activities for student_id: {student_id}")

    # 최근 채점 세션 조회
    # Note: English service uses grading_results (not grading_sessions) with different column names
    recent_grading_query = text("""
        SELECT gs.id, w.title, gs.graded_at, gs.total_score, gs.max_possible_score, 'math' as service_type
        FROM math_service.grading_sessions gs
        JOIN math_service.worksheets w ON gs.worksheet_id = w.id
        WHERE gs.graded_by = :student_id
        UNION ALL
        SELECT gs.id, w.title, gs.graded_at, gs.total_score, gs.max_possible_score, 'korean' as service_type
        FROM korean_service.grading_sessions gs
        JOIN korean_service.worksheets w ON gs.worksheet_id = w.id
        WHERE gs.graded_by = :student_id
        UNION ALL
        SELECT gr.result_id as id, w.worksheet_name as title, gr.created_at as graded_at,
               gr.total_score, gr.max_score as max_possible_score, 'english' as service_type
        FROM english_service.grading_results gr
        JOIN english_service.worksheets w ON gr.worksheet_id = w.worksheet_id
        WHERE gr.student_id = :student_id
        ORDER BY graded_at DESC
        LIMIT :limit
    """)

    results = db.execute(recent_grading_query, {"student_id": student_id, "limit": limit}).fetchall()
    print(f"[DEBUG] Found {len(results)} recent activities")

    activities = []
    for row in results:
        subject_map = {"math": "수학", "korean": "국어", "english": "영어"}
        subject = subject_map.get(row[5], row[5])
        score_percent = round((row[3] / row[4] * 100), 1) if row[4] > 0 else 0
        activities.append({
            "id": row[0],
            "description": f"{subject} 과제 완료: {row[1]} ({score_percent}점)",
            "timestamp": row[2],
            "activity_type": "grading"
        })

    print(f"[DEBUG] Returning {len(activities)} activities: {activities}")
    return activities