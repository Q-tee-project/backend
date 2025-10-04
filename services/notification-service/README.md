# Notification Service

Q-Tee 플랫폼의 실시간 알림 서비스입니다. SSE (Server-Sent Events)와 Redis Pub/Sub을 활용하여 사용자에게 실시간 알림을 전달합니다.

## 기능

- **실시간 알림 스트리밍**: SSE를 통한 실시간 알림 푸시
- **Redis Pub/Sub**: 분산 환경에서 알림 배포
- **알림 저장**: Redis에 알림 히스토리 저장
- **11가지 알림 타입 지원**:
  - 메시지 알림
  - 문제 생성/재생성 완료/실패
  - 과제 제출/배포
  - 클래스 가입 요청/승인
  - 채점 수정
  - 마켓 판매/신상품

## 기술 스택

- **FastAPI**: 비동기 웹 프레임워크
- **Redis**: 실시간 메시징 및 알림 저장
- **Pydantic**: 데이터 검증
- **SSE (Server-Sent Events)**: 실시간 단방향 스트리밍

## 프로젝트 구조

```
notification-service/
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 설정 관리
│   ├── routers/
│   │   └── notifications.py    # 알림 API 엔드포인트
│   ├── services/
│   │   └── notification_service.py  # 알림 비즈니스 로직
│   └── schemas/
│       └── notification.py     # Pydantic 스키마
├── INTEGRATION_GUIDE.md        # 다른 서비스 연동 가이드
├── requirements.txt
└── README.md
```

## 환경 설정

`.env` 파일 생성:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 설치 및 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 서비스 실행
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

## API 엔드포인트

### SSE 연결

```
GET /api/notifications/stream/{user_type}/{user_id}
```

실시간 알림을 수신하기 위한 SSE 연결

**Parameters:**
- `user_type`: "teacher" | "student"
- `user_id`: 사용자 ID

**Response:** Server-Sent Events stream

### 저장된 알림 조회

```
GET /api/notifications/{user_type}/{user_id}?limit=20
```

Redis에 저장된 알림 히스토리 조회

### 알림 읽음 처리

```
POST /api/notifications/{user_type}/{user_id}/read/{notification_id}
```

특정 알림을 읽음 상태로 표시

### 모든 알림 읽음 처리

```
POST /api/notifications/{user_type}/{user_id}/read-all
```

사용자의 모든 알림을 읽음 상태로 표시

### 알림 삭제

```
DELETE /api/notifications/{user_type}/{user_id}/{notification_type}/{notification_id}
```

특정 알림 삭제

### 타입별 알림 삭제

```
DELETE /api/notifications/{user_type}/{user_id}/type/{notification_type}
```

특정 타입의 모든 알림 삭제

### 전체 알림 삭제

```
DELETE /api/notifications/{user_type}/{user_id}/clear
```

사용자의 모든 알림 삭제

## 알림 전송 API

### 1. 문제 생성 알림

```
POST /api/notifications/problem/generation
```

**Request Body:**
```json
{
  "receiver_id": 1,
  "receiver_type": "teacher",
  "task_id": "task-123",
  "subject": "math",
  "worksheet_id": 1,
  "worksheet_title": "정수와 유리수",
  "problem_count": 10,
  "success": true,
  "error_message": null
}
```

### 2. 문제 재생성 알림

```
POST /api/notifications/problem/regeneration
```

**Request Body:**
```json
{
  "receiver_id": 1,
  "receiver_type": "teacher",
  "task_id": "task-456",
  "subject": "korean",
  "worksheet_id": 2,
  "worksheet_title": "문학 작품 분석",
  "problem_indices": [1, 3, 5],
  "success": true,
  "error_message": null
}
```

### 3. 과제 제출 알림

```
POST /api/notifications/assignment/submitted
```

**Request Body:**
```json
{
  "receiver_id": 1,
  "receiver_type": "teacher",
  "student_id": 10,
  "student_name": "홍길동",
  "class_id": 5,
  "class_name": "A반",
  "assignment_id": 20,
  "assignment_title": "수학 과제 1",
  "submitted_at": "2025-01-15T10:30:00"
}
```

### 4. 과제 배포 알림

```
POST /api/notifications/assignment/deployed
```

**Request Body:**
```json
{
  "receiver_id": 10,
  "receiver_type": "student",
  "class_id": 5,
  "class_name": "A반",
  "assignment_id": 20,
  "assignment_title": "수학 과제 1",
  "due_date": "2025-01-20T23:59:00"
}
```

### 5. 클래스 가입 요청 알림

