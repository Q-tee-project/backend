# AI Judge 문제 검증 시스템

## 개요

수학 문제 생성 시 AI-as-a-Judge 패턴을 사용하여 생성된 문제의 품질을 자동 검증합니다.

## 아키텍처

```
문제 생성 요청
    ↓
generate_problems() (최대 3회 재시도)
    ↓
gemini-2.5-pro로 문제 생성
    ↓
각 문제마다 _validate_with_ai_judge() 호출
    ↓
gemini-2.5-flash로 검증
    ↓
VALID → 통과
INVALID → 피드백 수집 → 재생성
```

## 검증 기준 (LaTeX 문법 제외)

### 1. mathematical_accuracy (수학적 정확성)
- 문제 자체에 논리적 모순이 없는가?
- 예: "x > 5이고 x < 3인 x를 구하시오" → 불합격

### 2. consistency (정답 일치성) ⭐ 가장 중요
- 해설을 통해 도출한 답 = `correct_answer`
- 객관식: `correct_answer`가 A,B,C,D 중 하나이고, `choices[해당인덱스]`가 실제 정답과 일치
- 단답형: 해설의 최종 답 = `correct_answer`

### 3. completeness (완결성)
- 객관식: `choices` 정확히 4개 존재, 중복 없음
- 해설: 문제 풀이에 필요한 단계가 모두 포함됨

### 4. logic_flow (해설의 논리성)
- 해설이 문제를 풀 수 있는 순차적 단계를 제공하는가?

## 통과 기준

- **consistency >= 4점** (80% 이상)
- 나머지 항목 평균 >= 3.5점 (70% 이상)

## 구현 위치

**파일**: `backend/services/math-service/app/services/problem_generator.py`

### 주요 메서드

#### `_validate_with_ai_judge(problem: Dict) -> tuple`
- gemini-2.5-flash 사용
- temperature=0.1 (일관성)
- max_output_tokens=512
- 영어 프롬프트로 빠른 처리
- Returns: `(is_valid: bool, scores: dict, feedback: str)`

#### `_rebuild_prompt_with_feedback(original_prompt: str, invalid_problems: List[Dict]) -> str`
- 검증 실패 시 피드백을 프롬프트에 추가
- 재생성 시 동일한 오류 반복 방지

#### `_call_ai_and_parse_response(prompt: str, max_retries: int = 3, target_count: int = None) -> List[Dict]`
- 문제 생성 후 자동으로 검증 실행
- **부분 재생성 로직**: 합격한 문제는 유지, 불합격만 재생성
- 최대 3회 재시도
- 모든 시도 실패 시 예외 발생

#### `_adjust_prompt_for_needed_count(original_prompt: str, needed_count: int) -> str`
- 부족한 문제 개수만큼만 생성하도록 프롬프트 조정
- 정규표현식으로 문제 개수 패턴 교체

## 비용 최적화

1. **gemini-2.5-flash 사용**: 검증용으로 빠르고 저렴한 모델
2. **영어 프롬프트**: 토큰 절약 및 처리 속도 향상
3. **부분 재생성**: 합격한 문제는 재생성하지 않음
4. **검증 실패 시에만 재시도**: 불필요한 API 호출 최소화

## 로깅

검증 과정은 콘솔에 출력됩니다:

```
============================================================
문제 생성 시도 1/3
현재 합격: 0개 / 목표: 10개
추가 필요: 10개
============================================================

🔍 AI Judge 검증 시작 - 10개 문제
  ✅ 문제 1번: VALID - 평균 4.2점 [수학정확성:4.0 정답일치:5.0 완결성:4.0 논리성:4.0]
  ✅ 문제 2번: VALID - 평균 4.5점 [수학정확성:5.0 정답일치:5.0 완결성:4.0 논리성:4.0]
  ❌ 문제 3번: INVALID - 평균 3.5점 [수학정확성:4.0 정답일치:3.0 완결성:3.5 논리성:3.5]
     💬 피드백: Explanation's final answer doesn't match correct_answer

⚠️ 부족: 1개 추가 생성 필요 (현재 9/10)
```

## 작동 흐름

1. Celery 비동기 태스크에서 `generate_math_problems_task` 실행
2. `math_service._generate_problems_with_ratio()` 호출
3. `problem_generator.generate_problems()` 실행
4. 각 문제 생성 후 자동 검증
5. **합격 문제는 누적 보관, 불합격만 재생성**
6. 목표 개수 달성 시 DB 저장
7. 최대 3회 재시도 (부족한 개수만큼만)

## 검증 예외 처리

**네트워크 오류 (TimeoutError, ConnectionError, OSError):**
- 기본 통과 처리 (너무 엄격하지 않게)
- 기본 점수 4.0 부여
- 로그: "⚠️ 네트워크 오류로 검증 생략, 기본 통과 처리"

**JSON 파싱 오류 (JSONDecodeError):**
- 예외 재발생 → 재시도 유도
- 로그: "❌ AI Judge 응답 JSON 파싱 실패"

**기타 오류:**
- 예외 재발생 → 재시도 유도
- 로그: "❌ AI Judge 검증 오류"

## 주의사항

- **LaTeX 문법은 검증하지 않음**: 프론트엔드에서 렌더링 처리
- **논리적 정합성만 검증**: 수식 오류, 정답 불일치 등
- **재시도 제한**: 3회 시도 후에도 실패 시 예외 발생

## 성능

- 검증 1회당 약 0.5~1초 소요 (gemini-2.5-flash)
- 10개 문제 생성 + 검증: 약 15~20초
- 재시도 1회 추가 시: +15~20초

## 개선 완료 사항 (2025-01-XX)

✅ **예외 처리 엄격화**: 네트워크 오류만 통과, 나머지는 재시도
✅ **검증 기준 완화**: consistency >= 4점, 전체 평균 >= 3.5점 (이전: consistency = 5점 필수)
✅ **부분 재생성 로직**: 합격한 문제는 유지, 불합격만 재생성
✅ **검증 로깅 개선**: 상세 점수 및 피드백 출력

## 향후 개선 사항

1. 검증 결과 DB 저장 (통계/분석용)
2. 배치 검증 (10개 문제를 한 번에 검증)
3. 검증 기준 동적 조정 (난이도별 다른 기준)
4. 수학적 동치성 검증 (sympy 활용)