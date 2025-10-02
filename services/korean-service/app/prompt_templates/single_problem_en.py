"""
English-based single problem template for Korean language problem generation
"""

from typing import Dict
from .base_template_en import EnglishKoreanPromptTemplate


class SingleProblemEnglishTemplate(EnglishKoreanPromptTemplate):
    """English-based template for single Korean problem generation"""

    def generate_prompt(self, source_text: str, korean_type: str,
                       question_type: str, difficulty: str,
                       user_prompt: str, korean_data: Dict) -> str:
        """Generate prompt for single problem creation"""

        system_instruction = self.get_system_instruction(korean_type)
        type_guidelines = self.get_type_specific_guidelines(korean_type)

        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels['중'])
        type_en = self.korean_types.get(korean_type, 'Korean Language')

        # 사용자 요구사항 추가
        user_requirements = ""
        if user_prompt and user_prompt.strip():
            user_requirements = f"\n**Special User Requirements:**\n{user_prompt}\n"

        prompt = f"""{system_instruction}

{type_guidelines}

---

## Your Task

Create **ONE (1) high-quality Korean language problem** based on the provided text.

**Problem Type:** {type_en}
**Difficulty Level:** {difficulty} ({difficulty_info['en']}) - {difficulty_info['description']}
**Question Type:** Multiple Choice (4 options)
{user_requirements}

---

## Source Text

```
{source_text}
```

---

## Output Format

Return ONLY valid JSON (no markdown, no code blocks):

{{
  "question": "<문제 질문 (Korean)>",
  "choices": ["<선택지 1 (Korean)>", "<선택지 2 (Korean)>", "<선택지 3 (Korean)>", "<선택지 4 (Korean)>"],
  "correct_answer": "<A/B/C/D>",
  "explanation": "<상세한 해설 (Korean)>",
  "difficulty": "{difficulty}",
  "source_text": "<지문 텍스트 (if applicable)>",
  "source_title": "<작품/지문 제목 (if applicable)>",
  "source_author": "<작가명 (if applicable)>"
}}

---

## Quality Checklist

Before submitting, verify:
- ✓ Question is clear and unambiguous
- ✓ All 4 choices are plausible and distinct
- ✓ Exactly ONE correct answer (no ambiguity)
- ✓ Distractors represent common misconceptions
- ✓ Explanation provides clear reasoning with textual evidence
- ✓ Appropriate difficulty level for {difficulty_info['en']} students
- ✓ ALL text content is in KOREAN language
- ✓ Professional, educational tone

Generate the problem now:
"""

        return prompt
