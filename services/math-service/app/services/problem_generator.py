"""
수학 문제 생성 로직 분리 - JSON 파싱 완벽 개선
"""
import os
import json
import re
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from .prompt_templates import PromptTemplates
from dotenv import load_dotenv

load_dotenv()

class ProblemGenerator:
    """수학 문제 생성 전용 클래스"""
    
    def __init__(self):
        # AI 모델 직접 초기화 (순환 import 방지)
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=gemini_api_key)

        # 기본 설정으로 복원 (타임아웃 해결을 위해 토큰 수 조정)
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=12288,
            top_p=0.8,
            top_k=40
        )

        self.model = genai.GenerativeModel(
            'gemini-2.5-pro',
            generation_config=generation_config
        )
        self.prompt_templates = PromptTemplates()
    
    def generate_problems(
        self, 
        curriculum_data: Dict, 
        user_prompt: str, 
        problem_count: int = 1, 
        difficulty_ratio: Dict = None
    ) -> List[Dict]:
        """수학 문제 생성 메인 로직"""
        
        # 난이도 분배 계산
        difficulty_distribution = self._calculate_difficulty_distribution(
            problem_count, difficulty_ratio
        )
        
        # 참고 문제 가져오기
        reference_problems = self._get_reference_problems(
            curriculum_data.get('chapter_name', ''), 
            difficulty_ratio
        )
        
        # 프롬프트 빌드
        prompt = self.prompt_templates.build_problem_generation_prompt(
            curriculum_data=curriculum_data,
            user_prompt=user_prompt,
            problem_count=problem_count,
            difficulty_distribution=difficulty_distribution,
            reference_problems=reference_problems
        )
        
        # AI 호출 및 응답 처리
        return self._call_ai_and_parse_response(prompt)
    
    def _calculate_difficulty_distribution(self, problem_count: int, difficulty_ratio: Dict) -> str:
        """난이도 분배 계산"""
        if difficulty_ratio:
            # 비율에 따른 각 난이도별 문제 개수 계산
            total_problems = problem_count
            a_count = round(total_problems * difficulty_ratio['A'] / 100)
            b_count = round(total_problems * difficulty_ratio['B'] / 100)
            c_count = total_problems - a_count - b_count  # 나머지는 C
            
            return f"A단계 {a_count}개, B단계 {b_count}개, C단계 {c_count}개"
        else:
            return f"모든 문제 B단계"
    
    def _get_reference_problems(self, chapter_name: str, difficulty_ratio: Dict) -> str:
        """참고 문제 가져오기"""
        try:
            problem_types_file_path = os.path.join(
                os.path.dirname(__file__), 
                "../../data/math_problem_types.json"
            )
            
            with open(problem_types_file_path, 'r', encoding='utf-8') as f:
                problem_types_data = json.load(f)
            
            # 챕터명으로 문제 유형 찾기
            chapter_problem_types = []
            for chapter_data in problem_types_data["math_problem_types"]:
                if chapter_data["chapter_name"] == chapter_name:
                    chapter_problem_types = chapter_data["problem_types"]
                    break
            
            if not chapter_problem_types:
                return f"'{chapter_name}' 챕터의 참고 문제를 찾을 수 없습니다."
            
            # 난이도별 문제 유형 분배
            total_types = len(chapter_problem_types)
            a_types = chapter_problem_types[:total_types//3] if total_types >= 3 else [chapter_problem_types[0]]
            b_types = chapter_problem_types[total_types//3:2*total_types//3] if total_types >= 6 else chapter_problem_types[1:2] if total_types >= 2 else []
            c_types = chapter_problem_types[2*total_types//3:] if total_types >= 3 else chapter_problem_types[-1:] if total_types >= 3 else []
            
            # 참고 문제 텍스트 구성 - 난이도별 차별화
            reference_text = f"**{chapter_name} 참고 문제 유형:**\n\n"

            if difficulty_ratio and difficulty_ratio.get('A', 0) > 0 and a_types:
                reference_text += f"**A단계 유형**: {', '.join(a_types[:4])}\n"
                reference_text += "   → 쎈 A단계: 공식 대입 수준의 기본 문제 (1~2줄, 정답률 80~90%)\n\n"

            if difficulty_ratio and difficulty_ratio.get('B', 0) > 0 and b_types:
                reference_text += f"**B단계 유형**: {', '.join(b_types[:4])}\n"
                reference_text += "   → 쎈 B단계: 실생활 응용/유형 문제 (3~4줄, 정답률 50~60%)\n\n"

            if difficulty_ratio and difficulty_ratio.get('C', 0) > 0 and c_types:
                reference_text += f"**C단계 유형**: {', '.join(c_types[:4])}\n"
                reference_text += "   → 쎈 C단계: 창의적 사고 필요한 심화 문제 (5~7줄, 정답률 20~30%)\n\n"
            
            return reference_text
            
        except Exception as e:
            print(f"참고 문제 로드 오류: {str(e)}")
            return f"'{chapter_name}' 참고 문제 로드 중 오류 발생"
    
    def _call_ai_and_parse_response(self, prompt: str) -> List[Dict]:
        """AI 호출 및 응답 파싱 - 개선된 버전"""
        try:
            response = self.model.generate_content(
                prompt,
                request_options={'timeout': 1200}  # 20분 타임아웃
            )
            content = response.text
            
            # JSON 추출 및 파싱
            problems = self._extract_and_parse_json(content)
            
            # LaTeX 검증 및 수정
            validated_problems = []
            for problem in problems:
                validated_problem = self._validate_and_fix_problem(problem)
                validated_problems.append(validated_problem)
            
            return validated_problems
            
        except Exception as e:
            import traceback
            error_msg = f"문제 생성 오류: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _extract_and_parse_json(self, content: str) -> List[Dict]:
        """JSON 추출 및 파싱 - 완전 개선 버전"""
        # 1. JSON 블록 추출
        json_str = self._extract_json_block(content)
        
        # 2. JSON 문자열 전처리
        preprocessed = self._preprocess_json_string(json_str)
        
        # 3. JSON 파싱 시도
        try:
            result = json.loads(preprocessed)
            return result if isinstance(result, list) else [result]
        except json.JSONDecodeError as e:
            # 4. 고급 복구 시도
            recovered = self._advanced_json_recovery(preprocessed)
            if recovered:
                return recovered
            
            # 5. 최후의 수단: 개별 객체 파싱
            individual_problems = self._parse_individual_problems(preprocessed)
            if individual_problems:
                return individual_problems
            
            raise Exception(f"JSON 파싱 실패: {str(e)}\n원본: {json_str[:500]}...")
    
    def _extract_json_block(self, content: str) -> str:
        """JSON 블록 추출"""
        # JSON 코드 블록 찾기
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            if json_end != -1:
                return content[json_start:json_end].strip()
        
        # 배열 패턴 찾기
        array_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
        if array_match:
            return array_match.group(0)
        
        # 그냥 전체 반환
        return content.strip()
    
    def _preprocess_json_string(self, json_str: str) -> str:
        """JSON 문자열 전처리 - 완전 개선"""
        if not json_str:
            return "[]"
        
        # 1. 기본 정리
        cleaned = json_str.strip()
        
        # 2. LaTeX 수식 보호 (임시 플레이스홀더로 교체)
        math_expressions = []
        
        def protect_math(match):
            expr = match.group(1)
            placeholder = f"__MATH_{len(math_expressions)}__"
            math_expressions.append(expr)
            return f'"{placeholder}"' if match.group(0).startswith('"') else placeholder
        
        # $ ... $ 형태의 수식 보호
        cleaned = re.sub(r'\$([^$]+)\$', protect_math, cleaned)
        
        # 3. 제어 문자 및 잘못된 문자 제거
        cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        # 4. 문자열 내 줄바꿈 처리
        def fix_multiline_strings(match):
            content = match.group(1)
            # 문자열 내부의 줄바꿈을 공백으로 변경
            content = re.sub(r'\s*\n\s*', ' ', content)
            return f'"{content}"'
        
        # 따옴표로 둘러싸인 문자열 내부 정리
        cleaned = re.sub(r'"([^"]*)"', fix_multiline_strings, cleaned)
        
        # 5. JSON 구조 정리
        # 끝부분 쉼표 제거
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        # 누락된 쉼표 추가
        cleaned = re.sub(r'}\s*{', '},{', cleaned)
        cleaned = re.sub(r']\s*\[', '],[', cleaned)
        
        # 6. 필드명 정리 (따옴표 확인)
        field_names = ['question', 'choices', 'correct_answer', 'explanation', 
                      'problem_type', 'difficulty', 'has_diagram', 'diagram_type', 
                      'diagram_elements']
        
        for field in field_names:
            # 따옴표 없는 필드명에 따옴표 추가
            cleaned = re.sub(f'(?<!")\\b{field}\\b(?!")', f'"{field}"', cleaned)
        
        # 7. 수식 복원
        for i, expr in enumerate(math_expressions):
            placeholder = f"__MATH_{i}__"
            # LaTeX 백슬래시 이스케이프
            escaped_expr = expr.replace('\\', '\\\\').replace('"', '\\"')
            cleaned = cleaned.replace(placeholder, f"${escaped_expr}$")
        
        # 8. 최종 정리
        cleaned = re.sub(r'\s+', ' ', cleaned)  # 다중 공백 제거
        
        return cleaned
    
    def _advanced_json_recovery(self, json_str: str) -> Optional[List[Dict]]:
        """고급 JSON 복구 시도"""
        try:
            # 1. 배열 구조 확인 및 수정
            if not json_str.startswith('['):
                json_str = '[' + json_str
            if not json_str.endswith(']'):
                json_str = json_str + ']'
            
            # 2. 개별 객체 추출 시도
            object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(object_pattern, json_str)
            
            if matches:
                problems = []
                for match in matches:
                    try:
                        # 개별 객체 파싱
                        obj = json.loads(match)
                        if self._is_valid_problem(obj):
                            problems.append(obj)
                    except:
                        continue
                
                if problems:
                    return problems
            
            # 3. 구조 복구 시도
            # 잘못된 중첩 구조 수정
            json_str = re.sub(r'(\w+):\s*{', r'"\1": {', json_str)
            json_str = re.sub(r'(\w+):\s*\[', r'"\1": [', json_str)
            json_str = re.sub(r'(\w+):\s*"', r'"\1": "', json_str)
            json_str = re.sub(r'(\w+):\s*(\d+)', r'"\1": \2', json_str)
            json_str = re.sub(r'(\w+):\s*(true|false|null)', r'"\1": \2', json_str)
            
            return json.loads(json_str)
            
        except:
            return None
    
    def _parse_individual_problems(self, json_str: str) -> Optional[List[Dict]]:
        """개별 문제 객체 파싱 - 최후의 수단"""
        problems = []
        
        # 각 문제 객체를 개별적으로 찾아서 파싱
        current_pos = 0
        while True:
            # { 찾기
            start = json_str.find('{', current_pos)
            if start == -1:
                break
            
            # 매칭되는 } 찾기
            bracket_count = 0
            end = start
            for i in range(start, len(json_str)):
                if json_str[i] == '{':
                    bracket_count += 1
                elif json_str[i] == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            
            if end > start:
                obj_str = json_str[start:end]
                try:
                    # 개별 객체 파싱 시도
                    obj = json.loads(obj_str)
                    if self._is_valid_problem(obj):
                        problems.append(obj)
                except:
                    # 파싱 실패 시 수동 파싱 시도
                    manual_obj = self._manual_parse_problem(obj_str)
                    if manual_obj:
                        problems.append(manual_obj)
                
                current_pos = end
            else:
                break
        
        return problems if problems else None
    
    def _manual_parse_problem(self, obj_str: str) -> Optional[Dict]:
        """수동으로 문제 객체 파싱"""
        try:
            problem = {}
            
            # 필드 추출 패턴
            patterns = {
                'question': r'"question"\s*:\s*"([^"]*(?:\\"[^"]*)*)"',
                'correct_answer': r'"correct_answer"\s*:\s*"([^"]*(?:\\"[^"]*)*)"',
                'explanation': r'"explanation"\s*:\s*"([^"]*(?:\\"[^"]*)*)"',
                'problem_type': r'"problem_type"\s*:\s*"([^"]*)"',
                'difficulty': r'"difficulty"\s*:\s*"([ABC])"',
                'has_diagram': r'"has_diagram"\s*:\s*(true|false)',
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, obj_str, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if field == 'has_diagram':
                        problem[field] = value.lower() == 'true'
                    else:
                        # 이스케이프된 따옴표 복원
                        value = value.replace('\\"', '"')
                        problem[field] = value
            
            # choices 배열 추출
            choices_match = re.search(r'"choices"\s*:\s*\[([^\]]*)\]', obj_str)
            if choices_match:
                choices_str = choices_match.group(1)
                choices = []
                for choice_match in re.finditer(r'"([^"]*(?:\\"[^"]*)*)"', choices_str):
                    choice = choice_match.group(1).replace('\\"', '"')
                    choices.append(choice)
                problem['choices'] = choices
            
            # 필수 필드 확인
            if 'question' in problem and 'correct_answer' in problem:
                # 기본값 설정
                problem.setdefault('problem_type', 'short_answer')
                problem.setdefault('difficulty', 'B')
                problem.setdefault('has_diagram', False)
                problem.setdefault('explanation', '')
                
                return problem
            
        except:
            pass
        
        return None
    
    def _is_valid_problem(self, obj: Dict) -> bool:
        """문제 객체 유효성 검사"""
        required_fields = ['question', 'correct_answer']
        return all(field in obj for field in required_fields)
    
    def _validate_and_fix_problem(self, problem: Dict) -> Dict:
        """문제 검증 및 수정 - 완전 개선"""
        # 1. 필수 필드 확인 및 기본값 설정
        problem = self._ensure_required_fields(problem)
        
        # 2. LaTeX 수식 검증 및 수정
        problem = self._fix_latex_in_problem(problem)
        
        # 3. 데이터 타입 검증
        problem = self._validate_data_types(problem)
        
        return problem
    
    def _ensure_required_fields(self, problem: Dict) -> Dict:
        """필수 필드 확인 및 기본값 설정"""
        defaults = {
            'question': '',
            'correct_answer': '',
            'explanation': '',
            'problem_type': 'short_answer',
            'difficulty': 'B',
            'has_diagram': False,
            'diagram_type': None,
            'diagram_elements': None
        }
        
        for field, default_value in defaults.items():
            if field not in problem:
                problem[field] = default_value
        
        # choices 필드는 객관식일 때만
        if problem['problem_type'] == 'multiple_choice' and 'choices' not in problem:
            problem['choices'] = []
        
        return problem
    
    def _fix_latex_in_problem(self, problem: Dict) -> Dict:
        """LaTeX 수식 수정 - KaTeX 호환"""
        # LaTeX 수정 패턴
        latex_fixes = [
            # 잘못된 명령어 수정
            (r'(?<!\\)frac\{', r'\\frac{'),
            (r'(?<!\\)sqrt\{', r'\\sqrt{'),
            (r'(?<!\\)sin(?!\w)', r'\\sin'),
            (r'(?<!\\)cos(?!\w)', r'\\cos'),
            (r'(?<!\\)tan(?!\w)', r'\\tan'),
            (r'(?<!\\)log(?!\w)', r'\\log'),
            (r'(?<!\\)ln(?!\w)', r'\\ln'),
            (r'(?<!\\)pi(?!\w)', r'\\pi'),
            (r'(?<!\\)alpha(?!\w)', r'\\alpha'),
            (r'(?<!\\)beta(?!\w)', r'\\beta'),
            (r'(?<!\\)theta(?!\w)', r'\\theta'),
            (r'(?<!\\)times(?!\w)', r'\\times'),
            (r'(?<!\\)div(?!\w)', r'\\div'),
            (r'(?<!\\)leq(?!\w)', r'\\leq'),
            (r'(?<!\\)geq(?!\w)', r'\\geq'),
            (r'(?<!\\)neq(?!\w)', r'\\neq'),
            
            # 단독 백슬래시 문자 제거
            (r'\\([fnglts])(?![a-zA-Z])', r''),
            
            # 중괄호 누락 수정
            (r'\^(\d{2,})', r'^{\1}'),  # 두 자리 이상 지수
            (r'_(\d{2,})', r'_{\1}'),   # 두 자리 이상 아래첨자
        ]
        
        # 텍스트 필드 처리
        text_fields = ['question', 'correct_answer', 'explanation']
        for field in text_fields:
            if field in problem and isinstance(problem[field], str):
                problem[field] = self._apply_latex_fixes(problem[field], latex_fixes)
        
        # choices 배열 처리
        if 'choices' in problem and isinstance(problem['choices'], list):
            problem['choices'] = [
                self._apply_latex_fixes(choice, latex_fixes) 
                if isinstance(choice, str) else choice
                for choice in problem['choices']
            ]
        
        return problem
    
    def _apply_latex_fixes(self, text: str, fixes: List[tuple]) -> str:
        """LaTeX 수정 규칙 적용"""
        if not text:
            return text
        
        fixed = text
        for pattern, replacement in fixes:
            fixed = re.sub(pattern, replacement, fixed)
        
        # $ 기호 확인 (수식이 제대로 감싸져 있는지)
        # 백슬래시로 시작하는 명령어가 $ 밖에 있으면 감싸기
        fixed = re.sub(r'(?<!\$)(\\(?:frac|sqrt|sin|cos|tan|log|pi|alpha|beta|theta)[^$]*?)(?!\$)', 
                      r'$\1$', fixed)
        
        return fixed
    
    def _validate_data_types(self, problem: Dict) -> Dict:
        """데이터 타입 검증 및 수정"""
        # difficulty는 대문자로
        if 'difficulty' in problem:
            difficulty = str(problem['difficulty']).upper()
            if difficulty not in ['A', 'B', 'C']:
                problem['difficulty'] = 'B'
            else:
                problem['difficulty'] = difficulty
        
        # problem_type 검증
        valid_types = ['multiple_choice', 'short_answer', 'essay']
        if 'problem_type' in problem:
            if problem['problem_type'] not in valid_types:
                # 추측
                if 'choices' in problem and problem['choices']:
                    problem['problem_type'] = 'multiple_choice'
                else:
                    problem['problem_type'] = 'short_answer'
        
        # has_diagram은 boolean으로
        if 'has_diagram' in problem:
            if isinstance(problem['has_diagram'], str):
                problem['has_diagram'] = problem['has_diagram'].lower() == 'true'
            elif not isinstance(problem['has_diagram'], bool):
                problem['has_diagram'] = False
        
        # 객관식 correct_answer 검증
        if problem.get('problem_type') == 'multiple_choice':
            if 'correct_answer' in problem:
                answer = str(problem['correct_answer']).upper()
                if answer not in ['A', 'B', 'C', 'D']:
                    # 숫자로 되어 있으면 변환
                    if answer in ['1', '2', '3', '4']:
                        problem['correct_answer'] = chr(ord('A') + int(answer) - 1)
                    # ①②③④로 되어 있으면 변환
                    elif answer in ['①', '②', '③', '④']:
                        mapping = {'①': 'A', '②': 'B', '③': 'C', '④': 'D'}
                        problem['correct_answer'] = mapping.get(answer, 'A')
                    else:
                        problem['correct_answer'] = 'A'  # 기본값
                else:
                    problem['correct_answer'] = answer
        
        return problem