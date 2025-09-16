import os
import json
import random
import google.generativeai as genai
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class KoreanProblemGenerator:
    def __init__(self):
        gemini_api_key = os.getenv("KOREAN_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("KOREAN_GEMINI_API_KEY or GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        # 데이터 파일 경로
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data")

    def load_source_text(self, korean_type: str) -> str:
        """문제 유형에 따른 지문 로드"""
        try:
            if korean_type == "시":
                poem_files = [f for f in os.listdir(os.path.join(self.data_path, "poem")) if f.endswith('.txt')]
                if poem_files:
                    selected_file = random.choice(poem_files)
                    with open(os.path.join(self.data_path, "poem", selected_file), 'r', encoding='utf-8') as f:
                        return f.read()

            elif korean_type == "소설":
                novel_files = [f for f in os.listdir(os.path.join(self.data_path, "novel")) if f.endswith('.txt')]
                if novel_files:
                    selected_file = random.choice(novel_files)
                    with open(os.path.join(self.data_path, "novel", selected_file), 'r', encoding='utf-8') as f:
                        return f.read()

            elif korean_type == "수필/비문학":
                nonfiction_files = [f for f in os.listdir(os.path.join(self.data_path, "non-fiction")) if f.endswith('.txt')]
                if nonfiction_files:
                    selected_file = random.choice(nonfiction_files)
                    with open(os.path.join(self.data_path, "non-fiction", selected_file), 'r', encoding='utf-8') as f:
                        return f.read()

            elif korean_type == "문법":
                with open(os.path.join(self.data_path, "grammar.txt"), 'r', encoding='utf-8') as f:
                    return f.read()

        except Exception as e:
            print(f"데이터 파일 로드 오류: {e}")
            return ""

        return ""

    def generate_problems(self, korean_data: Dict, user_prompt: str, problem_count: int = 1,
                         korean_type_ratio: Dict = None, question_type_ratio: Dict = None,
                         difficulty_ratio: Dict = None) -> List[Dict]:
        """국어 문제 생성"""
        try:
            problems = []

            # 비율에 따른 문제 생성 또는 단일 유형 문제 생성
            if korean_type_ratio and sum(korean_type_ratio.values()) == 100:
                # 비율에 따른 문제 생성
                for korean_type, ratio in korean_type_ratio.items():
                    count = int(problem_count * ratio / 100)
                    if count > 0:
                        type_problems = self._generate_problems_by_type(
                            korean_data, user_prompt, count, korean_type,
                            question_type_ratio, difficulty_ratio
                        )
                        problems.extend(type_problems)
            else:
                # 단일 유형 문제 생성
                korean_type = korean_data.get('korean_type', '시')
                problems = self._generate_problems_by_type(
                    korean_data, user_prompt, problem_count, korean_type,
                    question_type_ratio, difficulty_ratio
                )

            return problems[:problem_count]  # 정확한 개수로 제한

        except Exception as e:
            print(f"문제 생성 오류: {e}")
            return []

    def _generate_problems_by_type(self, korean_data: Dict, user_prompt: str, count: int,
                                  korean_type: str, question_type_ratio: Dict = None,
                                  difficulty_ratio: Dict = None) -> List[Dict]:
        """특정 유형의 문제 생성"""
        problems = []

        # 지문 로드
        source_text = self.load_source_text(korean_type)
        if not source_text:
            return []

        for i in range(count):
            try:
                # 문제 타입 결정
                question_type = self._determine_question_type(question_type_ratio, korean_data)

                # 난이도 결정
                difficulty = self._determine_difficulty(difficulty_ratio, korean_data)

                # AI를 통한 문제 생성
                problem = self._generate_single_problem(
                    source_text, korean_type, question_type, difficulty, user_prompt, korean_data
                )

                if problem:
                    problem['sequence_order'] = i + 1
                    problems.append(problem)

            except Exception as e:
                print(f"개별 문제 생성 오류: {e}")
                continue

        return problems

    def _determine_question_type(self, question_type_ratio: Dict, korean_data: Dict) -> str:
        """문제 형식 결정"""
        if question_type_ratio and sum(question_type_ratio.values()) == 100:
            # 비율에 따른 랜덤 선택
            types = list(question_type_ratio.keys())
            weights = list(question_type_ratio.values())
            return random.choices(types, weights=weights)[0]
        else:
            return korean_data.get('question_type', '객관식')

    def _determine_difficulty(self, difficulty_ratio: Dict, korean_data: Dict) -> str:
        """난이도 결정"""
        if difficulty_ratio and sum(difficulty_ratio.values()) == 100:
            # 비율에 따른 랜덤 선택
            difficulties = list(difficulty_ratio.keys())
            weights = list(difficulty_ratio.values())
            return random.choices(difficulties, weights=weights)[0]
        else:
            return korean_data.get('difficulty', '중')

    def _generate_single_problem(self, source_text: str, korean_type: str, question_type: str,
                                difficulty: str, user_prompt: str, korean_data: Dict) -> Dict:
        """단일 문제 생성"""
        try:
            # 프롬프트 구성
            prompt = self._build_prompt(source_text, korean_type, question_type, difficulty, user_prompt, korean_data)

            # AI 호출
            response = self.model.generate_content(prompt)
            result_text = response.text

            # JSON 파싱
            try:
                # JSON 부분만 추출
                if "```json" in result_text:
                    json_start = result_text.find("```json") + 7
                    json_end = result_text.find("```", json_start)
                    json_text = result_text[json_start:json_end].strip()
                else:
                    json_text = result_text.strip()

                problem_data = json.loads(json_text)

                # 필수 필드 검증 및 설정
                problem = {
                    'korean_type': korean_type,
                    'question_type': question_type,
                    'difficulty': difficulty,
                    'question': problem_data.get('question', ''),
                    'correct_answer': problem_data.get('correct_answer', ''),
                    'explanation': problem_data.get('explanation', ''),
                    'source_text': source_text[:500] + "..." if len(source_text) > 500 else source_text,
                    'source_title': problem_data.get('source_title', ''),
                    'source_author': problem_data.get('source_author', '')
                }

                # 객관식인 경우 선택지 추가
                if question_type == '객관식' and 'choices' in problem_data:
                    problem['choices'] = problem_data['choices']

                return problem

            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 텍스트: {result_text}")
                return None

        except Exception as e:
            print(f"AI 문제 생성 오류: {e}")
            return None

    def _build_prompt(self, source_text: str, korean_type: str, question_type: str,
                     difficulty: str, user_prompt: str, korean_data: Dict) -> str:
        """AI 프롬프트 구성"""

        # 난이도 설명
        difficulty_desc = {
            '상': '어려운 수준 (고차원적 사고, 복합적 이해 필요)',
            '중': '보통 수준 (기본 이해와 적용)',
            '하': '쉬운 수준 (기초 개념 확인)'
        }

        # 기본 프롬프트
        prompt = f"""
다음 지문을 바탕으로 {korean_type} 영역의 {question_type} 문제를 생성해주세요.

**지문:**
{source_text}

**문제 요구사항:**
- 학교급: {korean_data.get('school_level', '중학교')}
- 학년: {korean_data.get('grade', 1)}학년
- 학기: {korean_data.get('semester', '1학기')}
- 문제 유형: {korean_type}
- 문제 형식: {question_type}
- 난이도: {difficulty} ({difficulty_desc.get(difficulty, '')})
"""

        if user_prompt:
            prompt += f"\n**추가 요구사항:** {user_prompt}\n"

        if question_type == '객관식':
            prompt += """
**출력 형식 (JSON):**
```json
{
    "question": "문제 내용",
    "choices": ["1번 선택지", "2번 선택지", "3번 선택지", "4번 선택지"],
    "correct_answer": "정답 선택지 내용",
    "explanation": "해설",
    "source_title": "지문 제목 (있는 경우)",
    "source_author": "지문 작가 (있는 경우)"
}
```

**주의사항:**
- 4개의 선택지를 제공하고, 정답은 choices 배열의 실제 내용과 정확히 일치해야 합니다.
- 선택지는 명확하고 구별되어야 합니다.
"""
        else:
            prompt += """
**출력 형식 (JSON):**
```json
{
    "question": "문제 내용",
    "correct_answer": "정답",
    "explanation": "해설",
    "source_title": "지문 제목 (있는 경우)",
    "source_author": "지문 작가 (있는 경우)"
}
```

**주의사항:**
- 서술형/단답형 문제에 적합한 정답을 제시해주세요.
- 채점 기준이 명확해야 합니다.
"""

        prompt += f"""
**{korean_type} 영역 특성:**
"""

        if korean_type == '시':
            prompt += """
- 화자, 상황, 정서, 표현 기법, 주제 의식 등을 중심으로 문제 출제
- 운율, 은유, 의인법, 대조법 등의 문학적 표현 기법 분석
- 시어의 함축적 의미, 화자의 정서와 상황 파악
"""
        elif korean_type == '소설':
            prompt += """
- 인물, 배경, 사건, 갈등, 주제 등을 중심으로 문제 출제
- 서술자, 시점, 구성, 문체 등의 소설 기법 분석
- 인물의 심리, 갈등 상황, 주제 의식 파악
"""
        elif korean_type == '수필/비문학':
            prompt += """
- 글의 구조, 논리 전개, 주장과 근거, 핵심 내용 등을 중심으로 문제 출제
- 글쓴이의 관점, 의도, 글의 성격 파악
- 정보의 이해, 추론, 적용 능력 평가
"""
        elif korean_type == '문법':
            prompt += """
- 음운, 단어, 문장, 의미 등의 문법 요소를 중심으로 문제 출제
- 품사, 어휘, 문장 성분, 문법적 관계 분석
- 언어의 특성, 변화, 규칙 등에 대한 이해 평가
"""

        prompt += """
반드시 JSON 형식으로만 응답하고, 추가적인 설명은 포함하지 마세요.
"""

        return prompt