"""
AI 프롬프트 템플릿 관리 모듈 - 쎈 교재 스타일
"""
from typing import Dict

class PromptTemplates:
    """AI 프롬프트 템플릿 관리 클래스"""
    
    @staticmethod
    def build_problem_generation_prompt(
        curriculum_data: Dict,
        user_prompt: str,
        problem_count: int,
        difficulty_distribution: str,
        reference_problems: str
    ) -> str:
        """쎈 스타일 문제 생성 프롬프트 - Gemini LaTeX 능력 최대 활용"""
        return f"""당신은 대한민국 베스트셀러 수학 문제집 "쎈"의 출제 전문가이며, LaTeX 수식 작성의 전문가입니다.

**교육과정**: {curriculum_data.get('grade')} {curriculum_data.get('semester')} - {curriculum_data.get('unit_name')} > {curriculum_data.get('chapter_name')}
**사용자 요청**: "{user_prompt}"
**생성할 문제 수**: {problem_count}개
**난이도 분배**: {difficulty_distribution}

## 쎈 교재 스타일 문제 생성 가이드

### 난이도별 특징:
- **A단계**: 공식 직접 적용, 1-2단계 계산 (정답률 80-90%)
- **B단계**: 실생활 응용, 3-4단계 풀이 (정답률 50-60%)
- **C단계**: 창의적 사고, 5단계 이상 풀이 (정답률 20-30%)

{reference_problems}

### LaTeX 수식 작성 가이드:
당신의 LaTeX 지식을 활용하여 모든 수학적 표현을 올바르게 작성하세요:

**분수**: $\\frac{{분자}}{{분모}}$ 형식으로 작성
- 예: $\\frac{{3}}{{4}}$, $\\frac{{2x-1}}{{x+2}}$, $\\frac{{a+b}}{{c}}$

**절댓값**: $|표현식|$ 형식으로 작성
- 예: $|x|$, $|2x-3|$, $|a-b|$

**지수**: 두 자리 이상은 중괄호 사용
- 예: $x^2$, $x^{{10}}$, $2^{{n+1}}$

**함수**: 전체를 하나의 수식으로 작성
- 예: $f(x) = 2x + 1$, $P(a, b)$, $Q(x+y, x-y)$

**복합 수식**: 변수와 연산자를 포함한 전체 표현
- 예: $3x - 5$, $a + b$, $2x^2 - 3x + 1$

**부등호**: $\\leq$, $\\geq$, $\\neq$ 사용
- 예: $x \\leq 5$, $a \\geq 0$, $x \\neq 0$



**중요**: 모든 수학적 표현은 순수 LaTeX만 사용하고, HTML 태그는 절대 섞지 마세요.

### 응답 형식:
```json
[
  {{
    "question": "문제 내용 (모든 수식이 완벽한 LaTeX로 작성)",
    "choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "정답 (객관식: A/B/C/D, 단답형: 수식)",
    "explanation": "간결한 해설 (A: 50자, B: 100자, C: 150자 이하)",
    "problem_type": "multiple_choice/short_answer",
    "difficulty": "A/B/C",
    "has_diagram": false
  }}
]
```

### 품질 기준:
1. **LaTeX 완벽성**: 모든 수학적 표현이 올바른 LaTeX 문법으로 작성
2. **난이도 정확성**: 요청된 분배 비율 정확히 준수
3. **교육적 가치**: 각 난이도에 맞는 학습 목표 달성
4. **실용성**: 실제 교실에서 사용 가능한 문제

당신의 LaTeX 전문 지식을 활용하여 완벽한 수학 문제 {problem_count}개를 JSON 배열로 생성해주세요."""