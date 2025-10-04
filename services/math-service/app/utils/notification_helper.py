"""
Notification Service 연동 헬퍼 함수
"""
import httpx
import os
from typing import Literal, Optional
from datetime import datetime

NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8006")


async def send_problem_generation_notification(
    teacher_id: int,
    task_id: str,
    subject: Literal["math", "korean", "english"],
    worksheet_id: int,
    worksheet_title: str,
    problem_count: int,
    success: bool = True,
    error_message: Optional[str] = None
) -> bool:
    """문제 생성 완료/실패 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/problem/generation",
                json={
                    "receiver_id": teacher_id,
                    "receiver_type": "teacher",
                    "task_id": task_id,
                    "subject": subject,
                    "worksheet_id": worksheet_id,
                    "worksheet_title": worksheet_title,
                    "problem_count": problem_count,
                    "success": success,
                    "error_message": error_message
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 문제 생성 알림 전송 성공: teacher_id={teacher_id}, worksheet_id={worksheet_id}")
                return True
            else:
                print(f"⚠️ 문제 생성 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 문제 생성 알림 전송 실패: {e}")
        return False


async def send_problem_regeneration_notification(
    teacher_id: int,
    task_id: str,
    subject: Literal["math", "korean", "english"],
    worksheet_id: int,
    worksheet_title: str,
    problem_indices: list[int],
    success: bool = True,
    error_message: Optional[str] = None
) -> bool:
    """문제 재생성 완료/실패 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/problem/regeneration",
                json={
                    "receiver_id": teacher_id,
                    "receiver_type": "teacher",
                    "task_id": task_id,
                    "subject": subject,
                    "worksheet_id": worksheet_id,
                    "worksheet_title": worksheet_title,
                    "problem_indices": problem_indices,
                    "success": success,
                    "error_message": error_message
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 문제 재생성 알림 전송 성공: teacher_id={teacher_id}, worksheet_id={worksheet_id}")
                return True
            else:
                print(f"⚠️ 문제 재생성 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 문제 재생성 알림 전송 실패: {e}")
        return False


async def send_assignment_submitted_notification(
    teacher_id: int,
    student_id: int,
    student_name: str,
    class_id: int,
    class_name: str,
    assignment_id: int,
    assignment_title: str,
    submitted_at: str
) -> bool:
    """과제 제출 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/assignment/submitted",
                json={
                    "receiver_id": teacher_id,
                    "receiver_type": "teacher",
                    "student_id": student_id,
                    "student_name": student_name,
                    "class_id": class_id,
                    "class_name": class_name,
                    "assignment_id": assignment_id,
                    "assignment_title": assignment_title,
                    "submitted_at": submitted_at
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 과제 제출 알림 전송 성공: teacher_id={teacher_id}, assignment_id={assignment_id}")
                return True
            else:
                print(f"⚠️ 과제 제출 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 과제 제출 알림 전송 실패: {e}")
        return False


async def send_assignment_deployed_notification(
    student_id: int,
    class_id: int,
    class_name: str,
    assignment_id: int,
    assignment_title: str,
    due_date: Optional[str] = None
) -> bool:
    """과제 배포 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/assignment/deployed",
                json={
                    "receiver_id": student_id,
                    "receiver_type": "student",
                    "class_id": class_id,
                    "class_name": class_name,
                    "assignment_id": assignment_id,
                    "assignment_title": assignment_title,
                    "due_date": due_date
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 과제 배포 알림 전송 성공: student_id={student_id}, assignment_id={assignment_id}")
                return True
            else:
                print(f"⚠️ 과제 배포 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 과제 배포 알림 전송 실패: {e}")
        return False


async def send_grading_updated_notification(
    student_id: int,
    assignment_id: int,
    assignment_title: str,
    score: int,
    feedback: Optional[str] = None
) -> bool:
    """채점 수정 알림 전송"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/grading/updated",
                json={
                    "receiver_id": student_id,
                    "receiver_type": "student",
                    "assignment_id": assignment_id,
                    "assignment_title": assignment_title,
                    "score": score,
                    "feedback": feedback
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ 채점 수정 알림 전송 성공: student_id={student_id}, assignment_id={assignment_id}")
                return True
            else:
                print(f"⚠️ 채점 수정 알림 전송 실패: status={response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 채점 수정 알림 전송 실패: {e}")
        return False


def safe_send_notification(notification_func, *args, **kwargs):
    """안전하게 알림 전송 (실패해도 주요 로직에 영향 없음)"""
    try:
        import asyncio
        # 이벤트 루프가 이미 실행 중인지 확인
        try:
            loop = asyncio.get_running_loop()
            # 이미 실행 중인 루프가 있으면 태스크로 실행
            asyncio.create_task(notification_func(*args, **kwargs))
        except RuntimeError:
            # 실행 중인 루프가 없으면 새로 실행
            asyncio.run(notification_func(*args, **kwargs))
    except Exception as e:
        print(f"⚠️ 알림 전송 실패 (주요 로직 계속 진행): {e}")
