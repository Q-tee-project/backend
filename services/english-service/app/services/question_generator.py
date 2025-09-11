"""
문제 생성을 위한 유틸리티 함수들
"""
import math
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
import random
from sqlalchemy.orm import Session
from ..models.models import Word


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


class PromptGenerator:
    """프롬프트 생성 클래스"""
    
    def __init__(self):
        self.calculator = QuestionDistributionCalculator()
    
    def extract_vocabulary_by_difficulty(
        self, 
        db: Session, 
        difficulty_distribution: List[Dict[str, Any]], 
        total_words: int = 50
    ) -> str:
        """
        난이도 분배에 따라 words 테이블에서 단어를 추출하여 프롬프트용 문자열 생성
        
        중1 수준 매핑:
        - 하 → basic 레벨
        - 중/상 → middle 레벨 (high는 제외)
        """
        try:
            # 난이도별 비율 계산
            basic_ratio = 0
            middle_ratio = 0
            
            for diff in difficulty_distribution:
                if diff['difficulty'] == '하':
                    basic_ratio = diff['ratio']
                elif diff['difficulty'] in ['중', '상']:
                    middle_ratio += diff['ratio']
            
            # 단어 개수 계산
            basic_count = math.floor(total_words * basic_ratio / 100)
            middle_count = total_words - basic_count
            
            # 데이터베이스에서 단어 추출
            basic_words = []
            middle_words = []
            
            if basic_count > 0:
                basic_query = db.query(Word).filter(Word.level == 'basic').limit(basic_count * 2)  # 여유분 확보
                basic_words = [word.word for word in basic_query.all()]
                basic_words = random.sample(basic_words, min(basic_count, len(basic_words)))
            
            if middle_count > 0:
                middle_query = db.query(Word).filter(Word.level == 'middle').limit(middle_count * 2)  # 여유분 확보
                middle_words = [word.word for word in middle_query.all()]
                middle_words = random.sample(middle_words, min(middle_count, len(middle_words)))
            
            # 프롬프트용 문자열 생성
            vocabulary_text = "-- 단어목록 :"
            
            if basic_words:
                vocabulary_text += f"\n  기본({len(basic_words)}개): {', '.join(basic_words)}"
            
            if middle_words:
                vocabulary_text += f"\n  중급({len(middle_words)}개): {', '.join(middle_words)}"
            
            return vocabulary_text
            
        except Exception as e:
            print(f"단어 추출 중 오류 발생: {str(e)}")
            # 오류 시 기본 메시지 반환
            return "-- 단어목록 : 데이터베이스에서 적절한 수준의 영어 단어들을 활용하여 문제를 생성하세요."
    
    def generate_answer_sheet_prompt(self, worksheet_json: dict) -> str:
        """
        문제지 JSON을 받아 답안지 생성용 프롬프트를 만듭니다.
        변형된 지문/예문을 원본 상태로 복원하여 자연스러운 완성된 텍스트로 제공합니다.
        """
        return f"""
다음 영어 문제지의 답안지와 해설을 생성하세요:

{json.dumps(worksheet_json, ensure_ascii=False, indent=2)}

**답안지 생성 규칙**:

1. **지문 복원**: 
   - 모든 빈칸을 적절한 정답으로 채워 완전한 문장으로 만들기
   - 문단 순서 표시나 선택지 기호를 모두 제거하여 자연스러운 흐름으로 연결
   - 원래 지문이 가진 의미와 논리적 구조를 그대로 유지

2. **예문 복원**:
   - 흩어진 선택지들을 올바른 순서로 재배열하여 완전한 형태로 구성
   - 문법적으로 정확하고 의미가 통하는 자연스러운 영어 표현으로 완성

3. **정답**:
   - 객관식은 정답 번호, 주관식이나 서술형은 정답
   - 정답에는 정답만 작성, 정답에 대한 이유나 해설은 작성하지 않음

3. **해설 작성**:
   - 각 문제의 정답 근거를 명확히 설명
   - 문제 유형별 핵심 학습 포인트 제시 (문법/어휘/독해 기법/대화 표현 등)
   - 학습자가 이해하기 쉬운 한국어로 설명

**JSON 응답 형식**:
```json
{{
  "answer_sheet": {{
    "passages": [
      {{
        "passage_id": "1",
        "text_type": "글의 종류 (예: 일기, 편지, 안내문, 대화 등)",
        "original_content": "빈칸과 번호가 모두 제거된 완전하고 자연스러운 영어 지문",
        "korean_translation": "영어 지문의 자연스러운 한글 번역 (의역 포함, 읽기 쉽게)",
        "related_questions": ["1", "2", "3"]
      }}
    ],
    "examples": [
      {{
        "example_id": "1", 
        "original_content": "선택지가 올바른 순서로 배열된 완전한 대화/문장",
        "korean_translation": "예문의 자연스러운 한글 번역",
        "related_questions": "4"
      }}
    ],
    "questions": [
      {{
        "question_id": "1",
        "correct_answer": "정답 번호 또는 정답",
        "explanation": "정답 근거와 해설 (한국어)",
        "learning_point": "학습 포인트 (문법/어휘/독해 기법 등)"
      }}
    ]
  }}
}}
```

**중요**: 
- 지문과 예문의 original_content는 **완전히 자연스러운 영어**로 작성
- 빈칸, 번호, 선택지 표시 등은 모두 제거
- 문맥상 자연스럽게 연결되는 완성된 텍스트 제공

**번역 지침**:
- korean_translation은 **자연스럽고 읽기 쉬운 한국어**로 번역
- 직역보다는 의역을 통해 한국어답게 표현
- 학습자가 이해하기 쉽도록 명확하고 친근한 문체 사용
- 문화적 맥락을 고려한 적절한 번역
"""

    def generate_prompt(self, request_data: Dict[str, Any], db: Session = None) -> str:
        """입력 데이터를 기반으로 문제 생성 프롬프트를 만듭니다."""
        
        # DB에서 텍스트 유형 형식 가져오기 (내부에서 직접 처리)
        json_formats_text = ""
        try:
            from app.database import SessionLocal
            from app.models.models import TextType
            db = SessionLocal()
            text_types = db.query(TextType).all()
            
            if text_types:
                for text_type in text_types:
                    json_formats_text += f"\n{text_type.type_name} ({text_type.description}) : {text_type.json_format}"
            else:
                # DB에 데이터가 없는 경우 기본값 사용
                json_formats_text = """
article (일반 글) : content: title, paragraph로 구성된 배열
correspondence (서신/소통) : metadata: sender, recipient, subject, date 등, content: paragraph
dialogue (대화문) : metadata: participants 배열, content: { speaker: '이름', line: '대사' } 객체의 배열
informational (정보성 양식) : content: title, paragraph, list, 그리고 key_value 쌍 (예: { key: '장소', value: '시청 앞' })
review (리뷰/후기) : metadata: rating (별점), product_name 등"""
            
            db.close()
        except Exception as e:
            print(f"DB에서 텍스트 유형 조회 오류: {e}")
            # 기본값 사용
            json_formats_text = """
article (일반 글) : content: title, paragraph로 구성된 배열
correspondence (서신/소통) : metadata: sender, recipient, subject, date 등, content: paragraph
dialogue (대화문) : metadata: participants 배열, content: { speaker: '이름', line: '대사' } 객체의 배열
informational (정보성 양식) : content: title, paragraph, list, 그리고 key_value 쌍 (예: { key: '장소', value: '시청 앞' })
review (리뷰/후기) : metadata: rating (별점), product_name 등"""
        
        # 1. 기본 정보 추출
        school_level = request_data.get('school_level', '중학교')
        grade = request_data.get('grade', 1)
        total_questions = request_data.get('total_questions', 10)
        
        # 2. 영역별 문제 수 계산
        subject_ratios = request_data.get('subject_ratios', [])
        subject_distribution = self.calculator.calculate_distribution(total_questions, subject_ratios)
        
        # 3. 형식별 문제 수 계산
        format_ratios = request_data.get('format_ratios', [])
        format_distribution = self.calculator.calculate_distribution(total_questions, format_ratios)
        
        # 4. 난이도별 문제 수 계산
        difficulty_ratios = request_data.get('difficulty_distribution', [])
        difficulty_distribution = self.calculator.calculate_distribution(total_questions, difficulty_ratios)
        
        # 5. 세부 영역 정보 추출
        subject_details = request_data.get('subject_details', {})
        
        # 6. 추가 요구사항 추출
        additional_requirements = request_data.get('additional_requirements', '')
        
        # 형식별 문제 수 문자열 생성
        format_lines = []
        for fmt in format_distribution:
            format_lines.append(f"{fmt['format']} : {fmt['count']}문제")
        
        # 난이도별 문제 수 문자열 생성
        difficulty_lines = []
        for diff in difficulty_distribution:
            difficulty_lines.append(f"난이도 {diff['difficulty']} 문제 : {diff['count']}문제")
        
        # 영역별 문제 수 문자열 생성
        subject_lines = []
        for subj in subject_distribution:
            subject_lines.append(f"{subj['subject']} 문제 : {subj['count']}문제")
        
        # 영역별 출제 유형 문자열 생성
        subject_types_lines = []
        for subj in subject_distribution:
            subject_name = subj['subject']
            types = []
            
            if subject_name == '독해':
                types = subject_details.get('reading_types', [])
            elif subject_name == '문법':
                # 문법 카테고리와 토픽을 합쳐서 사용
                categories = subject_details.get('grammar_categories', [])
                topics = subject_details.get('grammar_topics', [])
                types = categories + topics
            elif subject_name == '어휘':
                types = subject_details.get('vocabulary_categories', [])
            
            types_str = str(types) if types else "[]"
            subject_types_lines.append(f"{subject_name} : {types_str}")
        
        # 단어목록 동적 생성
        vocabulary_list = ""
        if db is not None:
            try:
                vocabulary_list = self.extract_vocabulary_by_difficulty(
                    db, 
                    difficulty_distribution, 
                    total_words=50
                )
            except Exception as e:
                print(f"단어 추출 실패, 기본 메시지 사용: {str(e)}")
                vocabulary_list = "-- 단어목록 : 중학교 1학년 수준에 맞는 기본 및 중급 영어 단어들을 활용하여 문제를 생성하세요."
        else:
            vocabulary_list = "-- 단어목록 : 중학교 1학년 수준에 맞는 기본 및 중급 영어 단어들을 활용하여 문제를 생성하세요."
        
        # 프롬프트 첫 번째 부분
        prompt_part1 = f"""당신은 영어 교육 전문가이자 숙련된 문제 출제자입니다. 
주어진 조건에 따라 학습자의 수준에 맞는 고품질의 영어 문제를 출제해야 합니다.

다음 조건에 따라 {school_level} {grade}학년 영어 시험 문제를 출제해주세요:

#총 문제 수 : {total_questions}

#답변 형식
{chr(10).join(format_lines)}

#문제 난이도
{chr(10).join(difficulty_lines)}

#영역 별 문제 
{chr(10).join(subject_lines)}

#영역 별 문제 출제 유형
{chr(10).join(subject_types_lines)}

# 어휘 수준
- 제공되는 단어 목록을 최대한 활용하여 생성
{vocabulary_list}

# 난이도별 문제 요구사항
**하 단계 (쉬움)**: basic 레벨 단어, 기본 문장구조 
**중 단계 (보통)**: middle 레벨 단어, 적당한 추론 필요 
**상 단계 (어려움)**: middle 레벨 고급 단어, 종합적 사고 필요 

# 필수 조건
- **응답은 반드시 유효한 JSON 형태로만 응답 (다른 텍스트, 설명, 주석 등 일체 포함 금지)**
- **정답이나 해설은 절대 포함하지 마세요. 오직 문제만 생성하세요.**
- 문제 유형에 따라 필요한 경우 지문이나 예문을 수정
- 지문 및 예문은 문제id를 갖도록 (ex, "지문" : "[문제id, 문제id, 문제id]", 예문: "문제id")""" + (f"""

# 추가 요구사항
{additional_requirements}""" if additional_requirements else "") + f"""

# 문제에 사용 될 지문과 예문의 정의
- 지문은 120~150단어 이상의 긴 글을 의미
- 지문에는 2개 이상 3개 이하의 문제를 연계하여 출제
- 예문은 40단어 이하의 짧은 글을 의미(1~3줄)
- 지문은 반드시 유형 별 json형식을 참고하여 생성
- 예문의 소재는 글의 소재를 참고하여 생성
- 지문 글의 유형은 글의 소재, 영역 별 문제 출제 유형을 고려하여 자유롭게 선정해서 사용

# **중요: 문제 질문과 예문 분리 규칙**
- **문제의 질문(question_text)에는 영어 문장이나 긴 예시를 직접 포함하지 마세요**
- **영어 문장, 대화문, 긴 예시는 반드시 별도의 예문(examples)으로 분리하세요**
- **문제 질문은 순수한 한국어 질문만 포함하고, 예문 ID로 참조하세요**
- **예문이 없이 문제 질문과 선택지만 필요한 문제는 예문을 생성하지 않고 선택지에 내용이 포함되어야 합니다.**
- **지문이 있는 문제에 예문이 필요할 경우 둘 다 생성하세요.**

## 분리 예시:
**잘못된 방식:**
question_text: "다음 문장의 빈칸에 들어갈 말은?\\n\\nThey ___ good friends."

**올바른 방식:**
question_text: "다음 문장의 빈칸에 들어갈 말은?"
example_content: "They ___ good friends."
question_example_id: "1"

**잘못된 방식:**
question_text: "다음 대화를 순서대로 배열하시오\\n(A) Hi! (B) How are you? (C) Fine, thanks."

**올바른 방식:**
question_text: "다음 대화를 순서대로 배열하시오"
example_content: "(A) Hi!\\n(B) How are you?\\n(C) Fine, thanks."
question_example_id: "2"

**잘못된 방식:**
question_text: "다음과 같이 소유격을 사용하여 쓰시오\\n<보기> The book of Tom → Tom's book\\n<문제> The car of my father"

**올바른 방식:**
question_text: "다음과 같이 소유격을 사용하여 쓰시오"
example_content: "<보기> The book of Tom → Tom's book\\n<문제> The car of my father"
question_example_id: "3"

# 글의 소재
- 개인생활 관련: 취미, 오락, 여행, 운동, 쇼핑, 건강, 일상 등
- 가정생활 관련: 의복, 음식, 주거, 가족 행사, 집안일 등
- 학교생활 관련: 교육 내용, 학교 활동, 교우 관계, 진로 등
- 사회생활 관련: 대인 관계, 직업 윤리, 사회적 행사 등
- 문화 관련: 세대/성별 간 문화 차이, 다른 문화권의 관습 및 가치 등
- 민주시민 관련: 공중도덕, 인권, 양성평등, 사회 현안 등

- 지문 글의 유형
article (일반 글) : 설명문, 논설문, 기사, 연구 보고서, 블로그 포스트, 책의 한 부분 등 (가장 기본적인 '만능' 유형)
correspondence (서신/소통) : 이메일, 편지, 메모, 사내 공지 등
dialogue (대화문) : 문자 메시지, 채팅, 인터뷰, 연극 대본 등
informational (정보성 양식) : 광고, 안내문, 포스터, 일정표, 메뉴판, 영수증 등
review (리뷰/후기) : 상품 후기, 영화 평점, 식당 리뷰 등
social_media(SNS) : 트위터, 인스타그램 게시물, 페이스북 포스트 등

유형 별 json형식"""
        
        # 프롬프트 합치기
        prompt = prompt_part1 + json_formats_text + f"""

**중요: 반드시 유효한 JSON 형식으로만 응답해주세요. 다른 텍스트나 설명 없이 순수한 JSON만 반환해야 합니다.**
**정답 생성 금지: 정답, 해설, 답안, answer 등 어떤 형태의 정답도 포함하지 마세요.**


응답 형식 :
{{
    "worksheet_id": "1",
    "worksheet_name": "any_name", 
    "worksheet_date": "2025-01-01",
    "worksheet_time": "10:00",
    "worksheet_duration": "60",
    "worksheet_subject": "영어",
    "worksheet_level": "{school_level}",
    "worksheet_grade": "{grade}",
    "total_questions": {total_questions},
    "passages": [
        {{
            "passage_id": "1",
            "passage_type": "article|correspondence|dialogue|informational|review",
            "passage_content": 유형별_json형식에_따른_구조,
            "related_questions": ["1", "2"]
        }}
    ],
    "examples": [
        {{
            "example_id": "1",
            "example_content": "They ___ good friends.",
            "related_questions": ["1", "2"]
        }},
        {{
            "example_id": "2", 
            "example_content": "(A) Sounds great! What time should we meet?\\n(B) Hey, do you want to go see a movie?\\n(C) Let's meet at 2 p.m.\\n(D) Not really. Any plans?",
            "related_questions": ["3"]
        }}
    ],
    "questions": [
        {{
            "question_id": "1",
            "question_text": "다음 문장의 빈칸에 들어갈 말로 가장 적절한 것은?",
            "question_type": "객관식|단답형|서술형",
            "question_subject": "독해|문법|어휘", 
            "question_difficulty": "상|중|하",
            "question_detail_type": "입력받은 세부유형 중 해당되는 유형",
            "question_passage_id": "1" // 지문 참조시,
            "question_example_id": "1" // 예문 참조시,
            "question_choices": [
                "1",
                "2", 
                "3",
                "4",
                "5" // 단답형, 서술형일 시 빈칸
            ]
        }}
    ]
}}

**다시 한번 강조: 위의 JSON 형식을 정확히 따라 유효한 JSON만 응답해주세요. 추가 설명이나 텍스트는 절대 포함하지 마세요.**
**절대 정답을 생성하지 마세요: answer, correct_answer, solution, 정답, 해답 등 어떤 정답 관련 필드도 포함하지 마세요.**
**절대 추가적인 항목을 만들지 마세요.**

**문제 배치 및 순서 규칙**
- 지문과 연관된 문제들은 반드시 연속된 번호로 배치해야 합니다.

**중요한 배치 원칙:**
1. 같은 지문을 사용하는 문제들은 반드시 연속 번호로 배치
2. 문제 번호와 related_questions 배열이 정확히 일치해야 함

**배치 검증:**
- 각 지문의 related_questions는 연속된 숫자여야 함 
- 문제 총 개수와 questions 배열 길이가 일치해야 함 
- 모든 문제 번호는 1부터 총 문제 수까지 빠짐없이 존재해야 함 

**절대 엄수: 문제 질문에서 ID 언급 금지**
- question_text에서 지문이나 예문의 ID(P1, E1, 지문1, 예문1 등)를 절대 언급하지 마세요.
- 지문 참조 시: "위 글", "위 지문", "다음 글" 등으로만 표현
- 예문 참조 시: "다음 예문", "위 예문", "다음 문장" 등으로만 표현

**잘못된 예시들 (절대 사용 금지):**
- "지문 P1의 빈칸에 들어갈 말은?"
- "예문 E1에서 빈칸에 들어갈 말은?"  
- "지문 1의 내용에 따르면?"
- "예문 1을 보고 답하시오"

**올바른 예시들 (반드시 이렇게 작성):**
- "위 글의 빈칸에 들어갈 말은?"
- "다음 예문에서 빈칸에 들어갈 말은?"
- "위 글의 내용에 따르면?"
- "다음을 보고 답하시오"

**ID 형식 규칙:**
- 지문 ID: "1", "2", "3" (단순한 숫자)
- 예문 ID: "1", "2", "3" (단순한 숫자)

**다시 한번 강조: question_text에는 어떤 형태의 ID도 포함하지 마세요!**"""
        
        return prompt
    
    
    def get_distribution_summary(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """분배 결과 요약을 반환합니다."""
        total_questions = request_data.get('total_questions', 10)
        
        # 각 분배 계산
        subject_ratios = request_data.get('subject_ratios', [])
        format_ratios = request_data.get('format_ratios', [])
        difficulty_ratios = request_data.get('difficulty_distribution', [])
        
        subject_distribution = self.calculator.calculate_distribution(total_questions, subject_ratios)
        format_distribution = self.calculator.calculate_distribution(total_questions, format_ratios)
        difficulty_distribution = self.calculator.calculate_distribution(total_questions, difficulty_ratios)
        
        return {
            'total_questions': total_questions,
            'subject_distribution': subject_distribution,
            'format_distribution': format_distribution,
            'difficulty_distribution': difficulty_distribution,
            'validation_passed': self.calculator.validate_total([
                subject_distribution, 
                format_distribution, 
                difficulty_distribution
            ], total_questions)
        }


def test_prompt_generation():
    """테스트 함수"""
    # 샘플 데이터
    sample_data = {
        "school_level": "중학교",
        "grade": 1,
        "total_questions": 10,
        "subjects": ["독해", "문법"],
        "subject_details": {
            "reading_types": ["주제 및 요지 파악", "빈칸추론"],
            "grammar_categories": ["시제", "조동사"],
            "grammar_topics": ["현재완료", "과거완료"],
            "vocabulary_categories": ["일상생활"]
        },
        "subject_ratios": [
            {"subject": "독해", "ratio": 60},
            {"subject": "문법", "ratio": 40}
        ],
        "format_ratios": [
            {"format": "객관식", "ratio": 70},
            {"format": "주관식", "ratio": 30}
        ],
        "difficulty_distribution": [
            {"difficulty": "상", "ratio": 30},
            {"difficulty": "중", "ratio": 50},
            {"difficulty": "하", "ratio": 20}
        ]
    }
    
    generator = PromptGenerator()
    prompt = generator.generate_prompt(sample_data)
    summary = generator.get_distribution_summary(sample_data)
    
    return prompt, summary


if __name__ == "__main__":
    prompt, summary = test_prompt_generation()
    print("=== 분배 요약 ===")
    print(summary)
    print("\n=== 생성된 프롬프트 ===")
    print(prompt)
