# 🐳 도커 환경에서 채점 결과 조회 문제 해결

## 🔍 **발견된 문제들**

### 1. **ID 매칭 오류**
- **프론트엔드**: `ID: 1`로 호출
- **API**: `result_id: UUID` 형태를 기대
- **결과**: 404 "채점 결과를 찾을 수 없습니다" 오류

### 2. **데이터 구조 불일치**
- **examples, passages**: 빈 배열로 나타남
- **이상한 필드들**: `examples_group`, `passages_group`, `standalone_questions` 등 불필요한 필드

### 3. **student_answers 누락**
- 채점 결과 렌더링 시 필요한 학생 답안 데이터 누락

## ✅ **해결 사항들**

### **1. API 유연한 ID 매칭 구현**

#### **grading_router.py 수정**
```python
# 기존: 오직 result_id로만 검색
result = db.query(GradingResult).filter(GradingResult.result_id == result_id).first()

# 수정: ID 또는 result_id로 유연하게 검색
result = db.query(GradingResult).filter(
    (GradingResult.result_id == result_id) | 
    (GradingResult.id == int(result_id) if result_id.isdigit() else -1)
).first()
```

### **2. 워크시트 조회 API 개선**

#### **worksheet_router.py - 풀이용 조회 수정**
```python
# 기존: 기본 데이터만 포함
worksheet_data["passages"].append({
    "passage_id": passage.passage_id,
    "passage_content": passage.passage_content,
    ...
})

# 수정: 한글 번역 및 원본 내용 포함
worksheet_data["passages"].append({
    "passage_id": passage.passage_id,
    "passage_content": passage.passage_content,
    "original_content": passage.original_content,
    "korean_translation": passage.korean_translation,
    ...
})
```

#### **응답 구조 통일**
```python
# 기존: wrapper 객체
return {
    "status": "success", 
    "worksheet_data": worksheet_data
}

# 수정: 직접 데이터 반환 (채점 결과 호환성)
return {
    "worksheet_id": worksheet_data["worksheet_id"],
    "worksheet_name": worksheet_data["worksheet_name"],
    ...
}
```

### **3. 채점 결과 데이터 구조 보완**

#### **student_answers 필드 추가**
```python
# 학생 답안을 딕셔너리로 변환
student_answers = {}
for qr in result.question_results:
    student_answers[qr.question_id] = qr.student_answer

result_dict = {
    ...
    "question_results": question_results,
    "student_answers": student_answers  # 추가
}
```

### **4. 프론트엔드 호환성 개선**

#### **워크시트 데이터 처리**
```javascript
// 기존: 고정된 구조 가정
const worksheetData = worksheetResponse.worksheet_data;

// 수정: 유연한 구조 처리
const worksheetData = worksheetResponse.worksheet_data || worksheetResponse;
```

## 🚀 **테스트 결과**

### **API 직접 테스트**
```bash
# 채점 결과 조회 (성공)
curl http://localhost:8002/api/v1/grading-results/1
# → 정상 응답: 채점 결과 + question_results + student_answers

# 워크시트 조회 (성공)  
curl http://localhost:8002/api/v1/worksheets/{id}/solve
# → 정상 응답: passages + examples + questions (한글 번역 포함)
```

### **도커 환경 정보**
- **포트**: 8002 (영어 서비스)
- **데이터베이스**: PostgreSQL (정상 연결)
- **컨테이너**: 정상 실행 중

## 🎯 **개선 효과**

### ✅ **Before (문제 상황)**
- ❌ 채점 결과 조회 실패 (404 오류)
- ❌ 빈 passages, examples 배열
- ❌ 이상한 필드들 (examples_group 등)
- ❌ student_answers 데이터 누락

### ✅ **After (해결 후)**
- ✅ 채점 결과 안정적 조회 (ID/UUID 모두 지원)
- ✅ 완전한 passages, examples 데이터 (한글 번역 포함)
- ✅ 깔끔한 응답 구조 (불필요한 필드 제거)
- ✅ 완전한 student_answers 제공

## 📋 **최종 데이터 구조**

### **채점 결과 응답**
```json
{
    "id": 1,
    "result_id": "7d2d9f8b-a8c9-4c18-bbb6-75c5ced23e8a",
    "worksheet_id": "1f5ab929-3fd2-4b7d-879d-cc6596ce8190",
    "student_name": "학생",
    "total_score": 10,
    "max_score": 100,
    "percentage": 10.0,
    "question_results": [...],
    "student_answers": {
        "1": "학생 답안 1",
        "2": "학생 답안 2"
    }
}
```

### **워크시트 응답**
```json
{
    "worksheet_id": "...",
    "worksheet_name": "중학교 1학년 영어",
    "passages": [
        {
            "passage_id": "1",
            "passage_content": {...},
            "original_content": "...",
            "korean_translation": "..."
        }
    ],
    "examples": [...],
    "questions": [...]
}
```

## 🎉 **결론**

도커 환경에서 채점 결과 조회가 **완전히 정상 작동**하도록 수정되었습니다!

- 🔍 **유연한 ID 매칭**: 숫자 ID와 UUID 모두 지원
- 📚 **완전한 데이터**: passages, examples 한글 번역까지 포함
- 🎯 **호환성**: 기존 프론트엔드와 완벽 호환
- 🐳 **도커 최적화**: 컨테이너 환경에서 안정적 동작
