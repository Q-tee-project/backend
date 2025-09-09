# 영어 문제 생성기 (English Question Generator)

FastAPI와 Gemini AI를 사용한 중학교 영어 문제 자동 생성 시스템

## 🚀 주요 기능

- **맞춤형 문제 생성**: 학년, 난이도, 영역별 비율 설정
- **AI 기반 생성**: Google Gemini 2.5-pro 모델 사용
- **다양한 문제 유형**: 객관식, 단답형, 서술형 지원
- **구조화된 출력**: JSON 형식으로 체계적인 문제지 생성
- **웹 인터페이스**: 직관적인 웹 UI로 쉬운 조작

## 🛠️ 기술 스택

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: SQLite
- **AI**: Google Generative AI (Gemini)
- **Frontend**: HTML, JavaScript, CSS
- **Environment**: Python 3.12+

## 📋 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
conda create -n test1 python=3.12
conda activate test1

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
# .env 파일 생성
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. 데이터베이스 초기화
```bash
python init_text_types.py
```

### 4. 서버 실행
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 웹 접속
브라우저에서 `http://localhost:8000` 접속

## 📁 프로젝트 구조

```
├── main.py              # FastAPI 메인 애플리케이션
├── routes.py            # API 라우터 및 엔드포인트
├── models.py            # 데이터베이스 모델
├── schemas.py           # Pydantic 스키마
├── database.py          # 데이터베이스 연결 설정
├── question_generator.py # 문제 생성 로직 및 프롬프트
├── init_text_types.py   # 초기 데이터 설정
├── static/
│   └── index.html       # 웹 인터페이스
├── requirements.txt     # 의존성 목록
└── README.md           # 프로젝트 설명서
```

## 🎯 사용 방법

1. **기본 설정**
   - 학교급: 중학교/고등학교
   - 학년: 1~3학년
   - 총 문제 수: 원하는 문제 개수

2. **영역 설정**
   - 독해, 문법, 어휘 중 선택
   - 각 영역별 비율 조정 (슬라이더 또는 직접 입력)

3. **문제 형식**
   - 객관식, 단답형, 서술형 비율 설정

4. **난이도 분배**
   - 상, 중, 하 난이도별 비율 조정

5. **문제 생성**
   - "문제지 생성" 버튼 클릭
   - Gemini AI가 자동으로 문제 생성
   - 결과를 웹페이지에서 확인 및 복사

## 📊 출력 형식

생성된 문제는 다음과 같은 JSON 구조로 출력됩니다:

```json
{
  "worksheet_id": "1",
  "worksheet_name": "중학교 1학년 영어 문제지",
  "total_questions": 10,
  "passages": [...],
  "examples": [...],
  "questions": [...]
}
```

## 🔧 주요 특징

- **예문 분리**: 문제 질문과 영어 예문을 체계적으로 분리
- **지문 연계**: 긴 지문을 기반으로 한 복수 문제 생성
- **정답 미포함**: 문제만 생성하고 정답은 별도 관리
- **비율 기반 분배**: 입력된 비율에 따른 정확한 문제 분배

## 🚨 주의사항

- Gemini API 키가 필요합니다
- API 사용량에 따른 비용이 발생할 수 있습니다
- 생성된 문제는 검토 후 사용을 권장합니다

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.