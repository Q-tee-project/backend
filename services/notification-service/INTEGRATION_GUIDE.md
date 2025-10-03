# Notification Service Integration Guide

이 가이드는 다른 백엔드 서비스들이 notification-service와 연동하는 방법을 설명합니다.

## 서비스 구조

```
backend/services/
├── auth-service/
├── math-service/
├── korean-service/
├── english-service/
├── market-service/
└── notification-service/
```

## 알림 타입 및 연동 시나리오

### 1. Math/Korean/English Service → Notification Service

**문제 생성/재생성 완료 시**

```python
import httpx
from typing import Literal

NOTIFICATION_SERVICE_URL = "http://localhost:8006"  # notification-service port

async def send_problem_generation_notification(
    teacher_id: int,
    task_id: str,
    subject: Literal["math", "korean", "english"],
    worksheet_id: int,
    worksheet_title: str,
    problem_count: int,
    success: bool = True,
    error_message: str = None
):
    """문제 생성 완료/실패 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
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
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
# 문제 생성 API 엔드포인트에서:
@router.post("/generate")
async def generate_problems(request: GenerateProblemRequest):
    # ... 문제 생성 로직 ...

    # 생성 완료 후 알림 전송
    await send_problem_generation_notification(
        teacher_id=request.teacher_id,
        task_id=task_id,
        subject="math",  # or "korean", "english"
        worksheet_id=worksheet.id,
        worksheet_title=worksheet.title,
        problem_count=len(generated_problems),
        success=True
    )

    return {"task_id": task_id, "status": "completed"}

# 백그라운드 태스크에서 생성 실패 시:
async def background_generate_task(task_id: str, teacher_id: int, ...):
    try:
        # ... 문제 생성 로직 ...
        await send_problem_generation_notification(
            teacher_id=teacher_id,
            task_id=task_id,
            subject="math",
            worksheet_id=worksheet_id,
            worksheet_title=worksheet_title,
            problem_count=problem_count,
            success=True
        )
    except Exception as e:
        # 생성 실패 시 실패 알림
        await send_problem_generation_notification(
            teacher_id=teacher_id,
            task_id=task_id,
            subject="math",
            worksheet_id=worksheet_id,
            worksheet_title=worksheet_title,
            problem_count=0,
            success=False,
            error_message=str(e)
        )
```

**문제 재생성 완료 시**

```python
async def send_problem_regeneration_notification(
    teacher_id: int,
    task_id: str,
    subject: Literal["math", "korean", "english"],
    worksheet_id: int,
    worksheet_title: str,
    problem_indices: list[int],
    success: bool = True,
    error_message: str = None
):
    """문제 재생성 완료/실패 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
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
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
@router.post("/regenerate")
async def regenerate_problems(request: RegenerateProblemRequest):
    # ... 문제 재생성 로직 ...

    await send_problem_regeneration_notification(
        teacher_id=request.teacher_id,
        task_id=task_id,
        subject="korean",
        worksheet_id=worksheet.id,
        worksheet_title=worksheet.title,
        problem_indices=request.problem_indices,
        success=True
    )

    return {"task_id": task_id, "status": "completed"}
```

### 2. Auth Service → Notification Service

**과제 제출 시 (학생 → 선생님)**

```python
async def send_assignment_submitted_notification(
    teacher_id: int,
    student_id: int,
    student_name: str,
    class_id: int,
    class_name: str,
    assignment_id: int,
    assignment_title: str,
    submitted_at: str
):
    """과제 제출 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
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
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(assignment_id: int, submission: SubmissionData):
    # ... 과제 제출 로직 ...

    # 선생님에게 알림 전송
    await send_assignment_submitted_notification(
        teacher_id=assignment.teacher_id,
        student_id=current_user.id,
        student_name=current_user.name,
        class_id=assignment.class_id,
        class_name=assignment.class_name,
        assignment_id=assignment_id,
        assignment_title=assignment.title,
        submitted_at=datetime.now().isoformat()
    )

    return {"status": "submitted"}
```

**과제 배포 시 (선생님 → 학생들)**

```python
async def send_assignment_deployed_notification(
    student_id: int,
    class_id: int,
    class_name: str,
    assignment_id: int,
    assignment_title: str,
    due_date: str
):
    """과제 배포 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
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
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
@router.post("/assignments/deploy")
async def deploy_assignment(request: DeployAssignmentRequest):
    # ... 과제 배포 로직 ...

    # 클래스의 모든 학생들에게 알림 전송
    students = await get_class_students(request.class_id)
    for student in students:
        await send_assignment_deployed_notification(
            student_id=student.id,
            class_id=request.class_id,
            class_name=class_info.name,
            assignment_id=assignment.id,
            assignment_title=assignment.title,
            due_date=assignment.due_date
        )

    return {"status": "deployed", "student_count": len(students)}
```

**클래스 가입 요청 시 (학생 → 선생님)**

```python
async def send_class_join_request_notification(
    teacher_id: int,
    student_id: int,
    student_name: str,
    class_id: int,
    class_name: str,
    message: str = None
):
    """클래스 가입 요청 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/class/join-request",
                json={
                    "receiver_id": teacher_id,
                    "receiver_type": "teacher",
                    "student_id": student_id,
                    "student_name": student_name,
                    "class_id": class_id,
                    "class_name": class_name,
                    "message": message
                },
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
@router.post("/classes/{class_id}/join-request")
async def request_join_class(class_id: int, message: str = None):
    # ... 가입 요청 로직 ...

    await send_class_join_request_notification(
        teacher_id=class_info.teacher_id,
        student_id=current_user.id,
        student_name=current_user.name,
        class_id=class_id,
        class_name=class_info.name,
        message=message
    )

    return {"status": "requested"}
```

