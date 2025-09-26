from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Union
import math

from ..database import get_db
from ..services.auth_service import get_current_user
from ..services.message_service import MessageService
from ..schemas.message import (
    MessageSendRequest, MessageRecipient, MessageResponse,
    MessageListResponse, MessageReadRequest, MessageStarRequest
)
from ..models.user import Teacher, Student

router = APIRouter()
security = HTTPBearer()

def get_message_service(db: Session = Depends(get_db)):
    return MessageService(db)

async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """현재 사용자 정보를 가져오고 타입을 판단"""
    try:
        # teacher로 시도
        teacher = await get_current_user(credentials.credentials, db, "teacher")
        return {"user_id": teacher.id, "user_type": "teacher", "user": teacher}
    except:
        try:
            # student로 시도
            student = await get_current_user(credentials.credentials, db, "student")
            return {"user_id": student.id, "user_type": "student", "user": student}
        except:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.get("/recipients", response_model=List[MessageRecipient])
async def get_message_recipients(
    current_user: dict = Depends(get_current_user_info),
    message_service = Depends(get_message_service)
):
    """메시지를 보낼 수 있는 대상 목록 조회"""
    try:
        recipients = message_service.get_message_recipients(
            current_user["user_id"],
            current_user["user_type"]
        )
        return recipients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recipients: {str(e)}")

@router.post("/", response_model=dict)
async def send_message(
    message_request: MessageSendRequest,
    current_user: dict = Depends(get_current_user_info),
    message_service = Depends(get_message_service)
):
    """메시지 전송"""
    try:
        sent_messages = await message_service.send_message_async(
            current_user["user_id"],
            current_user["user_type"],
            message_request
        )

        if not sent_messages:
            raise HTTPException(status_code=400, detail="No valid recipients found")

        return {
            "success": True,
            "message": f"Message sent to {len(sent_messages)} recipients",
            "sent_count": len(sent_messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/", response_model=MessageListResponse)
async def get_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    filter_type: str = Query("all", regex="^(all|read|unread|starred)$"),
    search_query: str = Query(""),
    search_type: str = Query("subject", regex="^(subject|sender)$"),
    current_user: dict = Depends(get_current_user_info),
    message_service = Depends(get_message_service)
):
    """받은 메시지 목록 조회"""
    try:
        messages, total_count = message_service.get_messages(
            current_user["user_id"],
            current_user["user_type"],
            page=page,
            page_size=page_size,
            filter_type=filter_type,
            search_query=search_query,
            search_type=search_type
        )

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        return MessageListResponse(
            messages=messages,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@router.put("/{message_id}/read", response_model=dict)
async def mark_message_as_read(
    message_id: int,
    current_user: dict = Depends(get_current_user_info),
    message_service = Depends(get_message_service)
):
    """메시지 읽음 처리"""
    try:
        message = message_service.mark_as_read(
            message_id,
            current_user["user_id"],
            current_user["user_type"]
        )

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        return {"success": True, "message": "Message marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark message as read: {str(e)}")

@router.put("/{message_id}/star", response_model=dict)
async def toggle_message_star(
    message_id: int,
    star_request: MessageStarRequest,
    current_user: dict = Depends(get_current_user_info),
    message_service = Depends(get_message_service)
):
    """메시지 즐겨찾기 토글"""
    try:
        message = message_service.toggle_star(
            message_id,
            current_user["user_id"],
            current_user["user_type"],
            star_request.is_starred
        )

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        return {
            "success": True,
            "message": f"Message {'starred' if star_request.is_starred else 'unstarred'}",
            "is_starred": message.is_starred
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle message star: {str(e)}")

@router.delete("/{message_id}", response_model=dict)
async def delete_message(
    message_id: int,
    current_user: dict = Depends(get_current_user_info),
    message_service = Depends(get_message_service)
):
    """메시지 삭제"""
    try:
        message = message_service.delete_message(
            message_id,
            current_user["user_id"],
            current_user["user_type"]
        )

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        return {"success": True, "message": "Message deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message_detail(
    message_id: int,
    current_user: dict = Depends(get_current_user_info),
    message_service = Depends(get_message_service),
    db: Session = Depends(get_db)
):
    """메시지 상세 조회"""
    try:
        from ..models.message import Message
        from sqlalchemy import and_

        message = db.query(Message).filter(
            and_(
                Message.id == message_id,
                Message.receiver_id == current_user["user_id"],
                Message.receiver_type == current_user["user_type"],
                Message.is_deleted == False
            )
        ).first()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # 자동으로 읽음 처리
        if not message.is_read:
            message_service.mark_as_read(
                message_id,
                current_user["user_id"],
                current_user["user_type"]
            )

        # 발신자 정보 조회
        if message.sender_type == "teacher":
            sender = db.query(Teacher).filter(Teacher.id == message.sender_id).first()
        else:
            sender = db.query(Student).filter(Student.id == message.sender_id).first()

        # 수신자 정보 조회
        if message.receiver_type == "teacher":
            recipient = db.query(Teacher).filter(Teacher.id == message.receiver_id).first()
        else:
            recipient = db.query(Student).filter(Student.id == message.receiver_id).first()

        if not sender or not recipient:
            raise HTTPException(status_code=404, detail="Sender or recipient not found")

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

        return MessageResponse(
            id=message.id,
            subject=message.subject,
            content=message.content,
            sender=sender_data,
            recipient=recipient_data,
            is_read=message.is_read,
            is_starred=message.is_starred,
            sent_at=message.created_at,
            read_at=message.read_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get message detail: {str(e)}")