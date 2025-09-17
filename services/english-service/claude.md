# 🤖 English Service AI 개발 가이드

이 문서는 AI 어시스턴트가 `english-service` 프로젝트의 코드베이스를 이해하고, 일관성 있는 코드를 작성하며, 효과적으로 기여할 수 있도록 돕기 위한 가이드입니다.

## 1. 기술 스택 (Tech Stack)

- **언어**: Python 3.12+
- **프레임워크**: FastAPI
- **데이터베이스**:
  - **개발/독립 실행**: SQLite
  - **통합 환경 (Docker)**: PostgreSQL
- **ORM**: SQLAlchemy
- **데이터 유효성 검사**: Pydantic
- **AI 모델**: Google Gemini (Flash, Pro)
- **서버**: Uvicorn

## 2. 프로젝트 구조 (Project Structure)

`english-service`는 FastAPI 표준 구조를 따르며, 주요 파일과 디렉터리는 다음과 같습니다.

```
english-service/
├── app/
│   ├── core/
│   │   └── config.py          # 환경 변수 및 설정 관리
│   ├── database/
│   │   └── connection.py      # 데이터베이스 세션 관리
│   ├── models/
│   │   └── models.py          # SQLAlchemy 데이터베이스 모델
│   ├── routers/
│   │   └── generation.py      # 문제 생성/채점 관련 API 라우터
│   ├── schemas/
│   │   └── schemas.py         # Pydantic 스키마 (데이터 입출력 형식 정의)
│   ├── services/
│   │   ├── ai_service.py      # Gemini AI 호출 및 결과 파싱 (채점)
│   │   └── question_generator.py # 문제 생성 프롬프트 생성 및 로직
│   └── main.py                # FastAPI 애플리케이션 진입점
├── data/
│   └── ...                    # (필요 시) 초기 데이터 파일
├── static/
│   └── ...                    # 프론트엔드 정적 파일
├── .env                       # 환경 변수 (Git 추적 안 함)
├── requirements.txt           # Python 의존성 목록
└── README.md                  # 프로젝트 개요 및 사용법
```

## 3. 명령어 (Commands)

프로젝트 실행 및 관리를 위한 주요 명령어입니다.

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate # Linux/macOS
venv\Scripts\activate    # Windows

# 2. 의존성 설치
pip install -r requirements.txt

# 3. (최초 실행 시) 데이터베이스 초기화
python -m app.init_db # 예시 명령어, 실제 스크립트명 확인 필요

# 4. 개발 서버 실행 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# 5. Docker Compose로 전체 서비스 실행 (프로젝트 루트에서)
docker-compose up -d english-service
```

## 4. 코드 스타일 및 규칙 (Code Style & Conventions)

- **포맷팅**: `black` 포맷터를 따릅니다.
- **타입 힌트**: 모든 함수 정의와 변수 선언에 타입 힌트를 명시적으로 사용합니다. (`from typing import List, Dict, Any, Optional`)
- **Pydantic 모델**: API의 요청(Request) 및 응답(Response) 본문은 `schemas`에 정의된 Pydantic 모델을 사용합니다.
- **비동기 처리**: I/O 바운드 작업(DB 쿼리, 외부 API 호출)은 `async`/`await`를 사용합니다.
- **의존성 주입**: FastAPI의 `Depends`를 적극적으로 사용하여 DB 세션, 현재 사용자 정보 등을 주입합니다.
- **에러 처리**: 비즈니스 로직 상 예상되는 오류는 `HTTPException`을 발생시켜 명확한 상태 코드와 메시지를 클라이언트에 전달합니다.
- **환경 변수**: API 키, DB 정보 등 민감한 정보는 `config.py`를 통해 `.env` 파일에서 로드합니다. 코드에 직접 하드코딩하지 않습니다.

## 5. 저장소 에티켓 (Repository Etiquette)

- **브랜치 명명**: `feature/issue-123-brief-description` 또는 `fix/login-bug` 형식을 따릅니다.
- **커밋 메시지**: Conventional Commits 형식을 사용합니다.
  - `feat: 영어 문제 유형 추가 기능 구현`
  - `fix: AI 채점 시 JSON 파싱 오류 수정`
  - `docs: claude.md 가이드 파일 추가`
- **PR (Pull Request)**: `main` 브랜치로 직접 푸시하는 것을 금지합니다. 기능 개발 후 PR을 생성하여 코드 리뷰를 요청합니다.

## 6. 핵심 파일 및 유틸리티 (Core Files & Utilities)

- **`app/services/question_generator.py`**:
  - **역할**: 사용자의 요청(학년, 문제 수, 유형 비율 등)을 바탕으로 Gemini AI에 전달할 **프롬프트**를 동적으로 생성하는 핵심 로직이 담겨 있습니다.
  - **주요 클래스**: `PromptGenerator`, `QuestionDistributionCalculator`
  - **수정 시**: 프롬프트 구조 변경이 AI의 출력(JSON 형식)에 큰 영향을 미치므로 신중하게 접근해야 합니다.

- **`app/services/ai_service.py`**:
  - **역할**: 주관식/서술형 문제 채점을 위해 Gemini AI를 호출하고, AI의 응답(주로 텍스트)을 파싱하여 구조화된 JSON(점수, 피드백 등)으로 변환합니다.
  - **주요 클래스**: `AIService`
  - **수정 시**: AI 응답이 불안정할 수 있으므로, `_validate_and_fix_ai_response` 와 `_extract_fields_by_regex` 같은 예외 처리 및 데이터 보정 로직이 매우 중요합니다.

- **`app/schemas/schemas.py`**:
  - **역할**: API의 모든 데이터 입출력 형식을 Pydantic 모델로 정의합니다. API 엔드포인트를 수정할 때 반드시 함께 확인하고 수정해야 합니다.

## 7. "절대 건드리지 마시오" 목록 (Do Not Touch List)

- **프롬프트의 JSON 형식 정의**: `question_generator.py`의 `json_template` 변수와 프롬프트 내 "응답 형식" 부분은 AI 출력과 직접적으로 연결되므로 임의로 키(key) 이름을 변경하거나 구조를 수정하지 마세요. 변경이 필요하면 백엔드 전체 파싱 로직과 프론트엔드 표시 로직을 함께 수정해야 합니다.

- **AI 채점 프롬프트 규칙**: `ai_service.py`의 채점 프롬프트에 있는 "절대 규칙"과 "JSON 형식" 부분은 AI가 안정적인 포맷으로 응답하도록 유도하는 핵심 요소입니다. 이 부분을 완화하거나 제거하지 마세요.

- **기존 데이터베이스 모델 필드**: `models/models.py`에 정의된 기존 테이블의 컬럼을 삭제하거나 타입을 변경하지 마세요. 필드 추가는 가능하지만, 기존 데이터와의 호환성을 반드시 고려해야 합니다.

- **환경 변수 로직**: `core/config.py`의 설정 로드 방식을 변경하지 마세요. 새로운 설정이 필요하면 기존 패턴에 따라 추가합니다.