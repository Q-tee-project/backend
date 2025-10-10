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


# 소재 카테고리 (모든 학년 공통)
TOPIC_CATEGORIES = {
    "개인생활": [
        "취미, 오락, 여행, 운동, 쇼핑 등 여가 선용",
        "보건, 위생, 영양 등 개인 건강 관리",
        "생일, 관심사, 생활 방식 등 개인 일상"
    ],
    "가정생활": [
        "의복, 음식, 주거",
        "명절, 가족 행사, 집안일 등 가정 일상"
    ],
    "학교생활": [
        "다양한 교육 내용 및 방법, 학교 활동",
        "교우 관계, 진로, 진학 등 학교 일상"
    ],
    "사회생활": [
        "일, 노동, 직업 윤리 등 근로",
        "서신 왕래, 소셜 미디어 등 온라인 활동, 면대면 대화 등 대인 관계",
        "회의, 지역 행사, 졸업, 결혼, 장례식 등 사회적 행사"
    ],
    "문화": [
        "동일 문화권 내의 다른 세대, 성별 간의 문화적 차이",
        "우리의 문화와 생활 양식 소개",
        "우리 문화와 다른 문화의 언어⋅문화적 차이",
        "다양한 문화권의 관습, 규범, 가치, 사고방식, 행동 양식, 의사소통 방식",
        "세계 문화: 의식주, 명절과 축제, 종교, 언어, 문학, 음악, 예술, 대중문화, 여행 및 관광지, 건축물, 전통, 지리, 역사, 인물, 스포츠, 관혼상제 등",
        "다양한 문화권의 사람들과의 의사소통, 교류, 협력"
    ],
    "민주시민": [
        "공중도덕, 예절, 협력, 배려, 봉사, 정의, 책임감 등 인성",
        "인권, 양성평등, 글로벌 에티켓, 평화 등 민주시민 의식 및 세계시민 의식",
        "올바른 미디어 리터러시를 통한 비판적 사고의 성찰, 사회적 공감과 의사소통",
        "문제에 대한 비판적 사고와 민주적 의사 결정 및 갈등 해결",
        "가난 및 기아 해결, 인구 문제, 청소년 문제, 고령화, 다문화 사회, 사회 정의와 불평등 해소",
        "책임 있는 소비와 생산, 자원과 에너지 문제, 국제 문제 해결을 위한 협력 등 사회 현안",
        "변화하는 사회 및 국제적 현안을 해결하기 위한 가정, 학교, 지역, 국가 및 세계 공동체의 참여"
    ],
    "생태전환": [
        "인간과 생태계의 관계, 자연환경과 생태 윤리, 생태 감수성과 책임감",
        "현재 및 미래 세대의 권리로서 환경권 존중",
        "생태계의 특성과 시스템 탐구, 생태 시스템과 인간 사회 시스템의 연관성",
        "기후변화와 생태계 문제 탐구",
        "생태전환을 위한 사회 체계의 변화 제안 및 실천",
        "생태전환을 위한 지속가능한 과학 기술 제안 및 실천",
        "일상생활에서의 생태 전환 참여와 실천"
    ],
    "디지털및인공지능": [
        "컴퓨터와 인터넷 활용, 소프트웨어의 이해와 활용 등 디지털 기술의 이해와 활용",
        "정보의 공유, 온라인 활동 참여와 협업 등 디지털 의사소통과 협력",
        "정보의 수집, 관리, 분석, 표현 등 정보의 처리와 생성",
        "디지털 기술과 정보의 안전한 사용 및 윤리적 사용"
    ],
    "일반교양": [
        "생활 안전, 교통안전, 재난 안전, 직업 안전 등의 안전",
        "동식물 또는 계절, 날씨 등의 자연 현상",
        "애국심, 평화, 안보, 독도 교육 및 통일",
        "정치, 경제, 금융, 역사, 지리, 수학, 과학, 교통, 정보 통신, 우주, 해양, 탐험 등 일반 교양",
        "인문학, 사회 과학, 자연 과학, 예술 분야 등의 학문적 소양",
        "언어, 문학, 예술 등 심미적 심성과 창의력, 상상력"
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
        """학년별 내용 깊이 가이드라인"""

        if school_level == "중학교":
            if grade in [1, 2]:
                return {
                    "vocabulary_level": "기초 어휘 (CEFR A2 수준)",
                    "sentence_structure": "단문 중심, 기본 접속사(and, but, because) 사용",
                    "abstraction": "구체적 사례와 일상 경험 중심",
                    "information_density": "단일 주제, 명확한 주제문",
                    "cognitive_level": "사실 확인, 내용 이해 중심 (Remember, Understand)",
                    "content_approach": "개인 경험, 관찰 가능한 현상, 간단한 행동 묘사"
                }
            else:  # grade 3
                return {
                    "vocabulary_level": "중급 어휘 (CEFR B1 수준)",
                    "sentence_structure": "복문 사용, 기본 관계대명사, 접속부사",
                    "abstraction": "원인-결과 관계, 비교와 대조",
                    "information_density": "2-3개 관련 아이디어 연결",
                    "cognitive_level": "이유 설명, 간단한 추론 (Apply, Analyze)",
                    "content_approach": "행동의 이유와 결과, 간단한 문제-해결 구조"
                }

        else:  # 고등학교
            if grade == 1:
                return {
                    "vocabulary_level": "중급-고급 어휘 (CEFR B1-B2)",
                    "sentence_structure": "다양한 종속절, 분사구문, 관계절",
                    "abstraction": "사회적 맥락, 다양한 관점 소개",
                    "information_density": "다층적 정보, 구체적 예시 포함",
                    "cognitive_level": "비교 분석, 타당성 평가 (Evaluate)",
                    "content_approach": "개인과 사회 연결, 현상의 배경 설명, 다양한 입장"
                }
            elif grade == 2:
                return {
                    "vocabulary_level": "고급 어휘 (CEFR B2)",
                    "sentence_structure": "복잡한 구문, 수동태, 도치, 강조",
                    "abstraction": "추상적 개념, 철학적 질문",
                    "information_density": "복합적 논점, 암시적 의미",
                    "cognitive_level": "비판적 사고, 가치 판단 (Evaluate)",
                    "content_approach": "이론과 실제 연결, 윤리적 딜레마, 대안 탐색"
                }
            else:  # grade 3
                return {
                    "vocabulary_level": "고급 어휘 (CEFR B2+, 학술 어휘 포함)",
                    "sentence_structure": "학술적 문체, 복합 구문, 가정법",
                    "abstraction": "패러다임 전환, 메타 인지적 사고",
                    "information_density": "다학제적 접근, 함축적 의미",
                    "cognitive_level": "창의적 종합, 새로운 관점 제시 (Create, Synthesize)",
                    "content_approach": "개념 간 통합, 미래 전망, 근본적 질문"
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
        """학년별 소재 가이드라인을 반환합니다."""
        if school_level == '중학교':
            if grade <= 2:
                return """
- 개인생활: 취미, 여행, 운동, 건강 등 (일상적이고 친숙한 주제)
- 가정생활: 음식, 주거, 가족 행사 등 (구체적인 경험)
- 학교생활: 교육, 학교 활동, 진로 등 (학생 주변 환경)
- 친구 관계: 우정, 놀이, 대화 등 (또래 문화)
- 동물과 자연: 반려동물, 계절, 날씨 등 (관찰 가능한 대상)

**중요**: 친숙하고 구체적인 소재 중심, 학생의 직접 경험과 관련된 내용"""
            else:  # 중3
                return """- 사회적 이슈: 환경 보호, 건강한 생활습관, 청소년 문화 등
- 대중문화: 음악, 영화, 스포츠, SNS 등
- 과학 상식: 간단한 과학 원리, 기술 발전 등
- 진로와 직업: 다양한 직업 소개, 진로 탐색 등
- 문화 다양성: 다른 나라의 문화, 전통, 생활 방식 등

**중요**: 추상적 개념이 일부 포함되지만 이해 가능한 수준, 사회적 관심사"""
        elif school_level == '고등학교':
            if grade == 1:
                return """- 사회적 이슈: 환경 문제, 사회 정의, 기술 윤리 등
- 인문학적 주제: 역사, 문화, 예술의 기본 개념
- 과학과 기술: 현대 과학 기술, 디지털 시대 등
- 심리와 관계: 인간 심리, 사회적 관계, 소통 등
- 글로벌 이슈: 국제 협력, 세계 시민의식 등

**중요**: 논리적 사고가 필요한 주제, 다양한 관점 제시"""
            else:  # 고2~고3
                return """- 철학적 주제: 가치관, 윤리, 존재와 의미 등
- 심리학: 인간 행동의 원리, 인지 과학, 사회 심리 등
- 첨단 과학: 인공지능, 생명공학, 우주과학 등
- 경제와 사회: 경제 원리, 사회 구조, 정책 등
- 예술과 문화 이론: 예술 사조, 문화 비평, 미학 등

**중요**: 전문적이고 추상적인 개념, 고차원적 사고력 요구, 복합적 관점"""
        else:
            return """- 개인생활: 취미, 여행, 운동, 건강 등
- 가정생활: 음식, 주거, 가족 행사 등
- 학교생활: 교육, 학교 활동, 진로 등
- 사회생활: 대인 관계, 직업 등
- 문화: 다른 문화권의 관습 등"""

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
        topic_guidelines = self._get_topic_guidelines(school_level, grade)

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

# Grade-Level Depth Guidelines (Strictly Follow)
- Vocabulary Level: {depth_guide['vocabulary_level']}
- Sentence Structure: {depth_guide['sentence_structure']}
- Abstraction Level: {depth_guide['abstraction']}
- Information Density: {depth_guide['information_density']}
- Cognitive Level: {depth_guide['cognitive_level']}
- Content Approach: {depth_guide['content_approach']}

# Passage Generation Guidelines

## Passage Requirements:
- Word count: {word_count_range} (strictly follow for grade level)
- CEFR level: {cefr_level} (grade baseline)
- Difficulty: Match vocabulary and sentence structure to {difficulty} (see above)
- Select appropriate passage type and optimize content/structure for question type
- Strictly follow depth guidelines above
- Mix various topics and passage types

## Topic Categories (Common for all grades - adjust depth only):
{topic_categories_str}

Important: These topics are common across all grades. Adjust complexity and abstraction according to grade-level guidelines:
- Grades 7-8 (Middle 1-2): Concrete examples, daily experiences
- Grade 9 (Middle 3): Cause-effect, compare-contrast
- Grade 10 (High 1): Social context, diverse perspectives
- Grades 11-12 (High 2-3): Abstract concepts, philosophical thinking, complex arguments

## Passage Type JSON Structures:

1. article (General text):
   Description: Expository writing, editorials, news articles, research reports, blog posts, book excerpts (most versatile type)
   Required format: passage_content must contain {{"content": [{{"type": "title", "value": "..."}}, {{"type": "paragraph", "value": "..."}}]}}

2. informational (Informational format):
   Description: Advertisements, notices, posters, schedules, menus, receipts
   Required format: passage_content must contain {{"content": [{{"type": "title"}}, {{"type": "paragraph"}}, {{"type": "list", "items": [...]}}, {{"type": "key_value", "pairs": [...]}}]}}

3. dialogue (Conversation):
   Description: Text messages, chat, interviews, play scripts
   Required format: passage_content must contain {{"metadata": {{"participants": [...]}}, "content": [{{"speaker": "...", "line": "..."}}]}}

4. correspondence (Letters/Communication):
   Description: Emails, letters, memos, internal notices
   Required format: passage_content must contain {{"metadata": {{"sender": "...", "recipient": "...", "subject": "...", "date": "..."}}, "content": [{{"type": "paragraph", "value": "..."}}]}}

5. review (Reviews/Feedback):
   Description: Product reviews, movie ratings, restaurant reviews
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
        "correct_answer": answer_index (multiple choice) | "answer text" (short answer),
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

# Grade-Level Depth Guidelines (Strictly Follow)
- Vocabulary Level: {depth_guide['vocabulary_level']}
- Sentence Structure: {depth_guide['sentence_structure']}
- Abstraction Level: {depth_guide['abstraction']}
- Information Density: {depth_guide['information_density']}
- Cognitive Level: {depth_guide['cognitive_level']}
- Content Approach: {depth_guide['content_approach']}

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
    "correct_answer": answer_index (multiple choice) | "answer text" (short answer),
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