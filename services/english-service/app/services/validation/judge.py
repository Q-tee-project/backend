"""
AI Judge 프롬프트 생성
개별 문항의 품질을 평가하기 위한 프롬프트를 생성합니다.
"""

import json
from typing import Dict, Any


class QuestionJudge:
    """AI-as-a-Judge 프롬프트 생성기"""

    @staticmethod
    def format_question_for_evaluation(question_data: Dict[str, Any]) -> str:
        """생성된 문제를 평가용 형식으로 포맷팅"""

        # 독해 문제는 {passage: {...}, question: {...}} 구조
        # 문법/어휘는 question 정보만
        if 'question' in question_data:
            # 독해 문제
            passage = question_data.get('passage')
            question = question_data['question']
        else:
            # 문법/어휘 문제
            passage = None
            question = question_data

        # 기본 문제 정보
        formatted = f"""
## 문제 유형: {question.get('question_type', 'N/A')}
## 문제 영역: {question.get('question_subject', 'N/A')}
## 세부 유형: {question.get('question_detail_type', 'N/A')}
## 난이도: {question.get('question_difficulty', 'N/A')}

"""

        # 독해 문제인 경우 지문 포함
        if passage:
            formatted += f"""### 지문 (Passage)
{QuestionJudge._format_passage_content(passage)}

"""

        # 문법/어휘 문제인 경우 예문 포함
        if question.get('example_content'):
            formatted += f"""### 예문 (Example Sentence)
{question['example_content']}

"""
            if question.get('example_korean_translation'):
                formatted += f"""### 예문 번역 (Translation)
{question['example_korean_translation']}

"""

        # 문제 지시문
        formatted += f"""### 문제 (Question)
{question.get('question_text', 'N/A')}

"""

        # 선택지
        if question.get('question_choices'):
            formatted += "### 선택지 (Choices)\n"
            choices = question['question_choices']
            correct_answer = question.get('correct_answer')

            for idx, choice in enumerate(choices):
                # correct_answer가 인덱스인 경우
                marker = " ← 정답 (Correct Answer)" if correct_answer == idx else ""
                formatted += f"{idx + 1}. {choice}{marker}\n"
            formatted += "\n"

        # 정답 및 해설
        correct_answer = question.get('correct_answer', 'N/A')
        if isinstance(correct_answer, int) and question.get('question_choices'):
            # 인덱스를 1-based로 표시
            correct_answer = f"Option {correct_answer + 1}"

        formatted += f"""### 정답 (Correct Answer)
{correct_answer}

### 해설 (Explanation)
{question.get('explanation', 'N/A')}

### 학습 포인트 (Learning Point)
{question.get('learning_point', 'N/A')}
"""

        return formatted

    @staticmethod
    def _format_passage_content(passage: Dict[str, Any]) -> str:
        """지문 내용을 포맷팅"""
        if not passage.get('passage_content'):
            return "N/A"

        content = passage['passage_content']
        if isinstance(content, dict) and 'content' in content:
            # article, informational 등의 형식
            parts = []
            for item in content['content']:
                if item['type'] == 'paragraph':
                    parts.append(item['value'])
                elif item['type'] == 'title':
                    parts.append(f"**{item['value']}**")
            return '\n\n'.join(parts)
        elif isinstance(content, dict):
            # dialogue, correspondence, review 등 복잡한 형식
            return json.dumps(content, ensure_ascii=False, indent=2)
        else:
            return str(content)

    @staticmethod
    def create_judge_prompt(
        question_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """
        AI Judge 평가 프롬프트 생성

        Args:
            question_data: 생성된 문제 데이터
            metadata: 문제 메타데이터 (학년, 난이도, CEFR 등)

        Returns:
            평가용 프롬프트
        """

        # 학년 정보
        school_level = metadata.get('school_level', 'N/A')
        grade = metadata.get('grade', 'N/A')
        learner_level = f"{school_level} {grade}학년"

        # CEFR 레벨
        cefr_level = metadata.get('cefr_level', 'N/A')

        # 난이도
        difficulty = metadata.get('difficulty', 'N/A')

        # 문제 포맷팅
        formatted_question = QuestionJudge.format_question_for_evaluation(question_data)

        prompt = f"""You are an expert English education content evaluator for Korean students. Your task is to rigorously evaluate an AI-generated English question based on the provided context and criteria.

**[Context]**

* **Learner Level:** {learner_level}
* **Target Difficulty (CEFR):** {cefr_level}
* **Intended Difficulty:** {difficulty} (상: 도전적, 중: 표준적, 하: 기본적 - within the grade level)

**[Generated Question & Explanation]**

{formatted_question}

**[Evaluation Task]**
Evaluate the provided question and explanation using the following rubric. Provide a score for each sub-item, calculate total scores, determine a final judgment, and provide detailed rationales.

**[Evaluation Rubric]**

**A. Alignment (30 points total)**

1. **Curriculum Relevance (0-10 pts):** How well does the question align with the specified learner's grade level curriculum?
   - 10: Perfect alignment with grade-level curriculum standards
   - 7-9: Good alignment with minor issues
   - 4-6: Moderate alignment, some content may be too advanced or too simple
   - 1-3: Poor alignment, content mostly inappropriate for grade level
   - 0: Completely misaligned

2. **Difficulty Consistency (0-10 pts):** Does the question's actual difficulty match the target CEFR level and intended difficulty?
   - 10: Perfect match with target CEFR and difficulty level
   - 7-9: Good match with minor discrepancies
   - 4-6: Moderate match, noticeable difficulty mismatch
   - 1-3: Poor match, significantly easier or harder than intended
   - 0: Completely inconsistent

3. **Topic Appropriateness (0-10 pts):** Is the topic suitable and engaging for the learner's age and background?
   - 10: Highly appropriate, culturally relevant, engaging
   - 7-9: Appropriate with good relevance
   - 4-6: Somewhat appropriate but may lack relevance
   - 1-3: Questionable appropriateness or relevance
   - 0: Inappropriate or irrelevant

**B. Content & Question Quality (40 points total)**

1. **Passage Quality (0-10 pts):** Is the passage grammatically correct, natural, and logically sound?
   - 10: Flawless grammar, completely natural, perfectly logical
   - 7-9: Minor errors, mostly natural, logical
   - 4-6: Several errors, somewhat awkward, some logical issues
   - 1-3: Major errors, very awkward, illogical
   - 0: Severely flawed

2. **Instruction Clarity (0-10 pts):** Is the question prompt clear and unambiguous?
   - 10: Perfectly clear, no ambiguity
   - 7-9: Clear with minor room for interpretation
   - 4-6: Somewhat clear but has ambiguous elements
   - 1-3: Unclear or confusing
   - 0: Completely ambiguous

3. **Answer Accuracy (0-10 pts):** Is the correct answer unique, clear, and well-supported by the passage?
   - 10: Clearly correct answer with strong support
   - 7-9: Correct answer with good support
   - 4-6: Correct but support is weak
   - 1-3: Questionable correctness or support
   - 0: Wrong answer or no support

4. **Distractor Quality (0-10 pts):** Are the incorrect options plausible enough to effectively differentiate learners?
   - 10: All distractors are plausible and effective
   - 7-9: Most distractors are good
   - 4-6: Some distractors are weak or implausible
   - 1-3: Most distractors are poor
   - 0: All distractors are obviously wrong

**C. Explanation Quality (30 points total)**

1. **Logical Explanation (0-10 pts):** Is the explanation for the correct answer logical and easy to understand?
   - 10: Perfectly logical, very clear explanation
   - 7-9: Logical with minor clarity issues
   - 4-6: Somewhat logical but unclear in parts
   - 1-3: Illogical or very unclear
   - 0: No useful explanation

2. **Incorrect Answer Analysis (0-10 pts):** Does the explanation clarify why the other options are incorrect?
   - 10: All incorrect options thoroughly explained
   - 7-9: Most incorrect options well explained
   - 4-6: Some explanation but incomplete
   - 1-3: Minimal explanation of incorrect options
   - 0: No explanation of incorrect options

3. **Additional Information (0-10 pts):** Is the supplementary information (vocabulary, syntax) accurate and helpful?
   - 10: Highly accurate and very helpful
   - 7-9: Accurate and helpful
   - 4-6: Somewhat helpful but may have minor issues
   - 1-3: Limited usefulness or some inaccuracies
   - 0: Unhelpful or inaccurate

**[Final Judgment Criteria]**
- **Total Score 85-100: Pass** - High quality, ready to use
- **Total Score 60-84: Needs Revision** - Acceptable but requires improvements
- **Total Score 0-59: Fail** - Significant issues, regeneration needed

**[Output Requirements]**
Provide your evaluation in the following FLAT JSON structure (NO nested objects):

{{
  "final_judgment": "Pass",
  "total_score": 92,
  "curriculum_relevance": 10,
  "difficulty_consistency": 9,
  "topic_appropriateness": 10,
  "alignment_total": 29,
  "alignment_rationale": "Detailed explanation...",
  "passage_quality": 9,
  "instruction_clarity": 10,
  "answer_accuracy": 10,
  "distractor_quality": 8,
  "content_quality_total": 37,
  "content_quality_rationale": "Detailed explanation...",
  "logical_explanation": 9,
  "incorrect_answer_analysis": 8,
  "additional_information": 9,
  "explanation_quality_total": 26,
  "explanation_quality_rationale": "Detailed explanation...",
  "suggestions_for_improvement": ["Suggestion 1", "Suggestion 2"]
}}

IMPORTANT:
- Use FLAT structure (all fields at top level, NO nested objects)
- total_score must equal alignment_total + content_quality_total + explanation_quality_total
- If "Needs Revision" or "Fail", provide 2-3 specific suggestions
"""

        return prompt
