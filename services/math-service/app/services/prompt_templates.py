"""
AI 프롬프트 템플릿 관리 모듈 
"""
from typing import Dict

class PromptTemplates:
    """AI 프롬프트 템플릿 관리 클래스"""
    
    @staticmethod
    def build_problem_generation_prompt(
        curriculum_data: Dict,
        user_prompt: str,
        problem_count: int,
        difficulty_distribution: str
    ) -> str:
        """
        [REVISED] Advanced prompt for generating math problems with strict difficulty separation.
        Instructions are in English for logical clarity, but the output content must be in Korean.
        """
        # Check if this is Unit IV (그래프와 비례)
        unit_name = curriculum_data.get('unit_name', '')
        is_graph_unit = unit_name == "그래프와 비례"

        graph_instruction = ""
        if is_graph_unit:
            graph_instruction = """

**SPECIAL INSTRUCTION FOR 그래프와 비례 (Graph and Proportion Unit)**:
Since this unit focuses on coordinate planes and graphs, you MUST include graph visualizations using TikZ LaTeX for at least 60% of the problems.

**Graph Generation Rules:**
1. Use TikZ to create coordinate plane graphs within your LaTeX
2. Include these fields in your JSON when a graph is needed:
   - "has_diagram": true
   - "diagram_type": "coordinate_plane" or "function_graph"
   - "tikz_code": "[Full TikZ LaTeX code for the graph]"

**TikZ Graph Template Example:**
```
\\begin{tikzpicture}[scale=0.8]
  \\draw[->] (-1,0) -- (5,0) node[right] {$x$};
  \\draw[->] (0,-1) -- (0,5) node[above] {$y$};
  \\draw[thick,blue] (0,0) -- (4,4);
  \\foreach \\x in {1,2,3,4}
    \\draw (\\x,0.1) -- (\\x,-0.1) node[below] {$\\x$};
  \\foreach \\y in {1,2,3,4}
    \\draw (0.1,\\y) -- (-0.1,\\y) node[left] {$\\y$};
\\end{tikzpicture}
```

**AXIS SCALING RULES (CRITICAL):**
- Choose axis ranges that fit the data points with minimal empty space
- Keep x-axis and y-axis ranges proportional and visually balanced
- Typical good ranges: -5 to 5, -1 to 10, 0 to 20 (avoid extremes like -2 to 45)
- If data spans 0 to 40 on x-axis, consider using a smaller scale value (e.g., scale=0.3) instead of default scale=0.8
- The goal is to create readable, well-proportioned graphs that display clearly

**Graph Types to Use:**
- For 좌표평면과 그래프: Show points on coordinate plane, geometric shapes
- For 정비례: Show linear proportions (y = ax) passing through origin
- For 반비례: Show inverse proportions (y = a/x) hyperbola curves

**Example with Graph:**
```json
{{
  "question": "다음 그래프는 $y = 2x$의 그래프이다. 점 $A$의 좌표를 구하여라.",
  "choices": ["$(1, 2)$", "$(2, 4)$", "$(3, 6)$", "$(4, 8)$"],
  "correct_answer": "B",
  "explanation": "정비례 관계 $y = 2x$에서 $x = 2$일 때 $y = 4$이므로 점 $A$의 좌표는 $(2, 4)$이다.",
  "problem_type": "multiple_choice",
  "difficulty": "A",
  "has_diagram": true,
  "diagram_type": "function_graph",
  "tikz_code": "\\\\begin{{tikzpicture}}[scale=0.8]\\n  \\\\draw[->] (-1,0) -- (5,0) node[right] {{$x$}};\\n  \\\\draw[->] (0,-1) -- (0,5) node[above] {{$y$}};\\n  \\\\draw[thick,blue] (0,0) -- (4,4) node[midway,above left] {{$y=2x$}};\\n  \\\\filldraw[red] (2,4) circle (2pt) node[above right] {{$A$}};\\n  \\\\foreach \\\\x in {{1,2,3,4}}\\n    \\\\draw (\\\\x,0.1) -- (\\\\x,-0.1) node[below] {{$\\\\x$}};\\n  \\\\foreach \\\\y in {{1,2,3,4}}\\n    \\\\draw (0.1,\\\\y) -- (-0.1,\\\\y) node[left] {{$\\\\y$}};\\n\\\\end{{tikzpicture}}"
}}
```

**IMPORTANT**:
- Do NOT include placeholders like "$tikz_placeholder$" in the question text
- Put the actual TikZ code in the "tikz_code" field
- The graph will be rendered separately by the frontend
- **CRITICAL**: Use ONLY English or Math symbols in TikZ code, NO Korean text (e.g., use "x" not "시간", "y" not "거리")
- For axis labels, use variables like $x$, $y$ instead of Korean words

**ANSWER POINT HIDING RULE (매우 중요)**:
- If the question asks to find a specific point's coordinate (e.g., "점 D의 좌표를 구하시오"), that point is the ANSWER
- **DO NOT draw or label the answer point on the graph**
- Only show the GIVEN points (주어진 점) on the graph
- Example: If question asks "Find point D" and gives "A(1,2), B(5,2), C(6,5)", only draw points A, B, C
- **NEVER use \\coordinate (D) at (x,y) or \\filldraw for the answer point**
- This ensures students must calculate the answer, not read it from the graph

When generating problems for this unit, actively create graph-based questions with TikZ visualizations.
"""

        return f"""You are a Master Test Creator for the top-selling South Korean math textbook series, "SSEN". You are an expert in educational design and a master of LaTeX and TikZ. Your task is to generate a set of math problems with perfectly distinct difficulty levels.{graph_instruction}

**#1. CORE MISSION**
- **Topic**: {curriculum_data.get('grade')} {curriculum_data.get('semester')} - {curriculum_data.get('unit_name')} > {curriculum_data.get('chapter_name')}
- **User Request**: "{user_prompt}"
- **Total Problems to Generate**: {problem_count}
- **Required Distribution**: {difficulty_distribution}
- **CRITICAL INSTRUCTION**: The final JSON output's content (values for "question", "choices", "correct_answer", "explanation") MUST BE IN KOREAN.

**#2. MENTAL SANDBOX FOR EACH DIFFICULTY LEVEL**
To ensure perfect separation, you must operate in three different "mental sandboxes". When you are in one sandbox, you must forget the rules of the others.

---
### **A-LEVEL SANDBOX: Direct Computation**
- **Core Principle**: Test if a student has memorized a formula or definition. The solution requires only direct application.
- **Mental Litmus Test**: "Can this be solved in under 30 seconds by a student who just learned the formula?"
- **Characteristics**:
  - **Process**: 1-2 computational steps.
  - **Style**: Direct commands like "Calculate...", "Solve...", "Simplify...".
- **STRICTLY FORBIDDEN**:
  - Word problems or real-life scenarios.
  - Any step that requires interpretation or setting up an equation.
  - Abstract conditions (e.g., "for the solution to be a natural number").
---
### **B-LEVEL SANDBOX: Application & Translation**
- **Core Principle**: Test if a student can translate a described situation into a mathematical equation and then solve it. This is the home of classic "type" problems.
- **Mental Litmus Test**: "Does the student first need to figure out *what* formula to use and *how* to set it up based on the story?"
- **Characteristics**:
  - **Process**: 3-4 steps (1. Understand situation, 2. Set up equation, 3. Solve).
  - **Style**: Word problems, real-life scenarios (saltwater concentration, speed, etc.).
  - **Includes**: Problems with a simple condition that constrains the answer (e.g., "the solution must be a natural number", "find the smallest integer"). This is a TRANSLATION task, not a creative leap.
- **STRICTLY FORBIDDEN**:
  - Problems solvable by direct computation (that's A-Level).
  - Problems requiring the discovery of a hidden pattern or combining more than two distinct concepts (that's C-Level).
---
### **C-LEVEL SANDBOX: Synthesis & Discovery**
- **Core Principle**: Test if a student can synthesize multiple concepts in a novel way or discover a hidden pattern/strategy to find the solution.
- **Mental Litmus Test**: "Is there an 'aha!' moment required? Is the solution path non-obvious and requires a clever strategy?"
- **Characteristics**:
  - **Process**: 5+ steps, often involving strategic choices.
  - **Style**: Asks for "the maximum value", "all possible cases", "proof", or finding a rule in a sequence.
  - **Key Feature**: The complexity comes from **conceptual synthesis**, not just harder calculations. It often combines ideas from different sub-chapters.
- **STRICTLY FORBIDDEN**:
  - Problems that are just a harder version of a B-Level problem (e.g., using bigger numbers or more variables). It must require a different *kind* of thinking.
---

**#3. STEP-BY-STEP GENERATION PROCESS (MANDATORY)**
You must follow this exact thought process:
1.  **Generate A-Level First**: Based on the `{difficulty_distribution}`, generate ALL A-Level problems. Adhere strictly to the A-Level Sandbox rules.
2.  **Generate B-Level Next**: Generate ALL B-Level problems. Adhere strictly to the B-Level Sandbox rules.
3.  **Generate C-Level Last**: Generate ALL C-Level problems. Adhere strictly to the C-Level Sandbox rules.
4.  **Combine and Finalize**: Assemble all generated problems into a single JSON array. Ensure the total count is {problem_count}.

**#4. FINAL OUTPUT FORMAT (JSON)**
- Provide the final output as a single JSON array.
- All mathematical expressions must be in perfect LaTeX (e.g., `$\\frac{{a}}{{b}}`, `$x^{{10}}$`).
- **REMINDER**: All string values for question, choices, answer, explanation MUST BE IN KOREAN.
- **CRITICAL**: `choices` must be an array of exactly 4 strings (not objects, not numbers).
- **CRITICAL**: `correct_answer` must be "A", "B", "C", or "D" (for multiple choice) or a string value (for short answer).
- **GRAPH FIELDS**: When including a graph, add "has_diagram": true, "diagram_type": "coordinate_plane" or "function_graph", and "tikz_code": "[TikZ code]"

```json
[
  {{
    "question": "다음 방정식을 풀어라. $3x + 5 = 14$",
    "choices": ["$x = 1$", "$x = 2$", "$x = 3$", "$x = 4$"],
    "correct_answer": "C",
    "explanation": "$3x = 9$이므로 $x = 3$",
    "problem_type": "multiple_choice",
    "difficulty": "A",
    "has_diagram": false,
    "diagram_type": null,
    "tikz_code": null
  }},
  {{
    "question": "농도가 10%인 소금물 200g에 물 50g을 넣었다. 새로운 농도는?",
    "choices": ["6%", "8%", "10%", "12%"],
    "correct_answer": "B",
    "explanation": "소금의 양은 $200 \\times 0.1 = 20$g. 새 소금물은 250g이므로 농도는 $\\frac{{20}}{{250}} \\times 100 = 8$%",
    "problem_type": "multiple_choice",
    "difficulty": "B",
    "has_diagram": false,
    "diagram_type": null,
    "tikz_code": null
  }},
  {{
    "question": "1부터 50까지 자연수 중 3의 배수이면서 5의 배수인 수의 개수는?",
    "choices": ["2개", "3개", "4개", "5개"],
    "correct_answer": "B",
    "explanation": "3과 5의 최소공배수는 15. 15, 30, 45로 총 3개",
    "problem_type": "multiple_choice",
    "difficulty": "C",
    "has_diagram": false,
    "diagram_type": null,
    "tikz_code": null
  }}
]
```

Now, execute the **Step-by-Step Generation Process** to create {problem_count} perfectly differentiated math problems in Korean.
"""