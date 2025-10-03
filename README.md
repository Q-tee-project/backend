# Qt Project Backend

AI 기반 교육 플랫폼을 위한 마이크로서비스 아키텍처 백엔드 시스템입니다.

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Frontend)                        │
└─────────────────────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │   API Gateway   │ (Optional)
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│  Auth Service  │  │  Math Service  │  │ Korean Service │
│   (Port 8003)  │  │   (Port 8001)  │  │   (Port 8004)  │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                    │                    │
        │           ┌────────┴────────┐           │
        │           │                 │           │
┌───────▼────────┐  ▼                 ▼  ┌───────▼────────┐
│ Market Service │ English Service  Notification│
│   (Port 8005)  │                     │ Service (8006) │
└───────┬────────┘                     └───────┬────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼────────┐ ┌───▼────┐  ┌──────▼──────┐
│   PostgreSQL   │ │ Redis  │  │   Celery    │
│   (Port 5433)  │ │ (6379) │  │   Workers   │
└────────────────┘ └────────┘  └─────────────┘
```

### 아키텍처 특징

- **마이크로서비스 기반**: 독립적으로 배포 가능한 6개 서비스
- **중앙 인증**: Auth Service를 통한 JWT 토큰 검증
- **비동기 처리**: Celery + Redis를 활용한 백그라운드 작업
- **AI 통합**: Gemini 2.5 Pro, GPT-4o-mini 기반 문제 생성 및 검증
- **서비스 간 통신**: HTTP REST API
- **데이터 격리**: 서비스별 PostgreSQL 스키마 분리
- **확장성**: Docker Compose 기반 컨테이너 오케스트레이션

## 서비스 개요

### 1. Auth Service (Port 8003)

**인증 및 사용자 관리**

- **핵심 기능**:

  - 교사/학생 회원가입 및 로그인 (JWT)
  - 클래스룸 생성 및 학생 가입 관리
  - 교사-학생 간 쪽지 시스템
  - 중앙 토큰 검증 (`/api/auth/verify-token`)

- **주요 플로우**:

  1. 교사가 클래스 생성 → 고유 클래스 코드 발급
  2. 학생이 클래스 코드로 가입 신청 → 교사 승인/거부
  3. 승인된 학생과 교사 간 쪽지 송수신

- **데이터 모델**: Teacher, Student, ClassRoom, StudentJoinRequest, Message
- **기술**: FastAPI, PostgreSQL, JWT, bcrypt, Redis

### 2. Math Service (Port 8001)

**AI 기반 수학 문제 생성 및 채점**

- **핵심 기능**:

  - 교육과정 기반 문제 자동 생성 (Gemini 2.5 Pro)
  - AI Judge 검증 시스템 (GPT-4o-mini)
  - TikZ 그래프 자동 생성 (LaTeX)
  - OCR 기반 서술형 채점 (Google Vision API)
  - 난이도 3단계 (A: 직접계산, B: 응용번역, C: 통합발견)

- **주요 플로우**:

  1. 교사가 학년/단원/난이도 설정 → 문제 생성 요청
  2. Celery 백그라운드에서 Gemini로 문제 생성
  3. AI Judge가 수학정확성/정답일치/완결성/논리성 검증
  4. 불합격 문제는 피드백 포함 재생성 (최대 3회)
  5. 학생 답안 제출 → OCR 인식 → AI 채점 → 피드백 제공

- **데이터 모델**: Worksheet, Problem, GradingSession, Curriculum
- **기술**: FastAPI, Celery, Gemini, GPT-4o-mini, Google Vision API

### 3. Korean Service (Port 8004)

**AI 기반 국어 문제 생성 및 채점**

- **핵심 기능**:

  - 지문 기반 문제 생성 (시/소설/수필/문법)
  - AI Judge 유형별 검증 (문학성, 서사성, 논증성)
  - 병렬 처리 (ThreadPoolExecutor)
  - 과제 생성 및 배포

- **주요 플로우**:

  1. 교사가 국어 유형/난이도 설정 → 문제 생성 요청
  2. data/ 폴더에서 지문 랜덤 선택 (poem/novel/non-fiction/grammar)
  3. ThreadPoolExecutor로 작품별 병렬 생성
  4. AI Judge가 유형별 기준 검증 (각 항목 ≥ 3.5/5.0)
  5. 불합격 문제 재생성 → DB 저장
  6. 과제 배포 → 학생 제출 → 채점

- **데이터 모델**: Worksheet, Problem, GradingSession, Assignment
- **기술**: FastAPI, Celery, Gemini, GPT-4o-mini, ThreadPoolExecutor

### 4. Market Service (Port 8005)

**워크시트 마켓플레이스**

- **핵심 기능**:

  - 워크시트 상품 등록 및 판매
  - 포인트 시스템 (충전/구매/수익)
  - 자동 가격 책정 (10문제: 1,500P, 20문제: 3,000P)
  - 리뷰 시스템 (추천/보통/비추천)

- **주요 플로우**:

  1. 교사가 워크시트 등록 → 자동 가격 책정 및 태그 생성
  2. 다른 교사가 포인트로 구매
  3. 구매자 포인트 차감 → 판매자 수익 적립 (플랫폼 수수료 10%)
  4. 워크시트 자동 복사 → 구매자 계정에 추가
  5. 구매자 리뷰 작성 → 만족도 계산

- **데이터 모델**: MarketProduct, MarketPurchase, MarketReview, UserPoint
- **기술**: FastAPI, PostgreSQL, Auth Service 미들웨어

### 5. English Service (Port 8002)

**영어 문제 생성 및 관리** _(담당자: 다른 개발자)_

- **핵심 기능**: (추가 예정)

  - AI 기반 영어 문제 생성
  - 영어 워크시트 관리
  - 영어 채점 시스템

- **포트**: 8002
- **기술 스택**: FastAPI, PostgreSQL, AI Models

### 6. Notification Service (Port 8006)

**실시간 알림 및 WebSocket** _(담당자: 다른 개발자)_

- **핵심 기능**: (추가 예정)

  - WebSocket 기반 실시간 알림
  - 메시지 푸시 알림
  - 이벤트 브로드캐스팅

- **포트**: 8006
- **기술 스택**: FastAPI, Redis, WebSocket

## 기술 스택

### Core Framework

- **FastAPI**: 고성능 비동기 웹 프레임워크
- **SQLAlchemy**: ORM (PostgreSQL)
- **Pydantic**: 데이터 검증

### Database & Cache

- **PostgreSQL 15**: 메인 데이터베이스
- **Redis 7**: 캐싱 및 Celery 브로커

### AI & ML

- **Gemini 2.5 Pro**: 문제 생성
- **GPT-4o-mini**: AI Judge 검증
- **Google Vision API**: OCR (수학 서술형)

### Task Queue

- **Celery**: 비동기 작업 처리
- **Redis**: 메시지 브로커

### Authentication

- **JWT (HS256)**: 토큰 기반 인증
- **bcrypt**: 비밀번호 해싱

### Containerization

- **Docker**: 컨테이너화
- **Docker Compose**: 오케스트레이션

## 데이터 흐름

### 1. 문제 생성 플로우

```
교사 → Auth Service (인증) → Math/Korean Service
  ↓
