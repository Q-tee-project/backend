import json
import re
from typing import Dict, Any
from .gemini_client import GeminiClient


class AIService:
    """AI 기반 채점 서비스"""

    def __init__(self):
        self.gemini_client = GeminiClient()

    async def grade_subjective_question(self, question_text: str, correct_answer: str, student_answer: str, passage_content: str = None, example_content: str = None, explanation: str = None, learning_point: str = None) -> Dict[str, Any]:
        """
        AI를 사용하여 단답형/서술형 문제를 채점합니다.
        """
        if not self.gemini_client.is_available():
            return {"score": 0, "is_correct": False, "feedback": "AI 서비스가 비활성화되었습니다."}

        prompt_parts = [
            " 역할: 한국의 영어 문제 채점 전문가",
            "📝 임무: 학생 답안을 정확히 채점하고 데이터베이스에 저장할 JSON 형식으로 응답",
            "",
            " 절대 규칙 (위반시 시스템 오류 발생):",
            "1. 반드시 마크다운 JSON 블록으로만 응답 (```json ~ ```)",
            "2. score는 정수 0 또는 1만 허용 (0.5, [0], \"0\" 등 금지)",
            "3. is_correct는 boolean true 또는 false만 허용 ([true], \"true\" 등 금지)",
            "4. ai_feedback은 한국 중학생이 이해할 수 있는 한국어 문자열만 허용 (배열, 객체 금지)",
            "5. JSON 외의 설명, 주석, 부가 텍스트 절대 금지",
            "",
            " 데이터베이스 테이블 스키마:",
            "- score: INTEGER (0=틀림, 1=맞음)",
            "- is_correct: BOOLEAN (true/false)",
            "- ai_feedback: TEXT (한국어 피드백, 길이 무제한)",
            "",
            " 채점 기준:",
            "• 0점: 완전히 틀림 (의미 불일치, 전혀 다른 답안)",
            "• 1점: 정답 (의미 일치, 문법적 허용 오차 포함하지 마세요)",
            "",
            " 채점 상세 가이드:",
            "1. **의미 우선**: 철자/문법 실수가 없이 의미가 맞으면 1점",
            "2. **유연한 표현**: 정답과 다른 표현이어도 의미가 같으면 1점",
            "3. **부분 정답 불가**: 0점 또는 1점만 허용",
            "4. **빈 답안**: 공백, 무의미한 입력은 0점",
            "",
            " 필수 JSON 응답 형식 (반드시 준수):",
            "```json",
            "{",
            '  "score": 0,',
            '  "is_correct": false,',
            '  "ai_feedback": "피드백 내용"',
            "}",
            "```",
        ]

        # 지문이 있는 경우 추가
        if passage_content:
            prompt_parts.extend([
                "",
                " 관련 지문:",
                str(passage_content)
            ])

        # 예문이 있는 경우 추가
        if example_content:
            prompt_parts.extend([
                "",
                "📝 관련 예문:",
                str(example_content)
            ])

        # 해설이 있는 경우 추가
        if explanation:
            prompt_parts.extend([
                "",
                "💡 문제 해설:",
                str(explanation)
            ])

        # 학습 포인트가 있는 경우 추가
        if learning_point:
            prompt_parts.extend([
                "",
                "🎯 학습 포인트:",
                str(learning_point)
            ])

        prompt_parts.extend([
            "",
            "🔸 채점 대상:",
            f"문제: {question_text}",
            f"정답: {correct_answer}",
            f"학생 답안: {student_answer}",
            "",
            "📝 위 학생 답안을 채점하고 JSON으로 응답해주세요:"
        ])

        prompt = "\n".join(prompt_parts)

        # 프롬프트 로그 출력
        print("="*80)
        print("🤖 AI 채점 프롬프트:")
        print("="*80)
        print(prompt)
        print("="*80)

        try:
            response = await self.gemini_client.generate_content(prompt)
            if not response:
                return {"score": 0, "is_correct": False, "feedback": "AI 응답을 받지 못했습니다."}

            # AI 응답 로그 출력
            print("🤖 AI 원본 응답:")
            print("-"*40)
            print(response)
            print("-"*40)

            result = self._parse_ai_response(response)

            # 파싱된 결과 로그 출력
            print("🔍 파싱된 결과:")
            print("-"*40)
            print(result)
            print("-"*40)

            validated_result = self._validate_and_fix_ai_response(result)

            # 최종 검증된 결과 로그 출력
            print("✅ 최종 채점 결과:")
            print("-"*40)
            print(validated_result)
            print("="*80)

            return validated_result

        except Exception as e:
            print(f"AI 채점 중 오류 발생: {e}")
            return {"score": 0, "is_correct": False, "feedback": f"채점 중 오류가 발생했습니다: {str(e)}"}

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """AI 응답에서 JSON을 추출합니다."""
        # JSON 블록 패턴 매칭
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response, re.DOTALL)

        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 실패: {e}")
                print(f"응답 내용: {response}")

        # JSON 블록이 없는 경우 전체 응답에서 JSON 찾기
        try:
            # 응답 전체가 JSON인 경우
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # 정규식으로 필드별 추출 시도
        return self._extract_fields_by_regex(response)

    def _extract_fields_by_regex(self, response: str) -> Dict[str, Any]:
        """정규식을 사용해 AI 응답에서 필드를 추출합니다."""
        result = {"score": 0, "is_correct": False, "feedback": "응답 파싱에 실패했습니다."}

        # score 추출
        score_match = re.search(r'"?score"?\s*:\s*([01])', response)
        if score_match:
            result["score"] = int(score_match.group(1))
            result["is_correct"] = result["score"] == 1

        # feedback 추출
        feedback_match = re.search(r'"?feedback"?\s*:\s*"([^"]*)"', response)
        if feedback_match:
            result["feedback"] = feedback_match.group(1)
        else:
            # 다중 라인 feedback 처리
            feedback_match = re.search(r'"?feedback"?\s*:\s*"([^"]*(?:\n[^"]*)*)"', response, re.MULTILINE)
            if feedback_match:
                result["feedback"] = feedback_match.group(1)

        return result

    def _validate_and_fix_ai_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """AI 응답을 검증하고 필요시 수정합니다."""
        # score 검증 및 수정
        if "score" not in result or not isinstance(result["score"], int) or result["score"] not in [0, 1]:
            result["score"] = 0

        # is_correct 검증 및 수정
        if "is_correct" not in result or not isinstance(result["is_correct"], bool):
            result["is_correct"] = result["score"] == 1

        # feedback 검증 및 수정
        if "feedback" not in result or not isinstance(result["feedback"], str):
            result["feedback"] = "채점이 완료되었습니다."

        # score와 is_correct 일관성 확인
        if result["score"] == 1 and not result["is_correct"]:
            result["is_correct"] = True
        elif result["score"] == 0 and result["is_correct"]:
            result["is_correct"] = False

        return result