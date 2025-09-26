# 🚀 English Service API Reference

이 문서는 영어 서비스에서 제공하는 API의 명세와 사용법을 정리합니다.

**기본 URL**: `http://localhost:8002` (Docker 환경 기준)

## 📝 목차

1.  Health Check
2.  Categories
3.  Worksheets (문제지)
4.  Grading (채점)

---

## 1. Health Check

### `GET /api/v1/health`

- **설명**: 서버의 상태를 확인합니다.
- **요청 본문**: 없음
- **성공 응답 (200 OK)**:
  ```json
  {
    "status": "ok"
  }
  ```

---

## 2. Categories

### `GET /api/v1/categories`

- **설명**: 문제 생성에 사용될 문법, 어휘, 독해 카테고리 목록을 조회합니다.
- **요청 본문**: 없음
- **성공 응답 (200 OK)**:
  ```json
  {
    "grammar_categories": [
      {
        "id": 1,
        "name": "시제",
        "topics": [
          { "id": 101, "name": "현재완료" },
          { "id": 102, "name": "과거완료" }
        ]
      }
    ],
    "vocabulary_categories": [
      { "id": 201, "name": "일상생활" },
      { "id": 202, "name": "학교생활" }
    ],
    "reading_types": [
      { "id": 301, "name": "주제 및 요지 파악", "description": "글의 전체적인 주제나 요지를 파악하는 유형" },
      { "id": 302, "name": "빈칸 추론", "description": "문맥을 통해 빈칸에 들어갈 적절한 단어나 구를 추론하는 유형" }
    ]
  }
  ```

---

## 3. Worksheets (문제지)

### `POST /api/v1/question-generate`

- **설명**: AI를 사용하여 문제지를 생성합니다.
- **요청 본문**:
  ```json
  {
    "school_level": "중학교",
    "grade": 1,
    "total_questions": 10,
    "subjects": ["독해", "문법"],
    "subject_details": {
      "reading_types": ["주제 및 요지 파악", "빈칸추론"],
      "grammar_categories": ["시제"],
      "grammar_topics": ["현재완료"],
      "vocabulary_categories": []
    },
    "subject_ratios": [
      {"subject": "독해", "ratio": 60},
      {"subject": "문법", "ratio": 40}
    ],
    "question_format": "혼합형",
    "format_ratios": [
      {"format": "객관식", "ratio": 70},
      {"format": "주관식", "ratio": 30}
    ],
    "difficulty_distribution": [
      {"difficulty": "상", "ratio": 20},
      {"difficulty": "중", "ratio": 50},
      {"difficulty": "하", "ratio": 30}
    ],
    "additional_requirements": "일상생활과 관련된 주제로 출제해주세요."
  }
  ```
- **성공 응답 (200 OK)**:
  ```json
  {
    "message": "문제지와 답안지 생성이 완료되었습니다!",
    "status": "success",
    "llm_response": {
      "worksheet_id": "1",
      "worksheet_name": "중학교 1학년 영어 평가",
      "total_questions": 10,
      "passages": [
        {
          "passage_id": "1",
          "passage_content": "...",
          "original_content": "...",
          "korean_translation": "...",
          "related_questions": ["1", "2"]
        }
      ],
      "examples": [
        {
          "example_id": "1",
          "example_content": "...",
          "original_content": "...",
          "korean_translation": "...",
          "related_question": "3"
        }
      ],
      "questions": [
        {
          "question_id": "1",
          "question_text": "...",
          "correct_answer": "...",
          "explanation": "..."
        }
      ]
    },
    "llm_error": null
  }
  ```

### `POST /api/v1/worksheets`

- **설명**: 생성된 문제지를 데이터베이스에 저장합니다.
- **요청 본문**:
  ```json
  {
    "worksheet_data": {
      "worksheet_name": "저장할 문제지 제목",
      "worksheet_level": "중학교",
      "worksheet_grade": 1,
      "total_questions": 10,
      "passages": [],
      "examples": [],
      "questions": []
    }
  }
  ```
- **성공 응답 (200 OK)**:
  ```json
  {
    "message": "문제지가 성공적으로 저장되었습니다.",
    "worksheet_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "status": "success"
  }
  ```

### `GET /api/v1/worksheets`

- **설명**: 저장된 모든 문제지 목록을 조회합니다.
- **요청 본문**: 없음
- **성공 응답 (200 OK)**:
  ```json
  [
    {
      "id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
      "worksheet_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
      "worksheet_name": "중학교 1학년 기말고사 대비",
      "school_level": "중학교",
      "grade": "1",
      "subject": "영어",
      "total_questions": 20,
      "duration": 45,
      "created_at": "2023-10-27T10:00:00.000Z"
    }
  ]
  ```

### `GET /api/v1/worksheets/{worksheet_id}/edit`

