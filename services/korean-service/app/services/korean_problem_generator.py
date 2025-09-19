import os
import json
import random
import time
import google.generativeai as genai
from typing import Dict, List, Optional
from dotenv import load_dotenv

from ..prompt_templates.single_problem_template import SingleProblemTemplate
from ..prompt_templates.multiple_problems_template import MultipleProblemTemplate
from ..prompt_templates.extract_passage_template import ExtractPassageTemplate

load_dotenv()

class KoreanProblemGenerator:
    def __init__(self):
        gemini_api_key = os.getenv("KOREAN_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("KOREAN_GEMINI_API_KEY or GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

        # 데이터 파일 경로
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data")

        # 프롬프트 템플릿 인스턴스
        self.single_template = SingleProblemTemplate()
        self.multiple_template = MultipleProblemTemplate()
        self.extract_template = ExtractPassageTemplate()

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

    def _extract_key_passage(self, source_text: str, korean_type: str) -> str:
        """긴 지문에서 핵심 부분 발췌"""
        try:
            # 템플릿을 사용하여 프롬프트 생성
            prompt = self.extract_template.generate_prompt(source_text, korean_type)

            response = self.model.generate_content(prompt)
            extracted_text = response.text.strip()

            # 발췌가 실패한 경우 원본의 앞부분 사용
            if len(extracted_text) < 200:
                return source_text[:1200] + "..." if len(source_text) > 1200 else source_text

            return extracted_text

        except Exception as e:
            print(f"지문 발췌 오류: {e}")
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
                                                   user_prompt: str, korean_data: Dict) -> List[Dict]:
        """하나의 지문으로 여러 문제를 한 번에 생성"""

        # 문제 유형과 난이도 분포 결정
        question_types = self._distribute_question_types(count, question_type_ratio, korean_data)
        difficulties = self._distribute_difficulties(count, difficulty_ratio, korean_data)

        # 템플릿을 사용하여 프롬프트 생성
        prompt = self.multiple_template.generate_prompt(
            source_text, source_info, korean_type, count,
            question_types, difficulties, user_prompt, korean_data
        )

        # AI 호출
        response = self.model.generate_content(prompt)
        result_text = response.text

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
                problem = {
                    'korean_type': korean_type,
                    'question_type': '객관식',  # 국어는 모두 객관식
                    'difficulty': difficulties[idx] if idx < len(difficulties) else '중',
                    'question': problem_data.get('question', ''),
                    'correct_answer': problem_data.get('correct_answer', ''),
                    'explanation': problem_data.get('explanation', ''),
                    'source_text': source_text[:500] + "..." if len(source_text) > 500 else source_text,
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
                                difficulty: str, user_prompt: str, korean_data: Dict) -> Dict:
        """단일 문제 생성"""
        try:
            # 템플릿을 사용하여 프롬프트 생성
            prompt = self.single_template.generate_prompt(
                source_text, korean_type, question_type, difficulty, user_prompt, korean_data
            )

            # AI 호출
            response = self.model.generate_content(prompt)
            result_text = response.text

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

                # 필수 필드 검증 및 설정
                problem = {
                    'korean_type': korean_type,
                    'question_type': '객관식',  # 국어는 모두 객관식
                    'difficulty': difficulty,
                    'question': problem_data.get('question', ''),
                    'correct_answer': problem_data.get('correct_answer', ''),
                    'explanation': problem_data.get('explanation', ''),
                    'source_text': source_text[:500] + "..." if len(source_text) > 500 else source_text,
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