import random
import string
from sqlalchemy.orm import Session
from app.models.user import ClassRoom, Student, StudentJoinRequest
from app.services.redis_client import get_redis_client

def generate_class_code(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_classroom_with_code(db: Session, classroom_data: dict, teacher_id: int):
    class_code = generate_class_code()
    
    # Ensure unique class code
    while db.query(ClassRoom).filter(ClassRoom.class_code == class_code).first():
        class_code = generate_class_code()
    
    classroom = ClassRoom(
        name=classroom_data["name"],
        school_level=classroom_data["school_level"],
        grade=classroom_data["grade"],
        teacher_id=teacher_id,
        class_code=class_code
    )
    
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    
    # Store class code in Redis with class_id as value
    redis_client = get_redis_client()
    redis_client.set(f"class_code:{class_code}", classroom.id, ex=86400 * 365)  # 1 year expiry
    
    return classroom

def get_classroom_by_code(db: Session, class_code: str):
    return db.query(ClassRoom).filter(ClassRoom.class_code == class_code).first()

def create_join_request(db: Session, student_id: int, classroom_id: int):
    # Check if request already exists
    existing_request = db.query(StudentJoinRequest).filter(
        StudentJoinRequest.student_id == student_id,
        StudentJoinRequest.classroom_id == classroom_id,
        StudentJoinRequest.status == "pending"
    ).first()
    
    if existing_request:
        return None  # Request already exists
    
    join_request = StudentJoinRequest(
        student_id=student_id,
        classroom_id=classroom_id,
        status="pending"
    )
    
    db.add(join_request)
    db.commit()
    db.refresh(join_request)
    
    return join_request

def get_pending_join_requests_for_teacher(db: Session, teacher_id: int):
    return db.query(StudentJoinRequest).join(ClassRoom).filter(
        ClassRoom.teacher_id == teacher_id,
        StudentJoinRequest.status == "pending"
    ).all()

def approve_or_reject_join_request(db: Session, request_id: int, status: str):
    join_request = db.query(StudentJoinRequest).filter(StudentJoinRequest.id == request_id).first()
    if not join_request:
        return None
    
    join_request.status = status
    join_request.processed_at = db.query(StudentJoinRequest).first().requested_at.__class__.utcnow()
    
    db.commit()
    db.refresh(join_request)
    
    return join_request