"""
수학 문제 생성 로직 분리
"""
import os
import json
import google.generativeai as genai
from typing import Dict, List
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
        
        # API 키 설정 및 타임아웃 구성
        genai.configure(api_key=gemini_api_key)

        # 더 빠른 응답을 위한 최적화된 설정
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',  # 더 빠른 모델 사용
            generation_config=genai.types.GenerationConfig(
                temperature=0.6,  # 빠른 생성을 위해 낮춤
                top_p=0.9,       # 더 간결한 응답을 위해 높임
                top_k=20,        # 선택지 줄여서 빠른 생성
                max_output_tokens=4096,  # 토큰 수 절반으로 줄임
            )
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
        
        # AI 호출 및 응답 처리 (최적화된 매개변수 전달)
        return self._call_ai_and_parse_response(
            prompt=prompt,
            curriculum_data=curriculum_data,
            user_prompt=user_prompt,
            problem_count=problem_count,
            difficulty_ratio=difficulty_ratio
        )
    
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
            import os
            
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
            
            # 참고 문제 텍스트 구성
            reference_text = f"**{chapter_name} 참고 문제 유형:**\n\n"
            
            if difficulty_ratio and difficulty_ratio.get('A', 0) > 0 and a_types:
                reference_text += f"**A단계 유형**: {', '.join(a_types[:4])}\n"
                reference_text += "   → 기본 개념과 정의를 직접 적용하는 문제로 변형\n\n"
            
            if difficulty_ratio and difficulty_ratio.get('B', 0) > 0 and b_types:  
                reference_text += f"**B단계 유형**: {', '.join(b_types[:4])}\n" 
                reference_text += "   → 계산 과정과 공식 적용이 포함된 응용 문제로 변형\n\n"
                
            if difficulty_ratio and difficulty_ratio.get('C', 0) > 0 and c_types:
                reference_text += f"**C단계 유형**: {', '.join(c_types[:4])}\n"
                reference_text += "   → 조건 분석과 종합적 사고가 필요한 심화 문제로 변형\n\n"
            
            return reference_text
            
        except Exception as e:
            print(f"참고 문제 로드 오류: {str(e)}")
            return f"'{chapter_name}' 참고 문제 로드 중 오류 발생"
    
    def _call_ai_and_parse_response(self, prompt: str, curriculum_data: Dict = None, user_prompt: str = None, problem_count: int = 1, difficulty_ratio: Dict = None) -> List[Dict]:
        """AI 호출 및 응답 파싱 - 단계적 프롬프트 최적화"""
        import time
        from .optimized_prompt_templates import AdaptivePromptBuilder, PromptLengthAnalyzer

        try:
            # 프롬프트 길이 분석
            analysis = PromptLengthAnalyzer.analyze_prompt_length(prompt)
            print(f"📊 프롬프트 분석: {analysis['character_count']}자, 추정 토큰: {analysis['estimated_tokens']}")

            # 단계적 시도 정의
            retry_strategies = [
                {'level': 'detailed', 'timeout': 20, 'description': '상세 프롬프트'},
                {'level': 'standard', 'timeout': 15, 'description': '표준 프롬프트'},
                {'level': 'minimal', 'timeout': 10, 'description': '최소 프롬프트'}
            ]

            # 프롬프트 길이에 따라 시작 전략 조정
            if analysis['character_count'] > 2000:
                retry_strategies = retry_strategies[1:]  # 상세 프롬프트 건너뛰기
            elif analysis['character_count'] > 1500:
                retry_strategies[0]['timeout'] = 15  # 첫 시도 타임아웃 단축

            for attempt, strategy in enumerate(retry_strategies):
                try:
                    # 전략에 따른 프롬프트 생성
                    if attempt == 0 and strategy['level'] == 'detailed':
                        current_prompt = prompt  # 원본 프롬프트 사용
                    else:
                        # 최적화된 프롬프트 생성
                        if curriculum_data and user_prompt is not None:
                            difficulty_distribution = self._calculate_difficulty_distribution(problem_count, difficulty_ratio) if difficulty_ratio else "모든 문제 B단계"
                            current_prompt = AdaptivePromptBuilder.build_prompt(
                                detail_level=strategy['level'],
                                curriculum_data=curriculum_data,
                                user_prompt=user_prompt,
                                problem_count=problem_count,
                                difficulty_distribution=difficulty_distribution
                            )
                        else:
                            current_prompt = prompt  # 백업용

                    print(f"🤖 AI 생성 시도 {attempt + 1}/{len(retry_strategies)}: {strategy['description']} ({strategy['timeout']}초)")
                    print(f"📝 프롬프트 길이: {len(current_prompt)}자")

                    # 타임아웃과 함께 AI 모델로 컨텐츠 생성
                    import signal

                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"AI 생성 타임아웃 ({strategy['timeout']}초 초과)")

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(strategy['timeout'])

                    try:
                        response = self.model.generate_content(current_prompt)
                        content = response.text
                        signal.alarm(0)  # 타임아웃 해제
                        print(f"✅ AI 응답 성공 (시도 {attempt + 1}, {strategy['description']})")
                        break
                    except TimeoutError:
                        signal.alarm(0)  # 타임아웃 해제
                        raise TimeoutError(f"AI 응답 시간 초과 ({strategy['timeout']}초)")

                except (TimeoutError, Exception) as e:
                    print(f"❌ AI 생성 시도 {attempt + 1} 실패: {str(e)}")

                    if attempt < len(retry_strategies) - 1:
                        print(f"⏳ 다음 전략으로 즉시 시도...")
                    else:
                        print("❌ 모든 전략 실패 → 폴백으로 전환")
                        raise e

            # for 루프 밖에서 content 처리
            # JSON 부분만 추출
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content

            # JSON 정리 및 파싱
            problems_array = self._clean_and_parse_json(json_str)
            problems_list = problems_array if isinstance(problems_array, list) else [problems_array]

            # LaTeX 검증 및 수정
            validated_problems = []
            for problem in problems_list:
                validated_problem = self._validate_and_fix_latex(problem)
                validated_problems.append(validated_problem)

            return validated_problems

        except Exception as e:
            import traceback
            error_msg = f"문제 생성 오류: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _clean_and_parse_json(self, json_str: str):
        """JSON 문자열 정리 및 파싱 - 개선된 버전"""
        import re
        import json
        
        try:
            # 1차 시도: 원본 그대로 파싱
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"1차 JSON 파싱 실패: {str(e)}")
            
            try:
                # 2차 시도: 고급 전처리
                cleaned = self._preprocess_json_string(json_str)
                return json.loads(cleaned)
            except json.JSONDecodeError as e2:
                print(f"2차 JSON 파싱 실패: {str(e2)}")
                
                try:
                    # 3차 시도: JSON 배열 패턴 찾기 및 추가 정리
                    array_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
                    if array_match:
                        array_part = array_match.group(0)
                        array_cleaned = self._preprocess_json_string(array_part)
                        return json.loads(array_cleaned)
                    else:
                        raise e2
                except (json.JSONDecodeError, Exception) as e3:
                    print(f"3차 JSON 파싱 실패: {str(e3)}")
                    print(f"문제가 있는 JSON 앞부분: {json_str[:300]}...")
                    raise Exception(f"JSON 파싱 완전 실패: {str(e3)}")
    
    def _preprocess_json_string(self, json_str: str) -> str:
        """JSON 문자열 전처리 - LaTeX 및 특수문자 처리"""
        import re
        
        # 기본 정리
        cleaned = json_str.strip()
        
        # 1. 제어 문자 제거 (탭, 캐리지 리턴, 기타 제어문자)
        cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        # 2. 잘못된 줄바꿈 처리
        cleaned = re.sub(r'\n\s*"', ' "', cleaned)  # 줄바꿈 후 따옴표
        cleaned = re.sub(r',\s*\n\s*}', '}', cleaned)  # 끝부분 쉼표+줄바꿈
        cleaned = re.sub(r',\s*\n\s*]', ']', cleaned)  # 배열 끝부분 처리
        
        # 3. LaTeX 수학 표기법 안전하게 처리
        # $..$ 형태의 LaTeX를 찾아서 이스케이프 처리
        def escape_latex_math(match):
            content = match.group(1)
            # 백슬래시를 두 배로 만들어 JSON에서 안전하게 처리
            escaped = content.replace('\\', '\\\\')
            return f"${escaped}$"
        
        # $...$ 패턴 처리
        cleaned = re.sub(r'\$([^$]+)\$', escape_latex_math, cleaned)
        
        # 4. 일반적인 이스케이프 문자 처리
        # JSON 문자열 내부의 백슬래시 처리 (LaTeX 제외)
        def fix_escape_in_strings(match):
            quote = match.group(1)  # 시작 따옴표
            content = match.group(2)  # 문자열 내용
            end_quote = match.group(3)  # 끝 따옴표
            
            # LaTeX 수학 표기법이 아닌 경우만 처리
            if '$' not in content:
                # 잘못된 이스케이프 시퀀스 수정
                content = re.sub(r'\\(?!["\\/bfnrt])', r'\\\\', content)
            
            return f'{quote}{content}{end_quote}'
        
        # JSON 문자열 내부 처리
        cleaned = re.sub(r'(")([^"]*)(")(?=\s*[,}\]])', fix_escape_in_strings, cleaned)
        
        # 5. 특수 LaTeX 명령어들 보호
        latex_protections = [
            (r'\\frac\{', '__FRAC_START__'),
            (r'\\sqrt\{', '__SQRT_START__'),
            (r'\\sin\(', '__SIN_START__'),
            (r'\\cos\(', '__COS_START__'),
            (r'\\tan\(', '__TAN_START__'),
            (r'\\log\(', '__LOG_START__'),
            (r'\\pi\b', '__PI__'),
            (r'\\alpha\b', '__ALPHA__'),
            (r'\\beta\b', '__BETA__'),
            (r'\\theta\b', '__THETA__'),
            (r'\\leq\b', '__LEQ__'),
            (r'\\geq\b', '__GEQ__'),
            (r'\\neq\b', '__NEQ__'),
            (r'\\approx\b', '__APPROX__'),
        ]
        
        # 보호 적용
        protection_map = {}
        for pattern, placeholder in latex_protections:
            matches = re.findall(pattern, cleaned)
            for match in matches:
                if match not in protection_map:
                    protection_map[match] = placeholder
                cleaned = cleaned.replace(match, placeholder)
        
        # 6. 마지막 정리
        cleaned = re.sub(r',\s*}', '}', cleaned)  # 객체 끝 쉼표 제거
        cleaned = re.sub(r',\s*]', ']', cleaned)  # 배열 끝 쉼표 제거
        cleaned = re.sub(r'\s+', ' ', cleaned)    # 다중 공백 정리
        
        # 7. LaTeX 명령어 복원
        for original, placeholder in protection_map.items():
            cleaned = cleaned.replace(placeholder, original)
        
        return cleaned
    
    def _validate_and_fix_latex(self, problem: Dict) -> Dict:
        """LaTeX 구문 검증 및 수정"""
        import re
        
        # 잘못된 LaTeX 패턴들과 올바른 형태로의 매핑
        latex_fixes = [
            (r'rac\{([^}]+)\}\{([^}]+)\}', r'\\frac{\1}{\2}'),  # rac{} -> \frac{}{}
            (r'qrt\{([^}]+)\}', r'\\sqrt{\1}'),                # qrt{} -> \sqrt{}
            (r'in\(([^)]+)\)', r'\\sin(\1)'),                  # in() -> \sin()
            (r'os\(([^)]+)\)', r'\\cos(\1)'),                  # os() -> \cos()
            (r'an\(([^)]+)\)', r'\\tan(\1)'),                  # an() -> \tan()
            (r'og\(([^)]+)\)', r'\\log(\1)'),                  # og() -> \log()
            (r'lpha', r'\\alpha'),                             # lpha -> \alpha
            (r'eta', r'\\beta'),                               # eta -> \beta
            (r'heta', r'\\theta'),                             # heta -> \theta
            (r'i([^a-zA-Z])', r'\\pi\1'),                      # pi -> \pi (단독으로 나오는 경우)
            (r'eq([^a-zA-Z])', r'\\leq\1'),                    # leq -> \leq
            (r'eq([^a-zA-Z])', r'\\geq\1'),                    # geq -> \geq
            (r'eq([^a-zA-Z])', r'\\neq\1'),                    # neq -> \neq
        ]
        
        # 검사할 필드들
        text_fields = ['question', 'correct_answer', 'explanation']
        
        # 각 텍스트 필드에서 LaTeX 오류 수정
        for field in text_fields:
            if field in problem and isinstance(problem[field], str):
                original_text = problem[field]
                fixed_text = self._fix_latex_text(original_text, latex_fixes)
                if original_text != fixed_text:
                    print(f"LaTeX 수정 ({field}): {original_text} -> {fixed_text}")
                    problem[field] = fixed_text
        
        # choices 배열 처리
        if 'choices' in problem and isinstance(problem['choices'], list):
            for i, choice in enumerate(problem['choices']):
                if isinstance(choice, str):
                    original_choice = choice
                    fixed_choice = self._fix_latex_text(original_choice, latex_fixes)
                    if original_choice != fixed_choice:
                        print(f"LaTeX 수정 (choices[{i}]): {original_choice} -> {fixed_choice}")
                        problem['choices'][i] = fixed_choice
        
        return problem
    
    def _fix_latex_text(self, text: str, latex_fixes: List) -> str:
        """텍스트에서 LaTeX 오류 수정"""
        import re
        
        fixed_text = text
        for pattern, replacement in latex_fixes:
            fixed_text = re.sub(pattern, replacement, fixed_text)
        
        return fixed_text