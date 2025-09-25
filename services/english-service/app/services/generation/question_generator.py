"""
문제 생성을 위한 유틸리티 함수들
"""
import math
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
import random
from sqlalchemy.orm import Session
from app.models import Word


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
    
    def generate_prompt(self, request_data: Dict[str, Any], db: Session = None) -> str:
        """입력 데이터를 기반으로 문제 생성 프롬프트를 만듭니다."""
        
        # DB에서 텍스트 유형 형식 가져오기
        json_formats_text = self._get_text_type_formats(db)
        
        # 기본 정보 추출 및 분배 계산
        school_level = request_data.get('school_level', '중학교')
        grade = request_data.get('grade', 1)
        total_questions = request_data.get('total_questions', 10)
        subject_details = request_data.get('subject_details', {})
        additional_requirements = request_data.get('additional_requirements', '')
        
        # 분배 계산
        subject_distribution = self.calculator.calculate_distribution(
            total_questions, request_data.get('subject_ratios', [])
        )
        format_distribution = self.calculator.calculate_distribution(
            total_questions, request_data.get('format_ratios', [])
        )
        difficulty_distribution = self.calculator.calculate_distribution(
            total_questions, request_data.get('difficulty_distribution', [])
        )
        
        # problem_type 계산 (영역별 비율에 따라)
        subjects_with_count = [subj for subj in subject_distribution if subj['count'] > 0]
        print(f"🔍 영역별 분배: {subject_distribution}")
        print(f"🔍 문제 수가 있는 영역: {subjects_with_count}")

        if len(subjects_with_count) == 1:
            problem_type = subjects_with_count[0]['subject']
            print(f"✅ 단일 영역: {problem_type}")
        else:
            problem_type = "혼합형"
            print(f"✅ 혼합형: {len(subjects_with_count)}개 영역")

        # 동적 내용 생성
        format_lines = [f"{fmt['format']} : {fmt['count']}문제" for fmt in format_distribution]
        difficulty_lines = [f"난이도 {diff['difficulty']} 문제 : {diff['count']}문제" for diff in difficulty_distribution]
        subject_lines = [f"{subj['subject']} 문제 : {subj['count']}문제" for subj in subject_distribution]
        subject_types_lines = self._generate_subject_types_lines(subject_distribution, subject_details, db)
        vocabulary_list = self._get_vocabulary_list(db, difficulty_distribution)
        
        # JSON 응답 템플릿 정의
        json_template = f"""
        {{
            "worksheet_id": 1,
            "worksheet_name": "",
            "worksheet_date": "2025-01-01",
            "worksheet_time": "10:00",
            "worksheet_duration": "60",
            "worksheet_subject": "english",
            "worksheet_level": "{school_level}",
            "worksheet_grade": {grade},
            "problem_type": "{problem_type}",
            "total_questions": {total_questions},
            "passages": [
                {{
                    "passage_id": 1,
                    "passage_type": "article",
                    "passage_content": "json 형식에 따른 학생에게 보여질 지문 내용 (빈칸, 순서 배열용 보기 등 포함)",
                    "original_content": "json 형식에 따른 완전한 형태의 원본 지문",
                    "korean_translation": "json 형식에 따른 원본 지문의 자연스러운 한글 번역",
                    "related_questions": [1, 2]
                }}
            ],
            "questions": [
                {{
                    "question_id": 1,
                    "question_type": "객관식|단답형|서술형",
                    "question_subject": "독해|문법|어휘",
                    "question_detail_type": "입력받은 세부유형 중 해당되는 유형",
                    "question_difficulty": "상|중|하",
                    "question_text": "다음 문장의 빈칸에 들어갈 말로 가장 적절한 것은?",
                    "example_content": "학생에게 보여질 예문 내용 (빈칸, 순서 배열용 보기 등 포함)",
                    "example_original_content": "완전한 형태의 원본 예문",
                    "example_korean_translation": "원본 예문의 자연스러운 한글 번역",
                    "related_question": 1,
                    "question_passage_id": 1,
                    "question_choices": [
                        "선택지 1",
                        "선택지 2",
                        "선택지 3"
                    ],
                    "correct_answer": 0 | "정답 텍스트",
                    "explanation": "정답에 대한 상세한 해설 (한국어)",
                    "learning_point": "문제와 관련된 핵심 학습 포인트"
                }}
            ]
        }}"""
        
        # 프롬프트 구성
        prompt = f"""당신은 영어 교육 전문가이자 숙련된 문제 출제자입니다. 
주어진 조건에 따라 학습자의 수준에 맞는 고품질의 영어 문제를 출제해야 합니다.

다음 조건에 따라 {school_level} {grade}학년 영어 시험 문제를 출제해주세요:

# 총 문제 수: {total_questions}

# 답변 형식
{chr(10).join(format_lines)}

# 문제 난이도
{chr(10).join(difficulty_lines)}

# 영역별 문제 
{chr(10).join(subject_lines)}

# 영역별 문제 출제 유형
{chr(10).join(subject_types_lines)}

# 어휘 수준
- 제공되는 단어 목록을 최대한 활용하여 생성
{vocabulary_list}

# 난이도별 문제 요구사항
**하 단계 (쉬움)**: basic 레벨 단어, 기본 문장구조 
**중 단계 (보통)**: middle 레벨 단어, 적당한 추론 필요 
**상 단계 (어려움)**: middle 레벨 고급 단어, 종합적 사고 필요

# 필수 조건
- **응답은 반드시 아래에 명시된 통합 JSON 형식에 맞춰 유효한 JSON 객체 하나만 생성해야 합니다. (다른 텍스트, 설명, 주석 등 일체 포함 금지)**
- **문제(questions), 지문(passages), 예문(examples) 객체 안에 학생용 정보와 답안용 정보를 모두 포함하여 한 번에 생성해야 합니다.**
- `passage_content`와 `example_content`에는 학생에게 보여질 내용(빈칸, 순서 배열용 보기 등)을 포함하세요.
- `original_content`에는 빈칸이 채워지고 순서가 배열된 완전한 원본 텍스트를 포함하세요.
- `korean_translation`에는 `original_content`의 자연스러운 한글 번역을 포함하세요.
- `questions` 객체 안에는 문제 텍스트, 선택지뿐만 아니라 `correct_answer`, `explanation`, `learning_point`를 반드시 포함해야 합니다.

# 답안 및 해설 생성 규칙:
- **지문 복원**: 
   - 모든 빈칸을 적절한 정답으로 채워 완전한 문장으로 만들고, 문단 순서 표시나 선택지 기호를 모두 제거하여 자연스러운 흐름으로 연결하세요.
   - 원래 지문이 가진 의미와 논리적 구조를 그대로 유지하세요.
- **예문 복원**:
   - 흩어진 선택지들을 올바른 순서로 재배열하여 완전한 형태로 구성하고, 문법적으로 정확하고 의미가 통하는 자연스러운 영어 표현으로 완성하세요.
- **정답(correct_answer)**: 객관식은 정답 번호(문자열), 단답형/서술형은 정답 텍스트를 명확하게 기입하세요.
- **해설(explanation)**: 정답 근거를 명확히 설명하고, 오답의 이유도 간략히 언급하세요. 학습자가 이해하기 쉬운 한국어로 작성하세요.
- **학습 포인트(learning_point)**: 각 문제의 정답 근거를 명확히 설명하고, 문제 유형별 핵심 학습 포인트(문법/어휘/독해 기법/대화 표현 등)를 제시하세요.
- **번역 지침**: `korean_translation`은 자연스럽고 읽기 쉬운 한국어로 번역하고, 직역보다는 의역을 통해 한국어답게 표현하세요. 학습자가 이해하기 쉽도록 명확하고 친근한 문체 사용하고, 문화적 맥락을 고려한 적절한 번역을 제공하세요.

- **지문 생성 필수 조건**:
  - 독해 문제 {sum(subj['count'] for subj in subject_distribution if subj['subject'] == '독해')}개 = 지문 {sum(subj['count'] for subj in subject_distribution if subj['subject'] == '독해')}개 (1:1 매칭)
  - 각 지문의 related_questions 배열에 연결된 문제 번호 정확히 기입
  - passage_id는 1부터 순차적으로 부여
- **문제-지문 연결**:
  - 독해 문제는 question_passage_id로 지문과 연결
  - 지문 없는 문제는 question_passage_id를 null로 설정
"""

        # 추가 요구사항
        if additional_requirements:
            prompt += f"""

# 추가 요구사항
{additional_requirements}"""

        prompt += f"""

# 문제에 사용될 지문과 예문의 정의
- 지문은 120~150단어 이상의 긴 글을 의미 난이도와 상관없이 길이를 준수하여 생성
- 지문에는 2개 이상 3개 이하의 문제를 연계하여 출제
- 예문은 40단어 이하의 짧은 글을 의미(1~3줄) 난이도와 상관없이 길이를 준수하여 생성
- 지문은 반드시 유형별 json형식을 참고하여 생성
- 예문의 소재는 글의 소재를 참고하여 생성
- 지문 글의 유형은 글의 소재, 영역별 문제 출제 유형을 고려하여 자유롭게 선정해서 사용

# 문제 질문과 예문 분리 규칙 (절대 위반 금지)

## 핵심 원칙
- **example_content에는 절대 지시문을 포함하지 마세요!**
- **example_content는 순수한 영어 예문, 보기, 문제만 포함해야 합니다!**
- **모든 지시문과 한국어 설명은 question_text에만 들어가야 합니다!**

## 세부 규칙
- **문제의 질문(question_text)**: 순수한 한국어 지시문만 (예: "다음과 같이 소유격을 사용하여 쓰시오")
- **예문 내용(example_content)**: 순수한 영어 예문만 (예: "<보기> The book of Tom → Tom's book\\n<문제> The car of my father")
- **영어 문장, 대화문, 긴 예시는 반드시 별도의 예문(examples)으로 분리하세요**
- **예문이 없이 문제 질문과 선택지만 필요한 문제는 예문을 생성하지 않고 선택지에 내용이 포함되어야 합니다.**

## 절대 금지되는 잘못된 예시들:

### example_content에 지시문이 포함된 경우 (절대 금지!)
** 잘못된 방식:**
```
example_content: "다음 명사구를 <보기>와 같이 소유격 형태로 바꾸시오.\\n\\n<보기> the bag of the girl → the girl's bag\\n<문제> the hat of my brother"
```

** 올바른 방식:**
```
question_text: "다음과 같이 소유격을 사용하여 쓰시오"
example_content: "<보기> the bag of the girl → the girl's bag\\n<문제> the hat of my brother"
```

### question_text에 영어 문장이 포함된 경우
** 잘못된 방식:**
```
question_text: "다음 문장의 빈칸에 들어갈 말은?\\n\\nThey ___ good friends."
```

** 올바른 방식:**
```
question_text: "다음 문장의 빈칸에 들어갈 말은?"
example_content: "They ___ good friends."
question_example_id: "1"
```

### question_text에 대화문이 포함된 경우
** 잘못된 방식:**
```
question_text: "다음 대화를 순서대로 배열하시오\\n(A) Hi! (B) How are you? (C) Fine, thanks."
```

** 올바른 방식:**
```
question_text: "다음 대화를 순서대로 배열하시오"
example_content: "(A) Hi!\\n(B) How are you?\\n(C) Fine, thanks."
question_example_id: "2"
```

### 기억하세요!
- **question_text**: 순수한 한국어 지시문만!
- **example_content**: 순수한 영어 예문만! (지시문 절대 금지!)


# 글의 소재
- 개인생활 관련: 취미, 오락, 여행, 운동, 쇼핑, 건강, 일상 등
- 가정생활 관련: 의복, 음식, 주거, 가족 행사, 집안일 등
- 학교생활 관련: 교육 내용, 학교 활동, 교우 관계, 진로 등
- 사회생활 관련: 대인 관계, 직업 윤리, 사회적 행사 등
- 문화 관련: 세대/성별 간 문화 차이, 다른 문화권의 관습 및 가치 등
- 민주시민 관련: 공중도덕, 인권, 양성평등, 사회 현안 등

# 지문 글의 유형
article (일반 글) : 설명문, 논설문, 기사, 연구 보고서, 블로그 포스트, 책의 한 부분 등 (가장 기본적인 '만능' 유형)
correspondence (서신/소통) : 이메일, 편지, 메모, 사내 공지 등
dialogue (대화문) : 문자 메시지, 채팅, 인터뷰, 연극 대본 등
informational (정보성 양식) : 광고, 안내문, 포스터, 일정표, 메뉴판, 영수증 등
review (리뷰/후기) : 상품 후기, 영화 평점, 식당 리뷰 등

# 추가 요청이 없을 시 글의 소재와 글의 유형은 자유롭게 선정해서 사용 단, 유형별 JSON 형식을 반드시 준수하여 생성

# 유형별 JSON 형식
{json_formats_text}

# 응답 형식 - 절대 준수해야 함
{json_template}

# 문제와 지문 생성 규칙 (필수 준수)
- **독해 문제와 지문 수 일치**: 독해 문제가 {sum(subj['count'] for subj in subject_distribution if subj['subject'] == '독해')}개 있으므로, 반드시 {sum(subj['count'] for subj in subject_distribution if subj['subject'] == '독해')}개의 지문을 passages 배열에 생성해야 함
- **독해 문제별 지문 연결**: 각 독해 문제는 반드시 question_passage_id로 지문과 연결되어야 함
- **어휘/문법 문제**: 독해가 없다면 세부영역을 고려하여 필요시 지문 생성, 독해가 있다면 독해 지문과 연계 또는 독립 문제 모두 가능

# 문제 배치 및 순서 규칙
- 지문과 연관된 문제들은 반드시 연속된 번호로 배치해야 합니다.
- 같은 지문을 사용하는 문제들은 반드시 연속 번호로 배치
- 문제 번호와 related_questions 배열이 정확히 일치해야 함
- 각 지문의 related_questions는 연속된 숫자여야 함
- 문제 총 개수와 questions 배열 길이가 일치해야 함 
- 모든 문제 번호는 1부터 총 문제 수까지 빠짐없이 존재해야 함 



# ID 참조 규칙
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
- 지문 ID: 1, 2, 3 (단순한 숫자, integer)
- 예문 ID: 1, 2, 3 (단순한 숫자, integer)
- 문제 ID: 1, 2, 3 (단순한 숫자, integer)

**정답 형식 규칙:**
- 객관식 정답은 question_choices 배열의 인덱스 값 + 1(integer)으로 표시 (1, 2, 3, 4, 5), 절대 문자열 형식으로 표시하지 마세요
- 단답형, 서술형 정답은 반드시 텍스트로 표시

## 최종 검증 체크리스트 (응답 전 필수 확인!)
응답하기 전에 반드시 다음을 확인하세요:
1. example_content에 한국어 지시문이 없는가?
2. example_content에 "다음을", "~하시오" 같은 지시어가 없는가?
3. question_text에 영어 문장이 없는가?
4. question_text와 example_content가 명확히 분리되어 있는가?
5. 각 example_content는 순수한 영어 예문만 포함하는가?

** 주의: 위 체크리스트를 위반하면 전체 문제지가 사용 불가능해집니다!**

**최종 강조사항:**
- 위의 JSON 형식을 정확히 따라 유효한 JSON만 응답해주세요
- 추가 설명이나 텍스트는 절대 포함하지 마세요
- 추가적인 항목을 만들지 마세요
- question_text에는 어떤 형태의 ID도 포함하지 마세요!"""
        
        # 생성된 프롬프트 로그 출력
        print("\n" + "="*80)
        print("📝 생성된 프롬프트 (원문 그대로)")
        print("="*80)
        print(prompt)
        print("="*80)
        print(f"📊 프롬프트 길이: {len(prompt)} 문자")
        print("="*80 + "\n")
        
        return prompt
    
    def _get_text_type_formats(self, db: Session) -> str:
        """DB에서 텍스트 유형 형식을 가져옵니다."""
        try:
            from app.models import TextType
            text_types = db.query(TextType).all()
            
            if text_types:
                formats = []
                for text_type in text_types:
                    formats.append(f"{text_type.type_name} ({text_type.description}) : {text_type.json_format}")
                return "\n".join(formats)
            else:
                return self._get_default_text_formats()
        except Exception as e:
            print(f"DB에서 텍스트 유형 조회 오류: {e}")
            return self._get_default_text_formats()
    
    def _get_default_text_formats(self) -> str:
        """기본 텍스트 형식을 반환합니다."""
        return """article (일반 글) : content: title, paragraph로 구성된 배열
correspondence (서신/소통) : metadata: sender, recipient, subject, date 등, content: paragraph
dialogue (대화문) : metadata: participants 배열, content: { speaker: '이름', line: '대사' } 객체의 배열
informational (정보성 양식) : content: title, paragraph, list, 그리고 key_value 쌍 (예: { key: '장소', value: '시청 앞' })
review (리뷰/후기) : metadata: rating (별점), product_name 등"""
    
    def _generate_subject_types_lines(self, subject_distribution: List[Dict], subject_details: Dict, db: Session = None) -> List[str]:
        """영역별 출제 유형 문자열을 DB에서 조회하여 생성합니다."""
        subject_types_lines = []

        for subj in subject_distribution:
            subject_name = subj['subject']
            types_str = ""

            try:
                if subject_name == '독해' and db:
                    # DB에서 reading_types 조회
                    from app.models.content import ReadingType
                    reading_ids = subject_details.get('reading_types', [])
                    if reading_ids:
                        reading_types = db.query(ReadingType).filter(ReadingType.id.in_(reading_ids)).all()
                        types_list = [f"{rt.name} : {rt.description}" for rt in reading_types]
                        types_str = "\n".join([f"  {t}" for t in types_list])
                    else:
                        types_str = "  주제/제목/요지 추론, 세부 정보 파악, 내용 일치/불일치, 빈칸 추론 등"

                elif subject_name == '어휘' and db:
                    # DB에서 vocabulary_categories 조회
                    from app.models.vocabulary import VocabularyCategory
                    vocab_ids = subject_details.get('vocabulary_categories', [])
                    if vocab_ids:
                        vocab_categories = db.query(VocabularyCategory).filter(VocabularyCategory.id.in_(vocab_ids)).all()
                        types_list = [f"{vc.name} : {vc.learning_objective}" for vc in vocab_categories]
                        types_str = "\n".join([f"  {t}" for t in types_list])
                    else:
                        types_str = "  개인 및 주변 생활 어휘, 사회 및 공공 주제 어휘, 추상적 개념 및 감정 등"

                elif subject_name == '문법' and db:
                    # DB에서 grammar_categories로 해당 grammar_topics 조회
                    from app.models.grammar import GrammarCategory, GrammarTopic

                    category_ids = subject_details.get('grammar_categories', [])
                    types_list = []

                    if category_ids:
                        categories = db.query(GrammarCategory).filter(GrammarCategory.id.in_(category_ids)).all()
                        for category in categories:
                            types_list.append(f"▶ {category.name}")

                            # 해당 카테고리의 모든 토픽들 조회
                            category_topics = db.query(GrammarTopic).filter(
                                GrammarTopic.category_id == category.id
                            ).all()

                            for topic in category_topics:
                                types_list.append(f"  • {topic.name} : {topic.learning_objective}")

                    if types_list:
                        types_str = "\n".join(types_list)
                    else:
                        types_str = "  ▶ 문장의 기초\n  • 영어의 8품사, 문장의 5요소, 문장의 5형식\n  ▶ 동사와 시제\n  • be동사, 일반동사, 현재완료시제 등"

                else:
                    # DB 없거나 기타 경우 기본값
                    if subject_name == '독해':
                        types_str = "  주제/제목/요지 추론, 세부 정보 파악, 내용 일치/불일치, 빈칸 추론 등"
                    elif subject_name == '어휘':
                        types_str = "  개인 및 주변 생활 어휘, 사회 및 공공 주제 어휘, 추상적 개념 및 감정 등"
                    elif subject_name == '문법':
                        types_str = "  ▶ 문장의 기초\n  • 영어의 8품사, 문장의 5요소, 문장의 5형식\n  ▶ 동사와 시제\n  • be동사, 일반동사, 현재완료시제 등"
                    else:
                        types_str = "  기본 유형"

            except Exception as e:
                print(f"DB 조회 오류 ({subject_name}): {e}")
                # 오류 시 기본값
                if subject_name == '독해':
                    types_str = "  주제/제목/요지 추론, 세부 정보 파악, 내용 일치/불일치, 빈칸 추론 등"
                elif subject_name == '어휘':
                    types_str = "  개인 및 주변 생활 어휘, 사회 및 공공 주제 어휘, 추상적 개념 및 감정 등"
                elif subject_name == '문법':
                    types_str = "  ▶ 문장의 기초\n  • 영어의 8품사, 문장의 5요소, 문장의 5형식\n  ▶ 동사와 시제\n  • be동사, 일반동사, 현재완료시제 등"

            subject_types_lines.append(f"- {subject_name} :\n{types_str}")

        return subject_types_lines
    
    def _get_vocabulary_list(self, db: Session, difficulty_distribution: List[Dict]) -> str:
        """어휘 목록을 생성합니다."""
        if db is not None:
            try:
                return self.extract_vocabulary_by_difficulty(
                    db, 
                    difficulty_distribution, 
                    total_words=50
                )
            except Exception as e:
                print(f"단어 추출 실패, 기본 메시지 사용: {str(e)}")
        
        return "-- 단어목록 : 중학교 1학년 수준에 맞는 기본 및 중급 영어 단어들을 활용하여 문제를 생성하세요."
    
    
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