Celery Task 생성 → Redis Queue
  ↓
Celery Worker → AI 문제 생성 (Gemini)
  ↓
AI Judge 검증 (GPT-4o-mini)
  ↓
불합격 시 재시도 (피드백 포함)
  ↓
PostgreSQL 저장 → 교사에게 알림
```

### 2. 워크시트 구매 플로우

```
교사 → Auth Service (인증) → Market Service
  ↓
상품 조회 → 포인트 차감
  ↓
판매자 수익 적립 (90%)
  ↓
Math/Korean/English Service → 워크시트 복사
  ↓
구매자 계정에 워크시트 추가
  ↓
구매 기록 저장 → 알림 전송
```

### 3. 과제 배포 및 채점 플로우

```
교사 → Korean Service → 과제 생성
  ↓
클래스룸 학생들에게 배포
  ↓
학생 답안 제출 (OCR 포함)
  ↓
AI 채점 (Gemini) → 피드백 생성
  ↓
채점 결과 저장 → 교사/학생 알림
```

## 환경 설정

### 필수 환경 변수

```bash
# Database
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=qt_project_db

# AI API Keys
GEMINI_API_KEY=your-gemini-key
MATH_GEMINI_API_KEY=your-math-gemini-key (optional)
KOREAN_GEMINI_API_KEY=your-korean-gemini-key (optional)
ENGLISH_GEMINI_API_KEY=your-english-gemini-key (optional)
OPENAI_API_KEY=your-openai-key
GOOGLE_VISION_API_KEY=your-vision-key (optional)

