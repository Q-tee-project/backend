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

# 소재 카테고리 (모든 학년 공통)
TOPIC_CATEGORIES = {
    "Personal Life": [
        "Hobbies, entertainment, travel, sports, shopping and leisure activities",
        "Health, hygiene, nutrition and personal health management",
        "Birthdays, interests, lifestyle and daily routines"
    ],
    "Family Life": [
        "Clothing, food, housing",
        "Holidays, family events, household chores and family routines"
    ],
    "School Life": [
        "Various educational content and methods, school activities",
        "Peer relationships, career planning, academic advancement and school routines"
    ],
    "Social Life": [
        "Work, labor, work ethics and employment",
        "Correspondence, social media and online activities, face-to-face communication and interpersonal relationships",
        "Meetings, community events, graduation, weddings, funerals and social occasions"
    ],
    "Culture": [
        "Cultural differences between generations and genders within the same culture",
        "Introduction to Korean culture and lifestyle",
        "Linguistic and cultural differences between Korean and other cultures",
        "Customs, norms, values, mindsets, behaviors, and communication styles of diverse cultures",
        "World cultures: food/clothing/shelter, festivals, religion, language, literature, music, arts, pop culture, travel destinations, architecture, traditions, geography, history, notable figures, sports, life ceremonies",
        "Communication, exchange, and cooperation with people from diverse cultural backgrounds"
    ],
    "Democratic Citizenship": [
        "Public morals, etiquette, cooperation, consideration, service, justice, responsibility and character development",
        "Human rights, gender equality, global etiquette, peace, democratic citizenship and global citizenship awareness",
        "Critical thinking through proper media literacy, social empathy and communication",
        "Critical thinking for problem-solving, democratic decision-making and conflict resolution",
        "Addressing poverty and hunger, population issues, youth issues, aging society, multicultural society, social justice and inequality",
        "Responsible consumption and production, resource and energy issues, cooperation for solving international problems and social issues",
        "Family, school, community, national and global community participation to address changing social and international issues"
    ],
    "Ecological Transition": [
        "Relationship between humans and ecosystems, natural environment and ecological ethics, ecological sensitivity and responsibility",
        "Respect for environmental rights as rights of current and future generations",
        "Exploring characteristics and systems of ecosystems, connections between ecological and human social systems",
        "Exploring climate change and ecosystem problems",
        "Proposing and practicing social system changes for ecological transition",
        "Proposing and practicing sustainable science and technology for ecological transition",
        "Participating and practicing ecological transition in daily life"
    ],
    "Digital and AI": [
        "Understanding and utilizing digital technology including computer and internet usage, software understanding and application",
        "Digital communication and collaboration including information sharing, online activity participation and teamwork",
        "Information processing and creation including collection, management, analysis and presentation",
        "Safe and ethical use of digital technology and information"
    ],
    "General Knowledge": [
        "Safety including daily safety, traffic safety, disaster safety, occupational safety",
        "Natural phenomena including flora/fauna, seasons, weather",
        "Patriotism, peace, security, Dokdo education and unification",
        "General knowledge including politics, economics, finance, history, geography, mathematics, science, transportation, information technology, space, ocean, exploration",
        "Academic knowledge in humanities, social sciences, natural sciences, and arts",
        "Aesthetic sensibility, creativity and imagination through language, literature and arts"
    ]
}


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

    def _get_word_count_range(self, school_level: str, grade: int) -> str:
        """학년별 지문 단어 수 범위를 반환합니다."""
        if school_level == '중학교':
            if grade <= 2:
                return "50~150단어"
            else:  # 중3
                return "200~300단어"
        elif school_level == '고등학교':
            if grade == 1:
                return "200~300단어"
            else:  # 고2~고3
                return "400단어 이상"
        else:
            return "120~150단어"  # 기본값

    def _get_cefr_level(self, school_level: str, grade: int) -> str:
        """학년별 CEFR 레벨을 반환합니다."""
        if school_level == '중학교':
            if grade <= 2:
                return "A2 ~ B1 초반"
            else:  # 중3
                return "B1"
        elif school_level == '고등학교':
            if grade == 1:
                return "B1"
            else:  # 고2~고3
                return "B2 이상"
        else:
            return "B1"  # 기본값

    def _get_depth_guidelines(self, school_level: str, grade: int) -> dict:
        """Grade-level content depth guidelines"""

        if school_level == "중학교":
            if grade in [1, 2]:
                return {
                    "vocabulary_level": "Basic vocabulary (CEFR A2 level)",
                    "sentence_structure": "Simple sentences with basic conjunctions (and, but, because)",
                    "abstraction": "Concrete examples and everyday experiences",
                    "information_density": "Single topic with clear topic sentence",
                    "cognitive_level": "Fact verification and content comprehension (Remember, Understand)",
                    "content_approach": "Personal experiences, observable phenomena, simple action descriptions"
                }
            else:  # grade 3
                return {
                    "vocabulary_level": "Intermediate vocabulary (CEFR B1 level)",
                    "sentence_structure": "Complex sentences with basic relative pronouns and conjunctive adverbs",
                    "abstraction": "Cause-effect relationships, comparison and contrast",
                    "information_density": "2-3 related ideas connected",
                    "cognitive_level": "Explanation of reasons and simple inference (Apply, Analyze)",
                    "content_approach": "Reasons and consequences of actions, simple problem-solution structure"
                }

        else:  # 고등학교
            if grade == 1:
                return {
                    "vocabulary_level": "Intermediate-advanced vocabulary (CEFR B1-B2)",
                    "sentence_structure": "Various subordinate clauses, participial phrases, relative clauses",
                    "abstraction": "Social context and diverse perspectives",
                    "information_density": "Multilayered information with concrete examples",
                    "cognitive_level": "Comparative analysis and validity evaluation (Evaluate)",
                    "content_approach": "Connection between individual and society, background explanation of phenomena, diverse positions"
                }
            elif grade == 2:
                return {
                    "vocabulary_level": "Advanced vocabulary (CEFR B2)",
                    "sentence_structure": "Complex constructions, passive voice, inversion, emphasis",
                    "abstraction": "Abstract concepts and philosophical questions",
                    "information_density": "Multiple arguments and implicit meanings",
                    "cognitive_level": "Critical thinking and value judgment (Evaluate)",
                    "content_approach": "Theory-practice connection, ethical dilemmas, exploring alternatives"
                }
            else:  # grade 3
                return {
                    "vocabulary_level": "Advanced vocabulary (CEFR B2+, including academic vocabulary)",
                    "sentence_structure": "Academic writing style, complex constructions, subjunctive mood",
                    "abstraction": "Paradigm shifts and metacognitive thinking",
                    "information_density": "Interdisciplinary approach and implicit meanings",
                    "cognitive_level": "Creative synthesis and new perspective presentation (Create, Synthesize)",
                    "content_approach": "Integration of concepts, future outlook, fundamental questions"
                }

    def _format_topic_categories(self) -> str:
        """소재 카테고리를 프롬프트용 문자열로 변환"""
        result = []
        for category, items in TOPIC_CATEGORIES.items():
            result.append(f"\n**{category}**:")
            for item in items:
                result.append(f"  - {item}")
        return "\n".join(result)

    def _get_topic_guidelines(self, school_level: str, grade: int) -> str:
        """Returns grade-level topic guidelines in English."""
        if school_level == '중학교':
            if grade <= 2:
                return """
- Personal Life: Hobbies, travel, sports, health (daily and familiar topics)
- Family Life: Food, housing, family events (concrete experiences)
- School Life: Education, school activities, career exploration (student environment)
- Friendships: Friendship, play, conversation (peer culture)
- Animals and Nature: Pets, seasons, weather (observable subjects)

Important: Focus on familiar and concrete topics related to students' direct experiences"""
            else:  # 중3
                return """
- Social Issues: Environmental protection, healthy lifestyle, youth culture
- Popular Culture: Music, movies, sports, social media
- Science Knowledge: Simple scientific principles, technological advancement
- Career and Jobs: Introduction to various occupations, career exploration
- Cultural Diversity: Cultures, traditions, and lifestyles of different countries

Important: Some abstract concepts included but at comprehensible level, topics of social interest"""
        elif school_level == '고등학교':
            if grade == 1:
                return """
- Social Issues: Environmental problems, social justice, technology ethics
- Humanities Topics: Basic concepts of history, culture, and arts
- Science and Technology: Modern science and technology, digital era
- Psychology and Relationships: Human psychology, social relationships, communication
- Global Issues: International cooperation, global citizenship

Important: Topics requiring logical thinking, presentation of diverse perspectives"""
            else:  # 고2~고3
                return """
- Philosophical Topics: Values, ethics, existence and meaning
- Psychology: Principles of human behavior, cognitive science, social psychology
- Advanced Science: Artificial intelligence, biotechnology, space science
- Economics and Society: Economic principles, social structure, policy
- Arts and Cultural Theory: Art movements, cultural criticism, aesthetics

Important: Professional and abstract concepts requiring higher-order thinking and multiple perspectives"""
        else:
            return """
- Personal Life: Hobbies, travel, sports, health
- Family Life: Food, housing, family events
- School Life: Education, school activities, career
- Social Life: Interpersonal relationships, occupations
- Culture: Customs from different cultures"""

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

        school_level = request_data.get('school_level', '중학교')
        grade = request_data.get('grade', 1)

        # 학년별 설정 가져오기
        word_count_range = self._get_word_count_range(school_level, grade)
        cefr_level = self._get_cefr_level(school_level, grade)
        # topic_guidelines = self._get_topic_guidelines(school_level, grade)  # 현재 미사용 (프롬프트에 하드코딩됨)

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
                    reading_types_info = "\n# 독해 출제 유형 (지문 작성 시 반드시 고려):\n" + "\n".join(types_list) + "\n\n위 유형에 맞는 내용과 구조를 가진 지문을 작성해야 합니다."
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
            depth_guide = self._get_depth_guidelines(school_level, grade)
            topic_categories_str = self._format_topic_categories()

            # 독해 문제는 지문 생성 포함
            if needs_passage:
                prompt = f"""You are a Korean English education expert specializing in Korean national curriculum standards.

Generate 1 reading comprehension question WITH passage for Korean {school_level} Grade {grade} students.

# Question Information
- Question ID: {qid}
- Subject: {subject}
- Difficulty: {difficulty}
  Note: Difficulty is RELATIVE to Grade {grade} level within {school_level}
  - 하 (Low): Basic and easy within this grade
  - 중 (Medium): Standard for this grade
  - 상 (High): Challenging and complex within this grade
- Format: {format_type}
- Passage ID: {passage_id}
{reading_types_info}

# Question Types
{chr(10).join(subject_types_info)}

# Grade-Level Depth Guidelines - MANDATORY REQUIREMENTS
YOU MUST STRICTLY FOLLOW these guidelines. Violation will result in rejected content.

- Vocabulary Level: {depth_guide['vocabulary_level']}
  → Use ONLY words appropriate for this level. Check every word.

- Sentence Structure: {depth_guide['sentence_structure']}
  → Match sentence complexity exactly to this specification.

- Abstraction Level: {depth_guide['abstraction']}
  → Content must match this abstraction level precisely.

- Information Density: {depth_guide['information_density']}
  → Follow this density requirement strictly.

- Cognitive Level: {depth_guide['cognitive_level']}
  → Questions must target exactly this cognitive level.

- Content Approach: {depth_guide['content_approach']}
  → Approach content following this guideline exactly.

# Passage Generation Guidelines

## Passage Requirements:
- Word count: {word_count_range} (strictly follow for grade level)
- CEFR level: {cefr_level} (grade baseline)
- Difficulty: Match vocabulary and sentence structure to {difficulty} (see above)
- Select appropriate passage type and optimize content/structure for question type
- Strictly follow depth guidelines above

**IMPORTANT - Variety Requirement:**
- Vary passage GENRE/TYPE across questions (articles, stories, letters, advertisements, reviews, dialogues, etc.)
- Vary TOPICS across questions using the topic categories below
- Consider the topic categories and select diverse subjects for each passage

## Topic Categories (Common for all grades - adjust depth only):
{topic_categories_str}

Important: These topics are common across all grades. Adjust complexity and abstraction according to grade-level guidelines:
- Grades 7-8 (Middle 1-2): Concrete examples, daily experiences
- Grade 9 (Middle 3): Cause-effect, compare-contrast
- Grade 10 (High 1): Social context, diverse perspectives
- Grades 11-12 (High 2-3): Abstract concepts, philosophical thinking, complex arguments

## Passage Type JSON Structures:

1. article (General text):
   Description: Expository writing, editorials, news articles, research reports, blog posts, book excerpts, etc. (most versatile type)
   Required format: passage_content must contain {{"content": [{{"type": "title", "value": "..."}}, {{"type": "paragraph", "value": "..."}}]}}

2. informational (Informational format):
   Description: Advertisements, notices, posters, schedules, menus, receipts, etc.
   Required format: passage_content must contain {{"content": [{{"type": "title"}}, {{"type": "paragraph"}}, {{"type": "list", "items": [...]}}, {{"type": "key_value", "pairs": [...]}}]}}

3. dialogue (Conversation):
   Description: Text messages, chat, interviews, play scripts, etc.
   Required format: passage_content must contain {{"metadata": {{"participants": [...]}}, "content": [{{"speaker": "...", "line": "..."}}]}}

4. correspondence (Letters/Communication):
   Description: Emails, letters, memos, internal notices, etc.
   Required format: passage_content must contain {{"metadata": {{"sender": "...", "recipient": "...", "subject": "...", "date": "..."}}, "content": [{{"type": "paragraph", "value": "..."}}]}}

5. review (Reviews/Feedback):
   Description: Product reviews, movie ratings, restaurant reviews, etc.
   Required format: passage_content must contain {{"metadata": {{"rating": 4.5, "product_name": "...", "reviewer": "...", "date": "..."}}, "content": [{{"type": "paragraph", "value": "..."}}]}}

## Important Notes for Passage Writing:
- passage_type: Choose one from: article, dialogue, correspondence, informational, review
- passage_content: Use JSON structure matching the type (must distinguish between passage_content and type-specific content, never omit content key or metadata key)
- passage_content: For students (may include blanks/underlines), optimized for question type
  - Blank: Use `<u>___</u>` format
  - Underline: Use `<u>text</u>` format
  - Emphasis: Use `<strong>text</strong>` format
- original_content: Complete original with same structure as passage_content (no blanks, no HTML tags)
- korean_translation: Natural Korean translation of original_content with same structure

## Passage vs Example Distinction

### Passage: Main reading material for comprehension (Required)
- Long text (50+ words of reading material)
- Types: article, dialogue, correspondence, informational, review
- Written in JSON structure

### Example: Additional reference separate from passage/question/choices
- MUST be simple string only (no array, no object)
- Add only when question type requires it, otherwise set to null
- example_content: For students (may include blanks/underlines), optimized for question type
  - Blank: Use `<u>___</u>` format
  - Underline: Use `<u>text</u>` format
  - Emphasis: Use `<strong>text</strong>` format
- example_original_content: Complete original version
- example_korean_translation: Korean translation of example_original_content

AVOID DUPLICATION:
- Do NOT copy sentences from passage to example
- Do NOT extract parts of passage into example

IMPORTANT NOTES for question_text:
- question_text must be pure Korean instruction only
- Do NOT include English examples, choices, or sentences in question_text
- Underline negative expressions (ex: <u>does not</u> in English | <u>않은</u> in Korean)

# OUTPUT LANGUAGE REQUIREMENTS - CRITICAL

You MUST generate content in TWO languages according to these strict rules:

ENGLISH Content (Student reading material):
- passage_content: Write in ENGLISH
- example_content: Write in ENGLISH (if needed)
- question_choices: Write in ENGLISH

KOREAN Content (Instructions and explanations):
- question_text: Write in KOREAN (Korean instruction for students)
  Example: "위 글의 주제로 가장 적절한 것은?"
- question_detail_type: Write in KOREAN (Korean question type name)
  Example: "주제 파악"
- explanation: Write in KOREAN (Korean explanation)
  Example: "정답은 2번입니다. 지문에서..."
- learning_point: Write in KOREAN (Korean learning point)
  Example: "주제문은 글의 첫 문장이나 마지막 문장에 위치합니다."
- korean_translation: Write in KOREAN (Korean translation of passage)

# Response Format (JSON)
{{
    "passage": {{
        "passage_id": {passage_id},
        "passage_type": "Choose one: article, dialogue, correspondence, informational, review",
        "passage_content": {{...see JSON structure above...}},
        "original_content": {{...see JSON structure above...}},
        "korean_translation": {{...see JSON structure above...}}
    }},
    "question": {{
        "question_id": {qid},
        "question_type": "{format_type}",
        "question_subject": "{subject}",
        "question_detail_type": "Korean question type name",
        "question_difficulty": "{difficulty}",
        "question_text": "Pure Korean instruction only",
        "example_content": "English example if needed, null otherwise",
        "example_original_content": "Complete original English example if needed, null otherwise",
        "example_korean_translation": "Korean translation if example exists, null otherwise",
        "question_passage_id": {passage_id},
        "question_choices": ["Choice 1 in English", "Choice 2 in English", ...],
        "correct_answer": start with 1 (multiple choice) | "answer text" (short answer),
        "explanation": "Korean explanation",
        "learning_point": "Korean learning point"
    }}
}}

CRITICAL RULES:
- Response MUST include both passage and question in JSON
- example fields: Write only when question type requires (e.g. sentence insertion, fill-in-the-blank options)
- Simple topic/title/content questions: Set example fields to null
- question_text format: Must be in Korean like "위 글의 주제로 가장 적절한 것은?"
- Return ONLY JSON, no other text or explanation
"""
            else:
                # 문법/어휘 문제 (지문 없음)
                prompt = f"""You are a Korean English education expert specializing in Korean national curriculum standards.

Generate 1 {subject} question for Korean {school_level} Grade {grade} students.

# Question Information
- Question ID: {qid}
- Subject: {subject}
- Difficulty: {difficulty}
  Note: Difficulty is RELATIVE to Grade {grade} level within {school_level}
  - 하 (Low): Basic and easy within this grade
  - 중 (Medium): Standard for this grade
  - 상 (High): Challenging and complex within this grade
- Format: {format_type}
- CEFR level: {cefr_level} (grade baseline)

# Question Types
{chr(10).join(subject_types_info)}

# Grade-Level Depth Guidelines - MANDATORY REQUIREMENTS
YOU MUST STRICTLY FOLLOW these guidelines. Violation will result in rejected content.

- Vocabulary Level: {depth_guide['vocabulary_level']}
  → Use ONLY words appropriate for this level. Check every word.

- Sentence Structure: {depth_guide['sentence_structure']}
  → Match sentence complexity exactly to this specification.

- Abstraction Level: {depth_guide['abstraction']}
  → Content must match this abstraction level precisely.

- Information Density: {depth_guide['information_density']}
  → Follow this density requirement strictly.

- Cognitive Level: {depth_guide['cognitive_level']}
  → Questions must target exactly this cognitive level.

- Content Approach: {depth_guide['content_approach']}
  → Approach content following this guideline exactly.

# Example Sentence and Choices Guidelines

## Topic Categories (Common for all grades - adjust depth only):
{topic_categories_str}

Important: These topics are common across all grades. Adjust complexity and abstraction according to grade-level guidelines.

## Sentence Structure and Vocabulary:
- Use sentence structure and vocabulary matching CEFR {cefr_level} level
- Example sentences should be appropriate length and complexity for {school_level} Grade {grade}
- Strictly follow depth guidelines above for grade-appropriate examples

### Example: Additional reference separate from passage/question/choices
- MUST be simple string only (no array, no object)
- Add only when question type requires it, otherwise set to null
- example_content: For students (may include blanks/underlines), optimized for question type
  - Blank: Use `<u>___</u>` format
  - Underline: Use `<u>text</u>` format
  - Emphasis: Use `<strong>text</strong>` format
- example_original_content: Complete original version
- example_korean_translation: Korean translation of example_original_content

IMPORTANT NOTES for question_text:
- question_text must be pure Korean instruction only
- Do NOT include English examples, choices, or sentences in question_text
- Underline negative expressions (ex: <u>does not</u> in English | <u>않은</u> in Korean)

CORRECT EXAMPLES:

Example 1 - Fill in the blank:
example_content: "She <u>___</u> to school every day."
example_original_content: "She goes to school every day."
example_korean_translation: "그녀는 매일 학교에 간다."
question_text: "다음 빈칸에 알맞은 것을 고르시오."
question_choices: ["go", "goes", "went", "gone"]

Example 2 - Underlined grammar:
example_content: "I have <u>seen</u> that movie before."
example_original_content: "I have seen that movie before."
example_korean_translation: "나는 전에 그 영화를 본 적이 있다."
question_text: "다음 밑줄 친 부분이 문법적으로 올바른지 판단하시오."

Example 3 - Vocabulary meaning:
example_content: "The book was very <u>interesting</u>."
example_original_content: "The book was very interesting."
example_korean_translation: "그 책은 매우 흥미로웠다."
question_text: "다음 밑줄 친 단어의 의미로 가장 적절한 것은?"
question_choices: ["지루한", "흥미로운", "어려운", "쉬운"]

Important: example must be simple string only (no array, no object)

# OUTPUT LANGUAGE REQUIREMENTS - CRITICAL

You MUST generate content in TWO languages according to these strict rules:

ENGLISH Content (Student reading material):
- example_content: Write in ENGLISH (if needed)
- question_choices: Write in ENGLISH for grammar questions, KOREAN for vocabulary meaning questions

KOREAN Content (Instructions and explanations):
- question_text: Write in KOREAN (Korean instruction)
  Example: "다음 빈칸에 알맞은 것을 고르시오."
- question_detail_type: Write in KOREAN (Korean question type name)
  Example: "빈칸 추론"
- explanation: Write in KOREAN (Korean explanation)
  Example: "정답은 2번입니다. 주어가 3인칭 단수이므로..."
- learning_point: Write in KOREAN (Korean learning point)
  Example: "현재 시제에서 주어가 3인칭 단수일 때 동사에 -s를 붙입니다."
- example_korean_translation: Write in KOREAN (Korean translation of example)

# Response Format (JSON)
{{
    "question_id": {qid},
    "question_type": "{format_type}",
    "question_subject": "{subject}",
    "question_detail_type": "Korean question type name",
    "question_difficulty": "{difficulty}",
    "question_text": "Pure Korean instruction only",
    "example_content": "English example if needed, null otherwise",
    "example_original_content": "Complete original English example if needed, null otherwise",
    "example_korean_translation": "Korean translation if example exists, null otherwise",
    "question_passage_id": null,
    "question_choices": ["Choice 1", "Choice 2", ...],
    "correct_answer": start with 1 (multiple choice) | "answer text" (short answer | long answer),
    "explanation": "Korean explanation",
    "learning_point": "Korean learning point"
}}

CRITICAL RULES:
- question_text must be pure Korean instruction
- example fields: Write only when needed, null otherwise
- HTML tags: Blank `<u>___</u>`, Underline `<u>text</u>`, Emphasis `<strong>text</strong>`
- Example content and vocabulary must match {school_level} Grade {grade} level and topic guidelines above
- Return ONLY JSON, no other text or explanation
"""

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