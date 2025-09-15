# 🚨 백엔드 초기 설정 가이드

> **⚠️ 중요**: 백엔드를 처음 클론받은 후 `docker-compose up -d`를 실행하기 전에 **반드시** 이 가이드를 따라주세요.

## 📋 사전 요구사항

다음 프로그램들이 설치되어 있어야 합니다:

- **Docker** (>= 20.0)
- **Docker Compose** (>= 2.0)  
- **Git**

## 🛠️ 1단계: 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# 데이터베이스 설정
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_NAME=qt_project_db

# API 키 설정 (필수!)
GEMINI_API_KEY=your_gemini_api_key_here
MATH_GEMINI_API_KEY=your_gemini_api_key_here  
ENGLISH_GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here

# 인증 서비스 설정
AUTH_SECRET_KEY=your_very_secure_secret_key_for_jwt_tokens_change_this_in_production
```

**🔑 API 키 발급 방법:**

1. **Gemini API**: [Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급
2. **Google Vision API**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)에서 발급

## 🚀 2단계: Docker 컨테이너 실행

**⚠️ 중요: 순서대로 실행해야 합니다!**

### 방법 1: 순차적 실행 (권장)

```bash
# 1. 데이터베이스와 Redis 먼저 시작
docker-compose up -d postgres redis

# 2. 데이터베이스 초기화 대기 (20초)
echo "데이터베이스 초기화 중... 20초 대기"
sleep 20

# 3. Auth 서비스 시작 (shared 스키마 테이블 생성)
docker-compose up -d auth-service

# 4. Auth 서비스 테이블 생성 대기 (10초)  
echo "Auth 서비스 테이블 생성 중... 10초 대기"
sleep 10

# 5. 나머지 서비스 시작
docker-compose up -d math-service english-service celery-worker flower

# 6. 모든 서비스 상태 확인
docker-compose ps
```

### 방법 2: 한 번에 실행 (문제 발생 시 방법 1 사용)

```bash
docker-compose up -d
```

## 🔍 3단계: 서비스 상태 확인

### 컨테이너 상태 확인

```bash
# 모든 컨테이너가 실행 중인지 확인
docker-compose ps

# 특정 서비스 로그 확인
docker-compose logs auth-service
docker-compose logs math-service
```

**정상 상태일 때:**
```
NAME                    COMMAND                  SERVICE             STATUS              PORTS
auth_service           "python auth_main.py"     auth-service        running             0.0.0.0:8003->8000/tcp
math_service           "python math_main.py"     math-service        running             0.0.0.0:8001->8000/tcp
qt_project_db          "docker-entrypoint.s…"   postgres            running             0.0.0.0:5432->5432/tcp
qt_project_redis       "docker-entrypoint.s…"   redis               running             0.0.0.0:6379->6379/tcp
```

### API 연결 테스트

```bash
# Auth Service 헬스 체크
curl http://localhost:8003/health

# Math Service 연결 테스트
curl http://localhost:8001/

# English Service 연결 테스트  
curl http://localhost:8002/
```

### 웹 브라우저에서 확인

- **Auth Service API 문서**: http://localhost:8003/docs
- **Math Service API 문서**: http://localhost:8001/docs
- **English Service API 문서**: http://localhost:8002/docs
- **Celery 모니터링**: http://localhost:5555

## 🚨 문제 해결 가이드

### 자주 발생하는 오류들

#### 1. "테이블을 찾을 수 없음" 오류

```
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'worksheets.teacher_id' could not find table 'shared.teachers'
```

**원인**: Auth Service가 먼저 실행되지 않아서 `shared.teachers` 테이블이 생성되지 않음

**해결방법**:
```bash
# 모든 컨테이너 중지 및 삭제
docker-compose down -v

# 순차적으로 다시 시작 (방법 1 사용)
docker-compose up -d postgres redis
sleep 20
docker-compose up -d auth-service  
sleep 10
docker-compose up -d math-service english-service celery-worker flower
```

#### 2. "Connection refused" 오류

**원인**: 데이터베이스가 완전히 준비되기 전에 서비스가 연결을 시도

**해결방법**:
```bash
# 데이터베이스 로그 확인
docker-compose logs postgres

