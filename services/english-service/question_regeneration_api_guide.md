# 영어 문제 재생성 API 가이드 (v2.0)

이 문서는 영어 문제 재생성 API의 최신 사양을 설명합니다. 프론트엔드에서 문제 재생성 기능을 구현할 때 이 문서를 기준으로 삼아주세요.

## ✨ 주요 변경사항 (v2.0)

- **데이터 기반 재생성 API 추가**: DB에 저장되지 않은 문제(예: 생성 미리보기)도 재생성할 수 있는 엔드포인트가 추가되었습니다.
- **지문 및 연계 문제 동시 재생성**: 지문과 이에 연관된 모든 문제를 한 번의 요청으로 재생성하는 기능이 명확해졌습니다.

---

## 📁 API 엔드포인트 요약

| Method | 경로                                                              | 설명                                                 |
|--------|-------------------------------------------------------------------|------------------------------------------------------|
| `GET`  | `/worksheets/{worksheet_id}/questions/{question_id}/regeneration-info` | 재생성 폼 구성을 위한 현재 문제 정보를 조회합니다.   |
| `POST` | `/worksheets/{worksheet_id}/questions/{question_id}/regenerate`      | **DB에 저장된** 특정 문제를 재생성합니다.            |
| `POST` | `/questions/regenerate-data`                                      | **데이터 기반으로** 문제를 재생성합니다. (DB 저장 X) |

---

## ⚙️ API 상세 설명

### 1. 재생성 정보 조회

- **Method**: `GET`
- **Endpoint**: `/worksheets/{worksheet_id}/questions/{question_id}/regeneration-info`
- **목적**: 문제 재생성 모달(폼)을 띄우기 전에, 해당 문제의 현재 상태와 필요한 컨텍스트 정보를 백엔드로부터 가져옵니다.
- **응답 예시**:
  ```json
  {
    "question": {
      "id": 5,
      "question_type": "객관식",
      "question_subject": "독해",
      "question_detail_type": "제목 및 요지 추론",
      "question_difficulty": "상",
      "passage_id": 2
    },
    "worksheet": {
      "school_level": "중학교",
      "grade": 1,
      "problem_type": "혼합형"
    },
    "has_passage": true,
    "related_questions": [
      {"id": 6, "text": "다음 글의 내용과 일치하는 것은?"},
      {"id": 7, "text": "빈 칸에 들어갈 말로 가장 적절한 것은?"}
    ]
  }
  ```

### 2. 문제 재생성 (DB 기반)

- **Method**: `POST`
- **Endpoint**: `/worksheets/{worksheet_id}/questions/{question_id}/regenerate`
- **목적**: 이미 생성되어 DB에 저장된 문제를 사용자의 피드백에 따라 재생성하고, 결과를 다시 DB에 업데이트합니다.
- **Request Body**: `QuestionRegenerationRequest` 스키마 (아래 요청 예시 참고)

### 3. 문제 재생성 (데이터 기반)

- **Method**: `POST`
- **Endpoint**: `/questions/regenerate-data`
- **목적**: 아직 DB에 저장되지 않은 문제 데이터(예: 문제 생성 단계의 미리보기)를 기반으로 재생성합니다. 이 API는 DB에 아무런 영향을 주지 않으며, 순수하게 데이터만 변환하여 반환합니다.
- **Request Body**: `QuestionDataRegenerationRequest` 스키마
  ```json
  {
    "question_data": { ... }, // 재생성할 원본 문제 데이터
    "passage_data": { ... }, // (선택) 원본 지문 데이터
    "regeneration_request": { ... } // QuestionRegenerationRequest 스키마
  }
  ```

---

## 📋 핵심 시나리오별 요청 예시

### `QuestionRegenerationRequest` 공통 구조

모든 재생성 요청은 아래 구조를 따르는 `regeneration_request` 객체를 포함합니다.

```json
{
  "feedback": "문제 수정 요구사항 (필수)",
  "worksheet_context": { "school_level": "중학교", "grade": 1, "worksheet_type": "혼합형" },
  "current_question_type": "객관식",
  "current_subject": "독해",
  "current_detail_type": "제목 및 요지 추론",
  "current_difficulty": "상",

  "keep_passage": true,
  "regenerate_related_questions": false,
  "keep_question_type": true,
  "keep_difficulty": true,
  "keep_subject": true,
  "keep_detail_type": true,

  "target_question_type": null,
  "target_difficulty": null,
  "target_subject": null,
  "target_detail_type": null,

  "additional_requirements": null
}
```

---

### 🔹 시나리오 1: 내용만 수정 (기본 재생성)

- **상황**: 문제의 다른 조건은 모두 유지한 채, 피드백에 따라 내용만 개선하고 싶을 때.
- **요청**:
  ```json
  {
    "feedback": "문제가 너무 장황합니다. 더 간결하게 만들어주세요.",
    "worksheet_context": { ... },
    "current_question_type": "객관식",
    "current_subject": "문법",
    "current_detail_type": "시제",
    "current_difficulty": "중"
  }
  ```

