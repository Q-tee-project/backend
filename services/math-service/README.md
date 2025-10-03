# Math Service

AI 기반 수학 문제 생성, 채점, 관리를 담당하는 마이크로서비스입니다.

## 시스템 개요

Math Service는 Gemini 2.5 Pro와 GPT-4o-mini를 활용하여 교육과정 기반 수학 문제를 자동 생성하고, AI 채점 및 워크시트 관리 기능을 제공합니다.

### 주요 기능

#### 1. 문제 생성 (Problem Generation)
- **AI 기반 문제 생성**: Gemini 2.5 Pro를 활용한 수학 문제 자동 생성
- **AI Judge 검증**: GPT-4o-mini를 통한 4가지 기준 검증 (수학정확성, 정답일치, 완결성, 논리성)
- **교육과정 기반**: 학년/학기/단원/차시별 맞춤 문제 생성
- **난이도 조절**: A(직접계산), B(응용번역), C(통합발견) 3단계 난이도
- **문제 유형**: 객관식(multiple_choice), 단답형(short_answer)
- **TikZ 그래프 생성**: 그래프 단원에서 자동 LaTeX 시각화 코드 생성
- **재시도 메커니즘**: 불합격 문제 피드백 기반 재생성 (최대 3회)
- **비동기 처리**: Celery를 통한 백그라운드 작업

#### 2. 워크시트 관리 (Worksheet Management)
- **워크시트 생성**: 10개 또는 20개 문제로 구성된 문제지 생성
- **생성 이력 조회**: 교사별 문제 생성 기록 관리
- **워크시트 수정/삭제**: 제목, 설정 변경 및 삭제
- **워크시트 복사**: 마켓플레이스 구매 시 워크시트 복제
- **상태 관리**: draft, processing, completed, failed, published

#### 3. 문제 관리 (Problem Management)
- **문제 수정**: 개별 문제 내용, 정답, 해설 수정
- **문제 재생성**: AI를 통한 특정 요구사항 기반 문제 재생성
- **TikZ 지원**: 그래프 문제의 LaTeX 코드 관리

#### 4. AI 채점 (AI Grading)
- **객관식 자동 채점**: 즉시 정답 비교 및 점수 산출
- **서술형 AI 채점**: Gemini를 활용한 주관식 답안 분석
- **OCR 지원**: 손글씨 답안 이미지 텍스트 추출 (Google Vision API)
- **캔버스 방식**: 문제별 직접 입력 및 OCR 혼합 채점
- **피드백 제공**: AI 피드백, 잘한 점, 개선점, 키워드 분석

#### 5. 시험 세션 (Test Session)
- **시험 제출**: 학생의 시험 답안 제출
- **답안 저장**: 개별 문제별 답안 저장
- **OCR 답안 저장**: 손글씨 이미지 업로드 및 인식

#### 6. 교육과정 (Curriculum)
- **교육과정 구조 조회**: 학년/학기별 단원 및 차시 정보
- **단원 목록**: 특정 학년/학기의 단원 리스트
- **차시 목록**: 특정 단원의 차시 리스트

### 데이터 모델

#### Worksheet Models
- **Worksheet**: 문제지 정보 (title, school_level, grade, semester, unit_name, chapter_name, problem_count, difficulty_ratio, problem_type_ratio, status, celery_task_id, teacher_id)
- **WorksheetStatus**: draft, processing, completed, failed, published

#### Problem Models
- **Problem**: 문제 정보 (worksheet_id, sequence_order, problem_type, difficulty, question, choices, correct_answer, explanation, tikz_code, has_diagram, diagram_type)

#### Grading Models
- **GradingSession**: 채점 세션 (worksheet_id, celery_task_id, total_problems, correct_count, total_score, max_possible_score, ocr_text, ocr_results, input_method, graded_by)
- **ProblemGradingResult**: 문제별 채점 결과 (grading_session_id, problem_id, user_answer, correct_answer, is_correct, score, ai_score, ai_feedback, strengths, improvements)

#### Curriculum Model
- **Curriculum**: 교육과정 정보 (grade, subject, semester, unit_number, unit_name, chapter_number, chapter_name, learning_objectives, keywords, difficulty_levels)

### API 엔드포인트

#### Worksheets (`/api/worksheets`)
```
POST   /generate                    # 문제 생성 (비동기)
GET    /generation-history          # 생성 이력 조회
GET    /generation/{generation_id}  # 생성 상세 조회
GET    /                            # 워크시트 목록 조회
GET    /{worksheet_id}              # 워크시트 상세 조회
PUT    /{worksheet_id}              # 워크시트 수정
DELETE /{worksheet_id}              # 워크시트 삭제
POST   /copy                        # 워크시트 복사
```

#### Problems (`/api/problems`)
```
PUT    /{problem_id}                # 문제 수정
POST   /regenerate-async            # 문제 재생성 (비동기)
```

#### Grading (`/api/grading`)
```
POST   /                            # 워크시트 채점 (이미지 업로드)
POST   /canvas                      # 워크시트 채점 (캔버스 방식)
GET    /assignment-results          # 과제 채점 결과 목록
POST   /ai-grade                    # AI 채점 시작 (비동기)
GET    /task/{task_id}              # AI 채점 상태 조회
GET    /sessions/{session_id}       # 채점 세션 상세 조회
PUT    /sessions/{session_id}       # 채점 세션 수정
GET    /student/{student_id}        # 학생 채점 결과 조회
GET    /student/{student_id}/info   # 학생 정보 조회
```

