# 국어 문제 생성 시스템 플로우 (Korean Problem Generation Flow)

> **버전**: 2.0 (English Prompt + AI Judge 통합)
> **업데이트**: 2025-10-01
> **기술 스택**: Gemini 2.5 Pro (생성) + GPT-4o-mini (검증)

---

## 📌 시스템 개요

국어 문제 생성 시스템은 **4가지 유형**(시, 소설, 수필/비문학, 문법)에 대해 각각 최적화된 파이프라인을 제공합니다.

### 핵심 특징
- ✅ **영어 프롬프트 기반** - LLM 성능 최적화
- ✅ **2단계 검증 시스템** - Gemini (구조) + GPT-4o-mini (내용)
- ✅ **병렬 처리** - 작품별 동시 생성 (시/소설/수필)
- ✅ **유형별 맞춤 전처리** - AI 핵심 발췌, 영역 분할 등
- ✅ **재시도 메커니즘** - 안정성 확보

---

## 🎯 난이도 체계 (Difficulty Levels)

모든 유형에 공통 적용되는 난이도 기준:

| 난이도 | 영문 | 설명 | 특징 |
|--------|------|------|------|
| **상** | Advanced | 깊은 분석, 추론, 복잡한 사고 필요 | 고급 문학 기법, 비판적 사고, 통합 분석 |
| **중** | Intermediate | 중간 수준의 이해와 해석 필요 | 인과관계, 주제 파악, 기법 분석 |
| **하** | Basic | 표면적 이해와 회상 필요 | 직접 정보, 기본 이해, 명시적 내용 |

---

## 1️⃣ 시 (Poetry)

### 📖 플로우

```
📥 요청: 시 10문제 생성
    ↓
【작품 선택 및 병렬화】
├─ 작품 수 결정: 3개 (10문제 ≤ 10)
├─ data/poem/*.txt 에서 랜덤 선택
├─ 파일명 파싱: "제목-작가.txt"
└─ 문제 수 분배: [3, 3, 4]
    ↓
【전처리】
├─ 시는 전체 텍스트 사용 (일반적으로 짧음)
└─ 2000자 초과 시 앞부분만 사용 (연작시 대응)
    ↓
【병렬 생성】 - ThreadPoolExecutor
├─ 작품1: 3문제 (1회 Gemini 호출)
├─ 작품2: 3문제 (1회 Gemini 호출)
└─ 작품3: 4문제 (1회 Gemini 호출)
    ↓
【2단계 검증】
├─ 1단계: 구조 검증 (Gemini 자체)
│   ├─ 필수 필드: question, choices(4개), correct_answer, explanation
│   ├─ 지문 길이: 20~1000자
│   ├─ 작품명, 시인명 확인
│   └─ 정답 형식: A/B/C/D
│
└─ 2단계: AI Judge 검증 (GPT-4o-mini)
    ├─ literary_accuracy (1-5): 문학적 해석 정확성
    ├─ relevance (1-5): 시와의 관련성
    ├─ figurative_language_analysis (1-5): 비유적 표현 분석
    └─ answer_clarity (1-5): 정답의 명확성
    → 모든 점수 ≥ 3.5 시 VALID
    ↓
【DB 저장】
```

### 🎓 난이도별 출제 기준

| 난이도 | 출제 초점 | 예시 |
|--------|-----------|------|
| **하** | 표면적 이해, 화자 파악, 기본 정서, 직접적 이미지 | "시의 화자는 누구인가?", "시에서 반복되는 단어는?" |
| **중** | 비유적 표현, 어조, 분위기, 주제 요소, 시적 장치 | "이 시의 주된 시적 기법은?", "3연의 분위기는?" |
| **상** | 깊은 상징적 의미, 복잡한 문학 기법, 작가 의도, 비교 분석 | "상징적 의미는?", "시적 화자의 내면 변화는?" |

### 🔍 주요 출제 영역

- **문학 장치**: 은유(Metaphor), 의인법(Personification), 직유(Simile)
- **표현 기법**: 이미지(Imagery), 상징(Symbolism), 어조(Tone)
- **구조 요소**: 운율(Rhythm), 반복(Repetition), 대조(Contrast)

---

## 2️⃣ 소설 (Novel/Fiction)

### 📖 플로우

