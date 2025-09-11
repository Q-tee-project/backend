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
**범용 난이도 기준** (모든 단원 적용):

**A단계 (기본/개념)**:
- 단일 개념의 직접적 적용
- 정의나 공식을 그대로 사용하는 문제
- 1-2단계 계산으로 해결 가능
- 예: 기본 공식 대입, 개념 확인, 용어 정의
- 문제 길이: 1-2줄의 간단한 서술

**B단계 (응용/연산)** - **중간 난이도 필수**:
- 반드시 3-4줄의 구체적인 상황 설명 포함
- 2개 이상의 서로 다른 개념을 조합해야 함
- 최소 3-5단계의 계산 과정이 반드시 필요
- 문제 상황을 수식으로 변환하는 과정이 포함되어야 함
- 단순 공식 대입만으로는 해결되지 않는 문제
- 학생이 "어떤 공식을 사용해야 할까?" 고민하게 만드는 수준
- 예: 복합 응용 문제, 여러 도형 성질의 조합, 연립방정식 활용

**C단계 (심화/사고)** - **매우 어려운 문제 필수**:
- 반드시 5-7줄의 복잡한 문제 상황 제시
- 3개 이상의 조건이 동시에 주어져야 함
- 여러 단계의 논리적 추론 과정이 반드시 필요
- 단순 공식 적용으로는 절대 해결 불가능
- 창의적 접근 방법이나 특수한 아이디어가 필요
- 증명, 최적화, 경우의 수 분석, 패턴 발견 중 하나 이상 포함
- 문제를 읽고 즉시 풀이 방법이 떠오르지 않는 수준이어야 함
- 중학생도 "어, 이거 어떻게 풀지?" 하고 고민하는 문제여야 함
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
   - 복잡한 중첩 구조나 특수 패키지 명령어는 피하기
   - 한국어와 LaTeX 혼용 시 공백 주의
4. 해설은 난이도에 맞게 간결하게 (A:1문장, B:2-3문장, C:3-4문장)
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
**난이도별 차별화 강조**:
- A단계: 즉시 공식 적용 가능한 직관적 문제 (1-2줄, 1-2단계 계산)
- B단계: 여러 개념 조합과 다단계 계산이 필요한 응용 문제 (3-4줄, 3-5단계 계산)
- C단계: 창의적 접근과 통합적 사고가 필수인 복합 문제 (5-7줄, 복잡한 추론)

**B단계 문제 생성 시 반드시 지켜야 할 사항**:
1. 문제는 반드시 3-4줄의 구체적 상황 설명 포함
2. 최소 2개 이상의 서로 다른 개념을 조합해야 함
3. 3-5단계의 계산 과정이 반드시 필요
4. 단순 공식 대입만으로는 해결되지 않아야 함

**C단계 문제 생성 시 반드시 지켜야 할 사항**:
1. 문제 상황이 복잡하고 다층적이어야 함 (최소 5줄 이상)
2. 조건이 3개 이상 동시에 주어져야 함
3. 단순 계산이나 공식 대입으로는 해결 불가
4. 반드시 여러 단계의 추론 과정이 필요
5. 학생이 문제를 읽고 즉시 "어떻게 풀지?" 고민하게 만드는 수준
6. 증명, 최적화, 경우의 수, 패턴 분석 등이 포함되어야 함

**절대 금지**: B단계에서 1-2단계로 끝나는 간단한 문제 생성 금지! C단계에서 단순한 계산 문제나 공식 대입 문제는 절대 생성하지 마세요!
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

**중요한 지시사항**: 
- 모든 문제에서 correct_answer 필드는 반드시 문제 유형에 맞는 형식으로 정확히 작성해야 함
- 객관식: choices는 ["선택지내용1", "선택지내용2", "선택지내용3", "선택지내용4"], correct_answer는 "A"/"B"/"C"/"D"
- 단답형/서술형: correct_answer에 실제 답안을 LaTeX 형식 포함하여 완전히 작성

{PromptTemplates.get_difficulty_criteria()}

{reference_problems}

{PromptTemplates.get_generation_rules()}

{PromptTemplates.get_difficulty_requirements()}

{PromptTemplates.get_json_format()}"""

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