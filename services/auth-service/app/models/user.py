from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from .base import Base

class SchoolLevel(str, Enum):
    MIDDLE = "middle"
    HIGH = "high"

class Grade(int, Enum):
    GRADE_1 = 1
    GRADE_2 = 2
    GRADE_3 = 3

class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    classrooms = relationship("ClassRoom", back_populates="teacher")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    parent_phone = Column(String, nullable=False)
    school_level = Column(SQLEnum(SchoolLevel), nullable=False)
    grade = Column(Integer, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    join_requests = relationship("StudentJoinRequest", back_populates="student")

class ClassRoom(Base):
    __tablename__ = "classrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    school_level = Column(SQLEnum(SchoolLevel), nullable=False)
    grade = Column(Integer, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    class_code = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    teacher = relationship("Teacher", back_populates="classrooms")
    join_requests = relationship("StudentJoinRequest", back_populates="classroom")

class StudentJoinRequest(Base):
    __tablename__ = "student_join_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    student = relationship("Student", back_populates="join_requests")
    classroom = relationship("ClassRoom", back_populates="join_requests")