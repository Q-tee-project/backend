"""
최적화된 프롬프트 템플릿 - 타임아웃 문제 해결
"""
from typing import Dict, List

class OptimizedPromptTemplates:
    """최적화된 프롬프트 템플릿"""

    @staticmethod
    def get_core_prompt(curriculum_data: Dict, user_prompt: str,
                       problem_count: int, difficulty_distribution: str) -> str:
        """핵심 프롬프트만 포함 (최소화 버전)"""
        return f"""중학교 수학 문제를 생성하세요.

교육과정: {curriculum_data.get('grade')} {curriculum_data.get('unit_name')}
요청: {user_prompt}
난이도: {difficulty_distribution}

난이도 기준:
- A: 기본 개념, 1-2단계 계산
- B: 응용 문제, 3-5단계 계산, 2개 이상 개념 조합
- C: 심화 문제, 복잡한 추론, 창의적 접근 필요

JSON 형식:
[{{
  "question": "문제",
  "choices": ["A", "B", "C", "D"] (객관식만),
  "correct_answer": "정답",
  "explanation": "간단한 해설",
  "problem_type": "multiple_choice/short_answer/essay",
  "difficulty": "A/B/C"
}}]

규칙:
1. LaTeX: $x^2$, $\\frac{{a}}{{b}}$, $\\sqrt{{n}}$
2. 객관식 정답: "A", "B", "C", "D" 중 하나
3. 정확한 개수와 난이도 분배 준수"""

    @staticmethod
    def get_ultra_minimal_prompt(curriculum_data: Dict, user_prompt: str,
                                problem_count: int, difficulty_distribution: str) -> str:
        """극도로 간소화된 프롬프트 (타임아웃 마지막 시도)"""
        return f"""{curriculum_data.get('grade')} {curriculum_data.get('unit_name')} 문제 {problem_count}개

{user_prompt}
{difficulty_distribution}

A:기본 B:응용 C:심화

JSON: [{{"question":"", "choices":[], "correct_answer":"", "explanation":"", "problem_type":"", "difficulty":""}}]"""

    @staticmethod
    def build_batch_prompt(curriculum_data: Dict, user_prompt: str,
                          difficulty: str, batch_count: int) -> str:
        """난이도별 배치 생성용 프롬프트"""
        difficulty_desc = {
            'A': '기본 개념, 1-2단계 계산',
            'B': '응용 문제, 3-5단계 계산, 2개 개념 조합',
            'C': '심화 문제, 복잡한 추론, 창의적 접근'
        }

        return f"""중학 {curriculum_data.get('grade')} {curriculum_data.get('unit_name')} 문제

요청: {user_prompt}
난이도: {difficulty}단계 - {difficulty_desc.get(difficulty, '')}
개수: {batch_count}개

JSON 형식으로 정확히 {batch_count}개 생성:
[{{"question":"", "choices":[], "correct_answer":"", "explanation":"", "problem_type":"multiple_choice", "difficulty":"{difficulty}"}}]"""


class AdaptivePromptBuilder:
    """적응형 프롬프트 빌더"""

    DETAIL_LEVELS = {
        'minimal': 300,   # 300자 이하
        'standard': 800,  # 800자 이하
        'detailed': 2000  # 2000자 이하
    }

    @staticmethod
    def build_prompt(detail_level: str = 'standard', **kwargs) -> str:
        """상세도 레벨에 따른 프롬프트 생성"""

        if detail_level == 'minimal':
            return OptimizedPromptTemplates.get_ultra_minimal_prompt(
                kwargs['curriculum_data'],
                kwargs['user_prompt'],
                kwargs['problem_count'],
                kwargs['difficulty_distribution']
            )

        elif detail_level == 'standard':
            return OptimizedPromptTemplates.get_core_prompt(
                kwargs['curriculum_data'],
                kwargs['user_prompt'],
                kwargs['problem_count'],
                kwargs['difficulty_distribution']
            )

        else:  # detailed
            # 기존 상세 프롬프트 사용
            from .prompt_templates import PromptTemplates
            return PromptTemplates.build_problem_generation_prompt(
                curriculum_data=kwargs['curriculum_data'],
                user_prompt=kwargs['user_prompt'],
                problem_count=kwargs['problem_count'],
                difficulty_distribution=kwargs['difficulty_distribution'],
                reference_problems=kwargs.get('reference_problems', '')
            )


class CachedPromptSystem:
    """캐싱을 활용한 프롬프트 시스템"""

    def __init__(self):
        self.cache = {}
        self.common_patterns = self.load_common_patterns()

    def load_common_patterns(self):
        """자주 사용되는 문제 패턴 로드"""
        return {
            "일차방정식": "변수를 포함한 방정식을 풀이하는 문제",
            "방정식": "등식의 성질을 이용한 문제",
            "도형": "삼각형, 사각형 등의 성질을 활용하는 문제",
            "함수": "일차함수의 그래프와 성질 문제",
            "확률": "경우의 수와 확률 계산 문제",
            "통계": "자료의 정리와 해석 문제"
        }

    def get_optimized_prompt(self, curriculum_data: Dict, user_prompt: str,
                            problem_count: int, difficulty_distribution: str) -> str:
        """최적화된 프롬프트 반환"""
        chapter_name = curriculum_data.get('chapter_name', '')
        cache_key = f"{chapter_name}_{difficulty_distribution}_{problem_count}"

        if cache_key in self.cache:
            cached_prompt = self.cache[cache_key]
            # 사용자 프롬프트만 교체
            return cached_prompt.replace("{{USER_PROMPT}}", user_prompt)

        # 패턴 매칭으로 간소화
        if chapter_name in self.common_patterns:
            prompt = f"""중학 수학 {chapter_name} 문제 {problem_count}개 생성

요청: {{USER_PROMPT}}
분배: {difficulty_distribution}
패턴: {self.common_patterns[chapter_name]}

A:기본 B:응용 C:심화
JSON:[{{"question":"", "choices":[], "correct_answer":"", "explanation":"", "problem_type":"", "difficulty":""}}]"""
        else:
            prompt = OptimizedPromptTemplates.get_core_prompt(
                curriculum_data, "{{USER_PROMPT}}", problem_count, difficulty_distribution
            )

        self.cache[cache_key] = prompt
        return prompt.replace("{{USER_PROMPT}}", user_prompt)


class PromptLengthAnalyzer:
    """프롬프트 길이 분석기"""

    @staticmethod
    def analyze_prompt_length(prompt: str) -> Dict:
        """프롬프트 길이 분석"""
        return {
            'character_count': len(prompt),
            'word_count': len(prompt.split()),
            'estimated_tokens': len(prompt) // 4,  # 대략적인 토큰 수
            'recommended_level': PromptLengthAnalyzer.get_recommended_level(len(prompt))
        }

    @staticmethod
    def get_recommended_level(char_count: int) -> str:
        """문자 수에 따른 권장 레벨"""
        if char_count < 500:
            return 'minimal'
        elif char_count < 1500:
            return 'standard'
        else:
            return 'detailed'