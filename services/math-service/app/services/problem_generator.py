"""
수학 문제 생성 로직 분리 - JSON 파싱 완벽 개선
"""
import os
import json
import re
import google.generativeai as genai
from openai import OpenAI
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

        # OpenAI 클라이언트 초기화 (AI Judge용)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.openai_client = OpenAI(api_key=openai_api_key)

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
        difficulty_ratio: Dict = None,
        problem_type: str = None
    ) -> List[Dict]:
        """수학 문제 생성 메인 로직"""
        
        # 난이도 분배 계산
        difficulty_distribution = self._calculate_difficulty_distribution(
            problem_count, difficulty_ratio
        )

        # problem_type이 지정된 경우 강제 제약 추가
        enhanced_user_prompt = user_prompt
        if problem_type:
            if problem_type == "multiple_choice":
                type_constraint = f"""

**절대 준수 사항 - 위반 시 실패:**
- 정확히 {problem_count}개의 객관식 문제만 생성
- 모든 문제의 problem_type은 "multiple_choice"
- 각 문제는 정답이 1개만 존재 (A, B, C, D 중 하나)
- choices는 정확히 4개
- 단답형이나 서술형 문제는 절대 생성 금지
"""
            elif problem_type == "short_answer":
                type_constraint = f"""

**절대 준수 사항 - 위반 시 실패:**
- 정확히 {problem_count}개의 단답형 문제만 생성
- 모든 문제의 problem_type은 "short_answer"
- choices 필드는 null 또는 빈 배열
- 객관식이나 서술형 문제는 절대 생성 금지
"""
            else:
                type_constraint = ""

            enhanced_user_prompt = f"{user_prompt}{type_constraint}"

        # 프롬프트 빌드
        prompt = self.prompt_templates.build_problem_generation_prompt(
            curriculum_data=curriculum_data,
            user_prompt=enhanced_user_prompt,
            problem_count=problem_count,
            difficulty_distribution=difficulty_distribution
        )

        # 그래프 단원 확인 로그
        unit_name = curriculum_data.get('unit_name', '')
        if unit_name == "그래프와 비례":
            print(f"📊 그래프와 비례 단원 감지 - TikZ 생성 프롬프트 활성화")
            print(f"   챕터: {curriculum_data.get('chapter_name', '')}")

        # AI 호출 및 응답 처리 (target_count 전달)
        return self._call_ai_and_parse_response(prompt, target_count=problem_count)
    
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
    
    def _call_ai_and_parse_response(self, prompt: str, max_retries: int = 3, target_count: int = None) -> List[Dict]:
        """AI 호출 및 응답 파싱 - 부분 재생성 로직 포함"""

        if target_count is None:
            # 프롬프트에서 문제 개수 추출 시도 (기본값 1)
            target_count = 1

        valid_problems = []  # 합격한 문제 누적
        original_prompt = prompt  # 원본 프롬프트 백업

        for retry_attempt in range(max_retries):
            try:
                needed_count = target_count - len(valid_problems)

                if needed_count <= 0:
                    print(f"✅ 목표 달성: {len(valid_problems)}개 문제 생성 완료")
                    return valid_problems[:target_count]

                print(f"\n{'='*60}")
                print(f"문제 생성 시도 {retry_attempt + 1}/{max_retries}")
                print(f"현재 합격: {len(valid_problems)}개 / 목표: {target_count}개")
                print(f"추가 필요: {needed_count}개")
                print(f"{'='*60}\n")

                # 부족한 개수만큼만 생성하도록 프롬프트 조정
                if len(valid_problems) > 0:
                    # 이미 일부 합격한 경우 - 부족한 개수만 요청
                    adjusted_prompt = self._adjust_prompt_for_needed_count(original_prompt, needed_count)
                else:
                    adjusted_prompt = prompt

                response = self.model.generate_content(adjusted_prompt)
                content = response.text

                # JSON 추출 및 파싱
                problems = self._extract_and_parse_json(content)

                # 기본 구조 검증
                validated_problems = []
                for problem in problems:
                    validated_problem = self._validate_basic_structure(problem)
                    validated_problems.append(validated_problem)

                # AI Judge 검증
                print(f"🔍 AI Judge 검증 시작 - {len(validated_problems)}개 문제")

                invalid_problems = []

                current_batch_valid_count = 0
                for idx, problem in enumerate(validated_problems):
                    is_valid, scores, feedback = self._validate_with_ai_judge(problem)

                    # 상세 점수 출력
                    score_detail = f"[수학정확성:{scores.get('mathematical_accuracy', 0):.1f} " \
                                   f"정답일치:{scores.get('consistency', 0):.1f} " \
                                   f"완결성:{scores.get('completeness', 0):.1f} " \
                                   f"논리성:{scores.get('logic_flow', 0):.1f}]"

                    if is_valid:
                        current_batch_valid_count += 1
                        print(f"  ✅ 문제 {len(valid_problems) + current_batch_valid_count}번: VALID - 평균 {scores['overall_score']:.1f}점 {score_detail}")
                        valid_problems.append(problem)
                    else:
                        print(f"  ❌ 문제 {idx+1}번: INVALID - 평균 {scores['overall_score']:.1f}점 {score_detail}")
                        print(f"     💬 피드백: {feedback}")
                        invalid_problems.append({
                            "problem": problem,
                            "feedback": feedback,
                            "scores": scores
                        })

                # 목표 달성 확인
                if len(valid_problems) >= target_count:
                    print(f"\n✅ 목표 달성: {len(valid_problems)}개 문제 생성 완료!")
                    return valid_problems[:target_count]

                # 아직 부족한 경우
                if retry_attempt < max_retries - 1:
                    shortage = target_count - len(valid_problems)
                    print(f"\n⚠️ 부족: {shortage}개 추가 생성 필요 (현재 {len(valid_problems)}/{target_count})")

                    # 피드백을 포함한 프롬프트 재구성
                    if invalid_problems:
                        prompt = self._rebuild_prompt_with_feedback(original_prompt, invalid_problems)
                else:
                    # 마지막 시도에서도 부족한 경우
                    shortage = target_count - len(valid_problems)
                    raise Exception(f"검증 실패: {max_retries}회 시도 후 {shortage}개 부족 (현재 {len(valid_problems)}/{target_count})")

            except json.JSONDecodeError as e:
                if retry_attempt < max_retries - 1:
                    print(f"❌ JSON 파싱 실패, 재시도 중... ({str(e)})")
                    continue
                else:
                    raise
            except Exception as e:
                if retry_attempt < max_retries - 1 and "검증 실패" not in str(e):
                    print(f"❌ 오류 발생, 재시도 중... ({str(e)})")
                    continue
                else:
                    import traceback
                    error_msg = f"문제 생성 오류: {str(e)}\n{traceback.format_exc()}"
                    print(error_msg)
                    raise Exception(error_msg)

        raise Exception(f"문제 생성 실패: {max_retries}회 시도 모두 실패 (현재 {len(valid_problems)}/{target_count})")
    
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
    
    def _validate_basic_structure(self, problem: Dict) -> Dict:
        """기본 구조 검증만 수행 - LaTeX는 Gemini가 완벽하게 생성"""
        # 1. 필수 필드 확인 및 기본값 설정
        problem = self._ensure_required_fields(problem)

        # 2. 데이터 타입 검증만 수행
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
    
    
    def _validate_data_types(self, problem: Dict) -> Dict:
        """기본 데이터 타입 검증만 수행"""
        # difficulty는 대문자로
        if 'difficulty' in problem:
            difficulty = str(problem['difficulty']).upper()
            if difficulty not in ['A', 'B', 'C']:
                problem['difficulty'] = 'B'
            else:
                problem['difficulty'] = difficulty

        # problem_type 기본 검증
        valid_types = ['multiple_choice', 'short_answer', 'essay']
        if 'problem_type' in problem:
            if problem['problem_type'] not in valid_types:
                # 객관식 여부로 자동 판단
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

        return problem

    def _validate_with_ai_judge(self, problem: Dict) -> tuple:
        """
        AI Judge로 문제 검증 (OpenAI GPT-4o-mini) - 안전 필터 문제 해결

        Returns:
            (is_valid: bool, scores: dict, feedback: str)
        """
        try:
            # 원본 데이터 그대로 사용 (OpenAI는 LaTeX 처리 가능)
            question = problem.get('question', '')
            correct_answer = problem.get('correct_answer', '')
            explanation = problem.get('explanation', '')
            problem_type = problem.get('problem_type', '')
            choices = problem.get('choices', [])
            choices_text = ', '.join(map(str, choices)) if choices else 'None'

            # tikz_code와 diagram 관련 필드는 검증에서 제외 (선택적 필드)
            has_diagram = problem.get('has_diagram', False)
            diagram_note = " (Note: This problem may include graph/diagram fields which are optional and should not affect validation.)" if has_diagram else ""

            validation_prompt = f"""You are a math education expert. Please validate the following math problem.

The problem data is as follows:
- Question: {question}
- Correct Answer: {correct_answer}
- Explanation: {explanation}
- Problem Type: {problem_type}
- Choices: {choices_text}{diagram_note}

Evaluation criteria:
1. mathematical_accuracy (1-5): No mathematical or logical errors.
2. consistency (1-5): The final answer in the explanation matches the correct_answer.
3. completeness (1-5): All required fields are present (e.g., multiple_choice must have 4 choices). IGNORE optional fields like tikz_code, diagram_type, has_diagram.
4. logic_flow (1-5): The explanation is logical and easy to follow.

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "scores": {{"mathematical_accuracy": <score>, "consistency": <score>, "completeness": <score>, "logic_flow": <score>}},
  "overall_score": <average>,
  "decision": "VALID" or "INVALID",
  "feedback": "<brief feedback>"
}}

Decision rule: `consistency` must be 4 or higher, AND the average of the other scores must be 3.5 or higher to be "VALID".
"""

            # OpenAI API 호출
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a math education expert who validates math problems and returns structured JSON responses."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}  # JSON 모드 강제
            )

            result_text = response.choices[0].message.content.strip()

            # JSON 파싱
            result = json.loads(result_text)

            is_valid = result.get('decision') == 'VALID'
            scores = result.get('scores', {})
            scores['overall_score'] = result.get('overall_score', 0)
            feedback = result.get('feedback', 'No feedback')

            return is_valid, scores, feedback

        except json.JSONDecodeError as e:
            # JSON 파싱 오류는 재발생시켜 재시도 유도
            print(f"❌ AI Judge 응답 JSON 파싱 실패: {str(e)}")
            print(f"   응답 내용: {result_text[:200]}...")
            raise Exception(f"AI Judge validation failed - invalid JSON response: {str(e)}")

        except Exception as e:
            # 그 외 오류는 재발생시켜 재시도
            print(f"❌ AI Judge 검증 오류: {str(e)}")
            raise Exception(f"AI Judge validation error: {str(e)}")

    def _adjust_prompt_for_needed_count(self, original_prompt: str, needed_count: int) -> str:
        """부족한 개수만큼만 생성하도록 프롬프트 조정"""
        import re

        # 문제 개수 패턴 찾기 및 교체
        patterns = [
            (r'(\d+)개의?\s*문제', f'{needed_count}개 문제'),
            (r'(\d+)\s*problems?', f'{needed_count} problems'),
            (r'정확히\s*(\d+)개', f'정확히 {needed_count}개'),
            (r'Total Problems to Generate\*\*:\s*(\d+)', f'Total Problems to Generate**: {needed_count}'),
            (r'create\s+(\d+)\s+perfectly', f'create {needed_count} perfectly'),
            (r'Ensure the total count is\s+(\d+)', f'Ensure the total count is {needed_count}')
        ]

        adjusted = original_prompt
        for pattern, replacement in patterns:
            adjusted = re.sub(pattern, replacement, adjusted, flags=re.IGNORECASE)

        print(f"📝 프롬프트 조정: {needed_count}개 생성하도록 수정")
        return adjusted

    def _rebuild_prompt_with_feedback(self, original_prompt: str, invalid_problems: List[Dict]) -> str:
        """피드백을 포함한 프롬프트 재구성"""

        feedback_text = "\n\n**IMPORTANT: Previous attempt had issues. Fix these:**\n"
        for idx, item in enumerate(invalid_problems):
            feedback_text += f"\nProblem {idx+1} feedback:\n"
            feedback_text += f"- Scores: mathematical_accuracy={item['scores'].get('mathematical_accuracy')}, "
            feedback_text += f"consistency={item['scores'].get('consistency')}, "
            feedback_text += f"completeness={item['scores'].get('completeness')}, "
            feedback_text += f"logic_flow={item['scores'].get('logic_flow')}\n"
            feedback_text += f"- Issue: {item['feedback']}\n"

        feedback_text += "\n**MUST ensure**: consistency >= 4 (explanation's answer = correct_answer), all scores >= 3.5\n"

        return original_prompt + feedback_text