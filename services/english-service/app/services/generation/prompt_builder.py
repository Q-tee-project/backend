"""
AI 모델용 프롬프트 생성 모듈
"""
from typing import Dict, Any
from .topics import TOPIC_CATEGORIES


class PromptBuilder:
    """프롬프트 문자열을 생성하는 클래스"""

    @staticmethod
    def format_topic_categories() -> str:
        """소재 카테고리를 프롬프트용 문자열로 변환"""
        result = []
        for category, items in TOPIC_CATEGORIES.items():
            result.append(f"\n**{category}**:")
            for item in items:
                result.append(f"  - {item}")
        return "\n".join(result)

    @staticmethod
    def build_reading_prompt(
        question_id: int,
        passage_id: int,
        subject: str,
        difficulty: str,
        format_type: str,
        school_level: str,
        grade: int,
        word_count_range: str,
        cefr_level: str,
        depth_guide: Dict[str, str],
        reading_types_info: str,
        topic_categories_str: str,
        additional_requirements: str = None
    ) -> str:
        """독해 문제 생성 프롬프트를 빌드합니다 (지문 포함)"""
        return f"""You are a Korean English education expert specializing in Korean national curriculum standards.

Generate 1 reading comprehension question WITH passage for Korean {school_level} Grade {grade} students.

# Question Information
- Question ID: {question_id}
- Subject: {subject}
- Difficulty: {difficulty}
  **IMPORTANT: Difficulty (하/중/상) is RELATIVE difficulty WITHIN {school_level} Grade {grade} level ONLY**
  - 하 (Low): Easy within Grade {grade} level
  - 중 (Medium): Standard within Grade {grade} level
  - 상 (High): Challenging within Grade {grade} level
  This means "중" (Medium) for Grade 1 should remain at Grade 1 level, NOT move up to Grade 2-3 level
- Format: {format_type}
- Passage ID: {passage_id}

# Korean Learning Objectives for Passage & Question (지문 및 문제 출제 의도)
# This section is in Korean and contains the specific learning objectives for the question to be generated.
{reading_types_info}
# Based on the objectives above, create a passage and question with appropriate content and structure.

# Grade-Level Content Guidelines (MUST STRICTLY FOLLOW)
**These guidelines are MANDATORY for {school_level} Grade {grade} level. Do NOT exceed these limits.**

- Vocabulary Level: {depth_guide['vocabulary_level']}
  **STRICTLY use only vocabulary at this level. Do NOT use words above this level.**

- Sentence Structure: {depth_guide['sentence_structure']}
  **MUST follow this sentence structure. Do NOT use more complex structures.**

- Abstraction Level: {depth_guide['abstraction']}
  **Content MUST match this abstraction level exactly.**

- Information Density: {depth_guide['information_density']}
  **STRICTLY follow this information density guideline.**

- Cognitive Level: {depth_guide['cognitive_level']}
  **Questions MUST target this cognitive level only.**

- Content Approach: {depth_guide['content_approach']}
  **MUST follow this content approach strictly.**

# Passage Generation Guidelines

## Passage Requirements:
- Word count: {word_count_range} (STRICTLY stay within this range)
- CEFR level: {cefr_level} (MUST NOT exceed this level)
- Difficulty: {difficulty} is relative to Grade {grade} level ONLY - what would be challenging/standard/easy for Grade {grade} students specifically
- Select appropriate passage type and optimize content/structure for question type
- **STRICTLY follow all depth guidelines above - these are MANDATORY limits, not suggestions**

**IMPORTANT - Passage Type Selection:**

You MUST choose an appropriate passage type based on the question type and topic. Distribute passage types naturally across questions - DO NOT use only one type.

## Passage Type Selection Guide:

Choose passage type based on content and question type:

1. **article** - For most general topics
   Best for: General knowledge, educational content, opinion pieces, explanatory texts
   Examples: "Benefits of Reading", "Climate Change Effects", "Healthy Eating Habits"
   Required format: passage_content must contain {{"content": [{{"type": "title", "value": "..."}}, {{"type": "paragraph", "value": "..."}}]}}

2. **dialogue** - For conversational contexts
   Best for: Personal interactions, interviews, casual conversations, plays
   Examples: "Planning Weekend Activities", "School Club Meeting", "Job Interview"
   Required format: passage_content must contain {{"metadata": {{"participants": [...]}}, "content": [{{"speaker": "...", "line": "..."}}]}}

3. **correspondence** - For letters and formal communication
   Best for: Emails, letters, invitations, requests, announcements
   Examples: "Invitation to School Event", "Customer Service Email", "Thank You Letter"
   Required format: passage_content must contain {{"metadata": {{"sender": "...", "recipient": "...", "subject": "...", "date": "..."}}, "content": [{{"type": "paragraph", "value": "..."}}]}}

4. **informational** - For structured information and notices
   Best for: Schedules, advertisements, menus, posters, forms, guides
   Examples: "Library Hours", "Concert Poster", "Bus Schedule", "Restaurant Menu"
   Required format: passage_content must contain {{"content": [{{"type": "title"}}, {{"type": "paragraph"}}, {{"type": "list", "items": [...]}}, {{"type": "key_value", "pairs": [...]}}]}}

5. **review** - For opinions about products/services/experiences
   Best for: Product reviews, movie reviews, restaurant reviews, book reviews
   Examples: "Headphone Review", "Movie Rating", "Restaurant Experience"
   Required format: passage_content must contain {{"metadata": {{"rating": 4.5, "product_name": "...", "reviewer": "...", "date": "..."}}, "content": [{{"type": "paragraph", "value": "..."}}]}}

## Topic Categories (Common for all grades - adjust depth only):
{topic_categories_str}

Important: These topics are common across all grades. Adjust complexity and abstraction according to grade-level guidelines:
- Grades 7-8 (Middle 1-2): Concrete examples, daily experiences
- Grade 9 (Middle 3): Cause-effect, compare-contrast
- Grade 10 (High 1): Social context, diverse perspectives
- Grades 11-12 (High 2-3): Abstract concepts, philosophical thinking, complex arguments

{f'''## Additional Requirements from Teacher:
{additional_requirements}

**Please incorporate these requirements when selecting topics and generating content.**
''' if additional_requirements else ''}
## Important Notes for Passage Writing:
- passage_type: Select the MOST APPROPRIATE type from: article, dialogue, correspondence, informational, review
- Match passage type to topic naturally (e.g., schedule information → informational, conversation → dialogue)
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
  IMPORTANT: Include ALL of the following in explanation:
  1. State the correct answer clearly (e.g., "정답은 2번입니다")
  2. Provide evidence from the passage supporting the correct answer
  3. Explain why OTHER choices are incorrect (at least briefly mention each wrong answer)
  Example: "정답은 2번입니다. 지문에서 '남편의 취미가 가족의 유대를 강하게 만들었다'고 했으므로 긍정적 영향을 미쳤습니다. 1번은 전문 요리사라는 내용이 없고, 3번은 케이크가 완벽했다고 했으므로 틀렸으며, 4번은 처음에는 불안했다고 했으므로 오답입니다."
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
        "question_id": {question_id},
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

    @staticmethod
    def build_grammar_vocabulary_prompt(
        question_id: int,
        subject: str,
        difficulty: str,
        format_type: str,
        school_level: str,
        grade: int,
        cefr_level: str,
        depth_guide: Dict[str, str],
        subject_types_info: str,
        topic_categories_str: str,
        additional_requirements: str = None
    ) -> str:
        """문법/어휘 문제 생성 프롬프트를 빌드합니다 (지문 없음)"""
        return f"""You are a Korean English education expert specializing in Korean national curriculum standards.

