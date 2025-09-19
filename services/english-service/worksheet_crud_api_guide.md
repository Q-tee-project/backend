# Worksheet CRUD API 가이드

이 문서는 워크시트 편집을 위한 CRUD 서비스 로직을 설명합니다.

## 📁 서비스 구조

```
app/services/worksheet_crud/
├── __init__.py
├── question_service.py    # 문제 수정 서비스
├── passage_service.py     # 지문 수정 서비스
└── worksheet_service.py   # 워크시트 제목 수정 서비스
```

## 🔧 1. QuestionService

### 기능
- 문제의 모든 필드를 수정할 수 있음
- 엄격한 유효성 검사 적용

### 메서드
```python
update_question(worksheet_id: str, question_id: int, update_data: Dict[str, Any]) -> Question
```

### 수정 가능한 필드
- `question_text` - 문제 텍스트
- `question_type` - 문제 유형 (객관식/단답형/서술형)
- `question_subject` - 문제 영역 (독해/문법/어휘)
- `question_difficulty` - 난이도 (상/중/하)
- `question_detail_type` - 세부 유형
- `question_choices` - 선택지 배열 (객관식인 경우)
- `passage_id` - 연관 지문 ID
- `correct_answer` - 정답
- `example_content` - 예문 내용
- `example_original_content` - 예문 원본
- `example_korean_translation` - 예문 한글 번역
- `explanation` - 해설
- `learning_point` - 학습 포인트

### 유효성 검사 규칙
| 필드 | 유효한 값 | 비고 |
|------|-----------|------|
| `question_type` | "객관식", "단답형", "서술형" | 필수 |
| `question_subject` | "독해", "문법", "어휘" | 필수 |
| `question_difficulty` | "상", "중", "하" | 필수 |
| `question_choices` | Array 타입 | 객관식일 때만 사용 |
| `passage_id` | Integer 타입 또는 null | 선택적 |
| 텍스트 필드들 | String 타입 | 빈 문자열 허용 |

### 사용 예시
```javascript
// 프론트엔드에서 문제 수정
const updateData = {
    question_text: "수정된 문제 텍스트",
    question_difficulty: "중",
    correct_answer: "수정된 정답",
    explanation: "수정된 해설"
};

// API 호출
PUT /worksheets/{worksheet_id}/questions/{question_id}
Content-Type: application/json

{
    "question_text": "수정된 문제 텍스트",
    "question_difficulty": "중",
    "correct_answer": "수정된 정답",
    "explanation": "수정된 해설"
}
```

## 📄 2. PassageService

### 기능
- 지문의 내용만 수정 가능
- **JSON 구조는 반드시 유지해야 함**
- 지문 유형 변경 불가

### 메서드
```python
update_passage(worksheet_id: str, passage_id: int, update_data: Dict[str, Any]) -> Passage
```

### 수정 가능한 필드
- `passage_content` - 학생용 지문 내용 (빈칸 포함)
- `original_content` - 원본 지문 내용 (완전한 버전)
- `korean_translation` - 한글 번역
- `related_questions` - 연관 문제 ID 배열

### ❌ 수정 불가능한 항목
- `passage_type` - 지문 유형 (article, dialogue, correspondence 등)
- JSON 구조의 키와 타입

### 구조 보존 규칙
1. **최상위 키 유지**: 기존 JSON의 키들을 그대로 유지
2. **metadata 구조 유지**: metadata 객체의 키 구조 동일해야 함
3. **content 배열 길이 유지**: content 배열의 항목 개수 동일
4. **content 항목 타입 유지**: 각 content 항목의 type 값 동일
5. **구조적 키 유지**: 각 content 항목의 키 구조 동일

### 지문 유형별 JSON 구조

#### Article (일반 글)
```json
{
    "content": [
        {
            "type": "title",
            "value": "제목 텍스트"
        },
        {
            "type": "paragraph",
            "value": "문단 텍스트"
        }
    ]
}
```

#### Correspondence (서신/소통)
```json
{
    "metadata": {
        "sender": "발신자",
        "recipient": "수신자",
        "subject": "제목",
        "date": "날짜"
    },
    "content": [
        {
            "type": "paragraph",
            "value": "내용 텍스트"
        }
    ]
}
```

#### Dialogue (대화문)
```json
{
    "metadata": {
        "participants": ["참가자1", "참가자2"]
    },
    "content": [
        {
            "speaker": "참가자1",
            "line": "대화 내용"
        }
    ]
}
```

### 사용 예시
```javascript
// ✅ 올바른 수정 예시 - 구조 유지, 내용만 변경
const updateData = {
    passage_content: {
        "metadata": {
            "sender": "수정된 발신자",  // 값만 변경
            "recipient": "수정된 수신자",
            "subject": "수정된 제목",
            "date": "2025-09-19"
        },
        "content": [
            {
                "type": "paragraph",  // type은 동일하게 유지
                "value": "수정된 내용 텍스트"  // value만 변경
            }
        ]
    }
};

// ❌ 잘못된 수정 예시 - 구조 변경 시도
const wrongData = {
    passage_content: {
        "metadata": {
            "sender": "발신자",
            // "recipient" 키 삭제 - 에러 발생!
            "subject": "제목"
        },
        "content": [
            {
                "type": "title",  // "paragraph"에서 "title"로 변경 - 에러 발생!
                "value": "내용"
            }
        ]
    }
};
```

## 📝 3. WorksheetService

### 기능
- 워크시트 제목만 수정 가능

### 메서드
```python
update_worksheet_title(worksheet_id: str, new_title: str) -> Worksheet
```

### 유효성 검사 규칙
- 문자열 타입이어야 함
- 공백 제목 불가
- 최대 200자 제한

### 사용 예시
```javascript
// 워크시트 제목 수정
PUT /worksheets/{worksheet_id}/title
Content-Type: application/json

{
    "worksheet_name": "새로운 워크시트 제목"
}
```

## 🚨 에러 처리

### 공통 에러
- **404**: 존재하지 않는 워크시트/문제/지문
- **400**: 유효성 검사 실패
- **500**: 서버 내부 오류

### QuestionService 특정 에러
```json
{
    "error": "문제 유형은 ['객관식', '단답형', '서술형'] 중 하나여야 합니다."
}
```

### PassageService 특정 에러
```json
{
    "error": "기존 JSON 구조를 유지해야 합니다."
}
```

### WorksheetService 특정 에러
```json
{
    "error": "제목은 200자를 초과할 수 없습니다."
}
```

## 💡 프론트엔드 구현 팁

### 1. 문제 수정 시
- 수정하려는 필드만 전송 (전체 객체 불필요)
- 유효성 검사 에러 시 사용자에게 명확한 메시지 표시

### 2. 지문 수정 시
- **반드시 기존 JSON 구조를 유지**
- 수정 전에 기존 구조를 복사하고 값만 변경
- 구조 변경 시도 시 에러 메시지 표시

### 3. 워크시트 제목 수정 시
- 200자 제한 실시간 체크
- 공백 제목 방지

### 4. 공통 사항
- 모든 API 호출 시 적절한 에러 핸들링
- 성공 시 UI 즉시 업데이트
- 로딩 상태 표시