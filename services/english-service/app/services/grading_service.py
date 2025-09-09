"""
영어 문제 자동 채점 서비스

채점 방식:
1. 객관식: DB 정답과 직접 비교
2. 단답형/서술형: AI 채점 (주관성 허용)
3. 최종 검수: 사람의 수동 검토
"""

import json
import re
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ..models.models import Worksheet, Question, AnswerQuestion, AnswerPassage, AnswerExample, GradingResult, QuestionResult, Passage, Example
from .ai_service import AIService


class GradingService:
    def __init__(self):
        self.ai_service = AIService()
    
    async def perform_grading(self, worksheet: Worksheet, student_answers: Dict[str, str], db: Session, student_name: str = "익명", completion_time: int = 0) -> Dict[str, Any]:
        """
        전체 채점 수행
        
        Args:
            worksheet: 문제지 객체
            student_answers: 학생 답안 {"question_id": "answer", ...}
            db: 데이터베이스 세션
        
        Returns:
            채점 결과 딕셔너리
        """
        question_results = []
        total_score = 0
        max_score = 0
        needs_review = False
        
        # 정규화된 답안 데이터 조회
        answer_questions = db.query(AnswerQuestion).filter(
            AnswerQuestion.worksheet_id == worksheet.id
        ).all()
        
        answer_passages = db.query(AnswerPassage).filter(
            AnswerPassage.worksheet_id == worksheet.id
        ).all()
        
        answer_examples = db.query(AnswerExample).filter(
            AnswerExample.worksheet_id == worksheet.id
        ).all()
        
        if not answer_questions:
            print(f"DEBUG: 답안 데이터를 찾을 수 없습니다. worksheet.id={worksheet.id}")
            raise ValueError("답안 데이터를 찾을 수 없습니다.")
        
        print(f"DEBUG: 답안 데이터 조회 성공. questions: {len(answer_questions)}, passages: {len(answer_passages)}, examples: {len(answer_examples)}")
        
        # 각 문제별 채점
        for question in worksheet.questions:
            question_id = question.question_id
            student_answer = student_answers.get(question_id, "").strip()
            
            # 문제별 채점 수행
            result = await self._grade_single_question(
                question, student_answer, answer_questions, answer_passages, answer_examples, worksheet, db
            )
            
            question_results.append(result)
            total_score += result["score"]
            max_score += result["max_score"]
            
            # AI 채점이 필요한 경우 검수 필요 표시
            if result["grading_method"] == "ai" or result["needs_review"]:
                needs_review = True
        
        # 백분율 계산
        percentage = round((total_score / max_score * 100) if max_score > 0 else 0, 1)
        
        # 데이터베이스에 채점 결과 저장
        grading_result = await self._save_grading_result(
            worksheet, student_name, completion_time, 
            total_score, max_score, percentage, needs_review,
            question_results, db
        )
        
        return {
            "grading_result_id": grading_result.id,
            "result_id": grading_result.result_id,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "question_results": question_results,
            "needs_review": needs_review
        }
    
    async def _grade_single_question(
        self, 
        question: Question, 
        student_answer: str, 
        answer_questions: List[AnswerQuestion],
        answer_passages: List[AnswerPassage],
        answer_examples: List[AnswerExample],
        worksheet: Worksheet, 
        db: Session
    ) -> Dict[str, Any]:
        """
        단일 문제 채점
        
        Returns:
            {
                "question_id": str,
                "question_type": str,
                "student_answer": str,
                "correct_answer": str,
                "score": int,
                "max_score": int,
                "is_correct": bool,
                "grading_method": str,  # "db" | "ai"
                "ai_feedback": str,     # AI 채점 피드백 (해당되는 경우)
                "needs_review": bool    # 검수 필요 여부
            }
        """
        question_id = question.question_id
        question_type = question.question_type
        
        # question_id가 리스트인 경우 첫 번째 값 사용
        if isinstance(question_id, list):
            question_id = question_id[0] if question_id else "1"
        
        # question_type이 리스트인 경우 첫 번째 값 사용
        if isinstance(question_type, list):
            question_type = question_type[0] if question_type else "객관식"
        
        max_score = 1  # 기본 배점
        
        # 정답 정보 찾기
        correct_answer_info = self._find_correct_answer(question_id, answer_questions)
        
        if question_type == "객관식":
            return await self._grade_multiple_choice(
                question, student_answer, correct_answer_info, max_score
            )
        elif question_type in ["단답형", "주관식", "서술형"]:
            return await self._grade_subjective(
                question, student_answer, correct_answer_info, answer_passages, answer_examples, max_score
            )
        else:
            # 알 수 없는 문제 유형
            return {
                "question_id": question_id,
                "question_type": question_type,  # 이미 위에서 안전 처리됨
                "student_answer": student_answer,
                "correct_answer": "정답 정보 없음",
                "score": 0,
                "max_score": max_score,
                "is_correct": False,
                "grading_method": "unknown",
                "ai_feedback": "알 수 없는 문제 유형입니다.",
                "needs_review": True
            }
    
    def _find_correct_answer(self, question_id: str, answer_questions: List[AnswerQuestion]) -> Dict[str, Any]:
        """정규화된 답안 테이블에서 특정 문제의 정답 정보를 찾습니다."""
        print(f"DEBUG: 정답 찾기 - question_id={question_id} (타입: {type(question_id)})")
        
        # 답안 테이블에서 해당 문제 ID로 검색
        for answer_question in answer_questions:
            if str(answer_question.question_id) == str(question_id):
                result = {
                    "correct_answer": answer_question.correct_answer,
                    "explanation": answer_question.explanation,
                    "learning_point": answer_question.learning_point
                }
                print(f"DEBUG: 정답 찾음: {result}")
                return result
        
        print(f"DEBUG: 정답을 찾을 수 없음. question_id={question_id}, 총 답안 수={len(answer_questions)}")
        return {}
    
    async def _grade_multiple_choice(
        self, 
        question: Question, 
        student_answer: str, 
        correct_answer_info: Dict, 
        max_score: int
    ) -> Dict[str, Any]:
        """객관식 문제 채점 (DB 기반)"""
        correct_answer = correct_answer_info.get("correct_answer", "")
        
        # 대소문자 구분 없이 비교
        is_correct = student_answer.upper() == correct_answer.upper()
        score = max_score if is_correct else 0
        
        # question_type 안전 처리
        safe_question_type = question.question_type
        if isinstance(safe_question_type, list):
            safe_question_type = safe_question_type[0] if safe_question_type else "객관식"
        
        # question_id 안전 처리
        safe_question_id = question.question_id
        if isinstance(safe_question_id, list):
            safe_question_id = safe_question_id[0] if safe_question_id else "1"
        
        return {
            "question_id": safe_question_id,
            "question_type": safe_question_type,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "score": score,
            "max_score": max_score,
            "is_correct": is_correct,
            "grading_method": "db",
            "ai_feedback": "",
            "needs_review": False
        }
    
    async def _grade_subjective(
        self, 
        question: Question, 
        student_answer: str, 
        correct_answer_info: Dict, 
        answer_passages: List[AnswerPassage],
        answer_examples: List[AnswerExample],
        max_score: int
    ) -> Dict[str, Any]:
        """주관식 문제 채점 (AI 기반)"""
        
        # 빈 답안 처리
        if not student_answer.strip():
            return {
                "question_id": question.question_id,
                "question_type": question.question_type,
                "student_answer": student_answer,
                "correct_answer": correct_answer_info.get("correct_answer", ""),
                "score": 0,
                "max_score": max_score,
                "is_correct": False,
                "grading_method": "ai",
                "ai_feedback": "답안이 작성되지 않았습니다.",
                "needs_review": False
            }
        
        # AI 채점을 위한 컨텍스트 구성
        context = self._build_grading_context(question, answer_passages, answer_examples)
        
        # AI 채점 수행
        ai_result = await self._perform_ai_grading(
            context, 
            question, 
            student_answer, 
            correct_answer_info,
            max_score
        )
        
        # question_type 안전 처리
        safe_question_type = question.question_type
        if isinstance(safe_question_type, list):
            safe_question_type = safe_question_type[0] if safe_question_type else "주관식"
        
        return {
            "question_id": question.question_id,
            "question_type": safe_question_type,
            "student_answer": student_answer,
            "correct_answer": correct_answer_info.get("correct_answer", ""),
            "score": ai_result["score"],
            "max_score": max_score,
            "is_correct": ai_result["is_correct"],
            "grading_method": "ai",
            "ai_feedback": ai_result["feedback"],
            "needs_review": True  # AI 채점은 항상 검수 필요
        }
    
    def _build_grading_context(self, question: Question, answer_passages: List[AnswerPassage], answer_examples: List[AnswerExample]) -> Dict[str, str]:
        """AI 채점을 위한 컨텍스트 구성"""
        context = {
            "passage_content": None,
            "example_content": None
        }
        
        # 관련 지문 추가
        if question.passage_id:
            for answer_passage in answer_passages:
                if str(answer_passage.passage_id) == str(question.passage_id):
                    context["passage_content"] = answer_passage.original_content
                    break
        
        # 관련 예문 추가
        if question.example_id:
            for answer_example in answer_examples:
                if str(answer_example.example_id) == str(question.example_id):
                    context["example_content"] = answer_example.original_content
                    break
        
        return context
    
    async def _perform_ai_grading(
        self, 
        context: Dict[str, str], 
        question: Question, 
        student_answer: str, 
        correct_answer_info: Dict,
        max_score: int
    ) -> Dict[str, Any]:
        """AI를 이용한 주관식 채점"""
        
        # 정답과 해설 정보
        correct_answer = correct_answer_info.get("correct_answer", "")
        explanation = correct_answer_info.get("explanation", "")

        try:
            # AI 서비스의 grade_subjective_question 메서드 사용
            # 해설 정보도 함께 전달
            ai_result = await self.ai_service.grade_subjective_question(
                question_text=f"{question.question_text}\n\n[해설] {explanation}" if explanation else question.question_text,
                correct_answer=correct_answer,
                student_answer=student_answer,
                passage_content=context.get("passage_content"),
                example_content=context.get("example_content")
            )
            
            # 점수 검증 및 조정
            raw_score = ai_result.get("score", 0)
            # score가 리스트인 경우 첫 번째 값 사용
            if isinstance(raw_score, list):
                raw_score = raw_score[0] if raw_score else 0
            # 숫자가 아닌 경우 0으로 처리
            if not isinstance(raw_score, (int, float)):
                raw_score = 0
            
            score = max(0, min(int(raw_score), max_score))
            is_correct = ai_result.get("is_correct", False) or score == max_score
            feedback = ai_result.get("feedback", "AI 채점이 완료되었습니다.")
            
            return {
                "score": score,
                "is_correct": is_correct,
                "feedback": feedback
            }
            
        except Exception as e:
            # AI 채점 실패 시 기본값 반환
            return {
                "score": 0,
                "is_correct": False,
                "feedback": f"AI 채점 중 오류가 발생했습니다: {str(e)}"
            }
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """AI 응답을 JSON으로 파싱 (3단계 fallback)"""
        
        # 1단계: 직접 JSON 파싱
        try:
            return json.loads(ai_response.strip())
        except json.JSONDecodeError:
            pass
        
        # 2단계: 마크다운 코드 블록에서 JSON 추출
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # 3단계: 정규식으로 필드 추출
        try:
            score_match = re.search(r'"?score"?\s*:\s*(\d+)', ai_response)
            is_correct_match = re.search(r'"?is_correct"?\s*:\s*(true|false)', ai_response, re.IGNORECASE)
            feedback_match = re.search(r'"?feedback"?\s*:\s*"([^"]*)"', ai_response)
            
            return {
                "score": int(score_match.group(1)) if score_match else 0,
                "is_correct": is_correct_match.group(1).lower() == "true" if is_correct_match else False,
                "feedback": feedback_match.group(1) if feedback_match else "채점이 완료되었습니다."
            }
        except (ValueError, AttributeError):
            pass
        
        # 모든 파싱 실패 시 기본값
        return {
            "score": 0,
            "is_correct": False,
            "feedback": "AI 응답을 파싱할 수 없습니다."
        }
    
    async def _save_grading_result(
        self, 
        worksheet: Worksheet, 
        student_name: str, 
        completion_time: int,
        total_score: int, 
        max_score: int, 
        percentage: float, 
        needs_review: bool,
        question_results: List[Dict[str, Any]], 
        db: Session
    ) -> GradingResult:
        """채점 결과를 데이터베이스에 저장"""
        
        # 고유 결과 ID 생성
        result_id = f"GR_{worksheet.worksheet_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # 채점 결과 메인 레코드 생성
        grading_result = GradingResult(
            result_id=result_id,
            worksheet_id=worksheet.id,
            student_name=student_name,
            completion_time=completion_time,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            needs_review=needs_review,
            is_reviewed=False,
            created_at=datetime.now()
        )
        
        db.add(grading_result)
        db.flush()  # ID 생성을 위해 flush
        
        # 문제별 채점 결과 저장
        for result in question_results:
            question_result = QuestionResult(
                grading_result_id=grading_result.id,
                question_id=result["question_id"],
                question_type=result["question_type"],
                student_answer=result["student_answer"],
                correct_answer=result["correct_answer"],
                score=result["score"],
                max_score=result["max_score"],
                is_correct=result["is_correct"],
                grading_method=result["grading_method"],
                ai_feedback=result.get("ai_feedback"),
                needs_review=result["needs_review"],
                is_reviewed=False,
                created_at=datetime.now()
            )
            db.add(question_result)
        
        db.commit()
        return grading_result


# 전역 채점 서비스 인스턴스
grading_service = GradingService()

# 라우터에서 사용할 함수
async def perform_grading(worksheet: Worksheet, student_answers: Dict[str, str], db: Session, student_name: str = "익명", completion_time: int = 0) -> Dict[str, Any]:
    """채점 수행 (라우터에서 호출)"""
    return await grading_service.perform_grading(worksheet, student_answers, db, student_name, completion_time)