Generate 1 {subject} question for Korean {school_level} Grade {grade} students.

# Question Information
- Question ID: {question_id}
- Subject: {subject}
- Difficulty: {difficulty}
  **IMPORTANT: Difficulty (하/중/상) is RELATIVE difficulty WITHIN {school_level} Grade {grade} level ONLY**
  - 하 (Low): Easy within Grade {grade} level
  - 중 (Medium): Standard within Grade {grade} level
  - 상 (High): Challenging within Grade {grade} level
  This means "중" (Medium) for Grade 1 should remain at Grade 1 level, NOT move up to Grade 2-3 level
- Format: {format_type}
- CEFR level: {cefr_level} (grade baseline)

# Korean Learning Objectives (출제 의도)
# This section is in Korean and contains the specific learning objectives for the question to be generated.
{subject_types_info}

# Grade-Level Content Guidelines (MUST STRICTLY FOLLOW)
**These guidelines are MANDATORY for {school_level} Grade {grade} level. Do NOT exceed these limits.**

- Vocabulary Level: {depth_guide['vocabulary_level']}
  **STRICTLY use only vocabulary at this level. Do NOT use words above this level.**

- Sentence Structure: {depth_guide['sentence_structure']}
  **MUST follow this sentence structure. Do NOT use more complex structures.**

- Abstraction Level: {depth_guide['abstraction']}
  **Content MUST match this abstraction level exactly.**

- Information Density: {depth_guide['information_density']}
  **STRICTLY follow this information density guideline.**

- Cognitive Level: {depth_guide['cognitive_level']}
  **Questions MUST target this cognitive level only.**

- Content Approach: {depth_guide['content_approach']}
  **MUST follow this content approach strictly.**

# Example Sentence and Choices Guidelines

## Topic Categories (Common for all grades - adjust depth only):
{topic_categories_str}

Important: These topics are common across all grades. Adjust complexity and abstraction according to grade-level guidelines.

{f'''## Additional Requirements from Teacher:
{additional_requirements}

**Please incorporate these requirements when selecting topics and generating example sentences.**
''' if additional_requirements else ''}
## Sentence Structure and Vocabulary:
- **MUST use only sentence structure and vocabulary at CEFR {cefr_level} level - DO NOT exceed this level**
- Example sentences MUST be appropriate length and complexity for {school_level} Grade {grade}
- **STRICTLY follow all depth guidelines above - these are MANDATORY limits, not suggestions**

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
  IMPORTANT: For multiple choice questions, include:
  1. State the correct answer clearly (e.g., "정답은 2번입니다")
  2. Provide reasoning for the correct answer
  3. Briefly explain why other choices are incorrect when applicable
  Example: "정답은 2번입니다. 주어가 3인칭 단수 'She'이므로 동사에 -s를 붙인 'goes'가 정답입니다. 1번 'go'는 3인칭 단수 주어와 함께 쓸 수 없고, 3번 'went'는 과거형이며, 4번 'gone'은 과거분사로 단독으로 사용할 수 없습니다."
- learning_point: Write in KOREAN (Korean learning point)
  Example: "현재 시제에서 주어가 3인칭 단수일 때 동사에 -s를 붙입니다."
- example_korean_translation: Write in KOREAN (Korean translation of example)

# Response Format (JSON)
{{
    "question_id": {question_id},
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
