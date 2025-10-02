# Auth Service

학생-교사 교육 플랫폼의 인증 및 사용자 관리를 담당하는 마이크로서비스입니다.

## 시스템 개요

Auth Service는 교사와 학생의 회원가입, 인증, 클래스룸 관리, 쪽지 기능을 제공합니다.

### 주요 기능

#### 1. 사용자 인증 (Authentication)
- **교사/학생 회원가입**: 역할 기반 분리된 가입 프로세스
- **로그인/로그아웃**: JWT 토큰 기반 인증
- **아이디 중복 체크**: 실시간 중복 검증
- **프로필 조회**: 본인 정보 확인

#### 2. 클래스룸 관리 (Classroom Management)
- **클래스 생성**: 교사가 고유 클래스 코드로 클래스룸 생성
- **학생 가입 요청**: 클래스 코드로 가입 신청
- **가입 승인/거부**: 교사가 학생 요청 검토
- **학생 직접 등록**: 교사가 학생을 직접 등록 (자동 승인)
- **클래스 관리**: 클래스 정보 수정, 삭제, 학생 제거

#### 3. 쪽지 시스템 (Messaging)
- **쪽지 전송**: 같은 클래스의 교사-학생 간 메시지 전송
- **수신함 조회**: 페이지네이션, 필터링(읽음/안읽음/별표), 검색
- **읽음 처리**: 자동/수동 읽음 상태 업데이트
- **즐겨찾기**: 중요 메시지 별표 표시
- **삭제**: 논리적 삭제 (복구 가능)

### 데이터 모델

#### User Models
- **Teacher**: 교사 정보 (username, email, name, phone)
- **Student**: 학생 정보 (username, email, name, phone, parent_phone, school_level, grade)

#### Classroom Models
- **ClassRoom**: 클래스 정보 (name, school_level, grade, class_code, teacher_id)
- **StudentJoinRequest**: 학생 가입 요청 (student_id, classroom_id, status: pending/approved/rejected)

#### Message Model
- **Message**: 쪽지 정보 (subject, content, sender_id, sender_type, receiver_id, receiver_type, classroom_id)

### API 엔드포인트

#### Authentication (`/api/auth`)
```
POST   /check-username           # 아이디 중복 체크
POST   /teacher/signup           # 교사 회원가입
POST   /student/signup           # 학생 회원가입
POST   /teacher/login            # 교사 로그인
POST   /student/login            # 학생 로그인
GET    /teacher/me               # 교사 프로필 조회
GET    /student/me               # 학생 프로필 조회
GET    /students/{student_id}    # 특정 학생 정보 조회
```

#### Classrooms (`/api/classrooms`)
```
POST   /create                                   # 클래스 생성
GET    /my-classrooms                            # 내 클래스 목록 (교사)
GET    /my-classrooms/student                    # 내 클래스 목록 (학생)
GET    /{classroom_id}                           # 클래스 상세 조회
PUT    /{classroom_id}                           # 클래스 정보 수정
DELETE /{classroom_id}                           # 클래스 삭제
GET    /{classroom_id}/students                  # 클래스 학생 목록
POST   /{classroom_id}/students/register         # 학생 직접 등록
DELETE /{classroom_id}/students/{student_id}     # 학생 제거
POST   /join-request                             # 가입 요청 생성
GET    /join-requests/pending                    # 대기 중인 가입 요청 목록
PUT    /join-requests/{request_id}/approve       # 가입 요청 승인/거부
GET    /student/{student_id}/classrooms-with-teachers  # 학생의 클래스 및 교사 정보
```

#### Messages (`/api/messages`)
```
GET    /recipients                # 메시지 수신 가능한 대상 목록
POST   /                          # 메시지 전송
GET    /                          # 받은 메시지 목록 (페이징, 필터, 검색)
GET    /{message_id}              # 메시지 상세 조회
PUT    /{message_id}/read         # 읽음 처리
PUT    /{message_id}/star         # 즐겨찾기 토글
DELETE /{message_id}              # 메시지 삭제
```

### 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL (auth_service schema)
- **ORM**: SQLAlchemy
- **Authentication**: JWT (HS256)
- **Password Hashing**: bcrypt
- **Cache**: Redis (클래스 코드 저장)
- **External Services**: Notification Service (메시지 알림)

### 인증 방식

- JWT 토큰 기반 인증
- Bearer 토큰을 Authorization 헤더에 포함
- 토큰 유효기간: 7일 (개발 환경)
- 교사/학생 타입별 토큰 구분

### 보안 정책

- 비밀번호는 bcrypt로 해싱하여 저장
- 같은 클래스에 속한 교사-학생만 쪽지 전송 가능
- 본인 정보만 조회/수정 가능
- 교사만 클래스 생성/관리 가능

### 환경 변수

```bash
DATABASE_URL=postgresql://user:password@postgres:5432/qt_project_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key
NOTIFICATION_SERVICE_URL=http://notification-service:8000
PORT=8000
```

### 실행 방법

```bash
# Docker Compose로 실행
docker-compose up auth-service

# 개발 모드 (로컬)
cd backend/services/auth-service
pip install -r requirements.txt
uvicorn auth_main:app --reload --port 8000
```

### 포트

- **서비스 포트**: 8003 (외부) → 8000 (내부)

### 의존 서비스

- PostgreSQL (데이터베이스)
- Redis (캐싱)
- Notification Service (메시지 알림, 선택적)
