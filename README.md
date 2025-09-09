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

## 개발 환경 설정

### 1. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 각자의 API 키를 설정하세요:

```bash
cp .env.example .env
```

### 2. 개별 API 키 설정

각 개발자는 자신만의 API 키를 사용할 수 있습니다:

- `MATH_GEMINI_API_KEY`: 수학 서비스용 API 키
- `ENGLISH_GEMINI_API_KEY`: 영어 서비스용 API 키
- `GEMINI_API_KEY`: 공통 API 키 (개별 키가 없을 때 사용)

### 3. 데이터베이스 설정

각 서비스는 독립적인 데이터베이스를 사용하거나 공통 데이터베이스의 다른 스키마를 사용할 수 있습니다.

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