```
📥 요청: 소설 10문제 생성
    ↓
【작품 선택 및 병렬화】
├─ 작품 수 결정: 2개 (10문제 ≤ 10)
├─ data/novel/*.txt 에서 랜덤 선택
└─ 문제 수 분배: [5, 5]
    ↓
【전처리 - AI 핵심 발췌】⭐
├─ 1500자 초과 시 핵심 부분 추출
├─ 발췌 기준 (영어 프롬프트):
│   ├─ Character conflict (인물 갈등)
│   ├─ Dialogue revealing personality (성격 드러나는 대화)
│   ├─ Crucial plot development (중요 플롯 전개)
│   └─ Thematic significance (주제적 의미)
├─ 목표 길이: 800-1200자
└─ 실패 시 폴백: 원본 앞 1200자
    ↓
【병렬 생성】 - ThreadPoolExecutor
├─ 작품1: 5문제 (발췌된 핵심 부분으로)
└─ 작품2: 5문제 (발췌된 핵심 부분으로)
    ↓
【2단계 검증】
├─ 1단계: 구조 검증
│   ├─ 지문 길이: 300~3000자
│   └─ 작품명, 작가명 확인
│
└─ 2단계: AI Judge 검증 (GPT-4o-mini)
    ├─ narrative_comprehension (1-5): 서사 이해도
    ├─ relevance (1-5): 지문과의 관련성
    ├─ textual_analysis (1-5): 서사 기법 분석
    └─ answer_clarity (1-5): 정답의 명확성
    ↓
【DB 저장】
```

### 🎓 난이도별 출제 기준

| 난이도 | 출제 초점 | 예시 |
|--------|-----------|------|
| **하** | 플롯 순서, 인물 파악, 배경, 직접적 대화 해석 | "사건의 순서는?", "주인공은 누구인가?" |
| **중** | 인물 동기, 갈등 분석, 서술 관점, 인과관계 | "인물의 행동 동기는?", "갈등의 원인은?" |
| **상** | 주제의 깊이, 서사 기법, 심리적 복잡성, 상징적 해석 | "작품의 주제 의식은?", "서술자의 시점 변화 효과는?" |

### 🔍 주요 출제 영역

- **서사 요소**: 플롯, 인물, 배경, 갈등
- **서술 기법**: 시점, 서술자, 플래시백, 복선
- **인물 분석**: 심리, 동기, 관계, 성격 변화

---

## 3️⃣ 수필/비문학 (Essay/Non-fiction)

### 📖 플로우

```
📥 요청: 수필/비문학 10문제 생성
    ↓
【작품 선택 및 병렬화】
├─ 작품 수 결정: 2개 (10문제 ≤ 10)
├─ data/non-fiction/*.txt 에서 랜덤 선택
└─ 문제 수 분배: [5, 5]
    ↓
【전처리 - AI 핵심 발췌】⭐
├─ 1500자 초과 시 핵심 부분 추출
├─ 발췌 기준 (영어 프롬프트):
│   ├─ Main argument (핵심 주장)
│   ├─ Key evidence (주요 증거)
│   ├─ Central thesis (중심 논지)
│   └─ Author's main point (저자의 주요 논점)
├─ 목표 길이: 800-1200자
└─ 실패 시 폴백: 원본 앞 1200자
    ↓
【병렬 생성】 - ThreadPoolExecutor
├─ 작품1: 5문제 (발췌된 핵심 논지로)
└─ 작품2: 5문제 (발췌된 핵심 논지로)
    ↓
【2단계 검증】
├─ 1단계: 구조 검증
│   ├─ 지문 길이: 100자 이상
│   └─ 작가명 확인
│
└─ 2단계: AI Judge 검증 (GPT-4o-mini)
    ├─ content_accuracy (1-5): 내용의 정확성
    ├─ logical_consistency (1-5): 논리적 일관성
    ├─ relevance (1-5): 지문과의 관련성
    └─ answer_clarity (1-5): 정답의 명확성
    ↓
【DB 저장】
```

### 🎓 난이도별 출제 기준

| 난이도 | 출제 초점 | 예시 |
|--------|-----------|------|
| **하** | 주제 파악, 명시적 정보 회상, 기본 구조 | "글의 중심 내용은?", "글쓴이의 직업은?" |
| **중** | 논증 분석, 증거 평가, 논리적 관계, 글쓴이의 목적 | "주장을 뒷받침하는 근거는?", "논리 전개 방식은?" |
| **상** | 비판적 평가, 추론, 새로운 맥락 적용, 수사적 분석 | "글쓴이의 관점에 대한 비판은?", "다른 상황 적용은?" |

