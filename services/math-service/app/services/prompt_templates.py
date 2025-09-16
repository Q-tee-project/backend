"""
AI 프롬프트 템플릿 관리 모듈
"""
from typing import Dict, List

class PromptTemplates:
    """AI 프롬프트 템플릿 관리 클래스"""
    
    @staticmethod
    def get_difficulty_criteria() -> str:
        """난이도 기준 정의"""
        return """
**난이도별 생성 기준 - 확실한 차별화 필수**:

**A단계 (기본 계산)** - **엄청 쉬운 계산 문제**:
- 1-2줄의 짧은 문제
- 바로 계산할 수 있는 단순한 문제
- 예: (3x+2)-(-4x+5) 계산하기, 2x+5=11 풀기
- **해설**: 1-2문장으로 매우 간단명료하게

**B단계 (응용/연산)** - **중간 난이도 문제**:
- 3-4줄의 상황 설명 또는 복합 계산
- 여러 단계 계산이나 실생활 문제를 수식으로 바꿔서 풀어야 함
- 예: 소금물 농도, 속력 문제, 복잡한 연산, 도형의 성질 조합
- **해설**: 2-3문장으로 간결하게

**C단계 (심화 사고)** - **평범한 중학생이 "헉!" 소리나는 문제**:
- 5-7줄의 복잡한 조건
- 여러 단계 추론이 필요
- 즉시 풀이법이 떠오르지 않지만 풀 수는 있는 수준
- 창의적 접근이나 특별한 아이디어 필요
- **해설**: 4-5문장으로 상세한 단계별 설명
"""

    @staticmethod
    def get_generation_rules() -> str:
        """문제 생성 규칙"""
        return """
**생성 규칙**:
1. 정확히 요청된 개수만큼 문제를 난이도 순서대로 생성
2. 각 문제의 difficulty 필드를 분배에 맞게 정확히 설정
3. 수학 표기: 안전한 LaTeX 사용 ($x^2$, $\sqrt{16}$, $2 \times 3$, $\frac{a}{b}$)
   - 분수는 $\frac{분자}{분모}$ 형태로 정확히 작성
   - LaTeX 명령어는 반드시 백슬래시(\)로 시작 (예: \frac, \sqrt, \sin, \cos)
   - **절대 금지**: \f, \n, \l, \g 같은 불완전한 명령어 사용 금지
   - **허용되는 명령어만 사용**: \frac, \sqrt, \sin, \cos, \tan, \log, \pi, \alpha, \beta, \theta, \leq, \geq, \neq, \times, \div
   - 복잡한 중첩 구조나 특수 패키지 명령어는 피하기
   - 한국어와 LaTeX 혼용 시 공백 주의
4. **해설 작성 규칙 - 난이도별 차별화**:
   - **A단계**: 1문장으로 핵심만 (예: "양변에서 2를 빼면 x=3이다.")
   - **B단계**: 2문장으로 간결하게 (예: "소금의 양은 변하지 않으므로 농도 공식을 적용한다. 따라서 x=5이다.")
   - **C단계**: 3문장으로 핵심 단계만 (예: "조건을 정리하면 ... 이를 대입하면 ... 따라서 답은 ...")
   - **절대 금지사항**:
     * "(값이 복잡하여 문제 재설계)", "(문제 재설계)" 등의 설계 과정 언급 금지
     * "처음에는 ~로 생각했는데", "다시 계산해보니", "검토하겠습니다" 등의 사고과정 금지
     * "~를 확인해보겠습니다", "~로 접근해보겠습니다" 등의 접근 설명 금지
     * 계산 실수나 수정 과정 언급 금지
     * 오직 완성된 최종 풀이만 작성
5. 교육과정 범위를 벗어나지 않도록 주의
6. **correct_answer 필드는 절대 빈 값이나 null이 되어서는 안됨** - 모든 문제 유형에서 반드시 정답을 포함해야 함
7. 객관식: correct_answer는 반드시 "A", "B", "C", "D" 중 하나 (①②③④ 절대 금지)
8. 단답형/서술형: correct_answer에 실제 답안을 완전히 작성
9. **정확성 필수**: correct_answer와 explanation의 답이 반드시 일치해야 함
10. **LaTeX 안전성**:
   - 모든 LaTeX 명령어는 백슬래시(\)로 시작해야 함
   - 분수: $\frac{분자}{분모}$ (rac{} 절대 금지)
   - 제곱근: $\sqrt{내용}$ (qrt{} 절대 금지)
   - 삼각함수: $\sin(x)$, $\cos(x)$ (in(), os() 절대 금지)
   - JSON 문자열 내에서 백슬래시 이스케이프 주의
"""

    @staticmethod
    def get_difficulty_requirements() -> str:
        """난이도별 차별화 강조"""
        return """
**난이도별 구체적 예시**:

**A단계 예시 (엄청 쉬운 계산)**:
- "다음 식을 계산하시오: $(3x+2)-(-4x+5)$"
- "일차방정식 $2x+5=11$을 풀어라."
- "분수 $\frac{2}{3} + \frac{1}{6}$을 계산하시오."
→ 1-2줄, 바로 계산, 1-2단계

**B단계 예시 (응용/연산 문제)**:
- "소금물 200g에 소금이 15g 들어있다. 이 소금물의 농도를 구하고, 농도를 10%로 만들려면 물을 몇 g 더 넣어야 하는가?"
- "$(2x-3)(x+1) - (x-2)^2$을 전개하고 정리하시오."
- "연속하는 세 자연수의 합이 48일 때, 가장 작은 수를 구하시오."
→ 3-4줄, 여러 단계 계산, 응용

**C단계 예시 (매우 어려운 문제)**:
- "삼각형 ABC에서 AB = 8, BC = 6, CA = 10이다. 점 P는 삼각형 내부의 점으로 삼각형 PAB, PBC, PCA의 넓이가 모두 같다. 이때 점 P에서 각 변까지의 거리의 합을 구하고, 그 이유를 설명하시오."
- "자연수 n에 대해 $1^2 + 2^2 + 3^2 + ... + n^2 = \frac{n(n+1)(2n+1)}{6}$임이 알려져 있다. 이를 이용하여 $1^2 + 3^2 + 5^2 + ... + (2n-1)^2$의 값을 n에 대한 식으로 나타내고 증명하시오."
→ 5-7줄, 복잡한 조건, 창의적 사고

**난이도별 차별화 강조**:
- A단계: 즉시 공식 적용 가능한 직관적 문제 (1-2줄, 1-2단계 계산)
- B단계: 여러 개념 조합과 다단계 계산이 필요한 응용 문제 (3-4줄, 3-5단계 계산)
- C단계: 창의적 접근과 통합적 사고가 필수인 복합 문제 (5-7줄, 복잡한 추론)

**절대 금지**:
- A단계에서 복잡한 문제 생성 금지!
- B단계에서 1-2단계로 끝나는 간단한 문제 생성 금지!
- C단계에서 단순한 계산 문제나 공식 대입 문제는 절대 생성하지 마세요!
- **같은 난이도로 모든 문제를 생성하는 것 절대 금지!**
"""

    @staticmethod
    def get_json_format() -> str:
        """JSON 응답 형식"""
        return """
JSON 배열로 응답:
[
  {
    "question": "문제 내용",
    "choices": ["선택지1", "선택지2", "선택지3", "선택지4"] (객관식만, ①②③④ 표시 절대 금지),
    "correct_answer": "정답 (형식은 문제유형에 따라 다름)",
    "explanation": "간결한 해설",
    "problem_type": "multiple_choice/short_answer/essay",
    "difficulty": "A/B/C",
    "has_diagram": true/false,
    "diagram_type": "geometry/coordinate/graph/algebra/etc",
    "diagram_elements": {"objects": [], "values": {}, "labels": []}
  }
]

**difficulty 필드 필수 지시사항**:
- **반드시 요청된 난이도 분배에 맞게 설정**
- **A단계**: "difficulty": "A" - 매우 쉬운 기본 문제
- **B단계**: "difficulty": "B" - 중간 난이도 응용 문제
- **C단계**: "difficulty": "C" - 매우 어려운 심화 문제
- **절대 모든 문제를 같은 난이도로 설정하지 말 것**

**correct_answer 필드 필수 지시사항**:
- **객관식 (multiple_choice)**: 반드시 "A", "B", "C", "D" 중 하나만 사용 (①②③④ 절대 금지)
  예시: "correct_answer": "B"
- **단답형 (short_answer)**: 숫자, 식, 단답을 LaTeX 형식으로 작성
  예시: "correct_answer": "$x = 2$", "correct_answer": "15", "correct_answer": "$3x + 5$"
- **서술형 (essay)**: 모범답안을 완전한 문장으로 LaTeX 포함하여 작성
  예시: "correct_answer": "$x = 2$를 대입하면 $2 \times 2 + 3 = 7$이 되어 등식이 성립한다. 따라서 답은 $x = 2$이다."
"""

    @staticmethod
    def build_problem_generation_prompt(
        curriculum_data: Dict,
        user_prompt: str,
        problem_count: int,
        difficulty_distribution: str,
        reference_problems: str
    ) -> str:
        """문제 생성 프롬프트 빌드"""
        return f"""중학교 수학 문제 출제 전문가입니다. 다음 교육과정에 맞는 문제를 생성해주세요.

교육과정: {curriculum_data.get('grade')} {curriculum_data.get('semester')} - {curriculum_data.get('unit_name')} > {curriculum_data.get('chapter_name')}
사용자 요청: "{user_prompt}"
난이도 분배: {difficulty_distribution}

**핵심 요구사항 - 반드시 지켜야 함**:
1. **난이도별 확실한 차별화**: A단계는 매우 쉽게, B단계는 중간 정도, C단계는 매우 어렵게 생성
2. **difficulty 필드 정확 설정**: JSON에서 각 문제의 "difficulty" 필드를 "A", "B", "C"로 정확히 구분
3. **문제 복잡도 구분**:
   - A단계: 1-2줄, 1-2단계 계산
   - B단계: 3-4줄, 3-5단계 계산
   - C단계: 5-7줄, 복잡한 추론

**중요한 지시사항**:
- 모든 문제에서 correct_answer 필드는 반드시 문제 유형에 맞는 형식으로 정확히 작성해야 함
- 객관식: choices는 ["선택지내용1", "선택지내용2", "선택지내용3", "선택지내용4"], correct_answer는 "A"/"B"/"C"/"D"
- 단답형/서술형: correct_answer에 실제 답안을 LaTeX 형식 포함하여 완전히 작성

**해설 작성 시 절대 금지사항 (매우 중요)**:
- **AI 사고과정 노출 완전 금지**: "(값이 복잡하여 문제 재설계)", "(문제 재설계)", "확인해보겠습니다", "접근해보겠습니다" 등
- **계산 수정과정 노출 금지**: "처음에는 ~로 생각했는데", "다시 계산해보니", "답을 변경합니다", "검토하겠습니다" 등
- **내부 망설임 표현 금지**: "~인지 확인", "~해야 할 것 같다", "~로 보인다" 등
- **해설 길이 엄격 제한**: A단계 1문장, B단계 2문장, C단계 3문장 초과 금지
- **완성된 풀이만 제시**: 마치 교사가 학생에게 설명하듯 간결하고 명확하게

{PromptTemplates.get_difficulty_criteria()}

{reference_problems}

{PromptTemplates.get_generation_rules()}

{PromptTemplates.get_difficulty_requirements()}

{PromptTemplates.get_json_format()}

**해설 작성 완벽 가이드**:
- **A단계 해설 예시**: "양변에서 5를 빼면 x=3이다."
- **B단계 해설 예시**: "소금의 양은 변하지 않으므로 10×0.2 = (10+x)×0.15이다. 따라서 x=3.33g이다."
- **C단계 해설 예시**: "조건을 정리하면 2x+3y=12, x+y=5이다. 연립방정식을 풀면 x=3, y=2이다. 따라서 답은 6이다."

**최종 확인사항**:
- 각 문제의 "difficulty" 필드가 요청된 분배에 맞게 정확히 설정되었는지 확인
- A, B, C 단계가 확실히 다른 수준의 복잡도를 가지는지 확인
- 같은 난이도끼리는 비슷한 수준이지만, 다른 난이도와는 명확히 구분되는지 확인
- **해설에서 AI 사고과정이나 설계과정 언급 완전 금지 재확인**"""

    @staticmethod
    def build_grading_prompt_essay(question: str, correct_answer: str, explanation: str, student_answer: str) -> str:
        """서술형 채점 프롬프트"""
        return f"""당신은 중학교 수학 채점 전문가입니다. 학생의 답안을 정확하고 공정하게 평가하여 건설적인 피드백을 제공해주세요.

다음 수학 문제의 학생 답안을 채점해주세요.

문제: {question}
정답: {correct_answer}
해설: {explanation}

학생 답안: {student_answer}

서술형 채점 기준:
1. 최종 정답의 정확성 (40점)
2. 풀이 과정의 논리성과 타당성 (40점)
3. 수학적 표기와 계산의 정확성 (20점)

특별 고려사항:
- 최종 답이 틀려도 풀이 과정이 올바르면 부분점수 부여
- 풀이 과정이 없고 답만 맞으면 70%만 점수 부여
- 창의적이고 다른 방법의 올바른 풀이도 인정
- 계산 실수는 과정이 맞으면 10점만 감점

응답 형식 (JSON):
{{
    "score": 점수(0-100),
    "is_correct": true/false,
    "feedback": "상세한 피드백 (풀이과정과 정답에 대한 구체적 평가)",
    "strengths": "잘한 부분",
    "improvements": "개선할 부분",
    "process_score": 풀이과정점수(0-60),
    "answer_score": 정답점수(0-40)
}}"""

    @staticmethod
    def build_grading_prompt_objective(question: str, correct_answer: str, explanation: str, student_answer: str) -> str:
        """객관식/단답형 채점 프롬프트"""
        return f"""당신은 중학교 수학 채점 전문가입니다. 학생의 답안을 정확하고 공정하게 평가하여 건설적인 피드백을 제공해주세요.

다음 수학 문제의 학생 답안을 채점해주세요.

문제: {question}
정답: {correct_answer}
해설: {explanation}

학생 답안: {student_answer}

채점 기준:
1. 정답 여부 (50점)
2. 풀이 과정의 논리성 (30점)
3. 계산의 정확성 (20점)

응답 형식 (JSON):
{{
    "score": 점수(0-100),
    "is_correct": true/false,
    "feedback": "상세한 피드백",
    "strengths": "잘한 부분",
    "improvements": "개선할 부분"
}}"""