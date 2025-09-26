# 📊 **채점 결과 JSON 응답 형식**

## 🎯 **API 엔드포인트**
```
GET /api/v1/grading-results/{result_id}
```

## 📋 **완전한 JSON 응답 구조**

```json
{
  "result_id": "7d2d9f8b-a8c9-4c18-bbb6-75c5ced23e8a",
  "worksheet_id": "1f5ab929-3fd2-4b7d-879d-cc6596ce8190",
  "student_name": "학생",
  "completion_time": 48,
  "total_score": 10,
  "max_score": 100,
  "percentage": 10.0,
  "created_at": "2025-09-16T01:52:15.516058",
  
  "question_results": [
    {
      "question_id": "1",
      "question_type": "객관식",
      "student_answer": "1",
      "correct_answer": "2",
      "score": 0,
      "max_score": 10,
      "is_correct": false,
      "grading_method": "db",
      "ai_feedback": null
    },
    {
      "question_id": "9",
      "question_type": "서술형",
      "student_answer": "asfsa",
      "correct_answer": "I listen to peaceful music to relax on weekends.",
      "score": 0,
      "max_score": 10,
      "is_correct": false,
      "grading_method": "ai",
      "ai_feedback": "답안이 의미 있는 단어나 문장으로 구성되어 있지 않아 채점이 어렵습니다. 문제에서 요구하는 '자신의 주말에 대해 묘사하는 완전한 문장'을 작성하는 연습이 필요합니다. 예시 답안을 참고하여 다시 시도해 보세요."
    }
  ],
  
  "student_answers": {
    "1": "1",
    "2": "1",
    "3": "2",
    "4": "4",
    "5": "3",
    "6": "모름",
    "7": "4",
    "8": "fasf",
    "9": "asfsa",
    "10": "zxvfsa"
  },
  
  "worksheet_data": {
    "worksheet_id": "1f5ab929-3fd2-4b7d-879d-cc6596ce8190",
    "worksheet_name": "중학교 1학년 영어 dd",
    "worksheet_level": "중학교",
    "worksheet_grade": 1,
    "worksheet_subject": "영어",
    "total_questions": 10,
    "worksheet_duration": 45,
    
    "passages": [
      {
        "passage_id": "1",
        "passage_type": "article",
        "passage_content": {
          "content": [
            {
              "type": "title",
              "value": "My First Day at a New School"
            },
            {
              "type": "paragraph",
              "value": "Last week, I had to transfer to a new school. On my first day, I felt so alone. I didn't know anyone, and I was nervous. My teacher suggested I attend the welcome committee meeting to make new friends. ( ① ) I worried that I might not impress the other members. I took a slight step into the meeting room. ( ② ) There were several students there, and they were planning an event for new students like me. ( ③ ) After the meeting, I felt a real bond with them. I think this is a good first step at my new school. ( ④ ) I'm not worried anymore."
            }
          ]
        },
        "original_content": {
          "content": [
            {
              "type": "title", 
              "value": "My First Day at a New School"
            },
            {
              "type": "paragraph",
              "value": "Last week, I had to transfer to a new school. On my first day, I felt so alone. I didn't know anyone, and I was nervous. My teacher suggested I attend the welcome committee meeting to make new friends. I worried that I might not impress the other members. I took a slight step into the meeting room. Instead, everyone was very friendly and made me feel welcome. There were several students there, and they were planning an event for new students like me. After the meeting, I felt a real bond with them. I think this is a good first step at my new school. I'm not worried anymore."
            }
          ]
        },
        "korean_translation": {
          "content": [
            {
              "type": "title",
              "value": "새 학교 첫날"
            },
            {
              "type": "paragraph", 
              "value": "지난주, 나는 새 학교로 전학을 가야만 했다. 첫날 나는 너무 외로웠다. 아는 사람도 아무도 없었고, 긴장했다. 선생님은 새 친구들을 사귀기 위해 환영 위원회 모임에 참석해 보라고 하셨다. 나는 다른 위원들에게 좋은 인상을 주지 못할까 봐 걱정했다. 나는 조심스럽게 회의실에 들어갔다. 하지만 내 예상과는 달리, 모두가 매우 친절하고 나를 환영해 주었다. 그곳에는 여러 학생들이 있었고, 그들은 나와 같은 새 학생들을 위한 행사를 기획하고 있었다. 모임 후, 나는 그들과 진정한 유대감을 느꼈다. 이것은 새 학교에서의 좋은 첫걸음이라고 생각한다. 나는 더 이상 걱정하지 않는다."
            }
          ]
        },
        "related_questions": ["6", "7", "8"]
      }
    ],
    
    "examples": [
      {
        "example_id": "1",
        "example_content": "The clock on the wall ___ very old.",
        "original_content": "The clock on the wall is very old.",
        "korean_translation": "벽에 걸린 그 시계는 매우 오래되었다.",
        "related_question": "1"
      },
      {
        "example_id": "2", 
        "example_content": "He ___ to his neighbor with a friendly gesture.",
        "original_content": "He appeared to his neighbor with a friendly gesture.",
        "korean_translation": "그는 친근한 몸짓으로 그의 이웃에게 나타났다.",
        "related_question": "3"
      },
      {
        "example_id": "5",
        "example_content": "<조건>\n1. 'peaceful'과 'relax'를 모두 사용할 것.\n2. 완전한 영어 문장으로 쓸 것.",
        "original_content": "My home is a peaceful place where I can relax.",
        "korean_translation": "우리 집은 내가 쉴 수 있는 평화로운 장소이다.",
        "related_question": "9"
      }
    ],
    
    "questions": [
      {
        "question_id": "1",
        "question_text": "다음 문장의 빈칸에 들어갈 알맞은 것은?",
        "question_type": "객관식",
        "question_subject": "문법",
        "question_difficulty": "하",
        "question_detail_type": "현재시제와 과거형",
        "question_choices": ["am", "is", "are", "be"],
        "question_passage_id": null,
        "question_example_id": "1"
      },
      {
        "question_id": "6",
        "question_text": "이 글의 요지로 가장 알맞은 것은?",
        "question_type": "객관식",
        "question_subject": "독해", 
        "question_difficulty": "중",
        "question_detail_type": "내용 추론",
        "question_choices": [
          "전학 첫날 지난주에 전학했다.",
          "새 글쓰기 대회를 준비하고 있었다.",
          "환영 위원회에서 새 학생을 위한 행사를 준비하고 있었다.",
          "글쓰기 위원회 모임은 첫날부터 재미있었다."
        ],
        "question_passage_id": "1",
        "question_example_id": null
      },
      {
        "question_id": "9",
        "question_text": "다음 조건에 맞게 자신의 주말에 대해 묘사하는 문장을 쓰시오.",
        "question_type": "서술형",
        "question_subject": "어휘",
        "question_difficulty": "중",
        "question_detail_type": "",
        "question_choices": [],
        "question_passage_id": null,
        "question_example_id": "5"
      }
    ]
  }
}
```

