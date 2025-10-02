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
                prompt = f"""당신은 영어 교육 전문가입니다.

{school_level} {grade}학년 학생을 위한 독해 문제 1개를 **지문과 함께** 생성해주세요.

# 문제 정보
- 문제 번호: {qid}
- 영역: {subject}
- 난이도: {difficulty}
  - **난이도는 {school_level} {grade}학년 수준 내에서의 상대적 난이도입니다**
  - 하: 해당 학년에서 기본적이고 쉬운 수준
  - 중: 해당 학년에서 표준적인 수준
  - 상: 해당 학년에서 도전적이고 복잡한 수준
- 형식: {format_type}
- 지문 ID: {passage_id}
{reading_types_info}

# 출제 유형
{chr(10).join(subject_types_info)}

# 학년별 내용 깊이 가이드라인 (반드시 준수)
- **어휘 수준**: {depth_guide['vocabulary_level']}
- **문장 구조**: {depth_guide['sentence_structure']}
- **내용 추상도**: {depth_guide['abstraction']}
- **정보 밀도**: {depth_guide['information_density']}
- **인지 수준**: {depth_guide['cognitive_level']}
- **접근 방식**: {depth_guide['content_approach']}

# 지문 생성 가이드

## 지문 요구사항:
- 단어 수: {word_count_range} (학년 수준에 맞게 엄격히 준수)
- CEFR 레벨: {cefr_level} (학년 기준선)
- 난이도: {difficulty}에 맞는 어휘와 문장 구조 (위 난이도 설명 참고)
- **출제 유형, 소재를 고려하고 적합한 지문 유형을 선택하여 최적화된 내용과 구조로 작성**
- **위 깊이 가이드라인을 엄격히 준수하여 학년 수준에 맞는 내용 작성**
- **소재와 유형을 다양하게 섞어서 작성**

## 글의 소재 (모든 학년 공통 - 깊이만 조절):
{topic_categories_str}

**중요**: 위 소재는 모든 학년이 공통으로 사용하되, 학년별 깊이 가이드라인에 따라 내용의 복잡도와 추상도를 조절하세요.
- 중1-2: 구체적 사례, 일상 경험 중심
- 중3: 원인-결과, 비교-대조 중심
- 고1: 사회적 맥락, 다양한 관점 소개
- 고2-3: 추상적 개념, 철학적 사고, 복합적 논점

## 지문 유형별 JSON 구조:

**1. article (일반 글)**:
 - 설명 : 설명문, 논설문, 기사, 연구 보고서, 블로그 포스트, 책의 한 부분 등 (가장 기본적인 '만능' 유형)
반드시 passage_content안에 {{"content": [{{"type": "title", "value": "..."}}, {{"type": "paragraph", "value": "..."}}]}} 형식 사용

**2. informational (정보성 양식)**:
 - 설명 : 광고, 안내문, 포스터, 일정표, 메뉴판, 영수증 등
반드시 passage_content안에 {{"content": [{{"type": "title"}}, {{"type": "paragraph"}}, {{"type": "list", "items": [...]}}, {{"type": "key_value", "pairs": [...]}}]}} 형식 사용

**3. dialogue (대화문)**:
 - 설명 : 문자 메시지, 채팅, 인터뷰, 연극 대본 등
반드시 passage_content안에 {{"metadata": {{"participants": [...]}}, "content": [{{"speaker": "...", "line": "..."}}]}} 형식 사용

**4. correspondence (서신/소통)**:
 - 설명 : 이메일, 편지, 메모, 사내 공지 등
반드시 passage_content안에 {{"metadata": {{"sender": "...", "recipient": "...", "subject": "...", "date": "..."}}, "content": [{{"type": "paragraph", "value": "..."}}]}} 형식 사용

**5. review (리뷰/후기)**:
 - 설명 : 상품 후기, 영화 평점, 식당 리뷰 등
반드시 passage_content안에 {{"metadata": {{"rating": 4.5, "product_name": "...", "reviewer": "...", "date": "..."}}, "content": [{{"type": "paragraph", "value": "..."}}]}} 형식 사용

## 지문 작성 시 주의사항:
- passage_type: article, dialogue, correspondence, informational, review 중 선택
- passage_content: 해당 유형에 맞는 JSON 구조 사용 (반드시 passage_content와 유형 별 content를 구분해서 사용, 무조건 content 키 사용 혹은 metadata 키 사용 생략 금지)
- passage_content: 학생용 (빈칸/보기 포함 가능), **출제 유형에 최적화**
  - 빈칸: `<u>___</u>` 형식 사용
  - 밑줄: `<u>텍스트</u>` 형식 사용
  - 강조: `<strong>텍스트</strong>` 형식 사용
- original_content: passage_content와 동일한 구조의 완전한 원본 (빈칸 없음, HTML 태그 없음)
- korean_translation: passage_content와 동일한 구조의 original_content의 자연스러운 한글 번역

## 지문(passage) vs 예문(example) 구분

### 지문(passage): 독해 문제의 본문 (필수)
- **긴 글** (50단어 이상의 읽기 자료)
- article, dialogue, correspondence, informational, review 등
- JSON 구조로 작성

### 예문(example): 지문, 질문, 선택지와 별개의 추가적인 보기
- **반드시 단순 문자열** (no array, no object)
- **문제 유형에 따라 필요한 경우 추가, 필요없으면 null로 설정**
- example_content: 학생용 보기 (빈칸/보기 포함 가능), **출제 유형에 최적화**
  - 빈칸: `<u>___</u>` 형식 사용
  - 밑줄: `<u>텍스트</u>` 형식 사용
  - 강조: `<strong>텍스트</strong>` 형식 사용
- example_original_content: 완전한 원본 보기
- example_korean_translation: example_original_content의 한국어 번역

**지문 내용 중복 금지**:
- 지문에 있는 문장을 example에 다시 넣기
- 지문의 일부를 떼어서 example에 넣기

**지시문(question_text) 작성 시 주의사항**:
- 지시문은 순수한 한국어 지시문만
- 지시문은 영어 예문이나 보기, 선택지, 삽입할 문장 등을 포함하지 않음
- 부정 표현은 밑줄 표시 (ex, <u>does not</u> | ~~옳지 <u>않은</u>~~ 것을)

# 응답 형식 (JSON)
{{
    "passage": {{
        "passage_id": {passage_id},
        "passage_type": "article|dialogue|correspondence|informational|review 중 선택",
        "passage_content": {{...위 JSON 구조 참고...}},
        "original_content": {{...위 JSON 구조 참고..."}},
        "korean_translation": {{...위 JSON 구조 참고...}}
    }},
    "question": {{
        "question_id": {qid},
        "question_type": "{format_type}",
        "question_subject": "{subject}",
        "question_detail_type": "세부 유형명",
        "question_difficulty": "{difficulty}",
        "question_text": "순수한 한국어 지시문만",
        "example_content": "필요시 추가 예문 (예: 보기, 선택지, 삽입할 문장 등), 불필요하면 null",
        "example_original_content": "필요시 완전한 원본 예문, 불필요하면 null",
        "example_korean_translation": "필요시 예문 한글 번역, 불필요하면 null",
        "question_passage_id": {passage_id},
        "question_choices": ["선택지1", "선택지2", ...],
        "correct_answer": 정답인덱스(객관식) | "정답텍스트"(주관식),
        "explanation": "정답 해설 (한국어)",
        "learning_point": "핵심 학습 포인트"
    }}
}}

**중요 규칙**:
- 반드시 passage와 question을 모두 포함한 JSON 응답
- example 필드는 출제 유형에 따라 필요시 작성 (예: 문장 삽입, 빈칸에 들어갈 보기, 어법 선택 등)
- 단순한 주제/제목/내용 파악 문제는 example 필드를 null로 설정
- question_text는 "위 글의 주제로 가장 적절한 것은?" 같은 형식
- 다른 텍스트나 설명 없이 JSON만 응답
"""
            else:
                # 문법/어휘 문제 (지문 없음)
                prompt = f"""당신은 영어 교육 전문가입니다.

{school_level} {grade}학년 학생을 위한 {subject} 문제 1개를 생성해주세요.

# 문제 정보
- 문제 번호: {qid}
- 영역: {subject}
- 난이도: {difficulty}
  - **난이도는 {school_level} {grade}학년 수준 내에서의 상대적 난이도입니다**
  - 하: 해당 학년에서 기본적이고 쉬운 수준
  - 중: 해당 학년에서 표준적인 수준
  - 상: 해당 학년에서 도전적이고 복잡한 수준
- 형식: {format_type}
- CEFR 레벨: {cefr_level} (학년 기준선)

# 출제 유형
{chr(10).join(subject_types_info)}

# 학년별 내용 깊이 가이드라인 (반드시 준수)
- **어휘 수준**: {depth_guide['vocabulary_level']}
- **문장 구조**: {depth_guide['sentence_structure']}
- **내용 추상도**: {depth_guide['abstraction']}
- **정보 밀도**: {depth_guide['information_density']}
- **인지 수준**: {depth_guide['cognitive_level']}
- **접근 방식**: {depth_guide['content_approach']}

# 예문 및 선택지 작성 가이드

## 글의 소재 (모든 학년 공통 - 깊이만 조절):
{topic_categories_str}

**중요**: 위 소재는 모든 학년이 공통으로 사용하되, 학년별 깊이 가이드라인에 따라 내용의 복잡도와 추상도를 조절하세요.

## 문장 구조 및 어휘:
- CEFR {cefr_level} 수준에 맞는 문장 구조와 어휘 사용
- 예문은 {school_level} {grade}학년이 이해 가능한 길이와 복잡도로 작성
- **위 깊이 가이드라인을 엄격히 준수하여 학년 수준에 맞는 예문 작성**

### 예문(example): 지문, 질문, 선택지와 별개의 추가적인 보기
- **반드시 단순 문자열** (no array, no object)
- **문제 유형에 따라 필요한 경우 추가, 필요없으면 null로 설정**
- example_content: 학생용 보기 (빈칸/보기 포함 가능), **출제 유형에 최적화**
  - 빈칸: `<u>___</u>` 형식 사용
  - 밑줄: `<u>텍스트</u>` 형식 사용
  - 강조: `<strong>텍스트</strong>` 형식 사용
- example_original_content: 완전한 원본 보기
- example_korean_translation: example_original_content의 한국어 번역

**지시문(question_text) 작성 시 주의사항**:
- 지시문은 순수한 한국어 지시문만
- 지시문은 영어 예문이나 보기, 선택지, 삽입할 문장 등을 포함하지 않음
- 부정 표현은 밑줄 표시 (ex, <u>does not</u> | ~~옳지 <u>않은</u>~~ 것을 등)

**올바른 예시들:**
1. **빈칸 채우기**:
   ```
   example_content: "She <u>___</u> to school every day."
   example_original_content: "She goes to school every day."
   example_korean_translation: "그녀는 매일 학교에 간다."
   question_text: "다음 빈칸에 알맞은 것을 고르시오."
   question_choices: ["go", "goes", "went", "gone"]
   ```

2. **밑줄 친 부분 고르기**:
   ```
   example_content: "I have <u>seen</u> that movie before."
   example_original_content: "I have seen that movie before."
   example_korean_translation: "나는 전에 그 영화를 본 적이 있다."
   question_text: "다음 밑줄 친 부분이 문법적으로 올바른지 판단하시오."
   ```

3. **어휘 의미 파악**:
   ```
   example_content: "The book was very <u>interesting</u>."
   example_original_content: "The book was very interesting."
   example_korean_translation: "그 책은 매우 흥미로웠다."
   question_text: "다음 밑줄 친 단어의 의미로 가장 적절한 것은?"
   question_choices: ["지루한", "흥미로운", "어려운", "쉬운"]
   ```

**중요**: example은 단순 문자열만 허용 (no array, no object)

# 응답 형식 (JSON)
{{
    "question_id": {qid},
    "question_type": "{format_type}",
    "question_subject": "{subject}",
    "question_detail_type": "세부 유형명",
    "question_difficulty": "{difficulty}",
    "question_text": "순수한 한국어 지시문만",
    "example_content": "순수한 영어 예문 (필요 시)",
    "example_original_content": "완전한 원본 예문 (필요 시)",
    "example_korean_translation": "예문 한글 번역 (필요 시)",
    "question_passage_id": null,
    "question_choices": ["선택지1", "선택지2", ...],
    "correct_answer": 정답인덱스(객관식) | "정답텍스트"(주관식),
    "explanation": "정답 해설 (한국어)",
    "learning_point": "핵심 학습 포인트"
}}

**중요 규칙**:
- question_text는 순수 한국어 지시문만
- example 필드는 필요 시 작성, 불필요하면 null
- HTML 태그 사용: 빈칸 `<u>___</u>`, 밑줄 `<u>텍스트</u>`, 강조 `<strong>텍스트</strong>`
- **예문의 내용과 어휘는 반드시 {school_level} {grade}학년 수준과 위 소재 가이드에 맞춰 작성**
- 다른 텍스트나 설명 없이 JSON만 응답
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