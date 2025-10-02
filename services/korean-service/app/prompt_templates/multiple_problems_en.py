"""
English-based multiple problems generation template
"""

from typing import Dict, List
from .base_template_en import EnglishKoreanPromptTemplate


class MultipleProblemEnglishTemplate(EnglishKoreanPromptTemplate):
    """Multiple problem generation with English instructions, Korean output"""

    def generate_prompt(self, source_text: str, source_info: Dict, korean_type: str,
                       count: int, question_types: List[str], difficulties: List[str],
                       user_prompt: str, korean_data: Dict) -> str:
        """Generate enhanced English prompt for multiple Korean problems"""

        # System instruction
        prompt = self.get_system_instruction(korean_type)
        prompt += "\n\n"

        # Problem specifications
        prompt += self.get_base_requirements(korean_data, difficulties[0] if difficulties else '중', user_prompt)

        # Source text presentation
        if korean_type == '문법':
            prompt += f"""
**Reference Material:**
This is reference material about Korean grammar concepts. DO NOT reference it directly in your questions.
Use it as background knowledge to create standalone grammar problems with NEW examples.

```
{source_text[:3000]}  # Limit to prevent token overflow
```

**IMPORTANT:** Create independent grammar questions. If you need example sentences, create NEW ones.
"""
        else:
            prompt += f"""
**Source Text for Problems:**
Title: {source_info.get('title', 'Untitled')}
Author: {source_info.get('author', 'Unknown')}

```korean
{source_text}
```

**ALL {count} PROBLEMS MUST BE BASED ON THIS TEXT.**
"""

        # Problem requirements breakdown
        prompt += f"\n**Problem Set Requirements:**\n"
        prompt += f"Generate exactly {count} multiple-choice problems based on the text above.\n\n"

        prompt += "**Individual Problem Specifications:**\n"
        for i, (q_type, difficulty) in enumerate(zip(question_types, difficulties)):
            diff_info = self.difficulty_levels.get(difficulty, self.difficulty_levels['중'])
            prompt += f"- Problem {i+1}: {diff_info['en']} level - {diff_info['description']}\n"

        prompt += "\n"

        # Type-specific guidelines
        if korean_type == '시':
            prompt += self.get_poetry_guidelines()
        elif korean_type == '소설':
            prompt += self.get_novel_guidelines()
        elif korean_type == '수필/비문학':
            prompt += self.get_nonfiction_guidelines()
        elif korean_type == '문법':
            prompt += self.get_grammar_guidelines()

        # Output format for multiple problems
        prompt += self._get_multiple_output_format(count, source_info, korean_type)

        # Quality checklist
        prompt += self.get_quality_checklist()

        return prompt

    def _get_multiple_output_format(self, count: int, source_info: Dict, korean_type: str) -> str:
        """Output format for multiple problems"""

        example = self._get_example_question(korean_type)

        return f"""

**REQUIRED JSON OUTPUT FORMAT:**

```json
{{
    "problems": [
        {{
            "question": "문제 1 내용 (in Korean)",
            "choices": [
                "선택지 1 (in Korean)",
                "선택지 2 (in Korean)",
                "선택지 3 (in Korean)",
                "선택지 4 (in Korean)"
            ],
            "correct_answer": "A",
            "explanation": "해설 1 (in Korean)"
        }},
        {{
            "question": "문제 2 내용 (in Korean)",
            "choices": [
                "선택지 1 (in Korean)",
                "선택지 2 (in Korean)",
                "선택지 3 (in Korean)",
                "선택지 4 (in Korean)"
            ],
            "correct_answer": "B",
            "explanation": "해설 2 (in Korean)"
        }}
        // ... continue for all {count} problems
    ]
}}
```

**CRITICAL REQUIREMENTS:**
1. Output ONLY valid JSON - no markdown, no explanatory text
2. Create EXACTLY {count} problems
3. ALL content (questions, choices, explanations) MUST be in KOREAN
4. Each problem must have exactly 4 distinct choices
5. correct_answer must be "A", "B", "C", or "D" (corresponding to choice position)
6. All problems must relate to the provided text (except grammar - create new examples)
7. Problems should progressively test different aspects of the text
8. Ensure variety - don't ask similar questions repeatedly

**Problem Variety Guidelines:**
- Don't repeat the same question type (e.g., multiple "main idea" questions)
- Cover different parts of the text across problems
- Balance between literal comprehension and analytical thinking
- Each problem should offer unique insight into the text

**Answer Distribution:**
- Vary the correct answer position (don't make all answers "A" or follow a pattern)
- Natural distribution across A, B, C, D

**Explanation Quality:**
- Cite specific evidence from the text (e.g., "2문단에서...", "화자의 '...' 표현에서...")
- Explain WHY the correct answer is right
- Briefly explain WHY wrong answers are incorrect (when helpful)
- Keep explanations concise but thorough (2-4 sentences)
"""
