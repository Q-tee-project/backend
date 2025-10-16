"""
학년별 가이드라인 (단어 수, CEFR 레벨, 깊이, 주제)
"""
from typing import Dict

class GradeGuidelines:
    """학년별 설정 가이드라인을 제공하는 클래스"""

    @staticmethod
    def get_word_count_range(school_level: str, grade: int) -> str:
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

    @staticmethod
    def get_cefr_level(school_level: str, grade: int) -> str:
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

    @staticmethod
    def get_depth_guidelines(school_level: str, grade: int) -> Dict[str, str]:
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

    @staticmethod
    def get_topic_guidelines(school_level: str, grade: int) -> str:
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
