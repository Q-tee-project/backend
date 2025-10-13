from typing import Dict, Any, List
from .redis_client import redis_client
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class NotificationService:

    def _create_notification(self, notif_type: str, notif_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """공통 알림 객체 생성"""
        return {
            "type": notif_type,
            "id": notif_id,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read": False
        }

    def _send_notification(self, receiver_type: str, receiver_id: int, notification: Dict[str, Any]) -> bool:
        """알림 전송 공통 로직"""
        try:
            publish_success = redis_client.publish_notification(receiver_type, receiver_id, notification)
            store_success = redis_client.store_notification(receiver_type, receiver_id, notification)

            if publish_success or store_success:
                logger.info(f"{notification['type']} notification sent to {receiver_type}:{receiver_id}")
                return True
            else:
                logger.warning(f"Failed to send notification to {receiver_type}:{receiver_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    def send_message_notification(self, message_data: Dict[str, Any]) -> bool:
        """쪽지 알림 전송"""
        notification = self._create_notification(
            "message",
            f"msg_{message_data['message_id']}_{int(datetime.now().timestamp())}",
            {
                "message_id": message_data['message_id'],
                "sender_id": message_data['sender_id'],
                "sender_name": message_data['sender_name'],
                "sender_type": message_data['sender_type'],
                "subject": message_data['subject'],
                "preview": message_data.get('preview', ''),
                "classroom_id": message_data.get('classroom_id')
            }
        )
        return self._send_notification(message_data['receiver_type'], message_data['receiver_id'], notification)

    def send_problem_generation_notification(self, data: Dict[str, Any]) -> bool:
        """문제 생성 완료 알림"""
        notif_type = "problem_generation_failed" if not data.get('success', True) else "problem_generation"
        notification = self._create_notification(
            notif_type,
            f"prob_gen_{data['task_id']}_{int(datetime.now().timestamp())}",
            {
                "task_id": data['task_id'],
                "subject": data['subject'],
                "worksheet_id": data['worksheet_id'],
                "worksheet_title": data['worksheet_title'],
                "problem_count": data['problem_count'],
                "success": data.get('success', True),
                "error_message": data.get('error_message')
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_problem_regeneration_notification(self, data: Dict[str, Any]) -> bool:
        """문제 재생성 완료 알림"""
        notif_type = "problem_regeneration_failed" if not data.get('success', True) else "problem_regeneration"
        notification = self._create_notification(
            notif_type,
            f"prob_regen_{data['task_id']}_{int(datetime.now().timestamp())}",
            {
                "task_id": data['task_id'],
                "subject": data['subject'],
                "worksheet_id": data['worksheet_id'],
                "worksheet_title": data['worksheet_title'],
                "problem_number": data['problem_number'],
                "success": data.get('success', True),
                "error_message": data.get('error_message')
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_assignment_submitted_notification(self, data: Dict[str, Any]) -> bool:
        """과제 제출 알림 (선생님이 받음)"""
        notification = self._create_notification(
            "assignment_submitted",
            f"assign_submit_{data['assignment_id']}_{data['student_id']}_{int(datetime.now().timestamp())}",
            {
                "assignment_id": data['assignment_id'],
                "assignment_title": data['assignment_title'],
                "student_id": data['student_id'],
                "student_name": data['student_name'],
                "class_id": data['class_id'],
                "class_name": data['class_name'],
                "submitted_at": data['submitted_at']
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_assignment_deployed_notification(self, data: Dict[str, Any]) -> bool:
        """과제 배포 알림 (학생이 받음)"""
        notification = self._create_notification(
            "assignment_deployed",
            f"assign_deploy_{data['assignment_id']}_{int(datetime.now().timestamp())}",
            {
                "assignment_id": data['assignment_id'],
                "assignment_title": data['assignment_title'],
                "class_id": data['class_id'],
                "class_name": data['class_name'],
                "due_date": data.get('due_date')
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_class_join_request_notification(self, data: Dict[str, Any]) -> bool:
        """클래스 가입 요청 알림 (선생님이 받음)"""
        notification = self._create_notification(
            "class_join_request",
            f"class_join_{data['class_id']}_{data['student_id']}_{int(datetime.now().timestamp())}",
            {
                "student_id": data['student_id'],
                "student_name": data['student_name'],
                "class_id": data['class_id'],
                "class_name": data['class_name'],
                "message": data.get('message')
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_class_approved_notification(self, data: Dict[str, Any]) -> bool:
        """클래스 승인 알림 (학생이 받음)"""
        notification = self._create_notification(
            "class_approved",
            f"class_approved_{data['class_id']}_{int(datetime.now().timestamp())}",
            {
                "class_id": data['class_id'],
                "class_name": data['class_name'],
                "teacher_name": data['teacher_name']
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_grading_updated_notification(self, data: Dict[str, Any]) -> bool:
        """채점 수정 알림 (학생이 받음)"""
        notification = self._create_notification(
            "grading_updated",
            f"grading_{data['assignment_id']}_{int(datetime.now().timestamp())}",
            {
                "assignment_id": data['assignment_id'],
                "assignment_title": data['assignment_title'],
                "score": data['score'],
                "feedback": data.get('feedback')
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_market_sale_notification(self, data: Dict[str, Any]) -> bool:
        """마켓 판매 알림 (판매자가 받음)"""
        notification = self._create_notification(
            "market_sale",
            f"market_sale_{data['product_id']}_{int(datetime.now().timestamp())}",
            {
                "product_id": data['product_id'],
                "product_title": data['product_title'],
                "buyer_id": data['buyer_id'],
                "buyer_name": data['buyer_name'],
                "amount": data['amount']
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_market_new_product_notification(self, data: Dict[str, Any]) -> bool:
        """마켓 신상품 알림"""
        notification = self._create_notification(
            "market_new_product",
            f"market_new_{data['product_id']}_{int(datetime.now().timestamp())}",
            {
                "product_id": data['product_id'],
                "product_title": data['product_title'],
                "seller_name": data['seller_name']
            }
        )
        return self._send_notification(data['receiver_type'], data['receiver_id'], notification)

    def send_bulk_notifications(self, notifications_data: List[Dict[str, Any]]) -> int:
        """대량 알림 전송"""
        success_count = 0
        for notif_data in notifications_data:
            # type 필드로 어떤 알림인지 판단
            notif_type = notif_data.get('type', 'message')

            method_map = {
                'message': self.send_message_notification,
                'problem_generation': self.send_problem_generation_notification,
                'problem_regeneration': self.send_problem_regeneration_notification,
                'assignment_submitted': self.send_assignment_submitted_notification,
                'assignment_deployed': self.send_assignment_deployed_notification,
                'class_join_request': self.send_class_join_request_notification,
                'class_approved': self.send_class_approved_notification,
                'grading_updated': self.send_grading_updated_notification,
                'market_sale': self.send_market_sale_notification,
                'market_new_product': self.send_market_new_product_notification
            }

            method = method_map.get(notif_type, self.send_message_notification)
            if method(notif_data):
                success_count += 1

        logger.info(f"Sent {success_count}/{len(notifications_data)} notifications")
        return success_count

    def get_stored_notifications(self, user_type: str, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """저장된 알림 조회"""
        try:
            notifications = redis_client.get_stored_notifications(user_type, user_id, limit)
            logger.info(f"Retrieved {len(notifications)} stored notifications for {user_type}:{user_id}")
            return notifications
        except Exception as e:
            logger.error(f"Failed to get stored notifications: {e}")
            return []

notification_service = NotificationService()