"""
비동기 태스크 처리 개선을 위한 서비스
"""
import asyncio
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from ..models.problem import Problem
from ..models.worksheet import Worksheet

class AsyncTaskService:
    """비동기 태스크 처리를 위한 서비스"""

    def __init__(self):
        pass
    
    async def process_grading_batch(
        self, 
        problems: List[Problem], 
        answers: Dict[str, str], 
        points_per_problem: int,
        progress_callback: Optional[callable] = None
    ) -> List[Dict]:
        """문제 배치를 비동기로 채점 처리"""
        
        grading_results = []
        total_count = len(problems)
        
        # 비동기로 채점 작업들을 생성
        tasks = []
        for i, problem in enumerate(problems):
            user_answer = answers.get(str(problem.id), "")
            
            task = self._grade_single_problem_async(
                problem=problem,
                user_answer=user_answer,
                points_per_problem=points_per_problem,
                problem_index=i,
                total_count=total_count,
                progress_callback=progress_callback
            )
            tasks.append(task)
        
        # 모든 채점 작업을 병렬로 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 처리
        for result in results:
            if isinstance(result, Exception):
                print(f"채점 작업 중 오류 발생: {str(result)}")
                # 기본 결과 추가
                grading_results.append({
                    "score": 0,
                    "is_correct": False,
                    "error": str(result)
                })
            else:
                grading_results.append(result)
        
        return grading_results
    
    async def _grade_single_problem_async(
        self,
        problem: Problem,
        user_answer: str,
        points_per_problem: int,
        problem_index: int,
        total_count: int,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """단일 문제 비동기 채점"""
        
        # 진행률 업데이트
        if progress_callback:
            progress = 20 + (problem_index + 1) / total_count * 70
            await progress_callback(progress, f'채점 중... ({problem_index+1}/{total_count})')
        
        # 객관식/단답형: 직접 비교 (동기 처리)
        result = self._grade_objective_sync(problem, user_answer, points_per_problem)

        return result

    def _grade_objective_sync(self, problem: Problem, user_answer: str, points_per_problem: int) -> Dict:
        """객관식/단답형 문제 동기 채점"""
        
        # 객관식인 경우 선택지 인덱스를 실제 선택지 내용으로 변환
        actual_user_answer = user_answer
        if problem.problem_type == "multiple_choice" and problem.choices:
            actual_user_answer = self._convert_choice_to_content(problem, user_answer)
        
        # 답안 정규화 및 비교
        correct_normalized = self.grading_service.normalize_answer_for_comparison(problem.correct_answer)
        user_normalized = self.grading_service.normalize_answer_for_comparison(actual_user_answer)
        
        print(f"🔍 답안 비교: 정답 '{problem.correct_answer}' → '{correct_normalized}'")
        print(f"🔍 답안 비교: 학생 '{actual_user_answer}' → '{user_normalized}'")
        
        # 기본 문자열 매칭
        is_correct = correct_normalized == user_normalized
        
        # 수학 답안의 경우 유연한 매칭 적용
        if not is_correct and problem.problem_type == "short_answer":
            is_correct = self._flexible_math_matching(correct_normalized, user_normalized)
        
        score = points_per_problem if is_correct else 0
        
        return {
            "problem_id": problem.id,
            "problem_type": problem.problem_type,
            "user_answer": user_answer,
            "actual_user_answer": actual_user_answer,
            "correct_answer": problem.correct_answer,
            "is_correct": is_correct,
            "score": score,
            "points_per_problem": points_per_problem,
            "explanation": problem.explanation
        }
    
    def _calculate_keyword_score(self, correct_answer: str, user_answer: str) -> Dict:
        """키워드 점수 계산"""
        correct_answer_keywords = correct_answer.lower().split()
        user_answer_lower = user_answer.lower()
        
        keyword_matches = 0
        for keyword in correct_answer_keywords:
            if keyword in user_answer_lower:
                keyword_matches += 1
        
        keyword_score_ratio = (keyword_matches / len(correct_answer_keywords)) if correct_answer_keywords else 0
        
        return {
            "matches": keyword_matches,
            "total": len(correct_answer_keywords),
            "ratio": keyword_score_ratio
        }
    
    def _convert_choice_to_content(self, problem: Problem, user_answer: str) -> str:
        """객관식 선택지를 내용으로 변환"""
        choice_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        if user_answer.upper() in choice_map:
            try:
                import json
                choices = json.loads(problem.choices)
                choice_index = choice_map[user_answer.upper()]
                if 0 <= choice_index < len(choices):
                    return choices[choice_index]
            except (json.JSONDecodeError, IndexError):
                pass  # 변환 실패시 원래 답안 그대로 사용
        return user_answer
    
    def _flexible_math_matching(self, correct_normalized: str, user_normalized: str) -> bool:
        """수학 답안의 유연한 매칭"""
        import re
        
        # 정답에서 숫자나 수식 부분만 추출
        correct_values = re.findall(r'-?\d+(?:\.\d+)?', correct_normalized)
        user_values = re.findall(r'-?\d+(?:\.\d+)?', user_normalized)
        
        # 추출된 숫자들이 일치하는지 확인
        if correct_values and user_values:
            is_correct = correct_values == user_values
            print(f"🔍 디버그: 수학 답안 매칭 - 정답 숫자: {correct_values}, 학생 숫자: {user_values}, 결과: {is_correct}")
            if is_correct:
                return True
        
        # 추가적으로 콤마로 분리된 값들 비교
        correct_parts = [part.strip() for part in correct_normalized.replace('=', ',').split(',')]
        user_parts = [part.strip() for part in user_normalized.split(',')]
        
        correct_nums = []
        user_nums = []
        
        for part in correct_parts:
            nums = re.findall(r'-?\d+(?:\.\d+)?', part)
            correct_nums.extend(nums)
        
        for part in user_parts:
            nums = re.findall(r'-?\d+(?:\.\d+)?', part)
            user_nums.extend(nums)
        
        is_correct = correct_nums == user_nums
        print(f"🔍 디버그: 콤마 분리 매칭 - 정답 숫자: {correct_nums}, 학생 숫자: {user_nums}, 결과: {is_correct}")
        
        return is_correct