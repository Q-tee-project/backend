"""
문제 수와 비율 계산을 위한 모듈
"""
import math
from typing import Dict, List, Any


class QuestionDistributionCalculator:
    """문제 수와 비율을 계산하는 클래스"""

    @staticmethod
    def calculate_distribution(total_questions: int, ratios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        비율을 기반으로 실제 문제 수를 계산합니다.
        나누어 떨어지지 않는 경우 첫 번째 항목에 나머지를 추가합니다.
        """
        if not ratios or sum(r['ratio'] for r in ratios) != 100:
            raise ValueError("비율의 합계는 100%여야 합니다.")

        result = []
        total_allocated = 0

        # 각 항목별로 문제 수 계산
        for i, ratio_item in enumerate(ratios):
            if i == len(ratios) - 1:  # 마지막 항목은 나머지 모두 할당
                count = total_questions - total_allocated
            else:
                count = math.floor(total_questions * ratio_item['ratio'] / 100)
                total_allocated += count

            result.append({
                **ratio_item,
                'count': count
            })

        return result

    @staticmethod
    def validate_total(distributions: List[List[Dict[str, Any]]], total_questions: int) -> bool:
        """모든 분배의 총합이 총 문제 수와 일치하는지 확인"""
        for dist in distributions:
            if sum(item['count'] for item in dist) != total_questions:
                return False
        return True
