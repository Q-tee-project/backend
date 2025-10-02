"""
English-based prompt templates for Korean language problem generation
Designed with Korean language teacher perspective
"""

from typing import Dict, Optional


class EnglishKoreanPromptTemplate:
    """Enhanced English-based prompt template for Korean language problems"""

    def __init__(self):
        self.difficulty_levels = {
            '상': {
                'en': 'Advanced',
                'description': 'Requires deep analysis, inference, and complex reasoning'
            },
            '중': {
                'en': 'Intermediate',
                'description': 'Requires moderate comprehension and interpretation'
            },
            '하': {
                'en': 'Basic',
                'description': 'Requires surface-level comprehension and recall'
            }
        }

        self.korean_types = {
            '시': 'Poetry',
            '소설': 'Novel/Fiction',
            '수필/비문학': 'Essay/Non-fiction',
            '문법': 'Grammar'
        }

    def get_system_instruction(self, korean_type: str) -> str:
        """System-level instruction for the AI"""
        type_en = self.korean_types.get(korean_type, 'Korean Language')

        return f"""You are an expert Korean language teacher specializing in {type_en} education for middle school students.

Your task is to create high-quality, educationally sound Korean language problems that:
1. Are pedagogically appropriate for the target grade level
2. Test genuine comprehension and critical thinking skills
3. Have one clear, unambiguous correct answer
4. Include plausible distractors that represent common misconceptions
5. Are culturally appropriate and engaging for Korean students

**CRITICAL OUTPUT REQUIREMENT:**
- You MUST write ALL content (questions, choices, explanations) in KOREAN language
- The JSON structure uses English keys, but ALL VALUES must be in Korean
- Think in Korean pedagogical context while generating content"""

    def get_base_requirements(self, korean_data: Dict, difficulty: str, user_prompt: str = "") -> str:
        """Core problem requirements"""
        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels['중'])
        korean_type_en = self.korean_types.get(korean_data.get('korean_type', '시'), 'Korean')

        requirements = f"""
**Problem Specifications:**
- School Level: Middle School
- Grade: {korean_data.get('grade', 1)}
- Subject Area: {korean_type_en} (Korean Language)
- Question Format: Multiple Choice (4 options)
- Difficulty: {difficulty_info['en']} ({difficulty_info['description']})
"""

        if user_prompt:
            requirements += f"\n**Additional Requirements from Teacher:**\n{user_prompt}\n"

        return requirements

    def get_poetry_guidelines(self) -> str:
        """Specific guidelines for poetry problems"""
        return """
**Poetry Problem Creation Guidelines:**

Focus Areas (prioritize based on difficulty):
- Basic Level (하): Literal comprehension, speaker identification, basic emotions, surface imagery
- Intermediate Level (중): Figurative language, tone, mood, thematic elements, poetic devices
- Advanced Level (상): Deep symbolic meaning, complex literary techniques, authorial intent, comparative analysis

Essential Quality Criteria:
1. The question must directly relate to the provided poem
2. Test genuine literary analysis skills, not trivial details
3. Correct answer should be definitively supported by the text
4. Wrong choices should be plausible but clearly incorrect when analyzed carefully
5. Avoid questions that can be answered without reading the poem

Common Literary Devices to Consider:
- Metaphor (은유), Personification (의인법), Simile (직유)
- Imagery (이미지), Symbolism (상징), Tone (어조)
- Rhythm (운율), Repetition (반복), Contrast (대조)

**Remember:** Write ALL content in Korean, including the question, all 4 choices, and explanation."""

    def get_novel_guidelines(self) -> str:
        """Specific guidelines for novel/fiction problems"""
        return """
**Novel/Fiction Problem Creation Guidelines:**

Focus Areas (prioritize based on difficulty):
- Basic Level (하): Plot sequence, character identification, setting, direct dialogue interpretation
- Intermediate Level (중): Character motivation, conflict analysis, narrative perspective, cause-effect
- Advanced Level (상): Thematic depth, narrative techniques, psychological complexity, symbolic interpretation

Essential Quality Criteria:
1. Question must be answerable from the provided excerpt
2. Test narrative comprehension and literary analysis
3. Focus on character psychology, plot development, or narrative technique
4. Avoid yes/no questions or questions about trivial details
5. Ensure the passage provides sufficient context

Key Elements to Examine:
- Character Psychology (인물의 심리)
- Conflict Structure (갈등 구조)
- Narrative Point of View (서술 시점)
- Plot Development (사건 전개)
- Authorial Techniques (작가의 서술 기법)

**Remember:** Write ALL content in Korean, including the question, all 4 choices, and explanation."""

    def get_nonfiction_guidelines(self) -> str:
        """Specific guidelines for essay/non-fiction problems"""
        return """
**Essay/Non-fiction Problem Creation Guidelines:**

Focus Areas (prioritize based on difficulty):
- Basic Level (하): Main idea identification, explicit information recall, basic structure
- Intermediate Level (중): Argument analysis, evidence evaluation, logical relationships, author's purpose
- Advanced Level (상): Critical evaluation, inference, application to new contexts, rhetorical analysis

Essential Quality Criteria:
1. Test reading comprehension and critical thinking
2. Focus on logical structure, argumentation, or informational content
3. Questions should require understanding, not just information spotting
4. Evaluate student's ability to analyze and synthesize information
5. Avoid questions dependent on external knowledge

Key Elements to Examine:
- Central Argument (중심 주장)
- Supporting Evidence (근거/논거)
- Logical Structure (논리 전개)
- Author's Perspective (글쓴이의 관점)
- Text Organization (글의 구조)

**Remember:** Write ALL content in Korean, including the question, all 4 choices, and explanation."""

    def get_grammar_guidelines(self) -> str:
        """Specific guidelines for grammar problems"""
        return """
**Grammar Problem Creation Guidelines:**

Focus Areas (prioritize based on difficulty):
- Basic Level (하): Basic grammar terminology, simple rules, straightforward examples
- Intermediate Level (중): Grammar rule application, sentence structure analysis, part of speech identification
- Advanced Level (상): Complex grammar concepts, exception rules, comparative analysis, linguistic reasoning

Essential Quality Criteria:
1. Test genuine grammatical understanding, not memorization
2. Provide clear, relevant examples
3. Explain grammar concepts clearly in the explanation
4. One definitively correct answer
5. Wrong choices represent common grammatical misconceptions

Key Grammar Areas:
- Phonology (음운): Sound changes, pronunciation rules
- Morphology (형태론): Word formation, parts of speech
- Syntax (통사론): Sentence structure, components
- Semantics (의미론): Meaning relationships, lexical relations

**Important for Grammar Problems:**
- You may create NEW example sentences/contexts for the problem
- Do NOT reference the source material directly (e.g., "Based on section 01...")
- Present grammar concepts as standalone questions with clear examples

**Remember:** Write ALL content in Korean, including the question, all 4 choices, and explanation."""

    def get_output_format_instruction(self, korean_type: str) -> str:
        """JSON output format with detailed instructions"""

        example_question = self._get_example_question(korean_type)

        return f"""
**REQUIRED JSON OUTPUT FORMAT:**

```json
{{
    "question": "{example_question['question']}",
    "choices": [
        "{example_question['choice1']}",
        "{example_question['choice2']}",
        "{example_question['choice3']}",
        "{example_question['choice4']}"
    ],
    "correct_answer": "A",
    "explanation": "{example_question['explanation']}"
}}
```

**CRITICAL FORMATTING RULES:**
1. Output ONLY valid JSON - no additional text before or after
2. Use double quotes for all strings
3. ALL text content MUST be in KOREAN (question, choices, explanation)
4. correct_answer must be exactly one of: "A", "B", "C", or "D"
   - A = first choice, B = second choice, C = third choice, D = fourth choice
5. Ensure all 4 choices are distinct and non-overlapping
6. Explanation should clearly justify why the correct answer is right

**Choice Writing Guidelines:**
- Correct answer: Definitively accurate, directly supported by text/grammar rules
- Wrong choices: Plausible but incorrect, representing common errors or misconceptions
- All choices should be similar in length and complexity
- Avoid "all of the above" or "none of the above" options
- Each choice should be grammatically parallel in structure"""

    def _get_example_question(self, korean_type: str) -> Dict:
        """Provide type-specific example content"""
        examples = {
            '시': {
                'question': '이 시에서 화자가 느끼는 주된 정서는 무엇인가?',
                'choice1': '그리움과 슬픔',
                'choice2': '기쁨과 환희',
                'choice3': '분노와 좌절',
                'choice4': '두려움과 불안',
                'explanation': '시의 1연과 3연에서 "먼 곳을 바라보며"와 "돌아갈 수 없는" 등의 표현을 통해 화자의 그리움과 슬픔의 정서가 드러난다.'
            },
            '소설': {
                'question': '이 장면에서 주인공의 심리 상태를 가장 잘 나타낸 것은?',
                'choice1': '불안하고 초조한 심리',
                'choice2': '평온하고 만족스러운 심리',
                'choice3': '기대에 찬 심리',
                'choice4': '무관심한 심리',
                'explanation': '주인공의 "손을 떨며"와 "계속 뒤를 돌아보는" 행동에서 불안하고 초조한 심리 상태가 나타난다.'
            },
            '수필/비문학': {
                'question': '이 글의 중심 주장은 무엇인가?',
                'choice1': '기술 발전이 인간 관계를 개선한다',
                'choice2': '기술 의존도를 줄이고 직접 소통해야 한다',
                'choice3': '기술은 인간에게 해롭다',
                'choice4': '기술 발전을 막아야 한다',
                'explanation': '글쓴이는 2문단에서 "기술 자체가 문제가 아니라 과도한 의존이 문제"라고 하며, 직접적인 소통의 중요성을 강조하고 있다.'
            },
            '문법': {
                'question': '다음 중 피동 표현이 사용된 문장은?',
                'choice1': '문이 바람에 닫혔다.',
                'choice2': '동생이 문을 닫았다.',
                'choice3': '문을 닫아야 한다.',
                'choice4': '문을 닫고 있다.',
                'explanation': '"닫혔다"는 피동 접미사 "-히-"가 붙어 피동의 의미를 나타낸다. 나머지는 모두 능동 표현이다.'
            }
        }

        return examples.get(korean_type, examples['시'])

    def get_quality_checklist(self) -> str:
        """Final quality check instructions"""
        return """
**BEFORE SUBMITTING - QUALITY CHECKLIST:**

□ Is the question clearly written in Korean?
□ Does the question test meaningful comprehension/analysis skills?
□ Is there ONE definitively correct answer?
□ Are all 4 choices written in Korean and clearly distinct?
□ Do wrong choices represent plausible misconceptions?
□ Is the explanation written in Korean and logically sound?
□ Is the difficulty level appropriate?
□ Does the question avoid trivial or trick elements?
□ Is the correct_answer value exactly "A", "B", "C", or "D"?
□ Is the JSON format valid?

**OUTPUT REMINDER:** Respond with ONLY the JSON object, no additional text."""
