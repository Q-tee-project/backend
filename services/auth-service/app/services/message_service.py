from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Tuple
from ..models.message import Message
from ..models.user import Teacher, Student, ClassRoom, StudentJoinRequest
from ..schemas.message import MessageSendRequest, MessageRecipient, MessageResponse
from datetime import datetime
import math
import httpx
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service_url = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:8003')

    async def _send_notification_to_service(self, notification_data: dict) -> bool:
        """notification-service로 알림 전송"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.notification_service_url}/api/notifications/message",
                    json=notification_data
                )
                response.raise_for_status()
                logger.info(f"Notification sent successfully for message {notification_data['message_id']}")
                return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    def get_user_classrooms(self, user_id: int, user_type: str) -> List[int]:
        """사용자가 속한 클래스룸 ID 목록 반환"""
        if user_type == "teacher":
            classrooms = self.db.query(ClassRoom).filter(ClassRoom.teacher_id == user_id).all()
            return [classroom.id for classroom in classrooms]
        elif user_type == "student":
            # 승인된 가입 요청만 조회
            join_requests = self.db.query(StudentJoinRequest).filter(
                and_(
                    StudentJoinRequest.student_id == user_id,
                    StudentJoinRequest.status == "approved"
                )
            ).all()
            return [req.classroom_id for req in join_requests]
        return []

    def validate_message_permission(self, sender_id: int, sender_type: str,
                                  receiver_id: int, receiver_type: str) -> bool:
        """쪽지 전송 권한 검증 (같은 클래스 내 선생-학생만 가능)"""
        sender_classrooms = set(self.get_user_classrooms(sender_id, sender_type))
        receiver_classrooms = set(self.get_user_classrooms(receiver_id, receiver_type))

        # 공통 클래스룸이 있고, 선생-학생 관계인지 확인
        common_classrooms = sender_classrooms & receiver_classrooms
        if not common_classrooms:
            return False

        # 같은 타입끼리는 메시지 불가 (학생-학생, 선생-선생 불가)
        if sender_type == receiver_type:
            return False

        return True

    def get_message_recipients(self, user_id: int, user_type: str) -> List[MessageRecipient]:
        """메시지를 보낼 수 있는 대상 목록 조회"""
        classrooms = self.get_user_classrooms(user_id, user_type)
        recipients = []

        for classroom_id in classrooms:
            if user_type == "teacher":
                # 선생님은 해당 클래스의 학생들에게 메시지 전송 가능
                students = self.db.query(Student).join(StudentJoinRequest).filter(
                    and_(
                        StudentJoinRequest.classroom_id == classroom_id,
                        StudentJoinRequest.status == "approved"
                    )
                ).all()

                for student in students:
                    recipients.append(MessageRecipient(
                        id=student.id,
                        name=student.name,
                        email=student.email,
                        phone=student.phone,
                        type="student",
                        school_level=student.school_level.value,
                        grade=student.grade
                    ))

            elif user_type == "student":
                # 학생은 해당 클래스의 선생님에게 메시지 전송 가능
                classroom = self.db.query(ClassRoom).filter(ClassRoom.id == classroom_id).first()
                if classroom and classroom.teacher:
                    teacher = classroom.teacher
                    recipients.append(MessageRecipient(
                        id=teacher.id,
                        name=teacher.name,
                        email=teacher.email,
                        phone=teacher.phone,
                        type="teacher"
                    ))

        return recipients

    async def send_message_async(self, sender_id: int, sender_type: str,
                                message_request: MessageSendRequest) -> List[Message]:
        """메시지 전송 (비동기)"""
        sent_messages = []

        for receiver_id in message_request.recipient_ids:
            # 수신자 타입 결정
            receiver_type = "student" if sender_type == "teacher" else "teacher"

            # 권한 검증
            if not self.validate_message_permission(sender_id, sender_type, receiver_id, receiver_type):
                continue

            # 공통 클래스룸 찾기
            sender_classrooms = set(self.get_user_classrooms(sender_id, sender_type))
            receiver_classrooms = set(self.get_user_classrooms(receiver_id, receiver_type))
            common_classroom = list(sender_classrooms & receiver_classrooms)[0]

            # 메시지 생성 및 저장
            message = Message(
                subject=message_request.subject,
                content=message_request.content,
                sender_id=sender_id,
                sender_type=sender_type,
                receiver_id=receiver_id,
                receiver_type=receiver_type,
                classroom_id=common_classroom
            )

            self.db.add(message)
            self.db.flush()  # ID 생성을 위해 flush

            # 발신자 정보 조회
            if sender_type == "teacher":
                sender = self.db.query(Teacher).filter(Teacher.id == sender_id).first()
            else:
                sender = self.db.query(Student).filter(Student.id == sender_id).first()

            # 알림 데이터 준비
            notification_data = {
                "message_id": message.id,
                "sender_id": sender_id,
                "sender_name": sender.name if sender else "Unknown",
                "sender_type": sender_type,
                "receiver_id": receiver_id,
                "receiver_type": receiver_type,
                "subject": message_request.subject,
                "preview": message_request.content[:50] + "..." if len(message_request.content) > 50 else message_request.content,
                "classroom_id": common_classroom
            }

            # 알림 전송 (비동기, 실패해도 메시지 전송은 계속)
            try:
                await self._send_notification_to_service(notification_data)
            except Exception as e:
                logger.warning(f"Failed to send notification for message {message.id}: {e}")

            sent_messages.append(message)

        self.db.commit()
        return sent_messages

    def send_message(self, sender_id: int, sender_type: str,
                    message_request: MessageSendRequest) -> List[Message]:
        """메시지 전송 (동기 - 기존 호환성 유지)"""
        try:
            return asyncio.run(self.send_message_async(sender_id, sender_type, message_request))
        except Exception as e:
            logger.error(f"Error in async message sending, falling back to sync: {e}")
            # 알림 없이 메시지만 전송하는 폴백
            sent_messages = []

            for receiver_id in message_request.recipient_ids:
                receiver_type = "student" if sender_type == "teacher" else "teacher"

                if not self.validate_message_permission(sender_id, sender_type, receiver_id, receiver_type):
                    continue

                sender_classrooms = set(self.get_user_classrooms(sender_id, sender_type))
                receiver_classrooms = set(self.get_user_classrooms(receiver_id, receiver_type))
                common_classroom = list(sender_classrooms & receiver_classrooms)[0]

                message = Message(
                    subject=message_request.subject,
                    content=message_request.content,
                    sender_id=sender_id,
                    sender_type=sender_type,
                    receiver_id=receiver_id,
                    receiver_type=receiver_type,
                    classroom_id=common_classroom
                )

                self.db.add(message)
                sent_messages.append(message)

            self.db.commit()
            return sent_messages

    def get_messages(self, user_id: int, user_type: str,
                    page: int = 1, page_size: int = 15,
                    filter_type: str = "all",
                    search_query: str = "",
                    search_type: str = "subject") -> Tuple[List[MessageResponse], int]:
        """받은 메시지 목록 조회"""
        query = self.db.query(Message).filter(
            and_(
                Message.receiver_id == user_id,
                Message.receiver_type == user_type,
                Message.is_deleted == False
            )
        )

        # 필터링
        if filter_type == "read":
            query = query.filter(Message.is_read == True)
        elif filter_type == "unread":
            query = query.filter(Message.is_read == False)
        elif filter_type == "starred":
            query = query.filter(Message.is_starred == True)

        # 검색
        if search_query:
            if search_type == "subject":
                query = query.filter(Message.subject.ilike(f"%{search_query}%"))
            elif search_type == "sender":
                # 발신자 이름으로 검색 (복잡한 조인 필요)
                pass

        # 정렬 및 페이징
        total_count = query.count()
        messages = query.order_by(desc(Message.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        # MessageResponse로 변환
        message_responses = []
        for message in messages:
            # 발신자 정보 조회
            if message.sender_type == "teacher":
                sender = self.db.query(Teacher).filter(Teacher.id == message.sender_id).first()
            else:
                sender = self.db.query(Student).filter(Student.id == message.sender_id).first()

            # 수신자 정보 조회 (현재 사용자)
            if message.receiver_type == "teacher":
                recipient = self.db.query(Teacher).filter(Teacher.id == message.receiver_id).first()
            else:
                recipient = self.db.query(Student).filter(Student.id == message.receiver_id).first()

            if sender and recipient:
                sender_data = MessageRecipient(
                    id=sender.id,
                    name=sender.name,
                    email=sender.email,
                    phone=sender.phone,
                    type=message.sender_type,
                    school_level=sender.school_level.value if hasattr(sender, 'school_level') and sender.school_level else None,
                    grade=sender.grade if hasattr(sender, 'grade') else None
                )

                recipient_data = MessageRecipient(
                    id=recipient.id,
                    name=recipient.name,
                    email=recipient.email,
                    phone=recipient.phone,
                    type=message.receiver_type,
                    school_level=recipient.school_level.value if hasattr(recipient, 'school_level') and recipient.school_level else None,
                    grade=recipient.grade if hasattr(recipient, 'grade') else None
                )

                message_responses.append(MessageResponse(
                    id=message.id,
                    subject=message.subject,
                    content=message.content,
                    sender=sender_data,
                    recipient=recipient_data,
                    is_read=message.is_read,
                    is_starred=message.is_starred,
                    sent_at=message.created_at,
                    read_at=message.read_at
                ))

        return message_responses, total_count

    def mark_as_read(self, message_id: int, user_id: int, user_type: str) -> Optional[Message]:
        """메시지 읽음 처리"""
        message = self.db.query(Message).filter(
            and_(
                Message.id == message_id,
                Message.receiver_id == user_id,
                Message.receiver_type == user_type
            )
        ).first()

        if message:
            message.is_read = True
            message.read_at = datetime.now()
            self.db.commit()

        return message

    def toggle_star(self, message_id: int, user_id: int, user_type: str, is_starred: bool) -> Optional[Message]:
        """메시지 즐겨찾기 토글"""
        message = self.db.query(Message).filter(
            and_(
                Message.id == message_id,
                Message.receiver_id == user_id,
                Message.receiver_type == user_type
            )
        ).first()

        if message:
            message.is_starred = is_starred
            self.db.commit()

        return message

    def delete_message(self, message_id: int, user_id: int, user_type: str) -> Optional[Message]:
        """메시지 삭제 (논리 삭제)"""
        message = self.db.query(Message).filter(
            and_(
                Message.id == message_id,
                Message.receiver_id == user_id,
                Message.receiver_type == user_type
            )
        ).first()

        if message:
            message.is_deleted = True
            self.db.commit()

        return message