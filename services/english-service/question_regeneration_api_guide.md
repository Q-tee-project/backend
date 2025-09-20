# Question Regeneration API 가이드

이 문서는 영어 문제 재생성 API를 설명합니다. 프론트엔드에서 문제 재생성 기능을 구현할 때 참고하세요.

## 📁 API 엔드포인트

### 1. 재생성 정보 조회
```
GET /api/english/worksheets/{worksheet_id}/questions/{question_id}/regeneration-info
```

### 2. 문제 재생성 실행
```
POST /api/english/worksheets/{worksheet_id}/questions/{question_id}/regenerate
```

## 🔍 1. 재생성 정보 조회 API

### 목적
문제 재생성 폼을 구성하기 위한 현재 문제 정보를 조회합니다.

### 요청
```javascript
GET /api/english/worksheets/worksheet-123/questions/5/regeneration-info
```

### 응답 예시
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
    {
      "id": 6,
      "text": "다음 글의 내용과 일치하는 것은?"
    },
    {
      "id": 7,
      "text": "빈 칸에 들어갈 말로 가장 적절한 것은?"
    }
  ]
}
```

### 프론트엔드 활용법
```javascript
// 재생성 버튼 클릭 시
async function openRegenerationModal(worksheetId, questionId) {
  const response = await fetch(`/api/english/worksheets/${worksheetId}/questions/${questionId}/regeneration-info`);
  const info = await response.json();

  // 모달 폼 구성
  if (info.has_passage && info.related_questions.length > 0) {
    // 지문 연계 문제 → 경고 메시지 표시
    showPassageWarning(info.related_questions);
  }

  // 폼 초기값 설정
  setFormDefaults(info.question, info.worksheet);
}
```

## 🔧 2. 문제 재생성 API

### 기본 구조
```json
{
  "feedback": "사용자 피드백 (필수)",
  "keep_*": "유지할 조건들 (boolean)",
  "target_*": "변경할 값들 (선택적)",
  "worksheet_context": "문제지 컨텍스트 (필수)",
  "current_*": "현재 문제 정보 (필수)",
  "additional_requirements": "추가 요구사항 (선택적)"
}
```

### 유지/변경 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `keep_passage` | `true` | 지문 유지 여부 |
| `keep_question_type` | `true` | 문제 유형(객관식/단답형/서술형) 유지 |
| `keep_difficulty` | `true` | 난이도 유지 여부 |
| `keep_subject` | `true` | 문제 영역(독해/문법/어휘) 유지 |
| `keep_detail_type` | `true` | 세부 영역 유지 여부 |

### 유효성 검사 규칙
- `keep_*`가 `true`면 해당 `target_*` 설정 불가
- `feedback`은 필수 입력
- `worksheet_context`와 `current_*` 정보는 모두 필수

## 📋 3. 사용 시나리오별 예시

### 🔹 시나리오 1: 기본 재생성 (모든 조건 유지)
**상황**: 문제 내용만 바꾸고 싶을 때

```json
{
  "feedback": "문제를 더 쉽게 만들어주세요",
  "worksheet_context": {
    "school_level": "중학교",
    "grade": 1,
    "worksheet_type": "혼합형"
  },
  "current_question_type": "객관식",
  "current_subject": "독해",
  "current_detail_type": "제목 및 요지 추론",
  "current_difficulty": "상"
}
```

### 🔹 시나리오 2: 난이도 변경
**상황**: 문제가 너무 어려울 때

```json
{
  "feedback": "문제가 너무 어려워요. 중학교 1학년 수준으로 맞춰주세요",
  "keep_difficulty": false,
  "target_difficulty": "하",
  "worksheet_context": {
    "school_level": "중학교",
    "grade": 1,
    "worksheet_type": "문법"
  },
  "current_question_type": "객관식",
  "current_subject": "문법",
  "current_detail_type": "시제",
  "current_difficulty": "상",
  "additional_requirements": "기본적인 어휘만 사용하고, 예문을 일상생활 관련으로 만들어주세요"
}
```

### 🔹 시나리오 3: 지문과 함께 재생성
**상황**: 지문이 마음에 안 들 때

```json
{
  "feedback": "지문이 너무 길고 어려워요. 더 짧고 재미있는 내용으로 바꿔주세요",
  "keep_passage": false,
  "worksheet_context": {
    "school_level": "중학교",
    "grade": 1,
    "worksheet_type": "독해"
  },
  "current_question_type": "객관식",
  "current_subject": "독해",
  "current_detail_type": "내용 일치",
  "current_difficulty": "중",
  "additional_requirements": "스포츠나 취미 관련 주제로 만들어주세요"
}
```

### 🔹 시나리오 4: 영역 변경
**상황**: 독해 문제를 어휘 문제로 바꾸고 싶을 때

```json
{
  "feedback": "독해 문제 대신 어휘 문제로 바꿔주세요",
  "keep_subject": false,
  "keep_detail_type": false,
  "target_subject": "어휘",
  "target_detail_type": "빈칸 추론",
  "worksheet_context": {
    "school_level": "중학교",
    "grade": 1,
    "worksheet_type": "혼합형"
  },
  "current_question_type": "객관식",
  "current_subject": "독해",
  "current_detail_type": "제목 추론",
  "current_difficulty": "중"
}
```

## 📤 4. 응답 형식

### 성공 응답
```json
{
  "status": "success",
  "message": "문제가 성공적으로 재생성되었습니다.",
  "regenerated_question": {
    "id": 5,
    "question_text": "새로운 문제 텍스트",
    "question_type": "객관식",
    "question_subject": "독해",
    "question_difficulty": "하",
    "question_choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "선택지2",
    "explanation": "새로운 해설",
    // ... 기타 필드들
  },
  "regenerated_passage": null  // 지문 변경시에만 데이터 포함
}
```

### 실패 응답
```json
{
  "status": "error",
  "message": "재생성에 실패했습니다.",
  "error_details": "구체적인 오류 내용"
}
```

## 🚨 5. 에러 처리

### HTTP 상태 코드
- **200**: 성공
- **400**: 요청 데이터 오류 (유효성 검사 실패)
- **404**: 문제 또는 워크시트를 찾을 수 없음
- **500**: 서버 내부 오류

### 일반적인 오류 사례
```json
// 유효성 검사 오류
{
  "detail": "keep_difficulty가 True일 때는 target_difficulty를 설정할 수 없습니다"
}