# "database system is ready to accept connections" 메시지 확인 후 재시작
docker-compose restart math-service auth-service
```

#### 3. API 키 관련 오류

**원인**: `.env` 파일의 API 키가 잘못되거나 누락됨

**해결방법**:
1. `.env` 파일에서 API 키 확인
2. Gemini API 할당량 확인
3. Google Vision API 활성화 확인

#### 4. 포트 충돌 오류

**원인**: 이미 사용 중인 포트가 있음

**해결방법**:
```bash
# 포트 사용 확인
lsof -i :5432  # PostgreSQL
lsof -i :8001  # Math Service
lsof -i :8003  # Auth Service

# 해당 프로세스 종료 또는 docker-compose.yml에서 포트 변경
```

### 완전 초기화 방법

모든 문제를 해결하기 위한 완전 초기화:

```bash
# 1. 모든 컨테이너와 볼륨 삭제
docker-compose down -v --remove-orphans

# 2. Docker 시스템 정리
docker system prune -f

# 3. 이미지 다시 빌드
docker-compose build --no-cache

# 4. 순차적으로 재시작
docker-compose up -d postgres redis
sleep 20
docker-compose up -d auth-service
sleep 10  
docker-compose up -d math-service english-service celery-worker flower
```

## 📊 데이터베이스 구조 이해

### 스키마 구조

```
qt_project_db/
├── auth_service/        # 🔐 사용자 인증 및 계정 관리
│   ├── teachers         # 선생님 계정
│   ├── students         # 학생 계정  
│   ├── classrooms       # 교실
│   └── student_join_requests # 교실 가입 요청
├── math_service/        # 🧮 수학 서비스 전용
│   ├── worksheets       # 문제지
│   ├── problems         # 개별 문제
│   ├── grading_sessions # 채점 세션
│   └── problem_grading_results # 채점 결과
└── english_service/     # 🇬🇧 영어 서비스 전용
    ├── grammar_categories
    ├── vocabulary_categories  
    └── words
```

### 중요한 설계 원칙

1. **Auth Service Schema**: 사용자 인증 관련 테이블들을 별도 스키마로 관리
2. **Service Schema**: 각 서비스별 전용 테이블은 별도 스키마에 격리
3. **Cross-Schema Reference**: 다른 스키마 참조 시 스키마명 포함 (`auth_service.teachers.id`)

## 🎯 성공적인 설정 완료 체크리스트

- [ ] `.env` 파일이 생성되고 모든 필수 변수가 설정됨
- [ ] `docker-compose ps`에서 모든 서비스가 `running` 상태
- [ ] http://localhost:8003/health 에서 `{"status": "healthy"}` 응답
- [ ] http://localhost:8001/ 에서 Math Service 메시지 확인
- [ ] http://localhost:8002/ 에서 English Service 메시지 확인
- [ ] 서비스 로그에 오류 없음

모든 체크리스트가 완료되면 개발을 시작할 수 있습니다! 🎉

## 💡 추가 팁

### 개발 중 유용한 명령어

```bash
# 특정 서비스만 재시작
docker-compose restart math-service

# 실시간 로그 확인
docker-compose logs -f math-service auth-service

# 데이터베이스 직접 접속
docker-compose exec postgres psql -U postgres -d qt_project_db

# 스키마와 테이블 확인
docker-compose exec postgres psql -U postgres -d qt_project_db -c "\dn"
docker-compose exec postgres psql -U postgres -d qt_project_db -c "\dt auth_service.*"
```

### 성능 최적화

```bash
# Docker Desktop 메모리 할당 4GB 이상 권장
# Docker Desktop 설정 → Resources → Memory

# 불필요한 컨테이너 정리 (주기적 실행)
docker system prune -f --volumes
```

이 가이드를 따라 설정하면 모든 서비스가 정상적으로 실행될 것입니다! 🚀