#### Test Sessions (`/api/test-sessions`)
```
POST   /submit                      # 시험 제출
POST   /answers/save                # 답안 저장
POST   /answers/save-ocr            # OCR 답안 저장
```

#### Curriculum (`/api/curriculum`)
```
GET    /structure                   # 교육과정 구조 조회
GET    /units                       # 단원 목록 조회
GET    /chapters                    # 차시 목록 조회
```

#### Tasks (`/api/tasks`)
```
GET    /{task_id}/status            # Celery 태스크 상태 조회
GET    /status/{task_id}            # 태스크 상태 조회 (별칭)
```

### 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL (math_service schema)
- **ORM**: SQLAlchemy
- **Task Queue**: Celery + Redis
- **AI Models**:
  - Gemini 2.5 Pro (문제 생성)
  - GPT-4o-mini (AI Judge 검증)
  - Gemini (서술형 채점)
- **OCR**: Google Vision API
- **Authentication**: Auth Service (중앙 인증)
- **Cache**: Redis

### AI 문제 생성 플로우

1. **사용자 요청**: 학년/단원/난이도/문제 수 설정
2. **Celery 비동기 처리**: 백그라운드에서 문제 생성
3. **교육과정 로드**: JSON 파일에서 교육과정 데이터 조회
4. **프롬프트 생성**: 난이도별 Mental Sandbox 프롬프트 구성
5. **Gemini 호출**: 문제 생성 API 요청
6. **AI Judge 검증**: GPT-4o-mini로 4가지 기준 검증
   - mathematical_accuracy (1-5): 수학적 정확성
   - consistency (1-5): 정답 일치도 (필수 ≥ 4.0)
   - completeness (1-5): 완결성
   - logic_flow (1-5): 논리성
7. **재시도**: 불합격 문제는 피드백 포함 재생성 (최대 3회)
8. **DB 저장**: Worksheet 및 Problem 저장

### AI 채점 플로우

1. **답안 수집**: 객관식 선택 + 서술형 이미지/텍스트
2. **OCR 처리**: Google Vision API로 손글씨 텍스트 변환
3. **객관식 채점**: 정답 비교 및 즉시 점수 산출
4. **서술형 AI 채점**: Gemini로 주관식 답안 분석
   - AI 점수 (0-100)
   - 피드백, 잘한 점, 개선점
   - 키워드 매칭 비율
5. **결과 저장**: GradingSession 및 ProblemGradingResult 저장

### 인증 방식

- Auth Service를 통한 중앙 인증
- Bearer 토큰을 Authorization 헤더에 포함
- Auth Service의 `/api/auth/verify-token` 엔드포인트로 토큰 검증
- 교사/학생 구분 및 권한 관리

### 환경 변수

```bash
DATABASE_URL=postgresql://user:password@postgres:5432/qt_project_db
REDIS_URL=redis://redis:6379/0
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_VISION_API_KEY=your-google-vision-api-key
OPENAI_API_KEY=your-openai-api-key
AUTH_SERVICE_URL=http://auth-service:8000
PORT=8000
```

### 실행 방법

```bash
# Docker Compose로 실행
docker-compose up math-service celery-worker

# 개발 모드 (로컬)
cd backend/services/math-service
pip install -r requirements.txt

# FastAPI 서버
uvicorn app.main:app --reload --port 8000

# Celery Worker
celery -A app.celery_app worker --loglevel=info
```

### 포트

- **서비스 포트**: 8001 (외부) → 8000 (내부)

### 의존 서비스

- PostgreSQL (데이터베이스)
- Redis (캐싱, Celery 브로커)
- Auth Service (인증)
- Celery Worker (비동기 작업)

### 주요 특징

#### TikZ 그래프 생성
- **적용 단원**: "그래프와 비례" (좌표평면, 정비례, 반비례)
- **자동 생성**: 문제의 60% 이상 그래프 포함
- **답안 은닉**: 문제에서 묻는 점은 그래프에 표시하지 않음
- **LaTeX 코드**: 프론트엔드에서 SVG로 렌더링 가능한 TikZ 코드 제공

#### AI Judge 검증 시스템
- **4가지 평가 기준**: 각 1-5점 척도
- **엄격한 합격 조건**: consistency ≥ 4.0 AND 평균 ≥ 3.5
- **피드백 기반 재생성**: 불합격 문제의 피드백을 다음 프롬프트에 포함
- **부분 재생성**: 부족한 개수만큼만 추가 생성

#### 비동기 처리
- **Celery**: Redis를 브로커로 사용한 백그라운드 작업
- **Task 상태 추적**: task_id로 실시간 상태 조회
- **에러 핸들링**: 실패 시 error_message 저장

### 문서

- **플로우 다이어그램**: [MATH_PROBLEM_GENERATION_FLOW.md](./MATH_PROBLEM_GENERATION_FLOW.md)
- **교육과정 데이터**: [data/middle1_math_curriculum.json](./data/middle1_math_curriculum.json)