// 존재하지 않는 문제
{
  "detail": "문제를 찾을 수 없습니다."
}

// AI 생성 실패
{
  "status": "error",
  "message": "AI 문제 생성에 실패했습니다.",
  "error_details": "API 키가 유효하지 않거나 서비스가 일시적으로 사용할 수 없습니다."
}
```

## 💡 6. 프론트엔드 구현 팁

### UI/UX 권장사항

#### 6.1 재생성 버튼 위치
```html
<!-- 각 문제 카드에 재생성 버튼 추가 -->
<div class="question-card">
  <div class="question-header">
    <span class="question-number">문제 1</span>
    <button class="regenerate-btn" onclick="openRegenerationModal(worksheetId, 1)">
      🔄 재생성
    </button>
  </div>
  <!-- 문제 내용 -->
</div>
```

#### 6.2 지문 연계 경고
```javascript
function showPassageWarning(relatedQuestions) {
  const message = `
    ⚠️ 이 문제는 지문에 연결된 다른 문제들이 있습니다:
    ${relatedQuestions.map(q => `• ${q.text}`).join('\n')}

    지문을 변경하면 다른 문제들과 어울리지 않을 수 있습니다.
  `;

  // 경고 메시지 표시
  alert(message);
}
```

#### 6.3 폼 구성
```html
<form id="regeneration-form">
  <!-- 피드백 입력 (필수) -->
  <div class="form-group">
    <label>어떻게 수정하고 싶으신가요? *</label>
    <textarea name="feedback" required
              placeholder="예: 문제를 더 쉽게 만들어주세요"></textarea>
  </div>

  <!-- 유지/변경 옵션 -->
  <div class="form-group">
    <label>
      <input type="checkbox" name="keep_difficulty" checked>
      난이도 유지 (현재: 상)
    </label>
  </div>

  <!-- 난이도 변경 (조건부 표시) -->
  <div class="form-group" id="difficulty-options" style="display: none;">
    <label>변경할 난이도:</label>
    <select name="target_difficulty">
      <option value="하">하</option>
      <option value="중">중</option>
      <option value="상">상</option>
    </select>
  </div>

  <!-- 추가 요구사항 -->
  <div class="form-group">
    <label>추가 요구사항 (선택)</label>
    <textarea name="additional_requirements"
              placeholder="예: 스포츠 관련 주제로 만들어주세요"></textarea>
  </div>
