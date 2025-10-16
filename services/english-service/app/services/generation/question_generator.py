"""
문제 생성을 위한 유틸리티 함수들
"""
import math
import random
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.models import Word

# 분리된 모듈에서 import
from .constants import (
    SUBJECT_MAPPING,
    DIFFICULTY_MAPPING,
    FORMAT_MAPPING,
    SCHOOL_LEVEL_MAPPING
)
from .grade_guidelines import GradeGuidelines
from .distribution import QuestionDistributionCalculator
from .prompt_builder import PromptBuilder


class PromptGenerator:
    """프롬프트 생성 오케스트레이터 클래스"""

    def __init__(self):
        self.calculator = QuestionDistributionCalculator()
        self.prompt_builder = PromptBuilder()

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

    def generate_question_prompts(
        self,
        request_data: Dict[str, Any],
        passages: List[Dict[str, Any]] = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """각 문제를 병렬 생성하기 위한 프롬프트들을 생성합니다. (독해 문제는 지문 포함)"""

        total_questions = request_data.get('total_questions', 10)
        subject_ratios = request_data.get('subject_ratios', [])
        format_ratios = request_data.get('format_ratios', [])
        difficulty_distribution = request_data.get('difficulty_distribution', [])
        subject_details = request_data.get('subject_details', {})
        additional_requirements = request_data.get('additional_requirements')

        school_level = request_data.get('school_level', '중학교')
        grade = request_data.get('grade', 1)

        # 학년별 설정 가져오기
        word_count_range = GradeGuidelines.get_word_count_range(school_level, grade)
        cefr_level = GradeGuidelines.get_cefr_level(school_level, grade)

        # 영역별 분배 계산
        subject_dist = self.calculator.calculate_distribution(total_questions, subject_ratios)
        format_dist = self.calculator.calculate_distribution(total_questions, format_ratios)
        difficulty_dist = self.calculator.calculate_distribution(total_questions, difficulty_distribution)

        print(f"📝 총 {total_questions}문제 생성 프롬프트 준비 중...")

        # 문제 배치 계획 수립
        question_plan = []
        question_id = 1
        passage_id = 1

        # 독해 문제 배치 (지문 생성 포함)
        for subj in subject_dist:
            if subj['subject'] == '독해':
                for _ in range(subj['count']):
                    question_plan.append({
                        'question_id': question_id,
                        'subject': '독해',
                        'passage_id': passage_id,
                        'needs_passage': True
                    })
                    passage_id += 1
                    question_id += 1

        # 문법 문제 배치
        for subj in subject_dist:
            if subj['subject'] == '문법':
                for _ in range(subj['count']):
                    question_plan.append({
                        'question_id': question_id,
                        'subject': '문법',
                        'passage_id': None,
                        'needs_passage': False
                    })
                    question_id += 1

        # 어휘 문제 배치
        for subj in subject_dist:
            if subj['subject'] == '어휘':
                for _ in range(subj['count']):
                    question_plan.append({
                        'question_id': question_id,
                        'subject': '어휘',
                        'passage_id': None,
                        'needs_passage': False
                    })
                    question_id += 1

        reading_count = sum(1 for p in question_plan if p['needs_passage'])
        print(f"📋 배치 계획: 독해 {reading_count}문제(지문 포함), 문법/어휘 {total_questions - reading_count}문제")

        # 독해 세부 유형 정보 가져오기
        reading_types_info = ""
        if db and subject_details.get('reading_types'):
            try:
                from app.models.content import ReadingType
                reading_ids = subject_details.get('reading_types', [])
                reading_types = db.query(ReadingType).filter(ReadingType.id.in_(reading_ids)).all()
                if reading_types:
                    types_list = [f"- **{rt.name}**: {rt.description}" for rt in reading_types]
                    reading_types_info = "\n".join(types_list)
            except Exception as e:
                print(f"독해 세부 유형 조회 오류: {e}")

        # 각 문제에 대한 프롬프트 생성
        prompts = []

        for idx, plan in enumerate(question_plan):
            qid = plan['question_id']
            subject = plan['subject']
            needs_passage = plan['needs_passage']
            passage_id = plan.get('passage_id')

            # 난이도/형식 할당 (순환)
            difficulty = difficulty_dist[idx % len(difficulty_dist)]['difficulty']
            format_type = format_dist[idx % len(format_dist)]['format']

            # 세부 유형 정보
            subject_types_info = self._generate_subject_types_lines(
                [{'subject': subject, 'count': 1, 'ratio': 100}],
                subject_details,
                db
            )

            # 깊이 가이드라인 가져오기
            depth_guide = GradeGuidelines.get_depth_guidelines(school_level, grade)
            topic_categories_str = PromptBuilder.format_topic_categories()

            # 독해 문제는 지문 생성 포함
            if needs_passage:
                prompt = PromptBuilder.build_reading_prompt(
                    question_id=qid,
                    passage_id=passage_id,
                    subject=subject,
                    difficulty=difficulty,
                    format_type=format_type,
                    school_level=school_level,
                    grade=grade,
                    word_count_range=word_count_range,
                    cefr_level=cefr_level,
                    depth_guide=depth_guide,
                    reading_types_info=reading_types_info,
                    topic_categories_str=topic_categories_str,
                    additional_requirements=additional_requirements
                )
            else:
                prompt = PromptBuilder.build_grammar_vocabulary_prompt(
                    question_id=qid,
                    subject=subject,
                    difficulty=difficulty,
                    format_type=format_type,
                    school_level=school_level,
                    grade=grade,
                    cefr_level=cefr_level,
                    depth_guide=depth_guide,
                    subject_types_info=chr(10).join(subject_types_info),
                    topic_categories_str=topic_categories_str,
                    additional_requirements=additional_requirements
                )

            prompts.append({
                'question_id': qid,
                'subject': subject,
                'difficulty': difficulty,
                'format': format_type,
                'needs_passage': needs_passage,
                'passage_id': passage_id,
                'prompt': prompt,
                'metadata': {  # AI Judge 검증에 필요한 메타데이터
                    'school_level': school_level,
                    'grade': grade,
                    'cefr_level': cefr_level,
                    'difficulty': difficulty,
                    'subject': subject,
                    'format_type': format_type
                }
            })

        print(f"✅ 문제 {len(prompts)}개에 대한 프롬프트 생성 완료 (독해 {reading_count}개는 지문 포함)")
        return prompts