### 🔍 주요 출제 영역

- **논지 파악**: 중심 주장, 근거/논거, 논리 전개
- **글의 구조**: 서론-본론-결론, 글의 조직
- **글쓴이 의도**: 관점, 목적, 태도

---

## 4️⃣ 문법 (Grammar)

### 📖 플로우

```
📥 요청: 문법 10문제 생성
    ↓
【문법 영역 분할】 - 병렬 처리 없음 ⚠️
├─ data/grammar.txt 단일 파일 로드
└─ I~V 영역으로 분할:
    ├─ I. 음운 (Phonology)
    ├─ II. 품사와 어휘 (Morphology/Lexicon)
    ├─ III. 문장 (Syntax)
    ├─ IV. 기타 (Miscellaneous)
    └─ V. 부록 (Appendix)
    ↓
【문제 수 균등 분배】
└─ 10문제 ÷ 5영역 = [2, 2, 2, 2, 2]
    ↓
【순차 생성】 - 영역별 (병렬 X)
├─ I. 음운: 2문제 생성
│   ├─ ⭐ 새로운 예문 생성 가능
│   ├─ ⭐ grammar.txt 원본 참조 금지
│   └─ LLM이 문법 개념에 맞는 예문 작성
│
├─ II. 품사와 어휘: 2문제
├─ III. 문장: 2문제
├─ IV. 기타: 2문제
└─ V. 부록: 2문제
    ↓
    ↓ 폴백 메커니즘
    └─ 영역별 생성 실패 시 → 개별 생성 (_generate_problems_individually)
    ↓
【2단계 검증】
├─ 1단계: 구조 검증
│   └─ 해설 길이: 20자 이상 (문법은 상세 설명 필수)
│
└─ 2단계: AI Judge 검증 (GPT-4o-mini)
    ├─ grammatical_accuracy (1-5): 문법 개념의 정확성
    ├─ concept_clarity (1-5): 문법 개념의 명확성
    ├─ example_appropriateness (1-5): 예문의 적절성
    └─ answer_clarity (1-5): 정답의 명확성
    ↓
【source_text 처리】⭐
├─ LLM 생성 예문 → 문제에 표시
└─ grammar.txt 원본 → 숨김 (표시 안 함)
    ↓
【DB 저장】
```

### 🎓 난이도별 출제 기준

| 난이도 | 출제 초점 | 예시 |
|--------|-----------|------|
| **하** | 기본 문법 용어, 단순 규칙, 명확한 예시 | "주어의 역할은?", "명사의 정의는?" |
| **중** | 문법 규칙 적용, 문장 구조 분석, 품사 식별 | "문장 성분 분석", "용언의 활용형 구별" |
| **상** | 복잡한 문법 개념, 예외 규칙, 비교 분석, 언어학적 추론 | "음운 변동의 조건", "문법 범주의 상관관계" |

### 🔍 주요 출제 영역

- **음운론 (Phonology)**: 음운 변동, 발음 규칙
- **형태론 (Morphology)**: 품사, 단어 형성
- **통사론 (Syntax)**: 문장 구조, 문장 성분
- **의미론 (Semantics)**: 의미 관계, 어휘 관계

### ⚠️ 문법 특이사항

1. **병렬 처리 없음** - 영역별 순차 생성 (I → II → III → IV → V)
2. **새 예문 생성** - LLM이 문법 개념에 맞는 새로운 예문 작성 가능
3. **원본 숨김** - grammar.txt 원본 내용은 문제에 표시하지 않음
4. **영역별 폴백** - 각 영역 생성 실패 시 개별 생성 모드로 전환

---

## 🔄 재생성 플로우 (Regeneration)

모든 유형에 공통 적용:

```
📥 재생성 요청 (문제 ID + 요구사항)
    ↓
regenerate_single_problem(current_problem, requirements)
    ↓
【영어 프롬프트 구성】
├─ System: "You are an expert Korean language teacher"
├─ Current Problem: 기존 문제 정보 전달
├─ Requirements: 사용자 요구사항 (영어 또는 한글)
└─ Output: "ALL content MUST be in KOREAN"
    ↓
【Gemini 2.5 Pro 호출】
└─ 기존 문제 개선
    ↓
【JSON 파싱】
└─ {question, choices, correct_answer, explanation}
    ↓
【반환】
```

