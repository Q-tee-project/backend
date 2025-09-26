from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MessageSendRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    recipient_ids: List[int] = Field(..., min_items=1)

class MessageRecipient(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    type: str  # 'teacher' or 'student'
    school_level: Optional[str] = None
    grade: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    subject: str
    content: str
    sender: MessageRecipient
    recipient: MessageRecipient
    is_read: bool
    is_starred: bool
    sent_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class MessageReadRequest(BaseModel):
    is_read: bool

class MessageStarRequest(BaseModel):
    is_starred: bool