## 🔑 **주요 필드 설명**

### **📊 채점 결과 메타데이터**
- `result_id`: 채점 결과 고유 ID (UUID)
- `worksheet_id`: 문제지 ID 
- `student_name`: 학생 이름
- `completion_time`: 소요 시간 (초)
- `total_score`: 총 점수
- `max_score`: 만점
- `percentage`: 정답률 (%)

### **📝 문제별 채점 결과 (`question_results`)**
- `question_id`: 문제 ID
- `question_type`: 문제 유형 (객관식, 단답형, 서술형)
- `student_answer`: 학생 답안
- `correct_answer`: 정답
- `score`: 획득 점수
- `max_score`: 문제 만점
- `is_correct`: 정답 여부
- `grading_method`: 채점 방식 ("db" 또는 "ai")
- `ai_feedback`: AI 피드백 (AI 채점인 경우)

### **🎯 학생 답안 딕셔너리 (`student_answers`)**
- 문제 ID를 키로 하는 학생 답안 매핑
- 빠른 답안 조회를 위한 구조

### **📚 문제지 데이터 (`worksheet_data`)**
- `worksheet_*`: 문제지 메타정보
- `passages`: 지문 데이터 (원본, 학생용, 한글번역 포함)
- `examples`: 예문 데이터 (원본, 학생용, 한글번역 포함)
- `questions`: 문제 데이터 (선택지, 메타정보 포함)

## 🎯 **프론트엔드에서 사용 방법**

```javascript
// API 호출
const gradingResult = await ApiService.getGradingResult(resultId);

// 데이터 접근
const studentName = gradingResult.student_name;
const totalScore = gradingResult.total_score;
const worksheetData = gradingResult.worksheet_data;

// 문제별 데이터 접근
gradingResult.question_results.forEach(questionResult => {
    const studentAnswer = gradingResult.student_answers[questionResult.question_id];
    const correctAnswer = questionResult.correct_answer;
    const aiFeedback = questionResult.ai_feedback;
});

// 지문/예문 데이터 접근
const passages = worksheetData.passages;
const examples = worksheetData.examples;
const questions = worksheetData.questions;
```

## ✅ **특징**

1. **단일 API 호출**: 모든 데이터가 한 번에 제공
2. **완전한 데이터**: 채점 결과 + 문제지 데이터 + 학생 답안
3. **다국어 지원**: 한글 번역 포함
4. **AI 피드백**: AI 채점 문제의 상세 피드백
5. **유연한 구조**: 객관식, 단답형, 서술형 모든 문제 유형 지원
