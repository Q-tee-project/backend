from enum import Enum


# 열거형 정의
class SchoolLevel(str, Enum):
    MIDDLE = "중학교"
    HIGH = "고등학교"


class Grade(int, Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3


class Subject(str, Enum):
    ALL = "전체"
    READING = "독해"
    GRAMMAR = "문법"
    VOCABULARY = "어휘"


class QuestionFormat(str, Enum):
    ALL = "전체"
    MULTIPLE_CHOICE = "객관식"
    SHORT_ANSWER = "주관식"
    ESSAY = "서술형"


class Difficulty(str, Enum):
    HIGH = "상"
    MEDIUM = "중"
    LOW = "하"