</form>
```

#### 6.4 체크박스 동적 처리
```javascript
document.querySelectorAll('[name^="keep_"]').forEach(checkbox => {
  checkbox.addEventListener('change', function() {
    const targetField = this.name.replace('keep_', 'target_');
    const targetElement = document.querySelector(`[name="${targetField}"]`).closest('.form-group');

    if (this.checked) {
      targetElement.style.display = 'none';
      targetElement.querySelector('select, input').value = '';
    } else {
      targetElement.style.display = 'block';
    }
  });
});
```

#### 6.5 로딩 상태 처리
```javascript
async function regenerateQuestion(worksheetId, questionId, formData) {
  // 로딩 시작
  showLoading('문제를 재생성하고 있습니다...');

  try {
    const response = await fetch(`/api/english/worksheets/${worksheetId}/questions/${questionId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });

    const result = await response.json();

    if (result.status === 'success') {
      // 성공: UI 업데이트
      updateQuestionInUI(result.regenerated_question);
      showSuccess('문제가 성공적으로 재생성되었습니다!');
    } else {
      showError(result.message);
    }

  } catch (error) {
    showError('재생성 중 오류가 발생했습니다.');
  } finally {
    hideLoading();
  }
}
```

### 성능 최적화

#### 6.6 중복 요청 방지
```javascript
let isRegenerating = false;

async function regenerateQuestion(worksheetId, questionId, formData) {
  if (isRegenerating) return;

  isRegenerating = true;
  try {
    // 재생성 로직...
  } finally {
    isRegenerating = false;
  }
}
```

#### 6.7 결과 캐싱
```javascript
// 재생성 결과를 로컬에 임시 저장
const regenerationHistory = new Map();

function saveRegenerationResult(questionId, result) {
  regenerationHistory.set(questionId, {
    timestamp: Date.now(),
    result: result
  });
}
```

## 🔍 7. 디버깅 가이드

### 자주 발생하는 문제들

#### 7.1 유효성 검사 오류
```
문제: "keep_difficulty가 True일 때는 target_difficulty를 설정할 수 없습니다"
해결: 체크박스가 체크되어 있으면 target 필드를 비워야 함
```

#### 7.2 AI 생성 실패
```
문제: "AI 문제 생성에 실패했습니다"
원인: API 키 오류, 네트워크 문제, 프롬프트 문제
해결: 설정 확인, 재시도 로직 구현
```

#### 7.3 지문 관련 오류
```
문제: 지문 변경 시 다른 문제들과 불일치
해결: 사용자에게 미리 경고하고 선택권 제공
```

### 로그 확인
```javascript
// 개발자 도구에서 요청 로그 확인
console.log('재생성 요청:', formData);
console.log('응답:', result);
```

이 가이드를 참고하여 직관적이고 안정적인 문제 재생성 기능을 구현하세요!