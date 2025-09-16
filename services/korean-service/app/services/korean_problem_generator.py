import os
import json
import random
import time
import google.generativeai as genai
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class KoreanProblemGenerator:
    def __init__(self):
        gemini_api_key = os.getenv("KOREAN_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("KOREAN_GEMINI_API_KEY or GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        # 데이터 파일 경로
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data")

    def load_source_text(self, korean_type: str) -> str:
        """문제 유형에 따른 지문 로드"""
        try:
            if korean_type == "시":
                poem_files = [f for f in os.listdir(os.path.join(self.data_path, "poem")) if f.endswith('.txt')]
                if poem_files:
                    selected_file = random.choice(poem_files)
                    with open(os.path.join(self.data_path, "poem", selected_file), 'r', encoding='utf-8') as f:
                        return f.read()

            elif korean_type == "소설":
                novel_files = [f for f in os.listdir(os.path.join(self.data_path, "novel")) if f.endswith('.txt')]
                if novel_files:
                    selected_file = random.choice(novel_files)
                    with open(os.path.join(self.data_path, "novel", selected_file), 'r', encoding='utf-8') as f:
                        return f.read()

            elif korean_type == "수필/비문학":
                nonfiction_files = [f for f in os.listdir(os.path.join(self.data_path, "non-fiction")) if f.endswith('.txt')]
                if nonfiction_files:
                    selected_file = random.choice(nonfiction_files)
                    with open(os.path.join(self.data_path, "non-fiction", selected_file), 'r', encoding='utf-8') as f:
                        return f.read()

            elif korean_type == "문법":
                with open(os.path.join(self.data_path, "grammar.txt"), 'r', encoding='utf-8') as f:
                    return f.read()

        except Exception as e:
            print(f"데이터 파일 로드 오류: {e}")
            return ""

        return ""

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

    def load_multiple_source_texts_with_info(self, korean_type: str, user_prompt: str = "") -> List[tuple]:
        """사용자가 여러 작품을 언급했을 때 모든 작품의 지문과 정보를 로드"""
        try:
            if korean_type == "시":
                poem_files = [f for f in os.listdir(os.path.join(self.data_path, "poem")) if f.endswith('.txt')]
                if poem_files:
                    # 사용자가 특정 작품을 언급했는지 확인
                    user_specified_files = self._extract_user_specified_works(user_prompt, poem_files)
                    
                    if user_specified_files:
                        # 사용자가 지정한 모든 작품의 내용을 로드
                        source_texts = []
                        for selected_file in user_specified_files:
                            file_path = os.path.join(self.data_path, "poem", selected_file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # 파일명에서 제목과 작가 추출
                            title_author = selected_file.replace('.txt', '')
                            if '-' in title_author:
                                title, author = title_author.split('-', 1)
                            else:
                                title, author = title_author, "작자미상"
                            
                            source_texts.append((content, {"title": title, "author": author, "file": selected_file}))
                            print(f"사용자 지정 작품 로드: {selected_file} (제목: {title}, 작가: {author})")
                        
                        return source_texts
                    else:
                        # 사용자 지정이 없으면 랜덤 선택 (기존 로직)
                        import secrets
                        random_index = secrets.randbelow(len(poem_files))
                        selected_file = poem_files[random_index]
                        file_path = os.path.join(self.data_path, "poem", selected_file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        title_author = selected_file.replace('.txt', '')
                        if '-' in title_author:
                            title, author = title_author.split('-', 1)
                        else:
                            title, author = title_author, "작자미상"
                        
                        return [(content, {"title": title, "author": author, "file": selected_file})]
            
            # 다른 유형들도 동일하게 처리
            elif korean_type == "소설":
                novel_files = [f for f in os.listdir(os.path.join(self.data_path, "novel")) if f.endswith('.txt')]
                if novel_files:
                    user_specified_files = self._extract_user_specified_works(user_prompt, novel_files)
                    if user_specified_files:
                        source_texts = []
                        for selected_file in user_specified_files:
                            file_path = os.path.join(self.data_path, "novel", selected_file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            title_author = selected_file.replace('.txt', '')
                            if '-' in title_author:
                                title, author = title_author.split('-', 1)
                            else:
                                title, author = title_author, "작자미상"
                            source_texts.append((content, {"title": title, "author": author, "file": selected_file}))
                        return source_texts
                    else:
                        import secrets
                        random_index = secrets.randbelow(len(novel_files))
                        selected_file = novel_files[random_index]
                        file_path = os.path.join(self.data_path, "novel", selected_file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        title_author = selected_file.replace('.txt', '')
                        if '-' in title_author:
                            title, author = title_author.split('-', 1)
                        else:
                            title, author = title_author, "작자미상"
                        return [(content, {"title": title, "author": author, "file": selected_file})]
            
            elif korean_type == "수필/비문학":
                nonfiction_files = [f for f in os.listdir(os.path.join(self.data_path, "non-fiction")) if f.endswith('.txt')]
                if nonfiction_files:
                    user_specified_files = self._extract_user_specified_works(user_prompt, nonfiction_files)
                    if user_specified_files:
                        source_texts = []
                        for selected_file in user_specified_files:
                            file_path = os.path.join(self.data_path, "non-fiction", selected_file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            title_author = selected_file.replace('.txt', '')
                            if '-' in title_author:
                                title, author = title_author.split('-', 1)
                            else:
                                title, author = title_author, "작자미상"
                            source_texts.append((content, {"title": title, "author": author, "file": selected_file}))
                        return source_texts
                    else:
                        import secrets
                        random_index = secrets.randbelow(len(nonfiction_files))
                        selected_file = nonfiction_files[random_index]
                        file_path = os.path.join(self.data_path, "non-fiction", selected_file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        title_author = selected_file.replace('.txt', '')
                        if '-' in title_author:
                            title, author = title_author.split('-', 1)
                        else:
                            title, author = title_author, "작자미상"
                        return [(content, {"title": title, "author": author, "file": selected_file})]
            
            elif korean_type == "문법":
                file_path = os.path.join(self.data_path, "grammar.txt")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return [(content, {"title": "국어 문법", "author": "교육부", "file": "grammar.txt"})]

        except Exception as e:
            print(f"다중 데이터 파일 로드 오류: {e}")
            return []

        return []

    def load_source_text_with_info(self, korean_type: str, user_prompt: str = "") -> tuple:
        """문제 유형에 따른 지문과 정보 로드"""
        try:
            if korean_type == "시":
                poem_files = [f for f in os.listdir(os.path.join(self.data_path, "poem")) if f.endswith('.txt')]
                if poem_files:
                    # 사용자가 특정 작품을 언급했는지 확인
                    user_specified_files = self._extract_user_specified_works(user_prompt, poem_files)
                    
                    if user_specified_files:
                        # 사용자가 지정한 작품들 중에서 선택
                        import secrets
                        random_index = secrets.randbelow(len(user_specified_files))
                        selected_file = user_specified_files[random_index]
                        print(f"사용자 지정 작품 중 선택: {selected_file} (총 {len(user_specified_files)}개 중 {random_index}번째)")
                    else:
                        # 모든 작품 중에서 랜덤 선택
                        import secrets
                        random_index = secrets.randbelow(len(poem_files))
                        selected_file = poem_files[random_index]
                        print(f"전체 작품 중 랜덤 선택: {selected_file} (총 {len(poem_files)}개 중 {random_index}번째)")
                    file_path = os.path.join(self.data_path, "poem", selected_file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 파일명에서 제목과 작가 추출 (예: "나무-윤동주.txt")
                    title_author = selected_file.replace('.txt', '')
                    if '-' in title_author:
                        title, author = title_author.split('-', 1)
                    else:
                        title, author = title_author, "작자미상"
                    return content, {"title": title, "author": author, "file": selected_file}

            elif korean_type == "소설":
                novel_files = [f for f in os.listdir(os.path.join(self.data_path, "novel")) if f.endswith('.txt')]
                if novel_files:
                    # 더 강력한 랜덤 선택을 위해 여러 방법 조합
                    import secrets
                    random_index = secrets.randbelow(len(novel_files))
                    selected_file = novel_files[random_index]
                    
                    # 디버깅을 위한 로그
                    print(f"선택된 소설 파일: {selected_file} (총 {len(novel_files)}개 중 {random_index}번째)")
                    file_path = os.path.join(self.data_path, "novel", selected_file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    title_author = selected_file.replace('.txt', '')
                    if '-' in title_author:
                        title, author = title_author.split('-', 1)
                    else:
                        title, author = title_author, "작자미상"
                    return content, {"title": title, "author": author, "file": selected_file}

            elif korean_type == "수필/비문학":
                nonfiction_files = [f for f in os.listdir(os.path.join(self.data_path, "non-fiction")) if f.endswith('.txt')]
                if nonfiction_files:
                    # 더 강력한 랜덤 선택을 위해 여러 방법 조합
                    import secrets
                    random_index = secrets.randbelow(len(nonfiction_files))
                    selected_file = nonfiction_files[random_index]
                    
                    # 디버깅을 위한 로그
                    print(f"선택된 수필/비문학 파일: {selected_file} (총 {len(nonfiction_files)}개 중 {random_index}번째)")
                    file_path = os.path.join(self.data_path, "non-fiction", selected_file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    title_author = selected_file.replace('.txt', '')
                    if '-' in title_author:
                        title, author = title_author.split('-', 1)
                    else:
                        title, author = title_author, "작자미상"
                    return content, {"title": title, "author": author, "file": selected_file}

            elif korean_type == "문법":
                file_path = os.path.join(self.data_path, "grammar.txt")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content, {"title": "국어 문법", "author": "교육부", "file": "grammar.txt"}

        except Exception as e:
            print(f"데이터 파일 로드 오류: {e}")
            return "", {}

        return "", {}

    def _extract_key_passage(self, source_text: str, korean_type: str) -> str:
        """긴 지문에서 핵심 부분 발췌"""
        try:
            # AI를 사용하여 핵심 부분 추출
            prompt = f"""
다음 {korean_type} 지문에서 중학교 1학년 학생들이 이해하기에 적합한 핵심 부분을 발췌해주세요.

**지문:**
{source_text}

**발췌 기준:**
- 전체 지문의 핵심 내용을 담고 있어야 함
- 800-1200자 정도의 적절한 길이
- 문맥이 완결된 부분
- 문제 출제에 적합한 내용

발췌된 부분만 텍스트로 출력해주세요. 추가 설명은 필요하지 않습니다.
"""

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

    def _generate_multiple_problems_from_single_text(self, source_text: str, source_info: Dict, 
                                                   korean_type: str, count: int,
                                                   question_type_ratio: Dict, difficulty_ratio: Dict,
                                                   user_prompt: str, korean_data: Dict) -> List[Dict]:
        """하나의 지문으로 여러 문제를 한 번에 생성"""
        
        # 문제 유형과 난이도 분포 결정
        question_types = self._distribute_question_types(count, question_type_ratio, korean_data)
        difficulties = self._distribute_difficulties(count, difficulty_ratio, korean_data)
        
        # AI 프롬프트 구성
        prompt = self._build_multiple_problems_prompt(
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
                    'question_type': question_types[idx] if idx < len(question_types) else '객관식',
                    'difficulty': difficulties[idx] if idx < len(difficulties) else '중',
                    'question': problem_data.get('question', ''),
                    'correct_answer': problem_data.get('correct_answer', ''),
                    'explanation': problem_data.get('explanation', ''),
                    'source_text': source_text[:500] + "..." if len(source_text) > 500 else source_text,
                    'source_title': source_info.get('title', ''),
                    'source_author': source_info.get('author', ''),
                    'sequence_order': idx + 1
                }
                
                # 객관식인 경우 선택지 추가
                if problem['question_type'] == '객관식' and 'choices' in problem_data:
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

    def _distribute_question_types(self, count: int, question_type_ratio: Dict, korean_data: Dict) -> List[str]:
        """문제 수에 맞게 문제 유형 분배"""
        if question_type_ratio and sum(question_type_ratio.values()) == 100:
            types = list(question_type_ratio.keys())
            weights = list(question_type_ratio.values())
            return random.choices(types, weights=weights, k=count)
        else:
            default_type = korean_data.get('question_type', '객관식')
            return [default_type] * count

    def _distribute_difficulties(self, count: int, difficulty_ratio: Dict, korean_data: Dict) -> List[str]:
        """문제 수에 맞게 난이도 분배"""
        if difficulty_ratio and sum(difficulty_ratio.values()) == 100:
            difficulties = list(difficulty_ratio.keys())
            weights = list(difficulty_ratio.values())
            return random.choices(difficulties, weights=weights, k=count)
        else:
            default_difficulty = korean_data.get('difficulty', '중')
            return [default_difficulty] * count

    def generate_problems(self, korean_data: Dict, user_prompt: str, problem_count: int = 1,
                         korean_type_ratio: Dict = None, question_type_ratio: Dict = None,
                         difficulty_ratio: Dict = None) -> List[Dict]:
        """국어 문제 생성"""
        try:
            problems = []

            # 비율에 따른 문제 생성 또는 단일 유형 문제 생성
            if korean_type_ratio and sum(korean_type_ratio.values()) == 100:
                # 비율에 따른 문제 생성
                for korean_type, ratio in korean_type_ratio.items():
                    count = int(problem_count * ratio / 100)
                    if count > 0:
                        type_problems = self._generate_problems_by_type(
                            korean_data, user_prompt, count, korean_type,
                            question_type_ratio, difficulty_ratio
                        )
                        problems.extend(type_problems)
            else:
                # 단일 유형 문제 생성
                korean_type = korean_data.get('korean_type', '시')
                problems = self._generate_problems_by_type(
                    korean_data, user_prompt, problem_count, korean_type,
                    question_type_ratio, difficulty_ratio
                )

            return problems[:problem_count]  # 정확한 개수로 제한

        except Exception as e:
            print(f"문제 생성 오류: {e}")
            return []

    def _generate_problems_by_type(self, korean_data: Dict, user_prompt: str, count: int,
                                  korean_type: str, question_type_ratio: Dict = None,
                                  difficulty_ratio: Dict = None) -> List[Dict]:
        """특정 유형의 문제 생성 - 여러 작품으로 문제 생성"""
        problems = []

        # 여러 지문 로드 - 사용자 프롬프트 전달
        source_texts_info = self.load_multiple_source_texts_with_info(korean_type, user_prompt)
        if not source_texts_info:
            return []

        print(f"로드된 작품 수: {len(source_texts_info)}")
        
        # 여러 작품이 있는 경우 각 작품별로 문제 수 분배
        if len(source_texts_info) > 1:
            # 각 작품별로 문제 수를 균등 분배
            problems_per_work = count // len(source_texts_info)
            remaining_problems = count % len(source_texts_info)
            
            print(f"총 문제 수: {count}, 작품 수: {len(source_texts_info)}")
            print(f"작품별 문제 수: {problems_per_work}, 남은 문제: {remaining_problems}")
            
            for i, (source_text, source_info) in enumerate(source_texts_info):
                # 각 작품별 문제 수 계산 (남은 문제는 앞쪽 작품들에 분배)
                work_problem_count = problems_per_work + (1 if i < remaining_problems else 0)
                
                if work_problem_count > 0:
                    print(f"작품 {i+1}: {source_info.get('title', '')} - {work_problem_count}문제 생성")
                    
                    # 긴 지문인 경우 핵심 부분 발췌
                    if korean_type in ["소설", "수필/비문학"] and len(source_text) > 1000:
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
        else:
            # 단일 작품인 경우 기존 로직 사용
            source_text, source_info = source_texts_info[0]
            
            # 긴 지문인 경우 핵심 부분 발췌
            if korean_type in ["소설", "수필/비문학"] and len(source_text) > 1000:
                source_text = self._extract_key_passage(source_text, korean_type)

            # 하나의 지문으로 여러 문제 생성
            try:
                # AI를 통한 다중 문제 생성
                problems = self._generate_multiple_problems_from_single_text(
                    source_text, source_info, korean_type, count, 
                    question_type_ratio, difficulty_ratio, user_prompt, korean_data
                )
            except Exception as e:
                print(f"다중 문제 생성 오류: {e}")
                print(f"오류 타입: {type(e).__name__}")
                import traceback
                print(f"상세 오류: {traceback.format_exc()}")
                # 폴백: 기존 방식으로 개별 생성
                try:
                    problems = self._generate_problems_individually(
                        source_text, source_info, korean_type, count,
                        question_type_ratio, difficulty_ratio, user_prompt, korean_data
                    )
                except Exception as fallback_error:
                    print(f"개별 문제 생성도 실패: {fallback_error}")
                    print(f"폴백 오류 타입: {type(fallback_error).__name__}")
                    print(f"폴백 상세 오류: {traceback.format_exc()}")
                    raise fallback_error

        return problems

    def _determine_question_type(self, question_type_ratio: Dict, korean_data: Dict) -> str:
        """문제 형식 결정"""
        if question_type_ratio and sum(question_type_ratio.values()) == 100:
            # 비율에 따른 랜덤 선택
            types = list(question_type_ratio.keys())
            weights = list(question_type_ratio.values())
            return random.choices(types, weights=weights)[0]
        else:
            return korean_data.get('question_type', '객관식')

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
            # 프롬프트 구성
            prompt = self._build_prompt(source_text, korean_type, question_type, difficulty, user_prompt, korean_data)

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
                    'question_type': question_type,
                    'difficulty': difficulty,
                    'question': problem_data.get('question', ''),
                    'correct_answer': problem_data.get('correct_answer', ''),
                    'explanation': problem_data.get('explanation', ''),
                    'source_text': source_text[:500] + "..." if len(source_text) > 500 else source_text,
                    'source_title': problem_data.get('source_title', ''),
                    'source_author': problem_data.get('source_author', '')
                }

                # 객관식인 경우 선택지 추가
                if question_type == '객관식' and 'choices' in problem_data:
                    problem['choices'] = problem_data['choices']

                return problem

            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 텍스트: {result_text}")
                return None

        except Exception as e:
            print(f"AI 문제 생성 오류: {e}")
            return None

    def _build_prompt(self, source_text: str, korean_type: str, question_type: str,
                     difficulty: str, user_prompt: str, korean_data: Dict) -> str:
        """AI 프롬프트 구성"""

        # 난이도 설명
        difficulty_desc = {
            '상': '어려운 수준 (고차원적 사고, 복합적 이해 필요)',
            '중': '보통 수준 (기본 이해와 적용)',
            '하': '쉬운 수준 (기초 개념 확인)'
        }

        # 기본 프롬프트
        prompt = f"""
다음 지문을 바탕으로 {korean_type} 영역의 {question_type} 문제를 생성해주세요.

**지문:**
{source_text}

**문제 요구사항:**
- 학교급: {korean_data.get('school_level', '중학교')}
- 학년: {korean_data.get('grade', 1)}학년
- 문제 유형: {korean_type}
- 문제 형식: {question_type}
- 난이도: {difficulty} ({difficulty_desc.get(difficulty, '')})
"""

        if user_prompt:
            prompt += f"\n**추가 요구사항:** {user_prompt}\n"

        if question_type == '객관식':
            prompt += """
**출력 형식 (JSON):**
```json
{
    "question": "문제 내용",
    "choices": ["1번 선택지", "2번 선택지", "3번 선택지", "4번 선택지"],
    "correct_answer": "정답 선택지 내용",
    "explanation": "해설",
    "source_title": "지문 제목 (있는 경우)",
    "source_author": "지문 작가 (있는 경우)"
}
```

**주의사항:**
- 4개의 선택지를 제공하고, 정답은 choices 배열의 실제 내용과 정확히 일치해야 합니다.
- 선택지는 명확하고 구별되어야 합니다.
"""
        else:
            prompt += """
**출력 형식 (JSON):**
```json
{
    "question": "문제 내용",
    "correct_answer": "정답",
    "explanation": "해설",
    "source_title": "지문 제목 (있는 경우)",
    "source_author": "지문 작가 (있는 경우)"
}
```

**주의사항:**
- 서술형/단답형 문제에 적합한 정답을 제시해주세요.
- 채점 기준이 명확해야 합니다.
"""

        prompt += f"""
**{korean_type} 영역 특성:**
"""

        if korean_type == '시':
            prompt += """
- 화자, 상황, 정서, 표현 기법, 주제 의식 등을 중심으로 문제 출제
- 운율, 은유, 의인법, 대조법 등의 문학적 표현 기법 분석
- 시어의 함축적 의미, 화자의 정서와 상황 파악
"""
        elif korean_type == '소설':
            prompt += """
- 인물, 배경, 사건, 갈등, 주제 등을 중심으로 문제 출제
- 서술자, 시점, 구성, 문체 등의 소설 기법 분석
- 인물의 심리, 갈등 상황, 주제 의식 파악
"""
        elif korean_type == '수필/비문학':
            prompt += """
- 글의 구조, 논리 전개, 주장과 근거, 핵심 내용 등을 중심으로 문제 출제
- 글쓴이의 관점, 의도, 글의 성격 파악
- 정보의 이해, 추론, 적용 능력 평가
"""
        elif korean_type == '문법':
            prompt += """
- 음운, 단어, 문장, 의미 등의 문법 요소를 중심으로 문제 출제
- 품사, 어휘, 문장 성분, 문법적 관계 분석
- 언어의 특성, 변화, 규칙 등에 대한 이해 평가
"""

        prompt += """
반드시 JSON 형식으로만 응답하고, 추가적인 설명은 포함하지 마세요.
"""

        return prompt

    def _build_multiple_problems_prompt(self, source_text: str, source_info: Dict, korean_type: str,
                                      count: int, question_types: List[str], difficulties: List[str],
                                      user_prompt: str, korean_data: Dict) -> str:
        """하나의 지문으로 여러 문제를 생성하는 프롬프트"""
        
        # 난이도 설명
        difficulty_desc = {
            '상': '어려운 수준 (고차원적 사고, 복합적 이해 필요)',
            '중': '보통 수준 (기본 이해와 적용)',
            '하': '쉬운 수준 (기초 개념 확인)'
        }

        # 문제 유형별 분포 정보
        question_type_info = []
        for i, (q_type, difficulty) in enumerate(zip(question_types, difficulties)):
            question_type_info.append(f"- 문제 {i+1}: {q_type} ({difficulty} - {difficulty_desc.get(difficulty, '')})")

        prompt = f"""
다음 지문을 바탕으로 {korean_type} 영역의 문제 {count}개를 생성해주세요.

**지문 정보:**
- 제목: {source_info.get('title', '')}
- 작가: {source_info.get('author', '')}

**지문:**
{source_text}

**문제 요구사항:**
- 학교급: {korean_data.get('school_level', '중학교')}
- 학년: {korean_data.get('grade', 1)}학년
- 문제 유형: {korean_type}

**문제별 세부 요구사항:**
{chr(10).join(question_type_info)}
"""

        if user_prompt:
            prompt += f"\n**추가 요구사항:** {user_prompt}\n"

        prompt += f"""
**출력 형식 (JSON):**
```json
{{
    "source_info": {{
        "title": "{source_info.get('title', '')}",
        "author": "{source_info.get('author', '')}"
    }},
    "problems": [
        {{
            "question": "문제 내용",
            "choices": ["1번 선택지", "2번 선택지", "3번 선택지", "4번 선택지"],
            "correct_answer": "정답 선택지 내용",
            "explanation": "해설"
        }},
        {{
            "question": "문제 내용",
            "correct_answer": "정답",
            "explanation": "해설"
        }}
    ]
}}
```

**문제 생성 규칙:**
1. **하나의 지문에 연결된 문제들**: 모든 문제가 주어진 지문을 바탕으로 출제되어야 함
2. **문제 간 연관성**: 문제들이 서로 다른 관점에서 같은 지문을 다루되, 중복되지 않아야 함
3. **난이도별 특성**:
   - 하: 지문의 표면적 내용 이해 (누가, 언제, 어디서, 무엇을)
   - 중: 지문의 의미와 의도 파악 (왜, 어떻게)
   - 상: 지문의 깊은 의미와 작가의 의도, 표현 기법 분석
4. **문제 유형별 특성**:
   - 객관식: 명확한 정답이 있는 사실 확인 문제
   - 서술형: 개인적 해석과 근거 제시가 필요한 문제
   - 단답형: 간단한 답으로 해결되는 문제

**{korean_type} 영역 특성:**
"""

        if korean_type == '시':
            prompt += """
- 화자, 상황, 정서, 표현 기법, 주제 의식 등을 중심으로 문제 출제
- 운율, 은유, 의인법, 대조법 등의 문학적 표현 기법 분석
- 시어의 함축적 의미, 화자의 정서와 상황 파악
- 문제 1-3: 표면적 이해 (화자, 상황, 정서)
- 문제 4-7: 표현 기법과 시어 분석
- 문제 8-10: 주제 의식과 깊은 의미
"""
        elif korean_type == '소설':
            prompt += """
- 인물, 배경, 사건, 갈등, 주제 등을 중심으로 문제 출제
- 서술자, 시점, 구성, 문체 등의 소설 기법 분석
- 인물의 심리, 갈등 상황, 주제 의식 파악
- 문제 1-3: 인물과 사건 이해
- 문제 4-7: 갈등과 심리 분석
- 문제 8-10: 주제와 작가 의도
"""
        elif korean_type == '수필/비문학':
            prompt += """
- 글의 구조, 논리 전개, 주장과 근거, 핵심 내용 등을 중심으로 문제 출제
- 글쓴이의 관점, 의도, 글의 성격 파악
- 정보의 이해, 추론, 적용 능력 평가
- 문제 1-3: 핵심 내용 파악
- 문제 4-7: 논리 구조와 근거 분석
- 문제 8-10: 추론과 적용
"""
        elif korean_type == '문법':
            prompt += """
- 음운, 단어, 문장, 의미 등의 문법 요소를 중심으로 문제 출제
- 품사, 어휘, 문장 성분, 문법적 관계 분석
- 언어의 특성, 변화, 규칙 등에 대한 이해 평가
- 문제 1-3: 기본 문법 개념
- 문제 4-7: 문법 규칙 적용
- 문제 8-10: 복합 문법 분석
"""

        prompt += """
**주의사항:**
- 모든 문제가 주어진 지문과 직접적으로 연결되어야 함
- 문제들이 서로 다른 측면을 다루되 논리적으로 연결되어야 함
- 객관식 문제는 명확한 정답이 있어야 함
- 서술형/단답형 문제는 채점 기준이 명확해야 함
- 반드시 JSON 형식으로만 응답하고, 추가적인 설명은 포함하지 마세요.
"""

        return prompt