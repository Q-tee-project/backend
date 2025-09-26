from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class MessageNotificationRequest(BaseModel):
    message_id: int
    sender_id: int
    sender_name: str
    sender_type: str  # 'teacher' or 'student'
    receiver_id: int
    receiver_type: str  # 'teacher' or 'student'
    subject: str
    preview: str = ""
    classroom_id: int

class BulkNotificationRequest(BaseModel):
    notifications: List[MessageNotificationRequest]

class NotificationResponse(BaseModel):
    type: str
    id: str
    data: Dict[str, Any]
    timestamp: str
    read: bool

class StoredNotificationsResponse(BaseModel):
    notifications: List[Dict[str, Any]]