```
POST /api/notifications/class/join-request
```

**Request Body:**
```json
{
  "receiver_id": 1,
  "receiver_type": "teacher",
  "student_id": 10,
  "student_name": "홍길동",
  "class_id": 5,
  "class_name": "A반",
  "message": "가입 신청합니다"
}
```

### 6. 클래스 승인 알림

```
POST /api/notifications/class/approved
```

**Request Body:**
```json
{
  "receiver_id": 10,
  "receiver_type": "student",
  "class_id": 5,
  "class_name": "A반",
  "teacher_name": "김선생"
}
```

### 7. 채점 수정 알림

```
POST /api/notifications/grading/updated
```

**Request Body:**
```json
{
  "receiver_id": 10,
  "receiver_type": "student",
  "assignment_id": 20,
  "assignment_title": "수학 과제 1",
  "score": 85,
  "feedback": "잘했어요!"
}
```

### 8. 마켓 판매 알림

```
POST /api/notifications/market/sale
```

**Request Body:**
```json
{
  "receiver_id": 1,
  "receiver_type": "teacher",
  "buyer_id": 10,
  "buyer_name": "홍길동",
  "product_id": 30,
  "product_title": "수학 문제집",
  "amount": 5000
}
```

### 9. 마켓 신상품 알림

```
POST /api/notifications/market/new-product
```

**Request Body:**
```json
{
  "receiver_id": 10,
  "receiver_type": "student",
  "seller_id": 1,
  "seller_name": "김선생",
  "product_id": 30,
  "product_title": "수학 문제집",
  "price": 5000
}
```

## Redis 데이터 구조

### 알림 저장 키

```
notifications:{user_type}:{user_id}
```

예: `notifications:teacher:1`, `notifications:student:10`

### Pub/Sub 채널

```
notifications:{user_type}:{user_id}
```

예: `notifications:teacher:1`, `notifications:student:10`

### 알림 데이터 형식

```json
{
  "type": "problem_generation",
  "id": "notif-uuid",
  "data": {
    "task_id": "task-123",
    "subject": "math",
    "worksheet_id": 1,
    "worksheet_title": "정수와 유리수",
    "problem_count": 10,
    "success": true
  },
  "timestamp": "2025-01-15T10:30:00",
  "read": false
}
```

## 다른 서비스와 연동

자세한 연동 방법은 [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)를 참조하세요.

### 기본 연동 예시

```python
import httpx

async def send_notification_to_teacher(teacher_id: int, notification_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8006/api/notifications/problem/generation",
            json={
                "receiver_id": teacher_id,
                "receiver_type": "teacher",
                **notification_data
            },
            timeout=5.0
        )
        return response.status_code == 200
```

## 프론트엔드 연동

프론트엔드에서 SSE 연결:

```typescript
// src/services/notificationService.ts 사용
import { notificationService } from '@/services/notificationService';

// SSE 연결
notificationService.connect('teacher', 1);

// 알림 수신 리스너
notificationService.addListener((notification) => {
  console.log('새 알림:', notification);
});

// 연결 해제
notificationService.disconnect();
```

## 모니터링

### Redis 알림 확인

```bash
# Redis CLI
redis-cli

# 특정 사용자 알림 조회
LRANGE notifications:teacher:1 0 -1

# Pub/Sub 모니터링
PSUBSCRIBE notifications:*
```

### 로그 확인

```bash
# 서비스 로그
tail -f logs/notification-service.log
```

## 테스트

```bash
# 테스트 알림 전송
curl -X POST http://localhost:8006/api/notifications/test/teacher/1

# SSE 연결 테스트
curl -N http://localhost:8006/api/notifications/stream/teacher/1
```

## 트러블슈팅

### SSE 연결이 끊어지는 경우

- Nginx/프록시 타임아웃 설정 확인
- 클라이언트 재연결 로직 확인
- Redis 연결 상태 확인

### 알림이 전달되지 않는 경우

- Redis Pub/Sub 채널명 확인
- user_type과 user_id 정확성 확인
- 방화벽/네트워크 설정 확인

### Redis 메모리 관리

```python
# 알림 보관 기간 설정 (기본: 7일)
NOTIFICATION_RETENTION_DAYS=7

# 최대 알림 개수 제한 (기본: 100개)
MAX_NOTIFICATIONS_PER_USER=100
```

## 성능 최적화

- Redis 연결 풀 사용
- 비동기 처리로 블로킹 방지
- 알림 배치 처리 고려
- SSE 연결 수 모니터링

## 라이선스

MIT