# Auth
AUTH_SECRET_KEY=your-jwt-secret-key

# Redis
REDIS_URL=redis://redis:6379/0
```

### 서비스별 포트

| 서비스               | 외부 포트 | 내부 포트 | 스키마               |
| -------------------- | --------- | --------- | -------------------- |
| Math Service         | 8001      | 8000      | math_service         |
| English Service      | 8002      | 8000      | english_service      |
| Auth Service         | 8003      | 8000      | auth_service         |
| Korean Service       | 8004      | 8000      | korean_service       |
| Market Service       | 8005      | 8000      | market_service       |
| Notification Service | 8006      | 8000      | notification_service |
| PostgreSQL           | 5433      | 5432      | -                    |
| Redis                | 6379      | 6379      | -                    |

## 실행 방법

### 전체 시스템 실행

```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env 파일 수정

# 2. Docker Compose로 모든 서비스 실행
docker-compose up -d

# 3. 로그 확인
docker-compose logs -f

# 4. 특정 서비스만 재시작
docker-compose restart math-service

# 5. 전체 종료
docker-compose down
```

### 개별 서비스 실행 (개발 모드)

```bash
# Math Service
cd services/math-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Math Celery Worker
celery -A app.celery_app worker --loglevel=info

# Korean Service
cd services/korean-service
pip install -r requirements.txt
python korean_main.py

# Korean Celery Worker
celery -A app.celery_app worker --loglevel=info --concurrency=4

# Auth Service
cd services/auth-service
pip install -r requirements.txt
uvicorn auth_main:app --reload --port 8000

# Market Service
cd services/market-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API 문서

각 서비스는 자동 생성된 API 문서를 제공합니다:

- Math Service: http://localhost:8001/docs
- English Service: http://localhost:8002/docs
- Auth Service: http://localhost:8003/docs
- Korean Service: http://localhost:8004/docs
- Market Service: http://localhost:8005/docs
- Notification Service: http://localhost:8006/docs

## 보안

### 인증 흐름

1. **로그인**: 사용자가 Auth Service로 로그인
2. **토큰 발급**: JWT 토큰 생성 (7일 유효)
3. **토큰 검증**: 다른 서비스가 Auth Service의 `/api/auth/verify-token`으로 검증
4. **권한 확인**: 교사/학생 역할 기반 접근 제어

### 보안 정책

- JWT 토큰 기반 stateless 인증
- bcrypt 비밀번호 해싱 (rounds=12)
- CORS 설정 (프론트엔드 도메인만 허용)
- 서비스 간 내부 통신 (Docker 네트워크)
- 환경 변수로 민감 정보 관리

## 개발 가이드

### 새 서비스 추가

1. `services/` 디렉토리에 새 서비스 폴더 생성
2. `Dockerfile` 및 `requirements.txt` 작성
3. `docker-compose.yml`에 서비스 추가
4. PostgreSQL 스키마 생성 (`scripts/init-schema.sql`)
5. Auth Service 미들웨어 연동
6. README.md 작성

### 데이터베이스 마이그레이션

```bash
# 스키마 초기화 (주의: 데이터 손실)
docker-compose down -v
docker-compose up -d postgres

# 특정 서비스 스키마만 재생성
docker exec -it qt_project_db psql -U postgres -d qt_project_db
DROP SCHEMA math_service CASCADE;
# 서비스 재시작하면 자동 생성
```

### 로컬 개발 팁

- **Celery Worker**: 로컬에서는 `--pool=solo` 옵션 사용
- **Redis**: Docker로 실행하고 로컬에서 연결
- **PostgreSQL**: pgAdmin 또는 DBeaver로 DB 관리
- **Hot Reload**: `--reload` 옵션으로 자동 재시작

## 트러블슈팅

### 일반적인 문제

1. **포트 충돌**: `docker-compose down` 후 재시작
2. **DB 연결 실패**: PostgreSQL 컨테이너 상태 확인
3. **Celery 작업 실패**: Redis 연결 및 Worker 로그 확인
4. **AI API 에러**: API 키 유효성 및 할당량 확인
5. **인증 실패**: Auth Service 상태 및 토큰 만료 확인

### 로그 확인

```bash
# 전체 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f math-service

# Celery Worker 로그
docker-compose logs -f celery-worker
```
