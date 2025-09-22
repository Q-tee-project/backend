"""
수학 문제 검증 서비스 - AI 기반 품질 관리
"""
import os
import json
import re
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

class ProblemValidationService:
    """AI 기반 수학 문제 검증 전용 클래스"""

    def __init__(self):
        # 검증 전용 모델 (Gemini 2.5 Flash - 빠르고 저렴)
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=gemini_api_key)

        # Flash 모델로 빠르고 저렴한 검증
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,  # 낮은 temperature로 일관성 확보
            max_output_tokens=2048,
            top_p=0.8,
            top_k=20
        )

        self.validator_model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=generation_config
        )

    def validate_problem(self, problem: Dict) -> Dict:
        """단일 문제 검증"""
        try:
            # 검증 프롬프트 생성
            validation_prompt = self._build_validation_prompt(problem)

            # AI 검증 실행
            response = self.validator_model.generate_content(validation_prompt)

            # 결과 파싱
            validation_result = self._parse_validation_response(response.text)

            # 추가 검증 레이어
            validation_result = self._additional_validation_checks(problem, validation_result)

            return validation_result

        except Exception as e:
            print(f"문제 검증 오류: {str(e)}")
            return {
                "is_valid": False,
                "math_accuracy": "검증실패",
                "answer_correctness": "검증실패",
                "explanation_quality": "검증실패",
                "latex_syntax": "검증실패",
                "difficulty_appropriateness": "검증실패",
                "issues": [f"검증 시스템 오류: {str(e)}"],
                "confidence_score": 0.0,
                "auto_approve": False
            }

    def validate_problem_batch(self, problems: List[Dict]) -> List[Dict]:
        """여러 문제 일괄 검증"""
        validation_results = []

        for i, problem in enumerate(problems):
            print(f"문제 {i+1}/{len(problems)} 검증 중...")
            result = self.validate_problem(problem)
            validation_results.append(result)

        return validation_results

    def _build_validation_prompt(self, problem: Dict) -> str:
        """검증 프롬프트 구성"""
        question = problem.get('question', '')
        correct_answer = problem.get('correct_answer', '')
        explanation = problem.get('explanation', '')
        choices = problem.get('choices', [])
        difficulty = problem.get('difficulty', 'B')
        problem_type = problem.get('problem_type', 'short_answer')

        prompt = f"""
당신은 수학 교육 전문가이자 문제 검증 전문가입니다. 다음 수학 문제를 엄격하게 검증해주세요.

**검증할 문제:**
- 문제: {question}
- 정답: {correct_answer}
- 해설: {explanation}
- 문제 유형: {problem_type}
- 난이도: {difficulty}단계
"""

        if choices:
            prompt += f"- 선택지: {choices}\n"

        prompt += f"""

**검증 기준:**

1. **수학적 정확성**: 문제가 수학적으로 올바르고 해결 가능한가?
2. **정답 정확성**: 제시된 정답이 계산상 정확한가?
3. **해설 품질**: 해설이 논리적이고 이해하기 쉬운가?
4. **LaTeX 문법**: 수식 표기가 올바른가?
5. **난이도 적절성**: {difficulty}단계에 맞는 난이도인가?
6. **선택지 품질** (객관식인 경우): 선택지가 적절하고 정답이 유일한가?

**난이도 기준:**
- A단계: 공식 직접 적용, 1-2단계 계산 (정답률 80-90%)
- B단계: 개념 결합, 실생활 응용, 3-4단계 풀이 (정답률 50-60%)
- C단계: 창의적 사고, 다단계 추론, 심화 (정답률 20-30%)

다음 JSON 형식으로만 응답해주세요:

{{
    "is_valid": true/false,
    "math_accuracy": "정확/오류/의심",
    "answer_correctness": "정확/오류/의심",
    "explanation_quality": "우수/보통/부족",
    "latex_syntax": "정확/오류/없음",
    "difficulty_appropriateness": "적절/쉬움/어려움",
    "issues": ["발견된 구체적 문제점들"],
    "suggestions": ["개선 제안사항들"],
    "confidence_score": 0.95,
    "auto_approve": true/false
}}

**중요**:
- issues에는 발견된 모든 문제점을 구체적으로 기재
- confidence_score는 0.0-1.0 사이의 검증 신뢰도
- auto_approve는 인간 검토 없이 자동 승인 가능 여부
- 조금이라도 의심스러우면 auto_approve를 false로 설정
"""

        return prompt

    def _parse_validation_response(self, response_text: str) -> Dict:
        """AI 응답 파싱"""
        try:
            # JSON 블록 추출
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            result = json.loads(json_text)

            # 필수 필드 검증 및 기본값 설정
            default_result = {
                "is_valid": False,
                "math_accuracy": "검증실패",
                "answer_correctness": "검증실패",
                "explanation_quality": "검증실패",
                "latex_syntax": "검증실패",
                "difficulty_appropriateness": "검증실패",
                "issues": ["응답 파싱 오류"],
                "suggestions": [],
                "confidence_score": 0.0,
                "auto_approve": False
            }

            # 결과 병합
            for key, default_value in default_result.items():
                if key not in result:
                    result[key] = default_value

            return result

        except json.JSONDecodeError as e:
            print(f"검증 응답 파싱 오류: {e}")
            print(f"응답 텍스트: {response_text}")
            return {
                "is_valid": False,
                "math_accuracy": "파싱오류",
                "answer_correctness": "파싱오류",
                "explanation_quality": "파싱오류",
                "latex_syntax": "파싱오류",
                "difficulty_appropriateness": "파싱오류",
                "issues": [f"응답 파싱 실패: {str(e)}"],
                "suggestions": [],
                "confidence_score": 0.0,
                "auto_approve": False
            }

    def _additional_validation_checks(self, problem: Dict, ai_result: Dict) -> Dict:
        """추가 자동 검증 레이어"""
        additional_issues = []

        # 1. LaTeX 문법 검증
        latex_issues = self._validate_latex_syntax(problem.get('question', ''))
        if latex_issues:
            additional_issues.extend(latex_issues)
            ai_result["latex_syntax"] = "오류"

        # 2. 필수 필드 검증
        required_fields = ['question', 'correct_answer']
        for field in required_fields:
            if not problem.get(field) or not problem.get(field).strip():
                additional_issues.append(f"필수 필드 누락: {field}")

        # 3. 객관식 선택지 검증
        if problem.get('problem_type') == 'multiple_choice':
            choices = problem.get('choices', [])
            correct_answer = problem.get('correct_answer', '')

            if len(choices) < 2:
                additional_issues.append("객관식 선택지가 2개 미만")

            if correct_answer not in choices:
                additional_issues.append("정답이 선택지에 없음")

        # 4. 문제 길이 검증
        question_length = len(problem.get('question', ''))
        if question_length < 10:
            additional_issues.append("문제가 너무 짧음")
        elif question_length > 1000:
            additional_issues.append("문제가 너무 김")

        # 추가 이슈 반영
        if additional_issues:
            ai_result["issues"].extend(additional_issues)
            ai_result["is_valid"] = False
            ai_result["auto_approve"] = False

        # 최종 자동 승인 판정
        ai_result["auto_approve"] = self._determine_auto_approval(ai_result)

        return ai_result

    def _validate_latex_syntax(self, text: str) -> List[str]:
        """LaTeX 문법 검증"""
        issues = []

        # 기본 LaTeX 패턴 검증
        latex_patterns = [
            (r'\$[^$]*\$', "기본 수식"),
            (r'\\frac\{[^}]*\}\{[^}]*\}', "분수"),
            (r'\\sqrt\{[^}]*\}', "제곱근"),
            (r'\^[a-zA-Z0-9]|\^\{[^}]*\}', "지수"),
            (r'_[a-zA-Z0-9]|_\{[^}]*\}', "아래첨자")
        ]

        # 잘못된 패턴 검출
        error_patterns = [
            (r'\\frac\{\}\{\}', "빈 분수 표기"),
            (r'frac\{', "백슬래시 누락"),
            (r'\$[^$]*frac[^$]*\$', "백슬래시 누락 수식"),
            (r'\\le(?![qa])', "잘못된 부등호 (\\leq 사용)"),
            (r'\\ge(?![qa])', "잘못된 부등호 (\\geq 사용)")
        ]

        for pattern, description in error_patterns:
            if re.search(pattern, text):
                issues.append(f"LaTeX 오류: {description}")

        return issues

    def _determine_auto_approval(self, validation_result: Dict) -> bool:
        """자동 승인 여부 판정"""
        # 기본 조건들
        conditions = [
            validation_result.get("is_valid", False),
            validation_result.get("math_accuracy") == "정확",
            validation_result.get("answer_correctness") == "정확",
            validation_result.get("explanation_quality") in ["우수", "보통"],
            validation_result.get("latex_syntax") in ["정확", "없음"],
            validation_result.get("confidence_score", 0.0) >= 0.8,
            len(validation_result.get("issues", [])) == 0
        ]

        # 모든 조건을 만족해야 자동 승인
        return all(conditions)

    def get_validation_summary(self, validation_results: List[Dict]) -> Dict:
        """검증 결과 요약"""
        total_problems = len(validation_results)
        if total_problems == 0:
            return {"error": "검증할 문제가 없습니다"}

        valid_problems = sum(1 for r in validation_results if r.get("is_valid", False))
        auto_approved = sum(1 for r in validation_results if r.get("auto_approve", False))

        # 이슈 통계
        all_issues = []
        for result in validation_results:
            all_issues.extend(result.get("issues", []))

        common_issues = {}
        for issue in all_issues:
            common_issues[issue] = common_issues.get(issue, 0) + 1

        return {
            "total_problems": total_problems,
            "valid_problems": valid_problems,
            "invalid_problems": total_problems - valid_problems,
            "auto_approved": auto_approved,
            "manual_review_needed": total_problems - auto_approved,
            "validity_rate": round(valid_problems / total_problems * 100, 2),
            "auto_approval_rate": round(auto_approved / total_problems * 100, 2),
            "common_issues": dict(sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:5])
        }