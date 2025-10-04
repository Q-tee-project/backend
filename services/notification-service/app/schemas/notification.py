from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

# 알림 타입 정의
NotificationType = Literal[
    "message",                    # 쪽지 알림
    "problem_generation",         # 문제 생성 완료
    "problem_regeneration",       # 문제 재생성 완료
    "problem_generation_failed",  # 문제 생성 실패
    "problem_regeneration_failed",# 문제 재생성 실패
    "assignment_submitted",       # 과제 제출
    "assignment_deployed",        # 과제 배포
    "class_join_request",         # 클래스 가입 요청
    "class_approved",             # 클래스 승인
    "grading_updated",            # 채점 수정
    "market_sale",                # 상품 판매
    "market_new_product"          # 신상품 등록
]

# 기본 알림 요청 (모든 알림의 공통 필드)
class BaseNotificationRequest(BaseModel):
    receiver_id: int
    receiver_type: Literal["teacher", "student"]

# 쪽지 알림
class MessageNotificationRequest(BaseNotificationRequest):
    message_id: int
    sender_id: int
    sender_name: str
    sender_type: Literal["teacher", "student"]
    subject: str
    preview: str = ""
    classroom_id: Optional[int] = None

# 문제 생성 알림
class ProblemGenerationNotificationRequest(BaseNotificationRequest):
    task_id: str
    subject: Literal["math", "korean", "english"]
    worksheet_id: int
    worksheet_title: str
    problem_count: int
    success: bool = True
    error_message: Optional[str] = None

# 문제 재생성 알림
class ProblemRegenerationNotificationRequest(BaseNotificationRequest):
    task_id: str
    subject: Literal["math", "korean", "english"]
    worksheet_id: int
    worksheet_title: str
    problem_number: int
    success: bool = True
    error_message: Optional[str] = None

# 과제 제출 알림 (선생님이 받음)
class AssignmentSubmittedNotificationRequest(BaseNotificationRequest):
    assignment_id: int
    assignment_title: str
    student_id: int
    student_name: str
    class_id: int
    class_name: str
    submitted_at: str

# 과제 배포 알림 (학생이 받음)
class AssignmentDeployedNotificationRequest(BaseNotificationRequest):
    assignment_id: int
    assignment_title: str
    class_id: int
    class_name: str
    due_date: Optional[str] = None

# 클래스 가입 요청 알림 (선생님이 받음)
class ClassJoinRequestNotificationRequest(BaseNotificationRequest):
    student_id: int
    student_name: str
    class_id: int
    class_name: str
    message: Optional[str] = None

# 클래스 승인 알림 (학생이 받음)
class ClassApprovedNotificationRequest(BaseNotificationRequest):
    class_id: int
    class_name: str
    teacher_name: str

# 채점 수정 알림 (학생이 받음)
class GradingUpdatedNotificationRequest(BaseNotificationRequest):
    assignment_id: int
    assignment_title: str
    score: float
    feedback: Optional[str] = None

# 마켓 판매 알림 (판매자가 받음)
class MarketSaleNotificationRequest(BaseNotificationRequest):
    product_id: int
    product_title: str
    buyer_id: int
    buyer_name: str
    amount: int

# 마켓 신상품 알림 (관심있는 사용자가 받음)
class MarketNewProductNotificationRequest(BaseNotificationRequest):
    product_id: int
    product_title: str
    seller_name: str

# 대량 알림 요청
class BulkNotificationRequest(BaseModel):
    notifications: List[Dict[str, Any]]

# 알림 응답
class NotificationResponse(BaseModel):
    type: NotificationType
    id: str
    data: Dict[str, Any]
    timestamp: str
    read: bool

class StoredNotificationsResponse(BaseModel):
    notifications: List[Dict[str, Any]]