from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Teacher, Student, ClassRoom, StudentJoinRequest
from app.schemas.classroom import (
    ClassroomCreate, ClassroomResponse, ClassroomUpdate, StudentJoinRequestCreate,
    StudentJoinRequestResponse, StudentDirectRegister, JoinRequestApproval,
    ClassroomWithTeacherResponse
)
from app.schemas.auth import StudentResponse
from app.routers.auth import get_current_teacher, get_current_student
from app.services.classroom_service import (
    create_classroom_with_code, get_classroom_by_code, create_join_request,
    get_pending_join_requests_for_teacher, approve_or_reject_join_request,
    get_student_classrooms
)
from app.services.auth_service import get_password_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=ClassroomResponse)
async def create_classroom(
    classroom_data: ClassroomCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    classroom = create_classroom_with_code(
        db=db,
        classroom_data=classroom_data.dict(),
        teacher_id=current_teacher.id
    )
    return classroom

@router.get("/my-classrooms", response_model=List[ClassroomResponse])
async def get_my_classrooms(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """선생님용: 내가 생성한 클래스 목록 조회"""
    classrooms = db.query(ClassRoom).filter(
        ClassRoom.teacher_id == current_teacher.id,
        ClassRoom.is_active == True
    ).all()
    return classrooms

@router.get("/my-classrooms/student", response_model=List[ClassroomResponse])
async def get_student_classrooms_endpoint(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """학생용: 내가 가입한 클래스 목록 조회"""
    classrooms = get_student_classrooms(db, current_student.id)
    return classrooms

@router.get("/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    classroom = db.query(ClassRoom).filter(
        ClassRoom.id == classroom_id,
        ClassRoom.teacher_id == current_teacher.id,
        ClassRoom.is_active == True
    ).first()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    return classroom

@router.post("/join-request", response_model=StudentJoinRequestResponse)
async def create_join_request_endpoint(
    request_data: StudentJoinRequestCreate,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    classroom = get_classroom_by_code(db, request_data.class_code)
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid class code"
        )
    
    join_request = create_join_request(db, current_student.id, classroom.id)
    if not join_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Join request already exists"
        )
    
    return join_request

@router.get("/join-requests/pending", response_model=List[StudentJoinRequestResponse])
async def get_pending_requests(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    requests = get_pending_join_requests_for_teacher(db, current_teacher.id)
    return requests

@router.put("/join-requests/{request_id}/approve", response_model=StudentJoinRequestResponse)
async def approve_join_request(
    request_id: int,
    approval_data: JoinRequestApproval,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    # Verify that the request belongs to teacher's classroom
    join_request = db.query(StudentJoinRequest).join(ClassRoom).filter(
        StudentJoinRequest.id == request_id,
        ClassRoom.teacher_id == current_teacher.id
    ).first()
    
    if not join_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Join request not found"
        )
    
    updated_request = approve_or_reject_join_request(db, request_id, approval_data.status)
    return updated_request

@router.post("/{classroom_id}/students/register", response_model=StudentResponse)
async def register_student_directly(
    classroom_id: int,
    student_data: StudentDirectRegister,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    # Verify classroom belongs to teacher
    classroom = db.query(ClassRoom).filter(
        ClassRoom.id == classroom_id,
        ClassRoom.teacher_id == current_teacher.id
    ).first()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    # Check if email already exists
    existing_student = db.query(Student).filter(Student.email == student_data.email).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate username from email (or use a different strategy)
    username = student_data.email.split('@')[0]
    counter = 1
    original_username = username
    while db.query(Student).filter(Student.username == username).first():
        username = f"{original_username}{counter}"
        counter += 1
    
    # Create student with default password (they should change it)
    default_password = "student123"  # In production, generate a random password and send via email
    hashed_password = get_password_hash(default_password)
    
    student = Student(
        username=username,
        email=student_data.email,
        name=student_data.name,
        phone=student_data.phone,
        parent_phone=student_data.parent_phone,
        school_level=classroom.school_level,
        grade=classroom.grade,
        hashed_password=hashed_password
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    # Auto-approve the student to the classroom
    join_request = StudentJoinRequest(
        student_id=student.id,
        classroom_id=classroom_id,
        status="approved",
        processed_at=datetime.utcnow()
    )
    
    db.add(join_request)
    db.commit()
    
    return student

@router.get("/{classroom_id}/students", response_model=List[StudentResponse])
async def get_classroom_students(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    try:
        # First, let's check if the classroom exists at all
        classroom_exists = db.query(ClassRoom).filter(ClassRoom.id == classroom_id).first()
        if not classroom_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Classroom with id {classroom_id} does not exist"
            )
        
        # Check if classroom belongs to teacher
        if classroom_exists.teacher_id != current_teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Classroom {classroom_id} does not belong to teacher {current_teacher.id}"
            )
        
        # Get approved students in the classroom
        students = db.query(Student).join(StudentJoinRequest).filter(
            StudentJoinRequest.classroom_id == classroom_id,
            StudentJoinRequest.status == "approved"
        ).all()
        
        return students
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


# ===== 새로운 클래스룸 관리 API =====

@router.put("/{classroom_id}", response_model=ClassroomResponse)
async def update_classroom(
    classroom_id: int,
    classroom_update: ClassroomUpdate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """클래스룸 정보 수정 (교사만 가능)"""
    try:
        # 클래스룸 존재 확인
        classroom = db.query(ClassRoom).filter(ClassRoom.id == classroom_id).first()
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="클래스룸을 찾을 수 없습니다"
            )

        # 교사 권한 확인
        if classroom.teacher_id != current_teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 클래스룸을 수정할 권한이 없습니다"
            )

        # 클래스룸 정보 업데이트
        update_data = classroom_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(classroom, field, value)

        db.commit()
        db.refresh(classroom)

        logger.info(f"Teacher {current_teacher.id} updated classroom {classroom_id}")
        return classroom

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating classroom {classroom_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"클래스룸 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{classroom_id}")
async def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """클래스룸 삭제 (교사만 가능)"""
    try:
        # 클래스룸 존재 확인
        classroom = db.query(ClassRoom).filter(ClassRoom.id == classroom_id).first()
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="클래스룸을 찾을 수 없습니다"
            )

        # 교사 권한 확인
        if classroom.teacher_id != current_teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 클래스룸을 삭제할 권한이 없습니다"
            )

        # 소프트 삭제 (is_active = False)
        classroom.is_active = False
        db.commit()

        logger.info(f"Teacher {current_teacher.id} deleted classroom {classroom_id}")
        return {"message": "클래스룸이 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting classroom {classroom_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"클래스룸 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/student/{student_id}/classrooms-with-teachers", response_model=List[ClassroomWithTeacherResponse])
async def get_student_classrooms_with_teachers(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """학생의 클래스룸 목록과 교사 정보 조회 (본인만 가능)"""
    try:
        # 본인 확인
        if current_student.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 정보만 조회할 수 있습니다"
            )

        # 학생이 승인된 클래스룸 목록 조회 (교사 정보 포함)
        classrooms = db.query(ClassRoom).join(
            StudentJoinRequest,
            ClassRoom.id == StudentJoinRequest.classroom_id
        ).join(
            Teacher,
            ClassRoom.teacher_id == Teacher.id
        ).filter(
            StudentJoinRequest.student_id == student_id,
            StudentJoinRequest.status == "approved",
            ClassRoom.is_active == True
        ).all()

        # 각 클래스룸에 교사 정보 포함하여 응답
        result = []
        for classroom in classrooms:
            classroom_data = {
                "id": classroom.id,
                "name": classroom.name,
                "school_level": classroom.school_level,
                "grade": classroom.grade,
                "class_code": classroom.class_code,
                "is_active": classroom.is_active,
                "created_at": classroom.created_at,
                "teacher": {
                    "id": classroom.teacher.id,
                    "username": classroom.teacher.username,
                    "name": classroom.teacher.name,
                    "email": classroom.teacher.email,
                    "phone": classroom.teacher.phone,
                    "is_active": classroom.teacher.is_active,
                    "created_at": classroom.teacher.created_at
                }
            }
            result.append(classroom_data)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting classrooms for student {student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"클래스룸 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )