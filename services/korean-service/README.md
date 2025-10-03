# Korean Service

AI 기반 국어 문제 생성, 채점, 관리를 담당하는 마이크로서비스입니다.

## 시스템 개요

Korean Service는 Gemini 2.5 Pro와 GPT-4o-mini를 활용하여 시/소설/수필/문법 등 다양한 국어 지문 기반 객관식 문제를 자동 생성하고, AI 채점 및 워크시트 관리 기능을 제공합니다.

### 주요 기능

#### 1. 문제 생성 (Problem Generation)
- **AI 기반 문제 생성**: Gemini 2.5 Pro를 활용한 국어 문제 자동 생성
- **AI Judge 검증**: GPT-4o-mini를 통한 유형별 검증
  - **시**: literary_accuracy, relevance, figurative_language_analysis, answer_clarity
  - **소설**: narrative_comprehension, relevance, textual_analysis, answer_clarity
  - **수필/비문학**: argument_comprehension, relevance, critical_thinking, answer_clarity
  - **문법**: grammar_accuracy, example_quality, explanation_clarity, answer_clarity
- **다양한 지문 유형**: 시, 소설, 수필/비문학, 문법
- **문제 유형**: 객관식 (4지선다)
- **난이도 조절**: 상, 중, 하 3단계
- **지문 자동 추출**: 텍스트 파일에서 지문 자동 선택
- **병렬 처리**: ThreadPoolExecutor를 활용한 고속 생성
- **비동기 처리**: Celery를 통한 백그라운드 작업

#### 2. 워크시트 관리 (Worksheet Management)
- **워크시트 생성**: 사용자 지정 문제 수로 구성된 문제지 생성
- **생성 이력 조회**: 교사별 문제 생성 기록 관리
- **워크시트 수정/삭제**: 제목, 설정 변경 및 삭제
- **워크시트 복사**: 마켓플레이스 구매 시 워크시트 복제
- **상태 관리**: draft, processing, completed, failed, published

#### 3. 문제 관리 (Problem Management)
- **문제 수정**: 개별 문제 내용, 정답, 해설 수정
- **문제 재생성**: AI를 통한 특정 요구사항 기반 문제 재생성

#### 4. AI 채점 (AI Grading)
- **객관식 자동 채점**: 즉시 정답 비교 및 점수 산출
- **채점 세션 관리**: 채점 이력 및 결과 저장

#### 5. 과제 관리 (Assignment Management)
- **과제 생성**: 워크시트 기반 과제 생성
- **과제 배포**: 클래스룸 학생들에게 과제 배포
- **과제 제출**: 학생의 과제 답안 제출
- **과제 조회**: 학생별 과제 목록 및 상세 조회

### 데이터 모델

#### Worksheet Models
- **Worksheet**: 문제지 정보
  - title, school_level, grade, korean_type, question_type, difficulty
  - problem_count, question_type_ratio, difficulty_ratio
  - user_text, generation_id, teacher_id, status, celery_task_id
  - actual_korean_type_distribution, actual_question_type_distribution, actual_difficulty_distribution
- **WorksheetStatus**: draft, processing, completed, failed, published

#### Problem Models
- **Problem**: 문제 정보
  - worksheet_id, sequence_order, korean_type, problem_type, difficulty
  - question, choices (JSON), correct_answer, explanation
  - source_text, source_title, source_author, ai_model_used
- **ProblemType**: 객관식 (MULTIPLE_CHOICE)
- **KoreanType**: 시 (POEM), 소설 (NOVEL), 수필/비문학 (NON_FICTION), 문법 (GRAMMAR)
- **Difficulty**: 상 (HIGH), 중 (MEDIUM), 하 (LOW)

#### Grading Models
- **KoreanGradingSession**: 채점 세션
  - worksheet_id, celery_task_id, total_problems, correct_count
  - total_score, max_possible_score, points_per_problem
  - graded_by, input_method, created_at
- **KoreanProblemGradingResult**: 문제별 채점 결과
  - grading_session_id, problem_id, user_answer, correct_answer
  - is_correct, score, points_per_problem, problem_type, input_method
  - ai_score, ai_feedback, strengths, improvements, keyword_score_ratio, explanation

#### Assignment Models
- **Assignment**: 과제 정보
  - title, worksheet_id, classroom_id, teacher_id
  - korean_type, question_type, problem_count, is_deployed
- **AssignmentDeployment**: 과제 배포 정보
  - assignment_id, student_id, classroom_id, status
  - deployed_at, submitted_at, completed_at

### API 엔드포인트

#### Korean Generation (`/api/korean-generation`)
```
POST   /generate                    # 문제 생성 (비동기)
GET    /generation/history          # 생성 이력 조회
GET    /generation/{generation_id}  # 생성 상세 조회
GET    /tasks/{task_id}             # Celery 태스크 상태 조회
GET    /worksheets                  # 워크시트 목록 조회
GET    /worksheets/{worksheet_id}   # 워크시트 상세 조회
PUT    /worksheets/{worksheet_id}   # 워크시트 수정
DELETE /worksheets/{worksheet_id}   # 워크시트 삭제
PUT    /problems/{problem_id}       # 문제 수정
POST   /regenerate-problem/{problem_id}  # 문제 재생성 (비동기)
POST   /copy-worksheet              # 워크시트 복사
```

#### Grading (`/api/korean-generation/grading`)
```
POST   /grade                              # 채점 시작 (비동기)
GET    /sessions/{session_id}              # 채점 세션 상세 조회
PUT    /sessions/{session_id}              # 채점 세션 수정
GET    /sessions/{session_id}/results      # 채점 결과 조회
```

#### Assignments (`/api/korean-generation/assignments`)
```
POST   /                                   # 과제 생성
POST   /deploy                             # 과제 배포
GET    /student/{student_id}               # 학생 과제 목록
GET    /{assignment_id}                    # 과제 상세 조회
POST   /submit                             # 과제 제출
GET    /classroom/{classroom_id}           # 클래스룸 과제 목록
```

#### Market Integration (`/api/korean-generation/market`)
```
GET    /worksheets/{worksheet_id}          # 워크시트 기본 정보 조회
GET    /worksheets/{worksheet_id}/detail   # 워크시트 상세 (문제 포함)
GET    /my-worksheets                      # 사용자 워크시트 목록
POST   /copy-market-worksheet              # 마켓 워크시트 복사
```

### 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL (korean_service schema)
- **ORM**: SQLAlchemy
- **Task Queue**: Celery + Redis
- **AI Models**:
  - Gemini 2.5 Pro (문제 생성)
  - GPT-4o-mini (AI Judge 검증)
- **Authentication**: Auth Service (중앙 인증)
- **Cache**: Redis

### AI 문제 생성 플로우

1. **사용자 요청**: 학교급/학년/국어유형/문제유형/난이도/문제 수 설정
2. **Celery 비동기 처리**: 백그라운드에서 문제 생성 시작
3. **지문 선택**: data/ 폴더에서 해당 유형의 지문 랜덤 선택
   - 시: data/poem/*.txt
   - 소설: data/novel/*.txt
   - 수필/비문학: data/non-fiction/*.txt
   - 문법: data/grammar.txt
4. **병렬 처리**: ThreadPoolExecutor로 작품별 동시 생성 (문법 제외)
5. **프롬프트 생성**: 영어 기반 템플릿으로 문제 생성 프롬프트 구성
6. **Gemini 2.5 Pro 호출**: 문제 생성 API 요청 (배치 생성)
7. **AI Judge 검증**: GPT-4o-mini로 유형별 기준 검증
   - **시**:
     - literary_accuracy (1-5): 문학적 해석 정확성
     - relevance (1-5): 시와의 관련성
     - figurative_language_analysis (1-5): 비유적 표현 분석
     - answer_clarity (1-5): 정답의 명확성
   - **소설**:
     - narrative_comprehension (1-5): 서사 이해도
     - relevance (1-5): 지문과의 관련성
     - textual_analysis (1-5): 서사 기법 분석
     - answer_clarity (1-5): 정답의 명확성
   - **수필/비문학**:
     - argument_comprehension (1-5): 논증 이해도
     - relevance (1-5): 지문과의 관련성
     - critical_thinking (1-5): 비판적 사고
     - answer_clarity (1-5): 정답의 명확성
   - **문법**:
     - grammar_accuracy (1-5): 문법 개념의 정확성
     - example_quality (1-5): 예문의 품질
     - explanation_clarity (1-5): 설명의 명확성
     - answer_clarity (1-5): 정답의 명확성
8. **재시도**: 불합격 문제는 피드백 포함 재생성 (최대 3회)
   - 합격 기준: 모든 항목 ≥ 3.5/5.0
9. **DB 저장**: Worksheet 및 Problem 저장

### AI 채점 플로우

1. **답안 수집**: 객관식 선택
2. **객관식 채점**: 정답 비교 및 즉시 점수 산출
3. **결과 저장**: KoreanGradingSession 및 KoreanProblemGradingResult 저장

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
OPENAI_API_KEY=your-openai-api-key
AUTH_SERVICE_URL=http://auth-service:8000
PORT=8000
```

### 실행 방법

```bash
# Docker Compose로 실행
docker-compose up korean-service korean-celery-worker

# 개발 모드 (로컬)
cd backend/services/korean-service
pip install -r requirements.txt

# FastAPI 서버
python korean_main.py

# Celery Worker
celery -A app.celery_app worker --loglevel=info --concurrency=4 --queues=korean_queue,celery
```

### 포트

- **서비스 포트**: 8004 (외부) → 8000 (내부)

### 의존 서비스

- PostgreSQL (데이터베이스)
- Redis (캐싱, Celery 브로커)
- Auth Service (인증)
- Celery Worker (비동기 작업)

### 주요 특징

#### 지문 기반 문제 생성
- **다양한 지문 유형**: 시, 소설, 수필/비문학, 문법 지문 자동 선택
- **지문 저장소**: data/ 폴더에 텍스트 파일로 관리
- **지문 정보 포함**: 제목, 작가, 본문 자동 추출

#### AI Judge 검증 시스템
- **유형별 평가 기준**: 각 1-5점 척도
- **엄격한 합격 조건**: 모든 항목 ≥ 3.5/5.0
- **피드백 기반 재생성**: 불합격 문제의 피드백을 다음 프롬프트에 포함
- **부분 재생성**: 부족한 개수만큼만 추가 생성 (최대 3회 시도)

#### 비동기 처리
- **Celery**: Redis를 브로커로 사용한 백그라운드 작업
- **Task 상태 추적**: task_id로 실시간 상태 조회
- **에러 핸들링**: 실패 시 워크시트 status를 FAILED로 업데이트

#### 병렬 처리
- **ThreadPoolExecutor**: 작품별 동시 생성 (최대 5개 워커)
- **적용 유형**: 시, 소설, 수필/비문학
- **미적용 유형**: 문법 (순차 처리)
