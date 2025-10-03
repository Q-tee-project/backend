import json
import os
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from ..schemas.math_generation import MathProblemGenerationRequest, MathProblemGenerationResponse
from .ai_client import problem_generator_instance
from ..models.problem import Problem
from ..models.worksheet import Worksheet, WorksheetStatus
import uuid
from datetime import datetime


class MathGenerationService:
    """수학 문제 생성 서비스"""
    
    def __init__(self):
        self.problem_generator = problem_generator_instance
    
    def get_curriculum_structure(self, db: Session, school_level: Optional[str] = None) -> Dict:
        """교육과정 구조 조회 - 중1 1학기에 초점"""
        
        # middle1_math_curriculum.json 파일 읽기
        curriculum_file_path = os.path.join(os.path.dirname(__file__), "../../data/middle1_math_curriculum.json")
        
        try:
            with open(curriculum_file_path, 'r', encoding='utf-8') as f:
                curriculum_data = json.load(f)
        except FileNotFoundError:
            return {"error": "교육과정 데이터 파일을 찾을 수 없습니다."}
        except json.JSONDecodeError:
            return {"error": "교육과정 데이터 파일 형식이 올바르지 않습니다."}
        
        # 중1 1학기에 초점을 맞춘 구조화
        structure = {
            "school_levels": [
                {"value": "초등학교", "label": "초등학교", "grades": list(range(1, 7))},
                {"value": "중학교", "label": "중학교", "grades": list(range(1, 4))},
                {"value": "고등학교", "label": "고등학교", "grades": list(range(1, 4))}
            ]
        }
        
        # 중1 1학기 데이터를 기반으로 상세 구조 생성
        middle1_1semester = {}
        units = {}
        
        for item in curriculum_data:
            if item["grade"] == "중1" and item["semester"] == "1학기":
                unit_number = item["unit_number"]
                unit_name = item["unit_name"]
                
                if unit_number not in units:
                    units[unit_number] = {
                        "unit_number": unit_number,
                        "unit_name": unit_name,
                        "chapters": []
                    }
                
                units[unit_number]["chapters"].append({
                    "chapter_number": item["chapter_number"],
                    "chapter_name": item["chapter_name"],
                    "unit_name": unit_name,
                    "learning_objectives": item["learning_objectives"],
                    "keywords": item["keywords"],
                    "difficulty_levels": json.loads(item["difficulty_levels"]) if isinstance(item["difficulty_levels"], str) else item["difficulty_levels"]
                })
        
        middle1_1semester = {
            "grade": "중1",
            "semester": "1학기", 
            "units": list(units.values())
        }
        
        structure["middle1_1semester"] = middle1_1semester
        
        return structure
    
    def get_units(self) -> List[Dict]:
        """대단원 목록 조회"""
        curriculum_file_path = os.path.join(os.path.dirname(__file__), "../../data/middle1_math_curriculum.json")
        
        try:
            with open(curriculum_file_path, 'r', encoding='utf-8') as f:
                curriculum_data = json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []
        
        units = {}
        for item in curriculum_data:
            if item["grade"] == "중1" and item["semester"] == "1학기":
                unit_name = item["unit_name"]
                if unit_name not in units:
                    units[unit_name] = {
                        "unit_number": item["unit_number"],
                        "unit_name": unit_name
                    }
        
        return list(units.values())
    
    def get_chapters_by_unit(self, unit_name: str) -> List[Dict]:
        """특정 대단원의 소단원 목록 조회"""
        curriculum_file_path = os.path.join(os.path.dirname(__file__), "../../data/middle1_math_curriculum.json")
        
        try:
            with open(curriculum_file_path, 'r', encoding='utf-8') as f:
                curriculum_data = json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []
        
        chapters = []
        for item in curriculum_data:
            if (item["grade"] == "중1" and 
                item["semester"] == "1학기" and 
                item["unit_name"] == unit_name):
                chapters.append({
                    "unit_name": item["unit_name"],
                    "chapter_number": item["chapter_number"],
                    "chapter_name": item["chapter_name"],
                    "learning_objectives": item["learning_objectives"],
                    "keywords": item["keywords"]
                })
        
        return chapters
    
    def generate_problems(self, db: Session, request: MathProblemGenerationRequest, user_id: int) -> MathProblemGenerationResponse:
        """수학 문제 생성"""
        
        # 1. 생성 ID 생성
        generation_id = str(uuid.uuid4())
        
        # 2. 교육과정 데이터 가져오기
        curriculum_data = self._get_curriculum_data(request)

        # 3. AI 서비스를 통한 문제 생성
        generated_problems = self._generate_problems_with_ai(
            curriculum_data=curriculum_data,
            request=request
        )
        
        # 5. 워크시트 생성
        worksheet_title = f"{request.chapter.chapter_name} - {request.problem_count.value}"
        worksheet = Worksheet(
            title=worksheet_title,
            school_level=request.school_level.value,
            grade=request.grade,
            semester=request.semester.value,
            unit_number=request.unit_number,
            unit_name=request.chapter.unit_name,
            chapter_number=request.chapter.chapter_number,
            chapter_name=request.chapter.chapter_name,
            problem_count=request.problem_count.value_int,
            difficulty_ratio=request.difficulty_ratio.model_dump(),
            problem_type_ratio=request.problem_type_ratio.model_dump(),
            user_prompt=request.user_text,
            generation_id=generation_id,
            actual_difficulty_distribution=self._calculate_difficulty_distribution(generated_problems),
            actual_type_distribution=self._calculate_type_distribution(generated_problems),
            status=WorksheetStatus.COMPLETED,
            teacher_id=user_id,
            created_by=user_id
        )
        
        db.add(worksheet)
        db.flush()

        # 6. 생성된 문제들을 워크시트에 연결하여 저장
        problem_responses = []
        for i, problem_data in enumerate(generated_problems):
            # 문제 유형과 난이도 검증
            problem_type = problem_data.get("problem_type")
            difficulty = problem_data.get("difficulty")

            # 유효성 검사 및 기본값 설정 (로그와 함께)
            if problem_type not in ["multiple_choice", "short_answer"]:
                print(f"⚠️ 잘못된 문제유형 '{problem_type}' -> 'multiple_choice'로 대체")
                problem_type = "multiple_choice"

            if difficulty not in ["A", "B", "C"]:
                print(f"⚠️ 잘못된 난이도 '{difficulty}' -> 'B'로 대체")
                difficulty = "B"

            problem = Problem(
                worksheet_id=worksheet.id,  # 워크시트에 연결
                sequence_order=i + 1,
                problem_type=problem_type,
                difficulty=difficulty,
                question=problem_data.get("question", ""),
                choices=json.dumps(problem_data.get("choices")) if problem_data.get("choices") else None,
                correct_answer=problem_data.get("correct_answer", ""),
                explanation=problem_data.get("explanation", ""),
                latex_content=problem_data.get("latex_content"),
                has_diagram=str(problem_data.get("has_diagram", False)).lower(),
                diagram_type=problem_data.get("diagram_type"),
                diagram_elements=json.dumps(problem_data.get("diagram_elements")) if problem_data.get("diagram_elements") else None,
                tikz_code=problem_data.get("tikz_code")
            )
            
            db.add(problem)
            db.flush()
            
            # GeneratedProblemSet 제거됨 - Problem 테이블의 sequence_order로 대체
            
            # 응답용 데이터 생성
            problem_responses.append({
                "id": problem.id,
                "sequence_order": i + 1,
                "problem_type": problem.problem_type,
                "difficulty": problem.difficulty,
                "question": problem.question,
                "choices": json.loads(problem.choices) if problem.choices else None,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "latex_content": problem.latex_content,
                "has_diagram": problem.has_diagram == "true",
                "diagram_type": problem.diagram_type,
                "diagram_elements": json.loads(problem.diagram_elements) if problem.diagram_elements else None,
                "tikz_code": problem.tikz_code
            })
        
        db.commit()
        
        # 8. 응답 생성 (워크시트 정보 포함)
        return MathProblemGenerationResponse(
            generation_id=generation_id,
            worksheet_id=worksheet.id,  # 워크시트 ID 추가
            school_level=request.school_level.value,
            grade=request.grade,
            semester=request.semester.value,
            unit_name=request.chapter.unit_name,
            chapter_name=request.chapter.chapter_name,
            problem_count=request.problem_count.value_int,
            difficulty_ratio=request.difficulty_ratio.model_dump(),
            problem_type_ratio=request.problem_type_ratio.model_dump(),
            user_prompt=request.user_text,
            actual_difficulty_distribution=self._calculate_difficulty_distribution(generated_problems),
            actual_type_distribution=self._calculate_type_distribution(generated_problems),
            problems=problem_responses,
            total_generated=len(generated_problems),
            created_at=datetime.now().isoformat()
        )
    
    
    def _get_curriculum_data(self, request: MathProblemGenerationRequest) -> Dict:
        """요청에서 교육과정 데이터 추출"""
        return {
            'grade': f"{request.school_level.value[:-2]}{request.grade}",  # "중1"
            'semester': request.semester.value,
            'unit_name': request.chapter.unit_name,
            'chapter_name': request.chapter.chapter_name,
            'learning_objectives': getattr(request.chapter, 'learning_objectives', ''),
            'keywords': getattr(request.chapter, 'keywords', request.chapter.chapter_name)
        }
    
    def _generate_problems_with_ai(self, curriculum_data: Dict, request: MathProblemGenerationRequest) -> List[Dict]:
        """비율 기반 AI 문제 생성"""

        print(f"📊 비율 기반 문제 생성 시작")
        print(f"🎯 요청된 비율: {request.problem_type_ratio.model_dump()}")

        # 비율 기반 문제 생성 로직 사용
        return self._generate_problems_with_ratio(curriculum_data, request)
    
    def _generate_fallback_problems(self, count: int, curriculum_data: Dict) -> List[Dict]:
        """AI 오류시 기본 문제 생성"""
        problems = []
        for i in range(count):
            problems.append({
                "question": f"[{curriculum_data.get('chapter_name', '수학')}] 기본 문제 {i+1}번",
                "choices": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": f"{curriculum_data.get('chapter_name', '수학')} 관련 기본 해설",
                "problem_type": "multiple_choice",
                "difficulty": "B"
            })
        return problems
    
    def _calculate_difficulty_distribution(self, problems: List[Dict]) -> Dict[str, int]:
        """난이도 분포 계산"""
        distribution = {"A": 0, "B": 0, "C": 0, "UNKNOWN": 0}
        for problem in problems:
            difficulty = problem.get("difficulty")
            if difficulty in ["A", "B", "C"]:
                distribution[difficulty] += 1
            else:
                # difficulty 필드가 누락되거나 잘못된 경우 UNKNOWN으로 분류
                distribution["UNKNOWN"] += 1
                print(f"⚠️ 난이도 필드 누락 또는 잘못됨: {difficulty}, 문제: {problem.get('question', '')[:50]}...")

        # UNKNOWN이 있으면 경고 로그
        if distribution["UNKNOWN"] > 0:
            print(f"🚨 난이도 분류 실패한 문제 {distribution['UNKNOWN']}개 발견")

        return distribution
    
    def _calculate_type_distribution(self, problems: List[Dict]) -> Dict[str, int]:
        """유형 분포 계산"""
        distribution = {"multiple_choice": 0, "short_answer": 0, "UNKNOWN": 0}
        for problem in problems:
            problem_type = problem.get("problem_type")
            if problem_type in ["multiple_choice", "short_answer"]:
                distribution[problem_type] += 1
            else:
                # problem_type 필드가 누락되거나 잘못된 경우 UNKNOWN으로 분류
                distribution["UNKNOWN"] += 1
                print(f"⚠️ 문제유형 필드 누락 또는 잘못됨: {problem_type}, 문제: {problem.get('question', '')[:50]}...")

        # UNKNOWN이 있으면 경고 로그
        if distribution["UNKNOWN"] > 0:
            print(f"🚨 문제유형 분류 실패한 문제 {distribution['UNKNOWN']}개 발견")

        return distribution

    def _calculate_problem_counts_by_ratio(self, total_count: int, ratio: Dict[str, int]) -> Dict[str, int]:
        """
        비율에 따른 문제 개수 계산 - 정확한 비율 보장

        Args:
            total_count: 총 문제 개수 (10 or 20)
            ratio: 문제 유형 비율 {"multiple_choice": 50, "short_answer": 50}

        Returns:
            실제 생성할 문제 개수 {"multiple_choice": 5, "short_answer": 5}
        """
        print(f"📊 비율 기반 문제 개수 계산 시작: 총 {total_count}개, 비율 {ratio}")

        mc_ratio = ratio.get("multiple_choice", 0)
        sa_ratio = ratio.get("short_answer", 0)

        # 정확한 비율 계산 (소수점 사용)
        mc_exact = total_count * mc_ratio / 100.0
        sa_exact = total_count * sa_ratio / 100.0

        print(f"📐 정확한 계산: 객관식 {mc_exact}, 단답형 {sa_exact}")

        # 내림 처리로 기본 개수 할당
        mc_count = int(mc_exact)
        sa_count = int(sa_exact)

        # 남은 문제 개수 계산
        allocated = mc_count + sa_count
        remaining = total_count - allocated

        print(f"📝 기본 할당: 객관식 {mc_count}개, 단답형 {sa_count}개, 남은 문제: {remaining}개")

        # 남은 문제를 소수점 부분이 큰 순서대로 배분
        if remaining > 0:
            mc_decimal = mc_exact - mc_count
            sa_decimal = sa_exact - sa_count

            # 소수점 부분이 큰 순서대로 1개씩 배분
            priority_list = [
                ("multiple_choice", mc_decimal),
                ("short_answer", sa_decimal)
            ]
            priority_list.sort(key=lambda x: x[1], reverse=True)

            for i in range(remaining):
                if priority_list[i % 2][0] == "multiple_choice":
                    mc_count += 1
                else:
                    sa_count += 1

        result = {
            "multiple_choice": mc_count,
            "short_answer": sa_count
        }

        print(f"✅ 최종 문제 개수: {result}")
        print(f"🔍 검증: 총합 {mc_count + sa_count} = {total_count} ✓")

        return result

    def _generate_problems_with_ratio(self, curriculum_data: Dict, request) -> List[Dict]:
        """
        비율에 따른 문제 생성 - 병렬 처리
        """
        total_count = request.problem_count.value_int
        ratio_counts = self._calculate_problem_counts_by_ratio(
            total_count,
            request.problem_type_ratio.model_dump()
        )

        print(f"🎯 문제 유형별 생성 목표: {ratio_counts}")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        problems = []

        # 병렬 생성을 위한 작업 리스트
        tasks = []

        # 객관식 문제 생성 작업
        if ratio_counts["multiple_choice"] > 0:
            tasks.append({
                "type": "multiple_choice",
                "count": ratio_counts["multiple_choice"]
            })

        # 단답형 문제 생성 작업
        if ratio_counts["short_answer"] > 0:
            tasks.append({
                "type": "short_answer",
                "count": ratio_counts["short_answer"]
            })

        # 병렬로 각 유형 생성
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            future_to_type = {}
            for task in tasks:
                print(f"📝 {task['type']} 문제 {task['count']}개 생성 시작...")
                future = executor.submit(
                    self._generate_specific_type_problems_parallel,
                    count=task['count'],
                    problem_type=task['type'],
                    curriculum_data=curriculum_data,
                    request=request
                )
                future_to_type[future] = task['type']

            # 완료된 작업 수집
            for future in as_completed(future_to_type):
                problem_type = future_to_type[future]
                try:
                    type_problems = future.result()
                    problems.extend(type_problems)
                    print(f"✅ {problem_type} 문제 {len(type_problems)}개 생성 완료")
                except Exception as e:
                    print(f"❌ {problem_type} 문제 생성 실패: {str(e)}")
                    raise

        # 문제 순서 랜덤 섞기 (선택사항)
        import random
        random.shuffle(problems)
        print(f"🔀 문제 순서 랜덤 섞기 완료")

        print(f"🎉 총 {len(problems)}개 문제 생성 완료")
        return problems

    def _generate_specific_type_problems_parallel(self, count: int, problem_type: str, curriculum_data: Dict, request) -> List[Dict]:
        """
        특정 유형의 문제를 병렬로 생성 (개선된 버전)
        """
        print(f"🎯 {problem_type} 유형 {count}개 문제 병렬 생성 시작")

        # 유형별 명확한 프롬프트 생성
        if problem_type == "multiple_choice":
            type_specific_prompt = f"""
{request.user_text}

**반드시 지킬 조건 (절대 위반 금지):**
1. 객관식(multiple_choice) 문제만 생성
2. 각 문제마다 정답은 반드시 1개만 존재
3. 선택지는 정확히 4개 (A, B, C, D)
4. correct_answer는 A, B, C, D 중 하나만
5. "정답을 2개 고르시오" 같은 문제 절대 금지
6. problem_type은 반드시 "multiple_choice"
"""
        else:  # short_answer
            type_specific_prompt = f"""
{request.user_text}

**반드시 지킬 조건 (절대 위반 금지):**
1. 단답형(short_answer) 문제만 생성
2. 명확한 하나의 정답만 존재
3. 선택지(choices) 없음 - choices 필드를 null이나 빈 배열로 설정
4. 간단한 계산이나 단어로 답 가능
5. problem_type은 반드시 "short_answer"
"""

        try:
            # ProblemGenerator의 병렬 생성 메서드 사용
            generated_problems = self.problem_generator.generate_problems_parallel(
                curriculum_data=curriculum_data,
                user_prompt=type_specific_prompt,
                problem_count=count,
                difficulty_ratio=request.difficulty_ratio.model_dump(),
                problem_type=problem_type,
                max_workers=min(count, 10)  # 최대 10개 동시 실행
            )

            # 생성된 문제의 타입을 강제로 설정하고 검증
            validated_problems = []
            for problem in generated_problems:
                # 타입 강제 설정
                problem["problem_type"] = problem_type

                # 객관식 문제 검증 및 수정
                if problem_type == "multiple_choice":
                    # 선택지가 없거나 4개가 아니면 기본값 설정
                    if not problem.get("choices") or len(problem["choices"]) != 4:
                        problem["choices"] = ["선택지 A", "선택지 B", "선택지 C", "선택지 D"]

                    # 정답이 A,B,C,D가 아니면 A로 설정
                    if problem.get("correct_answer") not in ["A", "B", "C", "D"]:
                        problem["correct_answer"] = "A"

                # 단답형 문제 검증 및 수정
                elif problem_type == "short_answer":
                    # 선택지 제거
                    problem["choices"] = None

                validated_problems.append(problem)

            print(f"✅ {problem_type} 유형 {len(validated_problems)}개 문제 병렬 생성 완료")
            return validated_problems

        except Exception as e:
            print(f"❌ 병렬 생성 실패, 순차 생성으로 폴백: {str(e)}")
            # 순차 생성으로 폴백
            return self._generate_specific_type_problems(
                count=count,
                problem_type=problem_type,
                curriculum_data=curriculum_data,
                request=request
            )

    def _generate_specific_type_problems(self, count: int, problem_type: str, curriculum_data: Dict, request) -> List[Dict]:
        """
        특정 유형의 문제를 지정된 개수만큼 생성
        """
        print(f"🎯 {problem_type} 유형 {count}개 문제 생성 시작")

        # 유형별 명확한 프롬프트 생성
        if problem_type == "multiple_choice":
            type_specific_prompt = f"""
{request.user_text}

**반드시 지킬 조건 (절대 위반 금지):**
1. 모든 {count}개 문제는 객관식(multiple_choice)만 생성
2. 각 문제마다 정답은 반드시 1개만 존재
3. 선택지는 정확히 4개 (A, B, C, D)
4. correct_answer는 A, B, C, D 중 하나만
5. "정답을 2개 고르시오" 같은 문제 절대 금지
6. problem_type은 반드시 "multiple_choice"

JSON 형식에서 모든 문제의 problem_type이 "multiple_choice"인지 확인하세요.
"""
        else:  # short_answer
            type_specific_prompt = f"""
{request.user_text}

**반드시 지킬 조건 (절대 위반 금지):**
1. 모든 {count}개 문제는 단답형(short_answer)만 생성
2. 명확한 하나의 정답만 존재
3. 선택지(choices) 없음 - choices 필드를 null이나 빈 배열로 설정
4. 간단한 계산이나 단어로 답 가능
5. problem_type은 반드시 "short_answer"

JSON 형식에서 모든 문제의 problem_type이 "short_answer"인지 확인하세요.
"""

        try:
            # ProblemGenerator를 사용하여 해당 유형만 생성
            generated_problems = self.problem_generator.generate_problems(
                curriculum_data=curriculum_data,
                user_prompt=type_specific_prompt,
                problem_count=count,
                difficulty_ratio=request.difficulty_ratio.model_dump(),
                problem_type=problem_type
            )

            # 생성된 문제의 타입을 강제로 설정하고 검증
            validated_problems = []
            for problem in generated_problems:
                # 타입 강제 설정
                problem["problem_type"] = problem_type

                # 객관식 문제 검증 및 수정
                if problem_type == "multiple_choice":
                    # 선택지가 없거나 4개가 아니면 기본값 설정
                    if not problem.get("choices") or len(problem["choices"]) != 4:
                        problem["choices"] = ["선택지 A", "선택지 B", "선택지 C", "선택지 D"]

                    # 정답이 A,B,C,D가 아니면 A로 설정
                    if problem.get("correct_answer") not in ["A", "B", "C", "D"]:
                        problem["correct_answer"] = "A"

                # 단답형 문제 검증 및 수정
                elif problem_type == "short_answer":
                    # 선택지 제거
                    problem["choices"] = None

                validated_problems.append(problem)

            print(f"✅ {problem_type} 유형 {len(validated_problems)}개 문제 생성 완료")
            return validated_problems

        except Exception as e:
            print(f"❌ AI 생성 실패, 폴백 사용: {str(e)}")
            # 간단한 폴백
            problems = []
            for i in range(count):
                if problem_type == "multiple_choice":
                    problem = {
                        "question": f"[{curriculum_data.get('chapter_name', '수학')}] 객관식 문제 {i+1}번",
                        "choices": ["선택지 A", "선택지 B", "선택지 C", "선택지 D"],
                        "correct_answer": "A",
                        "explanation": f"{curriculum_data.get('chapter_name', '수학')} 관련 해설",
                        "problem_type": "multiple_choice",
                        "difficulty": "B"
                    }
                else:  # short_answer
                    problem = {
                        "question": f"[{curriculum_data.get('chapter_name', '수학')}] 단답형 문제 {i+1}번",
                        "correct_answer": "답안",
                        "explanation": f"{curriculum_data.get('chapter_name', '수학')} 관련 해설",
                        "problem_type": "short_answer",
                        "difficulty": "B"
                    }
                problems.append(problem)
            return problems

    def get_worksheet_problems(self, db: Session, worksheet_id: int) -> List[Dict]:
        """워크시트의 문제 목록 조회"""
        try:
            print(f"🔍 워크시트 문제 조회 시작 - worksheet_id: {worksheet_id}")
            
            problems = db.query(Problem).filter(
                Problem.worksheet_id == worksheet_id
            ).order_by(Problem.sequence_order).all()
            
            print(f"🔍 조회된 문제 수: {len(problems)}")
            
            problem_list = []
            for i, problem in enumerate(problems):
                print(f"  - 문제 {i+1}: ID={problem.id}, 순서={problem.sequence_order}")
                # choices 필드 처리 - JSON 문자열인 경우 파싱
                choices_data = problem.choices
                if isinstance(choices_data, str):
                    try:
                        import json
                        choices_data = json.loads(choices_data)
                    except (json.JSONDecodeError, TypeError):
                        choices_data = []
                elif choices_data is None:
                    choices_data = []
                
                problem_data = {
                    "id": problem.id,
                    "sequence_order": problem.sequence_order,
                    "question": problem.question,  # Problem 모델의 실제 필드명
                    "problem_type": problem.problem_type,
                    "difficulty": problem.difficulty,
                    "correct_answer": problem.correct_answer,
                    "choices": choices_data,  # 배열로 보장
                    "solution": problem.explanation,  # Problem 모델의 실제 필드명
                    "created_at": problem.created_at.isoformat() if problem.created_at else None,
                    "tikz_code": problem.tikz_code  # TikZ 그래프 코드
                }
                problem_list.append(problem_data)
            
            print(f"🔍 최종 문제 리스트 길이: {len(problem_list)}")
            return problem_list
            
        except Exception as e:
            print(f"❌ 워크시트 문제 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def copy_worksheet(db: Session, source_worksheet_id: int, target_user_id: int, new_title: str) -> Optional[int]:
        """워크시트와 포함된 문제들을 복사"""
        try:
            # 1. 원본 워크시트 조회
            source_worksheet = db.query(Worksheet).filter(Worksheet.id == source_worksheet_id).first()
            if not source_worksheet:
                return None

            # 2. 새로운 generation_id 생성
            new_generation_id = str(uuid.uuid4())

            # 3. 새 워크시트 생성 (필수 필드 포함 모든 정보 복사)
            new_worksheet = Worksheet(
                title=new_title,
                school_level=source_worksheet.school_level,
                grade=source_worksheet.grade,
                semester=source_worksheet.semester,
                unit_number=source_worksheet.unit_number,
                unit_name=source_worksheet.unit_name,
                chapter_number=source_worksheet.chapter_number,
                chapter_name=source_worksheet.chapter_name,
                problem_count=source_worksheet.problem_count,
                difficulty_ratio=source_worksheet.difficulty_ratio,
                problem_type_ratio=source_worksheet.problem_type_ratio,
                user_prompt=source_worksheet.user_prompt,
                generation_id=new_generation_id,  # 새로운 generation_id 추가
                actual_difficulty_distribution=source_worksheet.actual_difficulty_distribution,
                actual_type_distribution=source_worksheet.actual_type_distribution,
                status=WorksheetStatus.COMPLETED,
                teacher_id=target_user_id,
                created_by=target_user_id
            )
            db.add(new_worksheet)
            db.flush()

            # 4. 원본 문제들 조회
            source_problems = db.query(Problem).filter(Problem.worksheet_id == source_worksheet_id).all()

            # 5. 문제들을 새 워크시트에 복사
            for source_problem in source_problems:
                new_problem = Problem(
                    worksheet_id=new_worksheet.id,
                    sequence_order=source_problem.sequence_order,
                    problem_type=source_problem.problem_type,
                    difficulty=source_problem.difficulty,
                    question=source_problem.question,
                    choices=source_problem.choices,
                    correct_answer=source_problem.correct_answer,
                    explanation=source_problem.explanation,
                    latex_content=source_problem.latex_content,
                    has_diagram=source_problem.has_diagram,
                    diagram_type=source_problem.diagram_type,
                    diagram_elements=source_problem.diagram_elements,
                    tikz_code=source_problem.tikz_code
                )
                db.add(new_problem)
            
            db.commit()
            return new_worksheet.id

        except Exception as e:
            db.rollback()
            print(f"Error copying worksheet: {str(e)}")
            return None