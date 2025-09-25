from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "auth_service"}

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sender_id = Column(Integer, nullable=False)  # 발신자 ID (Teacher 또는 Student)
    sender_type = Column(String, nullable=False)  # 'teacher' 또는 'student'
    recipient_id = Column(Integer, nullable=False)  # 수신자 ID (Teacher 또는 Student)
    recipient_type = Column(String, nullable=False)  # 'teacher' 또는 'student'
    classroom_id = Column(Integer, ForeignKey("auth_service.classrooms.id"), nullable=False)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

    classroom = relationship("ClassRoom")