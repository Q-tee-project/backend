import json
import re
from typing import Dict, Any
from app.core.config import get_settings

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class AIService:
    def __init__(self):
        self.settings = get_settings()
        
        if not GEMINI_AVAILABLE:
            print("Warning: Google Generative AI library not found. AI grading will be disabled.")
            return
        
        if not self.settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel(self.settings.gemini_flash_model)

    async def grade_subjective_question(self, question_text: str, correct_answer: str, student_answer: str, passage_content: str = None, example_content: str = None) -> Dict[str, Any]:
        """
        AI를 사용하여 주관식/서술형 문제를 채점합니다.
        """
        if not GEMINI_AVAILABLE:
            return {"score": 0, "is_correct": False, "feedback": "AI 서비스가 비활성화되었습니다."}

        prompt_parts = [
            "🎯 역할: 한국의 영어 문제 채점 전문가",
            "📝 임무: 학생 답안을 정확히 채점하고 데이터베이스에 저장할 JSON 형식으로 응답",
            "",
            "⚠️ 절대 규칙 (위반시 시스템 오류 발생):",
            "1. 반드시 마크다운 JSON 블록으로만 응답 (```json ~ ```)",
            "2. score는 정수 0 또는 1만 허용 (0.5, [0], \"0\" 등 금지)",
            "3. is_correct는 boolean true 또는 false만 허용 ([true], \"true\" 등 금지)",
            "4. feedback은 한국어 문자열만 허용 (배열, 객체 금지)",
            "5. JSON 외의 설명, 주석, 부가 텍스트 절대 금지",
            "",
            "📊 데이터베이스 테이블 스키마:",
            "- score: INTEGER (0=틀림, 1=맞음)",
            "- is_correct: BOOLEAN (true/false)",
            "- ai_feedback: TEXT (한국어 피드백, 길이 무제한)",
            "",
            "🎯 채점 기준:",
            "• 0점: 완전히 틀림 (의미 불일치, 전혀 다른 답안)",
            "• 1점: 정답 (의미 일치, 사소한 오타 허용)",
            "",
            "📝 피드백 작성 규칙:",
            "• 반드시 한국어로 작성",
            "• 정답/오답 이유를 명확히 설명",
            "• 학습 포인트 포함 (문법, 어휘, 구문 등)",
            "• 격려와 개선점 제시",
            "",
            "✅ 올바른 응답 예시 1 (정답):",
            "```json",
            "{",
            "  \"score\": 1,",
            "  \"is_correct\": true,",
            "  \"feedback\": \"정답입니다! 'attended'는 'attend'의 과거형으로, 'last Friday'라는 과거 시점 표현과 일치합니다. 과거 시간 표현이 나올 때 동사를 과거형으로 변화시키는 규칙을 잘 적용했습니다.\"",
            "}",
            "```",
            "",
            "❌ 올바른 응답 예시 2 (오답):",
            "```json",
            "{",
            "  \"score\": 0,",
            "  \"is_correct\": false,",
            "  \"feedback\": \"아쉽게도 틀렸습니다. 학생이 'attends'라고 답했지만, 문장에 'last Friday'가 있어서 동사는 과거형 'attended'를 사용해야 합니다. 현재형(-s)과 과거형의 차이를 다시 학습해보세요.\"",
            "}",
            "```",
            "",
            "🚫 절대 금지 사항:",
            "- 배열 형태: {\"score\": [1], \"is_correct\": [true]}",
            "- 문자열 형태: {\"score\": \"1\", \"is_correct\": \"true\"}",
            "- 마크다운 블록 없는 응답",
            "- JSON 외의 설명이나 주석",
            "",
            "=== 📋 채점 대상 ===",
            f"문제: {question_text}",
            f"정답: {correct_answer}",
            f"학생 답안: {student_answer}",
        ]
        
        if passage_content:
            prompt_parts.insert(len(prompt_parts) - 3, f"**지문:** {passage_content}") # 문제 앞에 삽입
        if example_content:
            prompt_parts.insert(len(prompt_parts) - 3, f"**예문:** {example_content}") # 문제 앞에 삽입

        prompt = "\n".join(prompt_parts)

        try:
            response = await self.model.generate_content_async(prompt)
            response_text = response.text
            
            # 🔍 Gemini 원본 응답 로깅 (임시)
            print("="*80)
            print("🤖 Gemini 2.5-flash 원본 응답:")
            print("="*80)
            print(response_text)
            print("="*80)
            
            # 마크다운 코드 블록에서 JSON 추출
            json_match = re.search(r"```json\n({.*?})\n```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                ai_result = json.loads(json_str)
                
                # 🔍 파싱된 JSON 응답 로깅
                print("📋 파싱된 JSON 결과:")
                for key, value in ai_result.items():
                    print(f"   {key}: {value} (타입: {type(value)})")
                print("="*80)
                
                # 엄격한 타입 검증 및 보정
                ai_result = self._validate_and_fix_ai_response(ai_result)
            else:
                # 💡 마크다운 블록이 없는 경우, 더 강화된 정규식으로 JSON 추출 시도
                print("⚠️ 마크다운 JSON 블록이 없습니다. 정규식으로 파싱 시도...")
                
                # JSON 객체 전체를 찾아서 파싱 시도
                json_object_match = re.search(r'\{[^{}]*"score"[^{}]*\}', response_text, re.DOTALL)
                if json_object_match:
                    try:
                        json_str = json_object_match.group(0)
                        ai_result = json.loads(json_str)
                        print(f"✅ JSON 객체 파싱 성공: {json_str}")
                        # 타입 검증 및 보정 적용
                        ai_result = self._validate_and_fix_ai_response(ai_result)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 객체 파싱 실패: {e}")
                        # 개별 필드 추출로 폴백
                        ai_result = self._extract_fields_by_regex(response_text)
                else:
                    # 개별 필드 정규식 추출
                    ai_result = self._extract_fields_by_regex(response_text)
            
            return ai_result

        except Exception as e:
            print(f"AI 채점 중 오류 발생: {e}")
            return {"score": 0, "is_correct": False, "feedback": f"AI 채점 중 오류 발생: {e}"}

    def _validate_and_fix_ai_response(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI 응답의 타입을 검증하고 수정합니다.
        특히 is_correct가 리스트나 잘못된 타입으로 올 때 Boolean으로 강제 변환합니다.
        """
        # 기본값 설정
        validated_result = {
            "score": 0,
            "is_correct": False,
            "feedback": "AI 응답 형식 오류"
        }
        
        # score 검증 및 변환
        try:
            score = ai_result.get("score", 0)
            if isinstance(score, list):
                # 리스트인 경우 첫 번째 값 사용
                score = score[0] if score else 0
            validated_result["score"] = max(0, min(int(score), 1))  # 0 또는 1로 제한
        except (ValueError, TypeError):
            validated_result["score"] = 0
        
        # is_correct 검증 및 변환 (가장 중요!)
        try:
            is_correct = ai_result.get("is_correct", False)
            if isinstance(is_correct, list):
                # 리스트인 경우 첫 번째 값으로 변환
                is_correct = is_correct[0] if is_correct else False
                print(f"⚠️ AI가 is_correct를 리스트로 반환함: {ai_result.get('is_correct')} -> {is_correct}로 변환")
            elif isinstance(is_correct, str):
                # 문자열인 경우 boolean으로 변환
                is_correct = is_correct.lower() in ['true', '1', 'yes']
            elif not isinstance(is_correct, bool):
                # 다른 타입인 경우 False로 처리
                print(f"⚠️ is_correct가 예상치 못한 타입임: {type(is_correct)} - False로 처리")
                is_correct = False
            
            validated_result["is_correct"] = bool(is_correct)
        except Exception as e:
            print(f"⚠️ is_correct 변환 중 오류: {e} - False로 처리")
            validated_result["is_correct"] = False
        
        # feedback 검증 및 텍스트 정제
        try:
            feedback = ai_result.get("feedback", "")
            if isinstance(feedback, list):
                feedback = str(feedback[0]) if feedback else ""
            elif not isinstance(feedback, str):
                feedback = str(feedback)
            
            # 🧹 텍스트 정제 (공백/줄바꿈 제거)
            if feedback:
                # 1. 앞뒤 공백 제거
                feedback = feedback.strip()
                # 2. 연속된 공백을 하나로 변환
                feedback = re.sub(r'\s+', ' ', feedback)
                # 3. 불필요한 줄바꿈 제거 후 문장 사이 공백 정리
                feedback = re.sub(r'\n\s*\n', ' ', feedback)
                feedback = re.sub(r'\n+', ' ', feedback)
                # 4. 최종 공백 정리
                feedback = feedback.strip()
            
            validated_result["feedback"] = feedback or "채점이 완료되었습니다."
        except Exception:
            validated_result["feedback"] = "채점이 완료되었습니다."
        
        # 타입 변환이 이루어진 경우 로그 출력
        original_is_correct = ai_result.get("is_correct")
        if original_is_correct != validated_result["is_correct"]:
            print(f"🔧 AI 응답 수정됨 - is_correct: {original_is_correct} ({type(original_is_correct)}) -> {validated_result['is_correct']} (bool)")
        
        return validated_result

    def _extract_fields_by_regex(self, response_text: str) -> Dict[str, Any]:
        """
        정규식을 사용해 응답 텍스트에서 개별 필드를 추출합니다.
        마크다운 블록이나 완전한 JSON이 없을 때의 폴백 메서드입니다.
        """
        print("🔍 정규식으로 개별 필드 추출 시도...")
        
        # score 추출 (더 엄격한 패턴)
        score_patterns = [
            r'"score":\s*(\d+)',           # "score": 1
            r"'score':\s*(\d+)",           # 'score': 1
            r'점수[:：]\s*(\d+)',          # 점수: 1
            r'score[:\s=]+(\d+)'           # score 1, score: 1, score = 1
        ]
        score = 0
        for pattern in score_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                score = max(0, min(int(match.group(1)), 1))  # 0-1 범위로 제한
                print(f"✅ score 추출됨: {score} (패턴: {pattern})")
                break
        
        # is_correct 추출 (더 엄격한 패턴)
        is_correct_patterns = [
            r'"is_correct":\s*(true|false)',     # "is_correct": true
            r"'is_correct':\s*(true|false)",     # 'is_correct': true
            r'정답[:\s=]*(맞음|틀림|참|거짓)',      # 정답: 맞음
            r'is_correct[:\s=]*(true|false)'     # is_correct true
        ]
        is_correct = False
        for pattern in is_correct_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                value = match.group(1).lower()
                is_correct = value in ['true', '맞음', '참']
                print(f"✅ is_correct 추출됨: {is_correct} (값: {value})")
                break
        
        # feedback 추출 (더 유연한 패턴)
        feedback_patterns = [
            r'"feedback":\s*"([^"]*)"',          # "feedback": "내용"
            r"'feedback':\s*'([^']*)'",          # 'feedback': '내용'  
            r'"feedback":\s*"([^"\\]*(?:\\.[^"\\]*)*)"',  # 이스케이프 문자 포함
            r'피드백[:：]\s*"?([^"\n]+)"?',       # 피드백: 내용
            r'feedback[:\s=]+"?([^"\n]+)"?'      # feedback: 내용
        ]
        feedback = "AI 응답을 정확히 파싱할 수 없습니다."
        for pattern in feedback_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                feedback = match.group(1).strip()
                # 🧹 텍스트 정제 (공백/줄바꿈 제거)
                if feedback:
                    feedback = re.sub(r'\s+', ' ', feedback)  # 연속 공백을 하나로
                    feedback = re.sub(r'\n\s*\n', ' ', feedback)  # 빈 줄 제거
                    feedback = re.sub(r'\n+', ' ', feedback)  # 줄바꿈을 공백으로
                    feedback = feedback.strip()  # 최종 공백 제거
                    print(f"✅ feedback 추출됨: {feedback[:50]}...")
                    break
        
        result = {
            "score": score,
            "is_correct": is_correct,
            "feedback": feedback
        }
        
        print(f"📋 정규식 추출 결과: score={score}, is_correct={is_correct}, feedback_length={len(feedback)}")
        return result

