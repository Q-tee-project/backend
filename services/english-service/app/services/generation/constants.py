"""
문제 생성을 위한 매핑 상수들
"""

# Korean to English mappings for prompt data
SUBJECT_MAPPING = {
    '독해': 'Reading Comprehension',
    '문법': 'Grammar',
    '어휘': 'Vocabulary'
}

DIFFICULTY_MAPPING = {
    '상': 'High',
    '중': 'Medium',
    '하': 'Low'
}

FORMAT_MAPPING = {
    '객관식': 'Multiple Choice',
    '단답형': 'Short Answer',
    '서술형': 'Long Answer'
}

SCHOOL_LEVEL_MAPPING = {
    '중학교': 'Middle School',
    '고등학교': 'High School'
}
