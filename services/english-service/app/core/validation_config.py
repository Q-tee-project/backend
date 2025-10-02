"""
검증 설정
AI-as-a-Judge 방식의 문제 검증에 사용되는 기준과 임계값
"""

from typing import Dict, Any


# 검증 평가 기준 (총 100점)
VALIDATION_CRITERIA = {
    "alignment": {
        "total_points": 30,
        "description": "문항-콘텐츠 정합성",
        "sub_criteria": {
            "curriculum_relevance": {
                "points": 10,
                "description": "교육과정 연계성",
                "guidance": "학년별 교육과정 성취기준 및 핵심 어휘/문법 범위 준수"
            },
            "difficulty_consistency": {
                "points": 10,
                "description": "난이도 일치성",
                "guidance": "제시된 CEFR 레벨 및 난이도에 부합하는 어휘, 문장 구조, 추론 수준"
            },
            "topic_appropriateness": {
                "points": 10,
                "description": "소재의 적절성",
                "guidance": "학습자의 연령과 배경지식을 고려한 적절한 주제 선정"
            }
        }
    },
    "content_quality": {
        "total_points": 40,
        "description": "내용 및 문제 품질",
        "sub_criteria": {
            "passage_quality": {
                "points": 10,
                "description": "지문의 품질",
                "guidance": "문법적 정확성, 자연스러움, 논리적 명확성"
            },
            "instruction_clarity": {
                "points": 10,
                "description": "발문의 명확성",
                "guidance": "혼동의 여지 없는 명확하고 간결한 질문"
            },
            "answer_accuracy": {
                "points": 10,
                "description": "정답의 명확성",
                "guidance": "유일하고 명확한 정답, 지문 내 명확한 근거"
            },
            "distractor_quality": {
                "points": 10,
                "description": "선택지의 매력도",
                "guidance": "그럴듯한 오답으로 변별력 확보"
            }
        }
    },
    "explanation_quality": {
        "total_points": 30,
        "description": "해설 품질",
        "sub_criteria": {
            "logical_explanation": {
                "points": 10,
                "description": "해설의 논리성",
                "guidance": "지문 근거를 바탕으로 한 논리적이고 명확한 정답 설명"
            },
            "incorrect_answer_analysis": {
                "points": 10,
                "description": "오답 해설의 유용성",
                "guidance": "다른 선택지가 오답인 이유에 대한 유용한 설명"
            },
            "additional_information": {
                "points": 10,
                "description": "추가 정보의 유용성",
                "guidance": "어휘, 구문, 배경지식에 대한 유용하고 정확한 추가 설명"
            }
        }
    }
}


# 판정 기준 (점수 기반)
JUDGMENT_THRESHOLDS = {
    "pass": 85,  # 85점 이상: Pass
    "needs_revision": 60,  # 60-84점: Needs Revision
    # 59점 이하: Fail
}


# 검증 설정
VALIDATION_SETTINGS = {
    "max_retries": 3,  # 최대 재생성 시도 횟수
    "enable_by_default": True,  # 기본적으로 검증 활성화
    "log_all_attempts": True,  # 모든 시도 로깅
    "save_validation_metrics": True,  # 검증 메트릭 저장
}


# 학년별 추가 검증 가이드라인
GRADE_SPECIFIC_GUIDELINES = {
    "중학교": {
        1: {
            "cefr_range": ["A2", "B1"],
            "word_count_range": (50, 150),
            "key_focus": ["기초 문법", "친숙한 주제", "단순 문장 구조"]
        },
        2: {
            "cefr_range": ["A2", "B1"],
            "word_count_range": (50, 150),
            "key_focus": ["기초 문법", "친숙한 주제", "단순 문장 구조"]
        },
        3: {
            "cefr_range": ["B1"],
            "word_count_range": (200, 300),
            "key_focus": ["중급 문법", "사회적 이슈", "복합 문장"]
        }
    },
    "고등학교": {
        1: {
            "cefr_range": ["B1"],
            "word_count_range": (200, 300),
            "key_focus": ["중급 문법", "논리적 사고", "다양한 주제"]
        },
        2: {
            "cefr_range": ["B2", "B2+"],
            "word_count_range": (400, 600),
            "key_focus": ["고급 문법", "추상적 개념", "복잡한 구조"]
        },
        3: {
            "cefr_range": ["B2", "B2+"],
            "word_count_range": (400, 600),
            "key_focus": ["고급 문법", "전문적 주제", "수능 수준"]
        }
    }
}


def get_validation_config() -> Dict[str, Any]:
    """검증 설정 전체 반환"""
    return {
        "criteria": VALIDATION_CRITERIA,
        "thresholds": JUDGMENT_THRESHOLDS,
        "settings": VALIDATION_SETTINGS,
        "grade_guidelines": GRADE_SPECIFIC_GUIDELINES
    }


def get_grade_guidelines(school_level: str, grade: int) -> Dict[str, Any]:
    """특정 학년의 검증 가이드라인 반환"""
    return GRADE_SPECIFIC_GUIDELINES.get(school_level, {}).get(grade, {})