### 🔹 시나리오 2: 난이도 변경

- **상황**: 문제가 너무 어렵거나 쉬워서 난이도를 조절하고 싶을 때.
- **요청**:
  ```json
  {
    "feedback": "문제가 너무 어려워요. '하' 수준으로 낮춰주세요.",
    "keep_difficulty": false,       // 난이도 유지 안함
    "target_difficulty": "하",      // 목표 난이도를 '하'로 설정
    "worksheet_context": { ... },
    "current_question_type": "서술형",
    "current_subject": "독해",
    "current_detail_type": "내용 요약",
    "current_difficulty": "상"
  }
  ```

### ‼️ [중요] 시나리오 3: 지문과 모든 연계 문제 동시 재생성

- **상황**: 지문이 마음에 들지 않아, **지문 자체를 포함한 모든 관련 문제를 한 번에** 새로운 내용으로 바꾸고 싶을 때.
- **핵심 조건**: `keep_passage`를 `false`로, `regenerate_related_questions`를 `true`로 **반드시 함께 설정**해야 합니다.
- **요청**:
  ```json
  {
    "feedback": "지문이 너무 지루합니다. 흥미로운 과학 기사로 바꿔주세요.",
    "keep_passage": false,                  // ⬅️ 지문을 새로 생성
    "regenerate_related_questions": true,   // ⬅️ 연계된 문제들도 모두 재생성
    "worksheet_context": { ... },
    "current_question_type": "객관식",
    "current_subject": "독해",
    "current_detail_type": "내용 일치",
    "current_difficulty": "중"
  }
  ```
- **동작 방식**:
  1. 백엔드는 `keep_passage: false`를 보고 새로운 지문을 생성합니다.
  2. `regenerate_related_questions: true`를 확인하고, 기존 지문과 연결된 모든 문제(현재 요청한 문제 포함)를 가져옵니다.
  3. 각각의 연계 문제에 대해, **새로 생성된 지문**에 내용이 맞도록 자동으로 재생성을 실행합니다.
  4. 최종적으로, 새로 만들어진 지문 1개와 여러 개의 새로운 문제들을 응답으로 반환합니다.

---

## 📤 응답 데이터 상세

### 1. 단일 문제 재생성 성공 시

- **트리거**: 시나리오 1, 2 또는 `regenerate_related_questions: false`인 경우
- **응답 예시**:
  ```json
  {
    "status": "success",
    "message": "문제가 성공적으로 재생성되었습니다.",
    "regenerated_question": {
      "id": 5,
      "question_text": "새롭게 만들어진 문제 텍스트...",
      "question_type": "객관식",
      "question_difficulty": "하",
      ...
    },
    "regenerated_passage": null, // 지문을 바꾸지 않았으므로 null
    "regenerated_related_questions": null
  }
  ```

### 2. 지문과 연계 문제 동시 재생성 성공 시

- **트리거**: 시나리오 3 (`keep_passage: false` AND `regenerate_related_questions: true`)
- **응답 예시**:
  ```json
  {
    "status": "success",
    "message": "지문과 연계된 문제들이 모두 성공적으로 재생성되었습니다.",
    "regenerated_question": {
      "id": 5,
      "question_text": "새 지문에 맞는 첫 번째 문제...",
      ...
    },
    "regenerated_passage": {
      "passage_id": 2,
      "passage_content": "새로운 지문 내용...",
      ...
    },
    "regenerated_related_questions": [
      {
        "id": 6,
        "question_text": "새 지문에 맞는 두 번째 문제...",
        ...
      },
      {
        "id": 7,
        "question_text": "새 지문에 맞는 세 번째 문제...",
        ...
      }
    ]
  }
  ```
- **프론트엔드 처리**: 이 응답을 받으면, `regenerated_passage`로 지문 UI를 업데이트하고, `regenerated_question` 및 `regenerated_related_questions` 배열에 포함된 모든 문제들을 기존 문제 카드 UI와 교체해야 합니다.

---

## 💡 프론트엔드 구현 가이드

- **지문 연계 문제 경고**: `GET .../regeneration-info` 응답에 `related_questions`가 있으면, "지문을 변경하면 다른 문제도 영향을 받을 수 있습니다." 와 같은 안내를 표시해주세요.
- **동시 재생성 옵션 제공**: 위 경고와 함께 "지문과 모든 연계 문제 함께 재생성" 체크박스(또는 버튼)를 사용자에게 제공하여, 시나리오 3을 실행할 수 있도록 유도하는 것이 좋습니다. 이 체크박스를 선택하면 `keep_passage`를 `false`로, `regenerate_related_questions`를 `true`로 설정하여 API를 호출하도록 구현합니다.
- **로딩 처리**: 동시 재생성은 여러 문제를 생성하므로 일반 재생성보다 시간이 더 걸릴 수 있습니다. API 호출 시 "연관된 문제들을 함께 생성하고 있습니다..."와 같은 상세한 로딩 메시지를 표시하는 것을 권장합니다.
