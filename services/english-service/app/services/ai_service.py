import os
import json
import re
from typing import Dict, Any

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class AIService:
    def __init__(self):
        if not GEMINI_AVAILABLE:
            print("Warning: Google Generative AI library not found. AI grading will be disabled.")
            return
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def grade_subjective_question(self, question_text: str, correct_answer: str, student_answer: str, passage_content: str = None, example_content: str = None) -> Dict[str, Any]:
        """
        AI를 사용하여 주관식/서술형 문제를 채점합니다.
        """
        if not GEMINI_AVAILABLE:
            return {"score": 0, "is_correct": False, "feedback": "AI 서비스가 비활성화되었습니다."}

        prompt_parts = [
            "당신은 한국의 영어 문제 채점 전문가입니다. 학생의 답안을 채점하고 한국어로 피드백을 제공해주세요.",
            "다음은 문제, 정답, 학생 답안입니다. 지문이나 예문이 있다면 함께 제공됩니다.",
            "",
            "중요: 모든 피드백은 반드시 한국어로 작성해주세요!",
            "",
            "채점 기준:",
            "1. 정답과 의미가 일치하면 만점 (부분 점수 가능)",
            "2. 문법적 오류나 오타는 감점 요인이 될 수 있으나, 핵심 의미가 맞으면 부분 점수 이상 부여",
            "3. 주관식/서술형 문제의 특성상 다양한 정답이 있을 수 있음을 고려하여 유연하게 채점",
            "4. 학생의 창의성과 논리적 사고를 인정하여 관대하게 채점",
            "",
            "응답 형식:",
            "- 반드시 다음 JSON 형식으로만 응답하세요",
            "- 피드백은 반드시 한국어로 작성하세요",
            "- 다른 설명이나 부가 내용은 포함하지 마세요",
            "",
            "```json",
            "{",
            "  \"score\": [점수 (0 또는 1)],",
            "  \"is_correct\": [정답 여부 (true/false)],",
            "  \"feedback\": \"[한국어로 작성된 채점 근거 및 상세 피드백]\"",
            "}",
            "```",
            "",
            "=== 채점 대상 ===",
            f"**문제:** {question_text}",
            f"**정답:** {correct_answer}",
            f"**학생 답안:** {student_answer}",
        ]
        
        if passage_content:
            prompt_parts.insert(len(prompt_parts) - 3, f"**지문:** {passage_content}") # 문제 앞에 삽입
        if example_content:
            prompt_parts.insert(len(prompt_parts) - 3, f"**예문:** {example_content}") # 문제 앞에 삽입

        prompt = "\n".join(prompt_parts)

        try:
            response = await self.model.generate_content_async(prompt)
            response_text = response.text
            
            # 마크다운 코드 블록에서 JSON 추출
            json_match = re.search(r"```json\n({.*?})\n```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                ai_result = json.loads(json_str)
            else:
                # JSON 파싱 실패 시, 텍스트에서 점수와 피드백 추출 시도
                score_match = re.search(r"\"score\":\s*(\d+)", response_text)
                is_correct_match = re.search(r"\"is_correct\":\s*(true|false)", response_text, re.IGNORECASE)
                feedback_match = re.search(r"\"feedback\":\s*\"(.*?)\"", response_text, re.DOTALL)

                ai_result = {
                    "score": int(score_match.group(1)) if score_match else 0,
                    "is_correct": is_correct_match.group(1).lower() == 'true' if is_correct_match else False,
                    "feedback": feedback_match.group(1) if feedback_match else "AI 응답을 파싱할 수 없습니다."
                }
            
            return ai_result

        except Exception as e:
            print(f"AI 채점 중 오류 발생: {e}")
            return {"score": 0, "is_correct": False, "feedback": f"AI 채점 중 오류 발생: {e}"}