- **설명**: 특정 문제지를 편집하기 위해 모든 데이터(정답, 해설 포함)를 조회합니다.
- **요청 본문**: 없음
- **성공 응답 (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "편집용 문제지를 성공적으로 조회했습니다.",
    "worksheet_data": {
      "worksheet_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
      "worksheet_name": "중학교 1학년 기말고사 대비",
      "passages": [...],
      "examples": [...],
      "questions": [...]
    }
  }
  ```

### `GET /api/v1/worksheets/{worksheet_id}/solve`

- **설명**: 학생이 문제를 풀기 위해 문제지 데이터(정답, 해설 제외)를 조회합니다.
- **요청 본문**: 없음
- **성공 응답 (200 OK)**:
  ```json
  {
    "worksheet_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "worksheet_name": "중학교 1학년 기말고사 대비",
    "passages": [...],
    "examples": [...],
    "questions": [
      {
        "question_id": "1",
        "question_text": "다음 빈칸에 들어갈 말은?",
        "question_choices": ["choice1", "choice2"]
      }
    ]
  }
  ```

### `DELETE /api/v1/worksheets/{worksheet_id}`

- **설명**: 특정 문제지와 관련된 모든 데이터를 삭제합니다.
- **요청 본문**: 없음
- **성공 응답 (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "문제지 '중학교 1학년 기말고사 대비'이 성공적으로 삭제되었습니다.",
    "deleted_worksheet_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
  }
  ```

### 문제지 항목 수정 API

- **설명**: 문제지의 각 항목(제목, 문제, 선택지, 정답, 지문, 예문)을 개별적으로 수정합니다.
- **엔드포인트 및 요청/응답 예시**:
  - `PUT /api/v1/worksheets/{id}/title`
    - **요청**: `{ "worksheet_name": "새로운 문제지 제목" }`
    - **응답**: `{ "status": "success", "message": "문제지 제목이 업데이트되었습니다." }`
  - `PUT /api/v1/worksheets/{id}/questions/{qid}/text`
    - **요청**: `{ "question_text": "수정된 문제 질문" }`
    - **응답**: `{ "status": "success", "message": "문제 텍스트가 업데이트되었습니다." }`
  - `PUT /api/v1/worksheets/{id}/questions/{qid}/choice`
    - **요청**: `{ "choice_index": 0, "choice_text": "수정된 선택지 1번" }`
    - **응답**: `{ "status": "success", "message": "선택지가 업데이트되었습니다." }`
  - `PUT /api/v1/worksheets/{id}/questions/{qid}/answer`
    - **요청**: `{ "correct_answer": "수정된 정답" }`
    - **응답**: `{ "status": "success", "message": "정답이 업데이트되었습니다." }`
  - `PUT /api/v1/worksheets/{id}/passages/{pid}`
    - **요청**: `{ "passage_content": "수정된 지문 내용" }`
    - **응답**: `{ "status": "success", "message": "지문이 업데이트되었습니다." }`
  - `PUT /api/v1/worksheets/{id}/examples/{eid}`
    - **요청**: `{ "example_content": "수정된 예문 내용" }`
    - **응답**: `{ "status": "success", "message": "예문이 업데이트되었습니다." }`

---

## 4. Grading (채점)

### `POST /api/v1/worksheets/{worksheet_id}/submit`

- **설명**: 학생이 제출한 답안을 채점합니다.
- **요청 본문**:
  ```json
  {
    "student_name": "홍길동",
    "student_id": "student123",
    "answers": {
      "1": "2",
      "2": "apple",
      "3": "He is a boy."
    },
    "completion_time": 350
  }
  ```
- **성공 응답 (200 OK)**:
  ```json
  {
    "result_id": "g1h2i3j4-k5l6-m7n8-o9p0-q1r2s3t4u5v6",
    "worksheet_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "student_name": "홍길동",
    "total_score": 80,
    "max_score": 100,
    "percentage": 80.0,
    "message": "채점이 완료되었습니다."
  }
  ```

### `GET /api/v1/grading-results`

- **설명**: 모든 채점 결과 목록을 조회합니다.
- **요청 본문**: 없음
- **성공 응답 (200 OK)**:
  ```json
  [
    {
      "id": "g1h2i3j4-k5l6-m7n8-o9p0-q1r2s3t4u5v6",
      "worksheet_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
      "worksheet_name": "중학교 1학년 기말고사 대비",
      "student_name": "홍길동",
      "total_score": 80,
      "max_score": 100,
      "submitted_at": "2023-10-27T11:00:00.000Z",
      "completion_time": 350,
      "needs_review": true
    }
  ]
  ```

### `GET /api/v1/grading-results/{result_id}`

- **설명**: 특정 채점 결과의 상세 내용을 조회합니다. (문제지 데이터 포함)
- **요청 본문**: 없음
- **성공 응답 (200 OK)**:
  ```json
  {
    "result_id": "g1h2i3j4-k5l6-m7n8-o9p0-q1r2s3t4u5v6",
    "student_name": "홍길동",
    "total_score": 80,
    "max_score": 100,
    "percentage": 80.0,
    "question_results": [
      {
        "question_id": "1",
        "is_correct": true,
        "score": 10,
        "max_score": 10,
        "grading_method": "db"
      }
    ],
    "student_answers": {
      "1": "2"
    },
    "worksheet_data": {
      "worksheet_name": "중학교 1학년 기말고사 대비",
      "questions": [...]
    }
  }
  ```

### `PUT /api/v1/grading-results/{result_id}/review`

- **설명**: AI 채점 결과를 교사가 검수하고 수정합니다.
- **요청 본문**:
  ```json
  {
    "question_results": {
      "2": {
        "is_correct": true,
        "feedback": "유사한 의미의 단어도 정답으로 인정합니다."
      }
    }
  }
  ```
- **성공 응답 (200 OK)**:
  ```json
  {
    "result_id": "g1h2i3j4-k5l6-m7n8-o9p0-q1r2s3t4u5v6",
    "total_score": 90,
    "percentage": 90.0,
    "message": "채점 검수가 반영되었습니다."
  }
  ```

