# API 키 설정 가이드

이 프로젝트에서는 여러 API 서비스를 사용합니다. 각 서비스의 API 키를 발급받고 설정하는 방법을 안내합니다.

## 필요한 API 키

### 1. Google Gemini API 키 (필수)
- **용도**: AI 기반 문제 생성 및 채점
- **서비스**: Math Service, English Service 모두 사용
- **발급 방법**: [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급

### 2. Google Vision API 키 (Math Service용)
- **용도**: 손글씨/이미지 OCR (광학 문자 인식)
- **서비스**: Math Service에서만 사용
- **발급 방법**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)에서 발급

## API 키 발급 방법

### Google Gemini API 키
1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. API 키 복사

### Google Vision API 키
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "APIs & Services" > "Credentials" 이동
4. "CREATE CREDENTIALS" > "API key" 선택
5. Vision API 활성화 (APIs & Services > Library에서 "Cloud Vision API" 검색 후 Enable)
6. API 키 복사

## 환경 변수 설정

`.env` 파일에 다음과 같이 설정하세요:

```bash
# Gemini API 키 (개별 또는 공통)
MATH_GEMINI_API_KEY=your_math_gemini_api_key_here
ENGLISH_GEMINI_API_KEY=your_english_gemini_api_key_here
GEMINI_API_KEY=your_common_gemini_api_key_here

# Google Vision API 키
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here
```

## 개발자별 설정 예시

### 개발자 1 (수학 담당)
```bash
# 수학 개발자는 Gemini와 Vision API 키 모두 필요
MATH_GEMINI_API_KEY=AIzaSyC...
GOOGLE_VISION_API_KEY=AIzaSyD...
```

### 개발자 2 (영어 담당)
```bash
# 영어 개발자는 Gemini API 키만 필요
ENGLISH_GEMINI_API_KEY=AIzaSyE...
```

## 보안 주의사항

1. **API 키는 절대 Git에 커밋하지 마세요**
2. `.env` 파일은 `.gitignore`에 포함되어 있습니다
3. API 키를 공개 저장소에 노출시키지 마세요
4. 팀원과 API 키를 공유할 때는 안전한 채널을 사용하세요

## 테스트 방법

### Gemini API 테스트
```bash
curl -X POST "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=YOUR_API_KEY" \
-H 'Content-Type: application/json' \
-d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### Vision API 테스트
```bash
curl -X POST "https://vision.googleapis.com/v1/images:annotate?key=YOUR_API_KEY" \
-H 'Content-Type: application/json' \
-d '{
  "requests": [
    {
      "image": {
        "content": "base64_encoded_image"
      },
      "features": [
        {
          "type": "TEXT_DETECTION"
        }
      ]
    }
  ]
}'
```

## 문제 해결

### API 키 오류
- API 키가 올바른지 확인
- API가 활성화되어 있는지 확인
- 사용량 한도를 초과하지 않았는지 확인

### 권한 오류
- Google Cloud에서 해당 API에 대한 권한이 있는지 확인
- 결제 계정이 연결되어 있는지 확인 (Vision API의 경우)