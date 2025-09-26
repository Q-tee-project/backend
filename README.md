# 통합 교육 플랫폼 (Unified Education Platform)

수학 문제 생성/채점 시스템과 영어 문제 생성 시스템을 통합한 교육 플랫폼입니다.

## 프로젝트 구조

```
unified-education-platform/
├── services/
│   ├── math-service/          # 수학 문제 생성/채점 서비스
│   │   ├── app/              # FastAPI 애플리케이션
│   │   ├── static/           # 정적 파일
│   │   └── math_main.py      # 메인 애플리케이션
│   └── english-service/       # 영어 문제 생성 서비스
│       ├── models.py         # 데이터 모델
│       ├── routes.py         # API 라우트
│       └── english_main.py   # 메인 애플리케이션
├── shared/
│   ├── config/               # 공통 설정
│   ├── models/               # 공통 모델
│   └── utils/                # 공통 유틸리티
├── scripts/                  # 배포/관리 스크립트
└── docs/                     # 문서
```

## 🚨 중요: 초기 설정 가이드

백엔드를 처음 클론받은 후 Docker Compose를 실행하기 전에 **반드시** [SETUP_GUIDE.md](./SETUP_GUIDE.md)를 먼저 읽어주세요.

### 빠른 시작 (Quick Start)

```bash
# 1. 환경 변수 설정 (.env 파일 생성 필수)
cp .env.example .env  # 파일이 있다면
# 또는 직접 .env 파일 생성하여 API 키 설정

# 2. 순차적 실행 (권장)
docker-compose up -d postgres redis
sleep 20
docker-compose up -d auth-service  
sleep 10
docker-compose up -d math-service english-service korean-service celery-worker flower

# 3. 상태 확인
docker-compose ps
curl http://localhost:8003/health
```

문제 발생 시 전체 초기화:
```bash
docker-compose down -v --remove-orphans
docker-compose build --no-cache
# 위의 순차적 실행 다시 진행
```

## 개발 환경 설정

### 1. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# 데이터베이스 설정
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=qt_project_db

# API 키 설정 (실제 키로 교체 필요)
GEMINI_API_KEY=your_gemini_api_key_here
MATH_GEMINI_API_KEY=your_gemini_api_key_here
ENGLISH_GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here

# Auth 서비스 설정
AUTH_SECRET_KEY=your-secret-key-change-in-production-please-use-a-strong-random-key
```

### 2. 개별 설정

각 개발자는 자신만의 설정을 사용할 수 있습니다:

**API 키:**

- `MATH_GEMINI_API_KEY`: 수학 서비스용 Gemini API 키
- `ENGLISH_GEMINI_API_KEY`: 영어 서비스용 Gemini API 키
- `GEMINI_API_KEY`: 공통 Gemini API 키 (개별 키가 없을 때 사용)
- `GOOGLE_VISION_API_KEY`: Google Vision API 키 (수학 서비스의 손글씨/이미지 OCR용)

**데이터베이스 설정:**

- `DB_USER`: 데이터베이스 사용자명 (예: postgres, root)
- `DB_PASSWORD`: 데이터베이스 비밀번호 (예: 1234, mypassword123)
- `DB_NAME`: 데이터베이스 이름 (기본: education_platform)

### 3. Docker로 전체 환경 실행

**⚠️ 주의: 서비스 시작 순서가 중요합니다!**

```bash
# 방법 1: 순차적 시작 (권장)
# 1. 데이터베이스와 Redis 먼저 시작
docker-compose up -d postgres redis

# 2. 데이터베이스 초기화 대기 (15-20초)
sleep 20

# 3. Auth 서비스 시작 (teachers 테이블 생성)
docker-compose up -d auth-service

# 4. Auth 서비스 준비 대기 (10초)
sleep 15

# 5. 나머지 서비스 시작
docker-compose up -d math-service english-service celery-worker flower

# 방법 2: 전체 시작 (문제 발생 시 방법 1 사용)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

**Docker로 실행되는 서비스:**

- **PostgreSQL**: 포트 5432 (데이터베이스)
- **Redis**: 포트 6379 (Celery용)
- **Math Service**: 포트 8001 (수학 문제 생성/채점)
- **English Service**: 포트 8002 (영어 문제 생성)
- **Celery Worker**: 백그라운드 작업 처리
- **Flower**: 포트 5555 (Celery 모니터링)

## 서비스 실행

### Math Service (포트: 8000)

```bash
cd services/math-service
python math_main.py
```

### English Service (포트: 8000)

```bash
cd services/english-service
python english_main.py
```

**주의**: 두 서비스 모두 포트 8000을 사용하므로 동시에 실행할 수 없습니다. 개발 시에는 하나씩 실행하세요.

## Git 협업 워크플로우

### 1. 브랜치 생성

```bash
# 새로운 기능 브랜치 생성
git checkout -b feature/your-feature-name

# 또는 개발자별 브랜치
git checkout -b dev/your-name/feature-name
```

### 2. 일일 개발 사이클

```bash
# 작업 전 최신 코드 받기
git checkout main
git pull origin main
git checkout your-branch
git merge main

# 개발 및 커밋
git add .
git commit -m "feat: your feature description"
git push origin your-branch
```

### 3. Pull Request 생성

- GitHub에서 PR 생성
- 코드 리뷰 요청
- 승인 후 main 브랜치에 merge

## 브랜치 전략

- `main`: 메인 브랜치 (프로덕션 코드)
- `develop`: 개발 통합 브랜치
- `feature/*`: 새로운 기능 개발
- `hotfix/*`: 긴급 수정
- `dev/[name]/*`: 개발자별 개인 브랜치

## API 엔드포인트

### Math Service (http://localhost:8000)

- `POST /api/math-generation/generate`: 수학 문제 생성
- `POST /api/math-generation/grade`: 수학 문제 채점

### English Service (http://localhost:8000)

- `POST /generate-test`: 영어 문제 생성
- `GET /text-types`: 텍스트 유형 조회

## 개발 가이드라인

1. **코드 스타일**: 각 서비스의 기존 코드 스타일을 유지
2. **커밋 메시지**: Conventional Commits 형식 사용
3. **API 키 보안**: `.env` 파일은 절대 커밋하지 않기
4. **테스트**: 새로운 기능 추가 시 테스트 코드 작성
5. **문서화**: API 변경 시 문서 업데이트

## 환경 분리

- **개발 환경**: 각자의 로컬 환경
- **테스트 환경**: 공통 테스트 서버
- **프로덕션 환경**: 배포 서버

## 트러블슈팅

### 포트 설정

두 서비스 모두 포트 8000을 사용합니다. 개발 시에는 필요한 서비스만 실행하세요.

### API 키 오류

각 서비스별로 다른 API 키를 사용할 수 있습니다. `.env` 파일에서 개별 키를 설정하세요.

### 데이터베이스 연결 오류

`DATABASE_URL`을 확인하고 데이터베이스 서버가 실행 중인지 확인하세요.