---

## 📊 기술 스펙

### LLM 모델
- **생성**: Gemini 2.5 Pro (Google)
- **검증**: GPT-4o-mini (OpenAI)

### 프롬프트 언어
- **입력**: 영어 (English-based prompts)
- **출력**: 한국어 (Korean language content)

### 병렬 처리
- **엔진**: ThreadPoolExecutor
- **최대 워커**: min(작품 수, 5)
- **적용 유형**: 시, 소설, 수필/비문학
- **미적용 유형**: 문법 (순차 처리)

### 재시도 메커니즘
- **횟수**: 2회 (max_retries=2)
- **대기 시간**: 1초 (time.sleep(1))
- **적용 범위**: 모든 생성 메서드

---

## ✅ 검증 기준 요약

| 유형 | 구조 검증 | AI Judge 검증 기준 |
|------|-----------|-------------------|
| **시** | 지문 20~1000자<br/>작품명, 시인명 | literary_accuracy, relevance<br/>figurative_language_analysis, answer_clarity |
| **소설** | 지문 300~3000자<br/>작품명, 작가명 | narrative_comprehension, relevance<br/>textual_analysis, answer_clarity |
| **수필/비문학** | 지문 100자 이상<br/>작가명 | content_accuracy, logical_consistency<br/>relevance, answer_clarity |
| **문법** | 해설 20자 이상 | grammatical_accuracy, concept_clarity<br/>example_appropriateness, answer_clarity |

**공통 구조 검증**:
- 필수 필드: question, choices(4개), correct_answer, explanation, difficulty
- 정답 형식: A/B/C/D
- 선택지: 4개, 중복 없음
- 난이도: 상/중/하

**AI Judge 합격 기준**: 모든 항목 ≥ 3.5/5.0

---

## 📁 데이터 구조

```
backend/services/korean-service/data/
├── poem/           # 시 작품 파일들
│   └── *.txt       # 형식: "제목-작가.txt"
├── novel/          # 소설 작품 파일들
│   └── *.txt       # 형식: "제목-작가.txt"
├── non-fiction/    # 수필/비문학 파일들
│   └── *.txt       # 형식: "제목-작가.txt"
└── grammar.txt     # 문법 통합 파일 (I~V 영역)
```

---

## 🚀 성능 최적화

### 작품 수 자동 결정

| 문제 수 | 시 | 소설 | 수필/비문학 |
|---------|-----|------|-------------|
| ≤ 10 | 3개 | 2개 | 2개 |
| ≤ 20 | 6개 | 4개 | 4개 |
| > 20 | min(문제수 ÷ 3, 10)개 | min(문제수 ÷ 3, 10)개 | min(문제수 ÷ 3, 10)개 |

### 발췌 전략
- **시**: 2000자 이하 → 전체 사용
- **소설**: 1500자 초과 → AI 핵심 발췌 (갈등/대화 중심)
- **수필/비문학**: 1500자 초과 → AI 핵심 발췌 (논지/증거 중심)
- **문법**: 영역별 분할 (I~V)

---

## 📝 버전 히스토리

### v2.0 (2025-10-01)
- ✅ 영어 프롬프트 전면 도입
- ✅ GPT-4o-mini AI Judge 통합
- ✅ 유형별 전처리 최적화
- ✅ 재시도 메커니즘 강화
- ✅ 한글 템플릿 제거, 영어 템플릿 통합

### v1.0 (Initial)
- 기본 문제 생성 시스템
- 한글 프롬프트 사용
- 구조 검증만 적용

---

## 🔗 관련 파일

- **프롬프트 템플릿**: `app/prompt_templates/`
  - `base_template_en.py` - 영어 기반 템플릿
  - `single_problem_en.py` - 단일 문제 생성
  - `multiple_problems_en.py` - 다중 문제 생성

- **생성 로직**: `app/services/korean_problem_generator.py`
- **검증 로직**: `app/services/korean_problem_generator.py` (validate_* 메서드들)
- **작업 관리**: `app/tasks.py`
- **API 라우터**: `app/routers/korean_generation.py`

---

**문서 작성**: Claude (Anthropic)
**시스템 설계**: 항왕구 팀
**유지보수**: korean-service 팀
