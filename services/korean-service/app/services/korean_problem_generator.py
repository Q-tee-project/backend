import os
import json
import random
import time
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..prompt_templates.single_problem_en import SingleProblemEnglishTemplate
from ..prompt_templates.multiple_problems_en import MultipleProblemEnglishTemplate
from .validators.ai_judge_validator import AIJudgeValidator
from .utils.retry_handler import retry_with_backoff

# .env 파일 로드 (여러 경로 시도)
load_dotenv()  # 현재 디렉토리
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))  # backend/.env

class KoreanProblemGenerator:
    def __init__(self):
        gemini_api_key = os.getenv("KOREAN_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("KOREAN_GEMINI_API_KEY or GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

        # AI Judge Validator 초기화
        self.ai_judge_validator = AIJudgeValidator()

        # 데이터 파일 경로
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data")

        # 영어 프롬프트 템플릿 인스턴스
        self.single_template_en = SingleProblemEnglishTemplate()
        self.multiple_template_en = MultipleProblemEnglishTemplate()

    def _extract_user_specified_works(self, user_prompt: str, available_files: List[str]) -> List[str]:
        """사용자가 언급한 작품들을 추출하여 해당하는 파일들을 반환"""
        if not user_prompt:
            return []

        user_specified_files = []
        user_prompt_lower = user_prompt.lower()

        # 각 파일에 대해 사용자가 언급했는지 확인
        for file_name in available_files:
            # 파일명에서 제목과 작가 추출 (예: "나무-윤동주.txt" -> "나무", "윤동주")
            title_author = file_name.replace('.txt', '')
            if '-' in title_author:
                title, author = title_author.split('-', 1)
            else:
                title, author = title_author, ""

            # 사용자 프롬프트에서 제목이나 작가가 언급되었는지 확인
            title_mentioned = title.lower() in user_prompt_lower
            author_mentioned = author.lower() in user_prompt_lower if author else False

            # 제목-작가 형태로 언급되었는지도 확인 (예: "나무-윤동주")
            full_name_mentioned = title_author.lower() in user_prompt_lower

            if title_mentioned or author_mentioned or full_name_mentioned:
                user_specified_files.append(file_name)

        return user_specified_files

    def _preprocess_source_by_type(self, source_text: str, korean_type: str, source_info: Dict) -> str:
        """유형별 지문 전처리 - 4가지 유형에 맞게 최적화"""

        if korean_type == "시":
            return source_text[:2000] if len(source_text) > 2000 else source_text
        elif korean_type in ["소설", "수필/비문학"]:
            return self._extract_key_passage(source_text, korean_type) if len(source_text) > 1500 else source_text
        return source_text

    def _extract_key_passage(self, source_text: str, korean_type: str) -> str:
        """긴 지문에서 핵심 부분 발췌 (유형별 맞춤 영어 프롬프트 사용)"""
        try:
            # 유형별 발췌 기준 설정
            type_specific_criteria = {
                "소설": "Choose a passage with rich narrative content: character conflict, dialogue revealing personality, crucial plot development, or thematic significance. The passage should show character interactions or internal conflict.",
                "수필/비문학": "Choose a passage containing the main argument, key evidence, or central thesis. The passage should be logically complete and contain the author's main point or important supporting details.",
            }

            criteria = type_specific_criteria.get(korean_type, "Choose the most important and representative passage.")

            # 영어 프롬프트로 핵심 부분 추출 요청
            prompt = f"""You are an expert Korean literature teacher. Extract a key passage from the following {korean_type} text that is most suitable for creating comprehension questions.

**Requirements:**
- Extract 800-1200 characters (Korean characters)
- {criteria}
- The passage should be self-contained and understandable without additional context
- Preserve the exact original text (do not modify, paraphrase, or summarize)
- Include complete sentences only (start and end with complete thoughts)

**Original Text:**
```
{source_text[:3000]}
```

Return ONLY the extracted passage in Korean (no explanations, no markdown, no JSON, just the extracted text):
"""

            response = self.model.generate_content(prompt)
            extracted_text = response.text.strip()
            if len(extracted_text) < 200:
                return source_text[:1200] + "..." if len(source_text) > 1200 else source_text
            return extracted_text
        except Exception:
            return source_text[:1200] + "..." if len(source_text) > 1200 else source_text

    def _distribute_question_types(self, count: int, question_type_ratio: Dict, korean_data: Dict) -> List[str]:
        """문제 수에 맞게 문제 유형 분배 - 국어는 모두 객관식"""
        # 국어는 모든 문제를 객관식으로 생성
        return ['객관식'] * count

    def _distribute_difficulties(self, count: int, difficulty_ratio: Dict, korean_data: Dict) -> List[str]:
        """문제 수에 맞게 난이도 분배"""
        if difficulty_ratio and sum(difficulty_ratio.values()) == 100:
            difficulties = list(difficulty_ratio.keys())
            weights = list(difficulty_ratio.values())
            return random.choices(difficulties, weights=weights, k=count)
        else:
            default_difficulty = korean_data.get('difficulty', '중')
            return [default_difficulty] * count

    def _get_rendered_source_text(self, korean_type: str, source_text: str, problem_data: Dict = None) -> str:
        """유형별 렌더링할 지문 텍스트 결정"""
        if korean_type == "문법":
            if problem_data:
                llm_generated_text = problem_data.get('source_text', '')
                if llm_generated_text and llm_generated_text != source_text:
                    return llm_generated_text
            return ""
        return source_text

    def _generate_multiple_problems_from_single_text(self, source_text: str, source_info: Dict,
                                                   korean_type: str, count: int,
                                                   question_type_ratio: Dict, difficulty_ratio: Dict,
                                                   user_prompt: str, korean_data: Dict,
                                                   max_retries: int = 3) -> List[Dict]:
        """하나의 지문으로 여러 문제를 한 번에 생성 (AI Judge 재검증 로직 포함)"""

        # 문제 유형과 난이도 분포 결정
        question_types = self._distribute_question_types(count, question_type_ratio, korean_data)
        difficulties = self._distribute_difficulties(count, difficulty_ratio, korean_data)

        # 영어 템플릿을 사용하여 프롬프트 생성 (더 나은 LLM 성능)
        original_prompt = self.multiple_template_en.generate_prompt(
            source_text, source_info, korean_type, count,
            question_types, difficulties, user_prompt, korean_data
        )

        valid_problems = []  # 합격한 문제 누적
        prompt = original_prompt

        # 재시도 로직
        for attempt in range(max_retries):
            try:
                needed_count = count - len(valid_problems)
                if needed_count <= 0:
                    return valid_problems[:count]

                print(f"🔄 문제 생성 시도 {attempt + 1}/{max_retries} (현재 {len(valid_problems)}/{count}개 완료)")

                # AI 호출 및 파싱
                response = self.model.generate_content(prompt)
                problems = self._parse_and_validate_problems(
                    response.text, source_text, source_info, korean_type, needed_count, difficulties
                )

                if not problems:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    break

                # AI Judge 검증
                print(f"  📋 생성된 문제 {len(problems)}개 AI Judge 검증 시작...")
                invalid_problems = []
                for idx, problem in enumerate(problems):
                    try:
                        is_valid, scores, feedback = self.ai_judge_validator.validate_problem(problem, korean_type)
                        if is_valid:
                            valid_problems.append(problem)
                            print(f"  ✅ 문제 검증 통과 (누적: {len(valid_problems)}/{count}개)")
                        else:
                            print(f"  ❌ 문제 {idx+1} 검증 실패: {feedback}")
                            invalid_problems.append({"problem": problem, "feedback": feedback, "scores": scores})
                    except Exception as e:
                        invalid_problems.append({"problem": problem, "feedback": f"검증 오류: {str(e)}", "scores": {"overall_score": 0}})

                # 목표 달성 확인
                if len(valid_problems) >= count:
                    return valid_problems[:count]

                # 재시도
                if attempt < max_retries - 1 and invalid_problems:
                    prompt = self._rebuild_korean_prompt_with_feedback(original_prompt, invalid_problems, korean_type)
                    time.sleep(1)

            except Exception as e:
                print(f"❌ 시도 {attempt + 1} 실패: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                break

        return valid_problems if valid_problems else []

    def _parse_and_validate_problems(self, result_text: str, source_text: str,
                                     source_info: Dict, korean_type: str, count: int,
                                     difficulties: List[str]) -> List[Dict]:

        # JSON 파싱
        try:
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                json_text = result_text[json_start:json_end].strip()
            else:
                json_text = result_text.strip()

            problems_data = json.loads(json_text)

            # 문제 데이터 변환
            problems = []
            for idx, problem_data in enumerate(problems_data.get('problems', [])):
                rendered_source_text = self._get_rendered_source_text(korean_type, source_text, problem_data)
                problem = {
                    'korean_type': korean_type,
                    'question_type': '객관식',  # 국어는 모두 객관식
                    'difficulty': difficulties[idx] if idx < len(difficulties) else '중',
                    'question': problem_data.get('question', ''),
                    'correct_answer': problem_data.get('correct_answer', ''),
                    'explanation': problem_data.get('explanation', ''),
                    'source_text': rendered_source_text,
                    'source_title': source_info.get('title', ''),
                    'source_author': source_info.get('author', ''),
                    'sequence_order': idx + 1
                }

                # 객관식 선택지 추가 (국어는 항상 객관식)
                if 'choices' in problem_data:
                    problem['choices'] = problem_data['choices']

                problems.append(problem)

            return problems

        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 실패: {e}")
        except Exception as e:
            raise Exception(f"문제 생성 실패: {e}")

    def _generate_problems_individually(self, source_text: str, source_info: Dict, korean_type: str,
                                      count: int, question_type_ratio: Dict, difficulty_ratio: Dict,
                                      user_prompt: str, korean_data: Dict) -> List[Dict]:
        """폴백: 기존 방식으로 개별 문제 생성"""
        problems = []

        for i in range(count):
            try:
                # 문제 타입 결정
                question_type = self._determine_question_type(question_type_ratio, korean_data)

                # 난이도 결정
                difficulty = self._determine_difficulty(difficulty_ratio, korean_data)

                # AI를 통한 문제 생성
                problem = self._generate_single_problem(
                    source_text, korean_type, question_type, difficulty, user_prompt, korean_data
                )

                if problem:
                    problem['sequence_order'] = i + 1
                    problem['source_title'] = source_info.get('title', '')
                    problem['source_author'] = source_info.get('author', '')
                    problems.append(problem)

            except Exception:
                continue

        return problems

    def _determine_question_type(self, question_type_ratio: Dict, korean_data: Dict) -> str:
        """문제 형식 결정 - 국어는 모두 객관식"""
        # 국어는 모든 문제를 객관식으로 생성
        return '객관식'

    def _determine_difficulty(self, difficulty_ratio: Dict, korean_data: Dict) -> str:
        """난이도 결정"""
        if difficulty_ratio and sum(difficulty_ratio.values()) == 100:
            # 비율에 따른 랜덤 선택
            difficulties = list(difficulty_ratio.keys())
            weights = list(difficulty_ratio.values())
            return random.choices(difficulties, weights=weights)[0]
        else:
            return korean_data.get('difficulty', '중')

    def _generate_single_problem(self, source_text: str, korean_type: str, question_type: str,
                                difficulty: str, user_prompt: str, korean_data: Dict,
                                max_retries: int = 2) -> Dict:
        """단일 문제 생성 (재시도 로직 포함)"""

        # 영어 템플릿을 사용하여 프롬프트 생성
        prompt = self.single_template_en.generate_prompt(
            source_text, korean_type, question_type, difficulty, user_prompt, korean_data
        )

        # 재시도 로직
        for attempt in range(max_retries):
            try:
                # AI 호출
                response = self.model.generate_content(prompt)
                result_text = response.text

                # 문제 파싱 시도
                problem = self._parse_single_problem(result_text, source_text, korean_type)

                if problem:
                    return problem
                if attempt < max_retries - 1:
                    time.sleep(1)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise
        raise Exception("단일 문제 생성 실패")

    def _parse_single_problem(self, result_text: str, source_text: str, korean_type: str) -> Optional[Dict]:
        """단일 문제 JSON 파싱"""
        try:

            # JSON 파싱
            try:
                # JSON 부분만 추출
                if "```json" in result_text:
                    json_start = result_text.find("```json") + 7
                    json_end = result_text.find("```", json_start)
                    json_text = result_text[json_start:json_end].strip()
                else:
                    json_text = result_text.strip()

                problem_data = json.loads(json_text)
                rendered_source_text = self._get_rendered_source_text(korean_type, source_text, problem_data)
                problem = {
                    'korean_type': korean_type,
                    'question_type': '객관식',  # 국어는 모두 객관식
                    'difficulty': problem_data.get('difficulty', '중'),
                    'question': problem_data.get('question', ''),
                    'correct_answer': problem_data.get('correct_answer', ''),
                    'explanation': problem_data.get('explanation', ''),
                    'source_text': rendered_source_text,
                    'source_title': problem_data.get('source_title', ''),
                    'source_author': problem_data.get('source_author', '')
                }

                # 객관식 선택지 추가 (국어는 항상 객관식)
                if 'choices' in problem_data:
                    problem['choices'] = problem_data['choices']

                return problem

            except json.JSONDecodeError:
                return None
        except Exception:
            return None

    def generate_problems(self, korean_data: Dict, user_prompt: str, problem_count: int = 1,
                         korean_type_ratio: Dict = None, question_type_ratio: Dict = None,
                         difficulty_ratio: Dict = None) -> List[Dict]:
        """국어 문제 생성 - 단일 도메인 전용"""
        try:
            # 단일 유형 문제 생성 (개편된 버전)
            korean_type = korean_data.get('korean_type', '시')
            problems = self._generate_problems_by_single_domain(
                korean_data, user_prompt, problem_count, korean_type,
                question_type_ratio, difficulty_ratio
            )

            return problems[:problem_count]  # 정확한 개수로 제한

        except Exception:
            return []

    def _generate_problems_by_single_domain(self, korean_data: Dict, user_prompt: str, count: int,
                                          korean_type: str, question_type_ratio: Dict = None,
                                          difficulty_ratio: Dict = None) -> List[Dict]:
        """개편된 단일 도메인 문제 생성"""
        problems = []

        if korean_type == "문법":
            # 문법 영역은 특별 처리
            problems = self._generate_grammar_problems(
                korean_data, user_prompt, count, question_type_ratio, difficulty_ratio
            )
        else:
            # 시, 소설, 수필/비문학 처리
            source_texts_info = self._load_multiple_sources_for_single_domain(
                korean_type, user_prompt, count
            )

            if not source_texts_info:
                return []

            problems_per_work = count // len(source_texts_info)
            remaining_problems = count % len(source_texts_info)

            for i, (source_text, source_info) in enumerate(source_texts_info):
                work_problem_count = problems_per_work + (1 if i < remaining_problems else 0)
                if work_problem_count > 0:
                    if korean_type == "소설" and len(source_text) > 1000:
                        source_text = self._extract_key_passage(source_text, korean_type)
                    try:
                        work_problems = self._generate_multiple_problems_from_single_text(
                            source_text, source_info, korean_type, work_problem_count,
                            question_type_ratio, difficulty_ratio, user_prompt, korean_data
                        )
                        problems.extend(work_problems)
                    except Exception:
                        try:
                            work_problems = self._generate_problems_individually(
                                source_text, source_info, korean_type, work_problem_count,
                                question_type_ratio, difficulty_ratio, user_prompt, korean_data
                            )
                            problems.extend(work_problems)
                        except Exception:
                            continue

        return problems

    def _load_multiple_sources_for_single_domain(self, korean_type: str, user_prompt: str,
                                               problem_count: int) -> List[tuple]:
        """단일 도메인에 맞는 작품 수 선택"""
        try:
            # 문항 수에 따른 작품 수 결정
            if problem_count <= 10:
                if korean_type == "시":
                    work_count = 3
                elif korean_type == "소설":
                    work_count = 2
                elif korean_type == "수필/비문학":
                    work_count = 2
            elif problem_count <= 20:
                if korean_type == "시":
                    work_count = 6
                elif korean_type == "소설":
                    work_count = 4
                elif korean_type == "수필/비문학":
                    work_count = 4
            else:
                # 20문제 초과 시 기본값
                work_count = min(problem_count // 3, 10)

            # 해당 유형의 모든 파일 목록 가져오기
            if korean_type == "시":
                data_dir = os.path.join(self.data_path, "poem")
                all_files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
            elif korean_type == "소설":
                data_dir = os.path.join(self.data_path, "novel")
                all_files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
            elif korean_type == "수필/비문학":
                data_dir = os.path.join(self.data_path, "non-fiction")
                all_files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
            else:
                return []

            # 사용자가 특정 작품을 언급했는지 확인
            user_specified_files = self._extract_user_specified_works(user_prompt, all_files)

            if user_specified_files:
                selected_files = user_specified_files[:work_count]
            else:
                import secrets
                if len(all_files) <= work_count:
                    selected_files = all_files
                else:
                    selected_files = []
                    available_files = all_files.copy()
                    for _ in range(work_count):
                        if not available_files:
                            break
                        random_index = secrets.randbelow(len(available_files))
                        selected_files.append(available_files.pop(random_index))

            # 선택된 파일들의 내용과 정보 로드
            source_texts_info = []
            for file_name in selected_files:
                file_path = os.path.join(data_dir, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 파일명에서 제목과 작가 추출
                title_author = file_name.replace('.txt', '')
                if '-' in title_author:
                    title, author = title_author.split('-', 1)
                else:
                    title, author = title_author, "작자미상"

                source_texts_info.append((content, {
                    "title": title,
                    "author": author,
                    "file": file_name
                }))
            return source_texts_info
        except Exception:
            return []

    def _generate_grammar_problems(self, korean_data: Dict, user_prompt: str, count: int,
                                 question_type_ratio: Dict = None,
                                 difficulty_ratio: Dict = None) -> List[Dict]:
        """문법 영역 문제 생성 - I~V 영역별 분배"""
        problems = []

        try:
            # 전체 문법 내용 로드
            grammar_file_path = os.path.join(self.data_path, "grammar.txt")
            with open(grammar_file_path, 'r', encoding='utf-8') as f:
                full_grammar_content = f.read()

            grammar_sections = self._split_grammar_content(full_grammar_content)
            if not grammar_sections:
                return []

            problems_per_section = count // len(grammar_sections)
            remaining_problems = count % len(grammar_sections)
            section_names = ["I. 음운", "II. 품사와 어휘", "III. 문장", "IV. 기타", "V. 부록"]

            for i, (section_name, section_content) in enumerate(zip(section_names, grammar_sections)):
                if not section_content.strip():
                    continue
                section_problem_count = problems_per_section + (1 if i < remaining_problems else 0)
                if section_problem_count > 0:
                    try:
                        section_problems = self._generate_multiple_problems_from_single_text(
                            section_content,
                            {"title": section_name, "author": "교육부", "file": "grammar.txt"},
                            "문법", section_problem_count,
                            question_type_ratio, difficulty_ratio, user_prompt, korean_data
                        )
                        problems.extend(section_problems)
                    except Exception:
                        try:
                            section_problems = self._generate_problems_individually(
                                section_content,
                                {"title": section_name, "author": "교육부", "file": "grammar.txt"},
                                "문법", section_problem_count,
                                question_type_ratio, difficulty_ratio, user_prompt, korean_data
                            )
                            problems.extend(section_problems)
                        except Exception:
                            continue
            return problems
        except Exception:
            return []

    def _split_grammar_content(self, content: str) -> List[str]:
        """문법 내용을 I~V 영역별로 분할"""
        try:
            sections = []
            lines = content.split('\n')
            current_section = []

            section_markers = ["I. 음운", "II. 품사와 어휘", "III. 문장", "IV. 기타", "V. 부록"]
            current_section_index = -1

            for line in lines:
                # 새로운 섹션 시작 확인
                for i, marker in enumerate(section_markers):
                    if line.strip().startswith(marker):
                        # 이전 섹션 저장
                        if current_section_index >= 0 and current_section:
                            sections.append('\n'.join(current_section))

                        # 새 섹션 시작
                        current_section = [line]
                        current_section_index = i
                        break
                else:
                    # 현재 섹션에 라인 추가
                    if current_section_index >= 0:
                        current_section.append(line)

            # 마지막 섹션 저장
            if current_section_index >= 0 and current_section:
                sections.append('\n'.join(current_section))

            return sections
        except Exception:
            return []

    # ========== 병렬 처리 메서드 ==========

    def generate_problems_parallel(self, korean_data: Dict, user_prompt: str, problem_count: int,
                                   difficulty_ratio: Dict = None, max_workers: int = 5) -> List[Dict]:
        """병렬로 문제 생성"""

        korean_type = korean_data.get('korean_type', '시')
        problems = []

        if korean_type == "문법":
            # 문법은 기존 방식 사용
            return self._generate_grammar_problems(
                korean_data, user_prompt, problem_count, None, difficulty_ratio
            )

        # 시, 소설, 수필/비문학 - 병렬 처리
        source_texts_info = self._load_multiple_sources_for_single_domain(
            korean_type, user_prompt, problem_count
        )

        if not source_texts_info:
            return []

        # 각 작품별로 문제 수 분배
        problems_per_work = problem_count // len(source_texts_info)
        remaining_problems = problem_count % len(source_texts_info)

        # 병렬 작업 리스트 생성
        tasks = []
        for i, (source_text, source_info) in enumerate(source_texts_info):
            work_problem_count = problems_per_work + (1 if i < remaining_problems else 0)

            if work_problem_count > 0:
                # 유형별 지문 전처리
                processed_text = self._preprocess_source_by_type(source_text, korean_type, source_info)

                tasks.append({
                    'source_text': processed_text,
                    'source_info': source_info,
                    'count': work_problem_count,
                    'work_index': i
                })

        with ThreadPoolExecutor(max_workers=min(len(tasks), max_workers)) as executor:
            future_to_task = {}
            for task in tasks:
                future = executor.submit(
                    self._generate_problems_for_work_parallel,
                    task['source_text'],
                    task['source_info'],
                    korean_type,
                    task['count'],
                    difficulty_ratio,
                    user_prompt,
                    korean_data
                )
                future_to_task[future] = task

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    work_problems = future.result()
                    problems.extend(work_problems)
                except Exception as e:
                    print(f"❌ 작품 '{task['source_info'].get('title', 'Unknown')}' 생성 실패: {str(e)}")
        return problems[:problem_count]  # 정확한 개수로 제한

    def _generate_problems_for_work_parallel(self, source_text: str, source_info: Dict,
                                            korean_type: str, count: int,
                                            difficulty_ratio: Dict, user_prompt: str,
                                            korean_data: Dict) -> List[Dict]:
        """하나의 작품에 대해 문제를 생성 (병렬 처리용)"""
        try:
            return self._generate_multiple_problems_from_single_text(
                source_text, source_info, korean_type, count,
                None, difficulty_ratio, user_prompt, korean_data
            )
        except Exception:
            return self._generate_problems_individually(
                source_text, source_info, korean_type, count,
                None, difficulty_ratio, user_prompt, korean_data
            )

    def _rebuild_korean_prompt_with_feedback(self, original_prompt: str, invalid_problems: List[Dict], korean_type: str) -> str:
        """피드백을 포함한 국어 프롬프트 재구성"""

        feedback_text = "\n\n**IMPORTANT: Previous attempt had validation failures. Fix these issues:**\n"

        for idx, item in enumerate(invalid_problems):
            feedback_text += f"\nProblem {idx+1} feedback:\n"
            scores = item.get('scores', {})

            # 국어 유형별 점수 표시
            if korean_type == "시":
                feedback_text += f"- Scores: literary_accuracy={scores.get('literary_accuracy', 0):.1f}, "
                feedback_text += f"relevance={scores.get('relevance', 0):.1f}, "
                feedback_text += f"figurative_language_analysis={scores.get('figurative_language_analysis', 0):.1f}, "
                feedback_text += f"answer_clarity={scores.get('answer_clarity', 0):.1f}\n"
            elif korean_type == "소설":
                feedback_text += f"- Scores: narrative_comprehension={scores.get('narrative_comprehension', 0):.1f}, "
                feedback_text += f"relevance={scores.get('relevance', 0):.1f}, "
                feedback_text += f"textual_analysis={scores.get('textual_analysis', 0):.1f}, "
                feedback_text += f"answer_clarity={scores.get('answer_clarity', 0):.1f}\n"
            elif korean_type == "수필/비문학":
                feedback_text += f"- Scores: argument_comprehension={scores.get('argument_comprehension', 0):.1f}, "
                feedback_text += f"relevance={scores.get('relevance', 0):.1f}, "
                feedback_text += f"critical_thinking={scores.get('critical_thinking', 0):.1f}, "
                feedback_text += f"answer_clarity={scores.get('answer_clarity', 0):.1f}\n"
            elif korean_type == "문법":
                feedback_text += f"- Scores: grammar_accuracy={scores.get('grammar_accuracy', 0):.1f}, "
                feedback_text += f"example_quality={scores.get('example_quality', 0):.1f}, "
                feedback_text += f"explanation_clarity={scores.get('explanation_clarity', 0):.1f}, "
                feedback_text += f"answer_clarity={scores.get('answer_clarity', 0):.1f}\n"

            feedback_text += f"- Issue: {item.get('feedback', 'No feedback')}\n"

        feedback_text += "\n**MUST ensure**: All scores >= 3.5, answer_clarity >= 4.0, relevance to source text\n"

        return original_prompt + feedback_text