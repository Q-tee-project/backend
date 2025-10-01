import os
import json
import random
import time
import google.generativeai as genai
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..prompt_templates.single_problem_en import SingleProblemEnglishTemplate
from ..prompt_templates.multiple_problems_en import MultipleProblemEnglishTemplate

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

        # OpenAI 클라이언트 초기화 (AI Judge용)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("⚠️ Warning: OPENAI_API_KEY not found. AI Judge validation will be disabled.")
            print(f"   Available env vars: {[k for k in os.environ.keys() if 'API' in k or 'KEY' in k]}")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=openai_api_key)
            print(f"✅ OpenAI API Key loaded: {openai_api_key[:10]}***")

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
                print(f"사용자 지정 작품 발견: {file_name} (제목: {title}, 작가: {author})")

        return user_specified_files

    def _preprocess_source_by_type(self, source_text: str, korean_type: str, source_info: Dict) -> str:
        """유형별 지문 전처리 - 4가지 유형에 맞게 최적화"""

        if korean_type == "시":
            # 시: 전체 텍스트 사용 (보통 짧음)
            # 단, 너무 긴 경우(연작시 등) 적절히 제한
            if len(source_text) > 2000:
                print(f"⚠️ 시 텍스트가 너무 김 ({len(source_text)}자), 앞부분 사용")
                return source_text[:2000]
            return source_text

        elif korean_type == "소설":
            # 소설: 핵심 부분 발췌 (갈등, 클라이맥스, 인물 관계 등)
            if len(source_text) > 1500:
                print(f"📖 소설 핵심 부분 발췌 중... (원본: {len(source_text)}자)")
                return self._extract_key_passage(source_text, korean_type)
            return source_text

        elif korean_type == "수필/비문학":
            # 수필/비문학: 핵심 논지가 있는 부분 발췌
            if len(source_text) > 1500:
                print(f"📝 수필/비문학 핵심 부분 발췌 중... (원본: {len(source_text)}자)")
                return self._extract_key_passage(source_text, korean_type)
            return source_text

        else:
            # 기본값
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

            # 발췌가 실패한 경우 원본의 앞부분 사용
            if len(extracted_text) < 200:
                print(f"⚠️ 발췌 실패 (길이: {len(extracted_text)}), 원본 앞부분 사용")
                return source_text[:1200] + "..." if len(source_text) > 1200 else source_text

            print(f"✅ 핵심 부분 발췌 완료: {len(extracted_text)}자")
            return extracted_text

        except Exception as e:
            print(f"❌ 지문 발췌 오류: {e}")
            # 폴백: 원본의 앞부분 사용
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

    def _generate_multiple_problems_from_single_text(self, source_text: str, source_info: Dict,
                                                   korean_type: str, count: int,
                                                   question_type_ratio: Dict, difficulty_ratio: Dict,
                                                   user_prompt: str, korean_data: Dict,
                                                   max_retries: int = 2) -> List[Dict]:
        """하나의 지문으로 여러 문제를 한 번에 생성 (재시도 로직 포함)"""

        # 문제 유형과 난이도 분포 결정
        question_types = self._distribute_question_types(count, question_type_ratio, korean_data)
        difficulties = self._distribute_difficulties(count, difficulty_ratio, korean_data)

        # 영어 템플릿을 사용하여 프롬프트 생성 (더 나은 LLM 성능)
        prompt = self.multiple_template_en.generate_prompt(
            source_text, source_info, korean_type, count,
            question_types, difficulties, user_prompt, korean_data
        )

        # 재시도 로직
        for attempt in range(max_retries):
            try:
                # AI 호출
                response = self.model.generate_content(prompt)
                result_text = response.text

                # 문제 파싱 및 검증
                problems = self._parse_and_validate_problems(
                    result_text, source_text, source_info, korean_type, count, difficulties
                )

                if problems and len(problems) >= count:
                    return problems[:count]
                else:
                    print(f"⚠️ 생성된 문제 수 부족 ({len(problems)}/{count}), 재시도 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # 재시도 전 대기
                        continue

            except Exception as e:
                print(f"❌ 문제 생성 시도 {attempt + 1} 실패: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    raise

        # 모든 재시도 실패 시 빈 리스트 반환
        return []

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
                # 문서 타입별 source_text 처리
                if korean_type == "문법":
                    # 문법: LLM이 생성한 지문은 표시, grammar.txt 원본은 숨김
                    # problem_data에서 LLM이 생성한 source_text가 있으면 사용
                    llm_generated_text = problem_data.get('source_text', '')
                    if llm_generated_text and llm_generated_text != source_text:
                        # LLM이 새로 생성한 지문이면 사용
                        rendered_source_text = llm_generated_text
                    else:
                        # grammar.txt 원본이면 숨김
                        rendered_source_text = ""
                elif korean_type == "시":
                    # 시: 전체 지문 렌더링
                    rendered_source_text = source_text
                elif korean_type == "소설":
                    # 소설: LLM이 추출한 중요부분 전체 렌더링
                    rendered_source_text = source_text
                elif korean_type == "수필/비문학":
                    # 수필/비문학: 전체 지문 렌더링
                    rendered_source_text = source_text
                else:
                    # 기본값: 전체 지문
                    rendered_source_text = source_text

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
            print(f"다중 문제 JSON 파싱 오류: {e}")
            print(f"응답 텍스트 길이: {len(result_text)}")
            print(f"응답 텍스트 (처음 500자): {result_text[:500]}")
            print(f"응답 텍스트 (마지막 500자): {result_text[-500:]}")
            raise Exception(f"다중 문제 생성 실패 - JSON 파싱 오류: {e}")
        except Exception as e:
            print(f"다중 문제 생성 중 예상치 못한 오류: {e}")
            print(f"오류 타입: {type(e).__name__}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
            raise Exception(f"다중 문제 생성 실패 - 예상치 못한 오류: {e}")

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

            except Exception as e:
                print(f"개별 문제 생성 오류: {e}")
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
                else:
                    print(f"⚠️ 단일 문제 파싱 실패, 재시도 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue

            except Exception as e:
                print(f"❌ 단일 문제 생성 시도 {attempt + 1} 실패: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    raise

        raise Exception("단일 문제 생성 실패 - 모든 재시도 소진")

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

                # 문서 타입별 source_text 처리
                if korean_type == "문법":
                    # 문법: LLM이 생성한 지문은 표시, grammar.txt 원본은 숨김
                    # problem_data에서 LLM이 생성한 source_text가 있으면 사용
                    llm_generated_text = problem_data.get('source_text', '')
                    if llm_generated_text and llm_generated_text != source_text:
                        # LLM이 새로 생성한 지문이면 사용
                        rendered_source_text = llm_generated_text
                    else:
                        # grammar.txt 원본이면 숨김
                        rendered_source_text = ""
                elif korean_type == "시":
                    # 시: 전체 지문 렌더링
                    rendered_source_text = source_text
                elif korean_type == "소설":
                    # 소설: LLM이 추출한 중요부분 전체 렌더링
                    rendered_source_text = source_text
                elif korean_type == "수필/비문학":
                    # 수필/비문학: 전체 지문 렌더링
                    rendered_source_text = source_text
                else:
                    # 기본값: 전체 지문
                    rendered_source_text = source_text

                # 필수 필드 검증 및 설정
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

            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 텍스트: {result_text}")
                return None

        except Exception as e:
            print(f"AI 문제 생성 오류: {e}")
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

        except Exception as e:
            print(f"문제 생성 오류: {e}")
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

            print(f"로드된 작품 수: {len(source_texts_info)}")

            # 각 작품별로 문제 수 분배
            problems_per_work = count // len(source_texts_info)
            remaining_problems = count % len(source_texts_info)

            for i, (source_text, source_info) in enumerate(source_texts_info):
                # 각 작품별 문제 수 계산
                work_problem_count = problems_per_work + (1 if i < remaining_problems else 0)

                if work_problem_count > 0:
                    print(f"작품 {i+1}: {source_info.get('title', '')} - {work_problem_count}문제 생성")

                    # 소설의 경우 핵심 부분 발췌
                    if korean_type == "소설" and len(source_text) > 1000:
                        source_text = self._extract_key_passage(source_text, korean_type)

                    # 각 작품으로 문제 생성
                    try:
                        work_problems = self._generate_multiple_problems_from_single_text(
                            source_text, source_info, korean_type, work_problem_count,
                            question_type_ratio, difficulty_ratio, user_prompt, korean_data
                        )
                        problems.extend(work_problems)
                    except Exception as e:
                        print(f"작품 {i+1} 문제 생성 오류: {e}")
                        # 폴백: 개별 생성
                        try:
                            work_problems = self._generate_problems_individually(
                                source_text, source_info, korean_type, work_problem_count,
                                question_type_ratio, difficulty_ratio, user_prompt, korean_data
                            )
                            problems.extend(work_problems)
                        except Exception as fallback_error:
                            print(f"작품 {i+1} 개별 문제 생성도 실패: {fallback_error}")
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
                # 사용자가 지정한 작품들 우선 선택
                selected_files = user_specified_files[:work_count]
                print(f"사용자 지정 작품 {len(selected_files)}개 선택")
            else:
                # 랜덤 선택
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
                print(f"랜덤 선택 작품 {len(selected_files)}개 선택")

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
                print(f"로드된 작품: {title} - {author}")

            return source_texts_info

        except Exception as e:
            print(f"다중 소스 로드 오류: {e}")
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

            # I~V 영역별로 내용 분할
            grammar_sections = self._split_grammar_content(full_grammar_content)

            if not grammar_sections:
                print("문법 영역 분할 실패")
                return []

            # 각 영역별 문제 수 계산 (균등 분배)
            problems_per_section = count // len(grammar_sections)
            remaining_problems = count % len(grammar_sections)

            section_names = ["I. 음운", "II. 품사와 어휘", "III. 문장", "IV. 기타", "V. 부록"]

            for i, (section_name, section_content) in enumerate(zip(section_names, grammar_sections)):
                if not section_content.strip():
                    continue

                # 각 영역별 문제 수 계산
                section_problem_count = problems_per_section + (1 if i < remaining_problems else 0)

                if section_problem_count > 0:
                    print(f"문법 영역 {section_name}: {section_problem_count}문제 생성")

                    # 영역별 문제 생성
                    try:
                        section_problems = self._generate_multiple_problems_from_single_text(
                            section_content,
                            {"title": section_name, "author": "교육부", "file": "grammar.txt"},
                            "문법", section_problem_count,
                            question_type_ratio, difficulty_ratio, user_prompt, korean_data
                        )
                        problems.extend(section_problems)
                    except Exception as e:
                        print(f"문법 영역 {section_name} 문제 생성 오류: {e}")
                        # 폴백: 개별 생성
                        try:
                            section_problems = self._generate_problems_individually(
                                section_content,
                                {"title": section_name, "author": "교육부", "file": "grammar.txt"},
                                "문법", section_problem_count,
                                question_type_ratio, difficulty_ratio, user_prompt, korean_data
                            )
                            problems.extend(section_problems)
                        except Exception as fallback_error:
                            print(f"문법 영역 {section_name} 개별 문제 생성도 실패: {fallback_error}")
                            continue

            return problems

        except Exception as e:
            print(f"문법 문제 생성 오류: {e}")
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

            print(f"문법 섹션 분할 완료: {len(sections)}개 섹션")
            for i, section in enumerate(sections):
                print(f"섹션 {i+1}: {len(section)}자")

            return sections

        except Exception as e:
            print(f"문법 섹션 분할 오류: {e}")
            return []

    # ========== 병렬 처리 메서드 ==========

    def generate_problems_parallel(self, korean_data: Dict, user_prompt: str, problem_count: int,
                                   difficulty_ratio: Dict = None, max_workers: int = 5) -> List[Dict]:
        """병렬로 문제 생성 - 수학 서비스와 유사한 방식"""
        print(f"🚀 병렬 문제 생성 시작: {problem_count}개 문제")

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

        # 병렬로 각 작품의 문제 생성
        with ThreadPoolExecutor(max_workers=min(len(tasks), max_workers)) as executor:
            future_to_task = {}
            for task in tasks:
                print(f"📝 작품 {task['work_index']+1}: {task['source_info'].get('title', '')} - {task['count']}문제 생성 시작...")
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

            # 완료된 작업 수집
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    work_problems = future.result()
                    problems.extend(work_problems)
                    print(f"✅ 작품 {task['work_index']+1} 문제 {len(work_problems)}개 생성 완료")
                except Exception as e:
                    print(f"❌ 작품 {task['work_index']+1} 문제 생성 실패: {str(e)}")

        print(f"🎉 총 {len(problems)}개 문제 병렬 생성 완료")
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
        except Exception as e:
            print(f"작품 문제 생성 오류, 폴백 시도: {e}")
            # 폴백: 개별 생성
            return self._generate_problems_individually(
                source_text, source_info, korean_type, count,
                None, difficulty_ratio, user_prompt, korean_data
            )

    # ========== 검증 로직 ==========

    def validate_problem(self, problem: Dict, korean_type: str, use_ai_judge: bool = True) -> Dict:
        """
        2단계 문제 검증 (수학과 동일한 방식)
        1단계: 구조 검증 (Gemini가 생성 시 이미 수행)
        2단계: AI Judge 내용 검증 (GPT-4o-mini)
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'quality_score': 100,
            'ai_judge_scores': {},
            'ai_judge_feedback': ''
        }

        # 1. 필수 필드 검증 (구조 검증)
        required_fields = ['question', 'correct_answer', 'explanation', 'difficulty', 'choices']
        for field in required_fields:
            if field not in problem or not problem[field]:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"필수 필드 누락: {field}")
                validation_result['quality_score'] -= 20

        # 2. 객관식 선택지 검증 (국어는 모두 객관식)
        if 'choices' in problem:
            choices = problem['choices']
            if not isinstance(choices, list):
                validation_result['errors'].append("선택지가 리스트가 아님")
                validation_result['quality_score'] -= 15
            elif len(choices) != 4:
                validation_result['errors'].append(f"선택지 개수 오류: {len(choices)}개 (4개 필요)")
                validation_result['quality_score'] -= 15
            else:
                # 선택지 중복 검사
                if len(set(choices)) != 4:
                    validation_result['warnings'].append("선택지에 중복이 있음")
                    validation_result['quality_score'] -= 5

        # 3. 정답 검증
        if 'correct_answer' in problem and 'choices' in problem:
            correct = problem['correct_answer']
            if correct not in ['A', 'B', 'C', 'D', '1', '2', '3', '4']:
                validation_result['warnings'].append(f"정답 형식 비정상: {correct}")
                validation_result['quality_score'] -= 10

        # 4. 난이도 검증
        if 'difficulty' in problem:
            if problem['difficulty'] not in ['상', '중', '하', 'HIGH', 'MEDIUM', 'LOW']:
                validation_result['errors'].append(f"잘못된 난이도: {problem['difficulty']}")
                validation_result['quality_score'] -= 10

        # 5. 유형별 특화 검증
        if korean_type == "시":
            type_result = self._validate_poem_problem(problem)
        elif korean_type == "소설":
            type_result = self._validate_novel_problem(problem)
        elif korean_type == "수필/비문학":
            type_result = self._validate_nonfiction_problem(problem)
        elif korean_type == "문법":
            type_result = self._validate_grammar_problem(problem)
        else:
            type_result = {'warnings': [], 'quality_score': 0}

        # 유형별 검증 결과 병합
        validation_result['warnings'].extend(type_result.get('warnings', []))
        validation_result['quality_score'] += type_result.get('quality_score', 0)

        # 6. AI Judge 내용 검증 (2단계)
        if use_ai_judge and validation_result['is_valid'] and self.openai_client:
            try:
                is_valid_ai, ai_scores, ai_feedback = self._validate_with_ai_judge(problem, korean_type)
                validation_result['ai_judge_scores'] = ai_scores
                validation_result['ai_judge_feedback'] = ai_feedback

                if not is_valid_ai:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"AI Judge 검증 실패: {ai_feedback}")
                    validation_result['quality_score'] -= 30

            except Exception as e:
                # AI Judge 실패 시 경고만 추가 (검증 통과는 유지)
                validation_result['warnings'].append(f"AI Judge 검증 오류: {str(e)}")

        return validation_result

    def _validate_poem_problem(self, problem: Dict) -> Dict:
        """시 문제 특화 검증"""
        result = {'warnings': [], 'quality_score': 0}

        # 지문 길이 확인
        if 'source_text' in problem:
            source_text = problem['source_text']
            if len(source_text) < 20:
                result['warnings'].append("시 지문이 너무 짧음 (20자 미만)")
                result['quality_score'] -= 5
            elif len(source_text) > 1000:
                result['warnings'].append("시 지문이 너무 긴 것 같음")
                result['quality_score'] -= 3

        # 작품명, 작가명 확인
        if not problem.get('source_title'):
            result['warnings'].append("시 제목 누락")
            result['quality_score'] -= 5
        if not problem.get('source_author'):
            result['warnings'].append("시인 이름 누락")
            result['quality_score'] -= 5

        return result

    def _validate_novel_problem(self, problem: Dict) -> Dict:
        """소설 문제 특화 검증"""
        result = {'warnings': [], 'quality_score': 0}

        # 지문 길이 확인 (소설은 충분한 서사 필요)
        if 'source_text' in problem:
            source_text = problem['source_text']
            if len(source_text) < 300:
                result['warnings'].append("소설 지문이 너무 짧음 (300자 미만)")
                result['quality_score'] -= 10

        # 작품명, 작가명 확인
        if not problem.get('source_title'):
            result['warnings'].append("소설 제목 누락")
            result['quality_score'] -= 5
        if not problem.get('source_author'):
            result['warnings'].append("작가 이름 누락")
            result['quality_score'] -= 5

        return result

    def _validate_nonfiction_problem(self, problem: Dict) -> Dict:
        """수필/비문학 문제 특화 검증"""
        result = {'warnings': [], 'quality_score': 0}

        # 지문 길이 확인
        if 'source_text' in problem:
            source_text = problem['source_text']
            if len(source_text) < 100:
                result['warnings'].append("지문이 너무 짧음 (100자 미만)")
                result['quality_score'] -= 8

        # 작가명 확인 (제목은 선택)
        if not problem.get('source_author'):
            result['warnings'].append("작가 이름 누락")
            result['quality_score'] -= 3

        return result

    def _validate_grammar_problem(self, problem: Dict) -> Dict:
        """문법 문제 특화 검증"""
        result = {'warnings': [], 'quality_score': 0}

        # 문법 문제는 정답이 명확해야 함
        if 'explanation' in problem:
            explanation = problem['explanation']
            if len(explanation) < 20:
                result['warnings'].append("해설이 너무 짧음 (문법은 상세한 설명 필요)")
                result['quality_score'] -= 10

        return result

    def _validate_with_ai_judge(self, problem: Dict, korean_type: str) -> Tuple[bool, Dict, str]:
        """
        AI Judge로 국어 문제 내용 검증 (OpenAI GPT-4o-mini)

        Args:
            problem: 검증할 문제
            korean_type: 국어 문제 유형 (시/소설/수필/비문학/문법)

        Returns:
            (is_valid: bool, scores: dict, feedback: str)
        """
        if not self.openai_client:
            print("⚠️ AI Judge disabled (no OpenAI API key)")
            return True, {}, "AI Judge not available"

        try:
            question = problem.get('question', '')
            correct_answer = problem.get('correct_answer', '')
            explanation = problem.get('explanation', '')
            choices = problem.get('choices', [])
            choices_text = '\n'.join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)]) if choices else 'None'

            # 국어 유형별 검증 기준 설정
            type_specific_criteria = self._get_korean_validation_criteria(korean_type)

            validation_prompt = f"""You are an expert Korean language teacher. Please validate the following Korean language problem.

The problem data is as follows:
- Question: {question}
- Choices:
{choices_text}
- Correct Answer: {correct_answer}
- Explanation: {explanation}
- Korean Type: {korean_type}

Evaluation criteria (score 1-5 for each):
{type_specific_criteria}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "scores": {{"criterion1": <score>, "criterion2": <score>, "criterion3": <score>, "criterion4": <score>}},
  "overall_score": <average>,
  "decision": "VALID" or "INVALID",
  "feedback": "<brief feedback in Korean>"
}}

Decision rule: All scores must be 3.5 or higher to be "VALID".
"""

            # OpenAI API 호출
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Korean language education expert who validates Korean language problems and returns structured JSON responses."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)

            is_valid = result.get('decision') == 'VALID'
            scores = result.get('scores', {})
            scores['overall_score'] = result.get('overall_score', 0)
            feedback = result.get('feedback', 'No feedback')

            return is_valid, scores, feedback

        except json.JSONDecodeError as e:
            print(f"❌ AI Judge 응답 JSON 파싱 실패: {str(e)}")
            raise Exception(f"AI Judge validation failed - invalid JSON response: {str(e)}")

        except Exception as e:
            print(f"❌ AI Judge 검증 오류: {str(e)}")
            raise Exception(f"AI Judge validation error: {str(e)}")

    def _get_korean_validation_criteria(self, korean_type: str) -> str:
        """국어 유형별 AI Judge 검증 기준 반환"""

        criteria_map = {
            '시': """1. literary_accuracy (1-5): The question and explanation accurately interpret the poem's literary devices, imagery, and meaning
2. relevance (1-5): The question directly relates to the provided poem and tests genuine comprehension
3. figurative_language_analysis (1-5): Proper analysis of metaphors, symbolism, tone, and poetic techniques
4. answer_clarity (1-5): The correct answer is clearly justified in the explanation with textual evidence""",

            '소설': """1. narrative_comprehension (1-5): The question accurately tests understanding of plot, characters, conflict, or theme
2. relevance (1-5): The question directly relates to the provided text and doesn't require external knowledge
3. textual_analysis (1-5): Proper analysis of narrative techniques, character development, or literary context
4. answer_clarity (1-5): The correct answer is clearly justified in the explanation with specific references""",

            '수필/비문학': """1. content_accuracy (1-5): The question accurately reflects the information and arguments in the text
2. logical_consistency (1-5): The reasoning in the question and explanation is logically sound
3. relevance (1-5): The question tests genuine comprehension of the non-fiction content
4. answer_clarity (1-5): The correct answer is clearly justified with textual evidence""",

            '문법': """1. grammatical_accuracy (1-5): The grammatical concepts and rules are correctly explained
2. concept_clarity (1-5): The grammatical concept being tested is clearly defined and applied
3. example_appropriateness (1-5): Example sentences (if any) correctly demonstrate the grammar point
4. answer_clarity (1-5): The correct answer is unambiguous and well-justified"""
        }

        return criteria_map.get(korean_type, criteria_map['수필/비문학'])

    def validate_problems_batch(self, problems: List[Dict], korean_type: str, use_ai_judge: bool = True) -> Dict:
        """전체 문제 세트 검증 (2단계: 구조 + AI Judge)"""
        validation_summary = {
            'total_problems': len(problems),
            'valid_problems': 0,
            'invalid_problems': 0,
            'average_quality_score': 0,
            'average_ai_judge_score': 0,
            'difficulty_distribution': {'상': 0, '중': 0, '하': 0},
            'ai_judge_enabled': use_ai_judge and self.openai_client is not None,
            'issues': []
        }

        total_quality = 0
        total_ai_score = 0
        ai_score_count = 0

        for i, problem in enumerate(problems):
            result = self.validate_problem(problem, korean_type, use_ai_judge=use_ai_judge)

            if result['is_valid']:
                validation_summary['valid_problems'] += 1
            else:
                validation_summary['invalid_problems'] += 1
                issue = {
                    'problem_index': i + 1,
                    'errors': result['errors'],
                    'warnings': result['warnings']
                }

                # AI Judge 피드백 추가
                if result.get('ai_judge_feedback'):
                    issue['ai_judge_feedback'] = result['ai_judge_feedback']
                    issue['ai_judge_scores'] = result.get('ai_judge_scores', {})

                validation_summary['issues'].append(issue)

            total_quality += result['quality_score']

            # AI Judge 점수 집계
            if result.get('ai_judge_scores') and 'overall_score' in result['ai_judge_scores']:
                total_ai_score += result['ai_judge_scores']['overall_score']
                ai_score_count += 1

            # 난이도 분포 계산
            difficulty = problem.get('difficulty', '중')
            if difficulty in validation_summary['difficulty_distribution']:
                validation_summary['difficulty_distribution'][difficulty] += 1

        validation_summary['average_quality_score'] = (
            total_quality / len(problems) if problems else 0
        )

        validation_summary['average_ai_judge_score'] = (
            total_ai_score / ai_score_count if ai_score_count > 0 else 0
        )

        return validation_summary