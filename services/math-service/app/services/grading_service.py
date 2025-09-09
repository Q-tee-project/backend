"""
채점 서비스 로직 분리
"""
import os
import json
import google.generativeai as genai
from typing import Dict
from .prompt_templates import PromptTemplates
from dotenv import load_dotenv

load_dotenv()

class GradingService:
    """수학 문제 채점 전용 클래스"""
    
    def __init__(self):
        # AI 모델 직접 초기화 (순환 import 방지)
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.prompt_templates = PromptTemplates()
    
    def grade_essay_problem(
        self, 
        question: str, 
        correct_answer: str, 
        student_answer: str, 
        explanation: str
    ) -> Dict:
        """서술형 문제 채점"""
        
        prompt = self.prompt_templates.build_grading_prompt_essay(
            question=question,
            correct_answer=correct_answer,
            explanation=explanation,
            student_answer=student_answer
        )
        
        return self._call_ai_grading(prompt)
    
    def grade_objective_problem(
        self, 
        question: str, 
        correct_answer: str, 
        student_answer: str, 
        explanation: str
    ) -> Dict:
        """객관식/단답형 문제 채점"""
        
        prompt = self.prompt_templates.build_grading_prompt_objective(
            question=question,
            correct_answer=correct_answer,
            explanation=explanation,
            student_answer=student_answer
        )
        
        return self._call_ai_grading(prompt)
    
    def _call_ai_grading(self, prompt: str) -> Dict:
        """AI 채점 호출"""
        try:
            response = self.model.generate_content(prompt)
            content = response.text
            
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content
            
            return json.loads(json_str)
            
        except Exception as e:
            print(f"AI 채점 오류: {str(e)}")
            return {
                "score": 0,
                "is_correct": False,
                "feedback": "채점 중 오류가 발생했습니다.",
                "strengths": "",
                "improvements": ""
            }
    
    def normalize_answer_for_comparison(self, answer: str) -> str:
        """답안을 비교용으로 정규화"""
        import re
        from fractions import Fraction
        
        answer = answer.strip().lower()
        
        # 분수 표현을 찾아서 기약분수로 변환
        fraction_patterns = [
            r'(\d+)/(\d+)',  # 2/7
            r'(\d+)분의(\d+)',  # 7분의2
            r'(\d+) *분의 *(\d+)',  # 7 분의 2
        ]
        
        def normalize_fraction(match):
            if '분의' in match.group(0):
                # '분의' 패턴: 분모가 먼저 온다
                denominator = int(match.group(1))
                numerator = int(match.group(2))
            else:
                # 일반 분수: 분자가 먼저 온다
                numerator = int(match.group(1))
                denominator = int(match.group(2))
            
            try:
                frac = Fraction(numerator, denominator)
                return f"{frac.numerator}/{frac.denominator}"
            except:
                return match.group(0)
        
        for pattern in fraction_patterns:
            answer = re.sub(pattern, normalize_fraction, answer)
        
        return answer
    
    def normalize_fraction_text(self, text: str) -> str:
        """OCR 텍스트에서 세로 분수 패턴을 찾아서 표준 형태로 변환"""
        import re
        
        # 여러 줄로 나뉜 분수 패턴 찾기
        lines = text.split('\n')
        normalized_lines = []
        
        i = 0
        while i < len(lines):
            current_line = lines[i].strip()
            
            # 분수 패턴 찾기: 숫자 → 선(-, ―, —) → 숫자
            if (i + 2 < len(lines) and 
                re.match(r'^\s*\d+\s*$', current_line) and  # 첫 줄: 숫자만
                re.match(r'^\s*[-―—_]+\s*$', lines[i + 1].strip()) and  # 둘째 줄: 선
                re.match(r'^\s*\d+\s*$', lines[i + 2].strip())):  # 셋째 줄: 숫자만
                
                numerator = current_line
                denominator = lines[i + 2].strip()
                
                # 표준 분수 형태로 변환
                fraction_text = f"{numerator}/{denominator}"
                
                print(f"🔍 세로 분수 발견: {numerator} over {denominator} → {fraction_text}")
                normalized_lines.append(fraction_text)
                i += 3  # 3줄을 처리했으므로 건너뛰기
                continue
            
            # 분수가 아닌 경우 그대로 추가
            normalized_lines.append(current_line)
            i += 1
        
        # 공백으로 분리된 숫자들을 분수로 변환하기
        result_text = ' '.join(normalized_lines)
        
        # 연속된 두 숫자 사이에 공백이 있는 경우 분수로 해석
        def replace_space_fractions(match):
            num1, num2 = match.groups()
            # 두 숫자 모두 20 이하인 경우만 분수로 변환
            if int(num1) <= 20 and int(num2) <= 20:
                return f"{num1}/{num2}"
            return match.group(0)  # 원래 텍스트 그대로
        
        result_text = re.sub(r'(\d+)\s+(\d+)(?!\d)', replace_space_fractions, result_text)
        
        return result_text