**클래스 승인 시 (선생님 → 학생)**

```python
async def send_class_approved_notification(
    student_id: int,
    class_id: int,
    class_name: str,
    teacher_name: str
):
    """클래스 승인 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/class/approved",
                json={
                    "receiver_id": student_id,
                    "receiver_type": "student",
                    "class_id": class_id,
                    "class_name": class_name,
                    "teacher_name": teacher_name
                },
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
@router.post("/classes/{class_id}/approve-student/{student_id}")
async def approve_student(class_id: int, student_id: int):
    # ... 승인 로직 ...

    await send_class_approved_notification(
        student_id=student_id,
        class_id=class_id,
        class_name=class_info.name,
        teacher_name=current_user.name
    )

    return {"status": "approved"}
```

**채점 수정 시 (선생님 → 학생)**

```python
async def send_grading_updated_notification(
    student_id: int,
    assignment_id: int,
    assignment_title: str,
    score: int,
    feedback: str = None
):
    """채점 수정 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
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
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
@router.put("/assignments/{assignment_id}/grade")
async def update_grading(assignment_id: int, grading: GradingUpdate):
    # ... 채점 수정 로직 ...

    await send_grading_updated_notification(
        student_id=submission.student_id,
        assignment_id=assignment_id,
        assignment_title=assignment.title,
        score=grading.score,
        feedback=grading.feedback
    )

    return {"status": "updated"}
```

### 3. Market Service → Notification Service

**상품 판매 시 (구매자 → 판매자)**

```python
async def send_market_sale_notification(
    seller_id: int,
    buyer_id: int,
    buyer_name: str,
    product_id: int,
    product_title: str,
    amount: int
):
    """마켓 판매 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
            # 판매자가 teacher인지 student인지 확인 필요
            seller_type = await get_user_type(seller_id)

            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/market/sale",
                json={
                    "receiver_id": seller_id,
                    "receiver_type": seller_type,
                    "buyer_id": buyer_id,
                    "buyer_name": buyer_name,
                    "product_id": product_id,
                    "product_title": product_title,
                    "amount": amount
                },
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
@router.post("/products/{product_id}/purchase")
async def purchase_product(product_id: int):
    # ... 구매 로직 ...

    await send_market_sale_notification(
        seller_id=product.seller_id,
        buyer_id=current_user.id,
        buyer_name=current_user.name,
        product_id=product_id,
        product_title=product.title,
        amount=product.price
    )

    return {"status": "purchased"}
```

**신상품 등록 시 (판매자 → 구독자들/전체)**

```python
async def send_market_new_product_notification(
    receiver_id: int,
    receiver_type: Literal["teacher", "student"],
    seller_id: int,
    seller_name: str,
    product_id: int,
    product_title: str,
    price: int
):
    """마켓 신상품 알림 전송"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/notifications/market/new-product",
                json={
                    "receiver_id": receiver_id,
                    "receiver_type": receiver_type,
                    "seller_id": seller_id,
                    "seller_name": seller_name,
                    "product_id": product_id,
                    "product_title": product_title,
                    "price": price
                },
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

# 사용 예시
@router.post("/products")
async def create_product(product: ProductCreate):
    # ... 상품 생성 로직 ...

    # 판매자를 팔로우하는 사용자들에게 알림
    followers = await get_seller_followers(current_user.id)
    for follower in followers:
        await send_market_new_product_notification(
            receiver_id=follower.id,
            receiver_type=follower.type,
            seller_id=current_user.id,
            seller_name=current_user.name,
            product_id=created_product.id,
            product_title=created_product.title,
            price=created_product.price
        )

    return created_product
```

## 환경 변수 설정

각 서비스의 `.env` 파일에 추가:

```env
NOTIFICATION_SERVICE_URL=http://localhost:8006
```

## 의존성 추가

각 서비스의 `requirements.txt`에 추가 (없다면):

```
httpx>=0.24.0
```

## 에러 핸들링

알림 전송 실패는 주요 비즈니스 로직에 영향을 주지 않도록 처리:

```python
async def safe_send_notification(notification_func, *args, **kwargs):
    """안전하게 알림 전송 (실패해도 주요 로직 영향 없음)"""
    try:
        await notification_func(*args, **kwargs)
    except Exception as e:
        # 로깅만 하고 에러를 throw하지 않음
        print(f"Notification failed but continuing: {e}")
        # 필요시 Sentry 등으로 에러 트래킹
```

## 테스트

각 서비스에서 알림 전송 테스트:

```python
# 테스트 예시
async def test_notification_integration():
    result = await send_problem_generation_notification(
        teacher_id=1,
        task_id="test-task-123",
        subject="math",
        worksheet_id=1,
        worksheet_title="Test Worksheet",
        problem_count=10,
        success=True
    )
    assert result == True
```

## 다음 단계

1. 각 서비스에 notification helper 함수 추가
2. 비즈니스 로직에서 적절한 시점에 알림 전송 호출
3. 에러 로깅 및 모니터링 설정
4. 프론트엔드에서 SSE 연결 확인 및 알림 수신 테스트
