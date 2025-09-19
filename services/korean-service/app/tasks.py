from celery import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import uuid
import json
from datetime import datetime

from .celery_app import celery_app
from .database import SessionLocal
from .models.korean_generation import KoreanGeneration
from .models.worksheet import Worksheet, WorksheetStatus
from .models.problem import Problem, ProblemType, Difficulty, KoreanType
from .services.ai_service import AIService


@celery_app.task(bind=True)
def generate_korean_problems_task(self, request_data: dict, user_id: int):
    """국어 문제 생성 태스크"""
    try:
        db = SessionLocal()
        ai_service = AIService()

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '문제 생성 세션 초기화 중...'}
        )

        # 생성 세션 ID 생성
        generation_id = str(uuid.uuid4())

        # 생성 세션 저장
        generation_session = KoreanGeneration(
            generation_id=generation_id,
            user_id=user_id,
            school_level=request_data['school_level'],
            grade=request_data['grade'],
            korean_type=request_data['korean_type'],
            question_type=request_data['question_type'],
            difficulty=request_data['difficulty'],
            problem_count=request_data['problem_count'],
            question_type_ratio=request_data.get('question_type_ratio'),
            difficulty_ratio=request_data.get('difficulty_ratio'),
            user_text=request_data.get('user_text', ''),
            celery_task_id=self.request.id,
            status='processing'
        )
        db.add(generation_session)
        db.commit()

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': '국어 문제 생성 중...'}
        )

        # 새로운 단일 도메인 문제 생성 시스템 사용
        from .services.korean_problem_generator import KoreanProblemGenerator

        korean_data = {
            'school_level': request_data['school_level'],
            'grade': request_data['grade'],
            'korean_type': request_data['korean_type'],
            'question_type': request_data['question_type'],
            'difficulty': request_data['difficulty']
        }

        # 새로운 생성기 사용
        generator = KoreanProblemGenerator()
        problems = generator.generate_problems(
            korean_data=korean_data,
            user_prompt=request_data.get('user_text', ''),
            problem_count=request_data['problem_count'],
            korean_type_ratio=None,  # 단일 도메인이므로 제거
            question_type_ratio=request_data.get('question_type_ratio'),
            difficulty_ratio=request_data.get('difficulty_ratio')
        )

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 60, 'total': 100, 'status': '워크시트 생성 중...'}
        )

        # 워크시트 생성 - 지문 정보 포함
        if problems and len(problems) > 0:
            # 첫 번째 문제에서 지문 정보 추출
            first_problem = problems[0]
            source_title = first_problem.get('source_title', '')
            source_author = first_problem.get('source_author', '')
            
            if source_title and source_author:
                worksheet_title = f"{source_title} - {source_author} ({request_data['problem_count']}문제)"
            else:
                worksheet_title = f"{request_data['korean_type']} - {request_data['question_type']} ({request_data['problem_count']}문제)"
        else:
            worksheet_title = f"{request_data['korean_type']} - {request_data['question_type']} ({request_data['problem_count']}문제)"

        worksheet = Worksheet(
            title=worksheet_title,
            school_level=request_data['school_level'],
            grade=request_data['grade'],
            korean_type=request_data['korean_type'],
            question_type=request_data['question_type'],
            difficulty=request_data['difficulty'],
            problem_count=request_data['problem_count'],
            question_type_ratio=request_data.get('question_type_ratio'),
            difficulty_ratio=request_data.get('difficulty_ratio'),
            user_text=request_data.get('user_text', ''),
            generation_id=generation_id,
            teacher_id=user_id,
            status=WorksheetStatus.PROCESSING
        )
        db.add(worksheet)
        db.flush()  # ID 생성을 위해

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': '문제 저장 중...'}
        )

        # 문제들 저장
        saved_problems = []
        korean_type_counts = {}
        question_type_counts = {}
        difficulty_counts = {}

        for idx, problem_data in enumerate(problems):
            if not problem_data:
                continue

            # Enum 값 처리
            korean_type_enum = getattr(KoreanType, problem_data.get('korean_type', 'POEM').upper().replace('/', '_').replace(' ', '_'), KoreanType.POEM)
            problem_type_enum = getattr(ProblemType, problem_data.get('question_type', '객관식').replace('객관식', 'MULTIPLE_CHOICE').replace('서술형', 'ESSAY').replace('단답형', 'SHORT_ANSWER'), ProblemType.MULTIPLE_CHOICE)
            difficulty_enum = getattr(Difficulty, problem_data.get('difficulty', '중').replace('상', 'HIGH').replace('중', 'MEDIUM').replace('하', 'LOW'), Difficulty.MEDIUM)

            problem = Problem(
                worksheet_id=worksheet.id,
                sequence_order=idx + 1,
                korean_type=korean_type_enum,
                problem_type=problem_type_enum,
                difficulty=difficulty_enum,
                question=problem_data.get('question', ''),
                choices=json.dumps(problem_data.get('choices'), ensure_ascii=False) if problem_data.get('choices') else None,
                correct_answer=problem_data.get('correct_answer', ''),
                explanation=problem_data.get('explanation', ''),
                source_text=problem_data.get('source_text', ''),
                source_title=problem_data.get('source_title', ''),
                source_author=problem_data.get('source_author', ''),
                ai_model_used='gemini-2.5-pro'
            )
            db.add(problem)
            saved_problems.append(problem)

            # 분포 계산
            korean_type_key = problem_data.get('korean_type', '')
            question_type_key = problem_data.get('question_type', '')
            difficulty_key = problem_data.get('difficulty', '')

            korean_type_counts[korean_type_key] = korean_type_counts.get(korean_type_key, 0) + 1
            question_type_counts[question_type_key] = question_type_counts.get(question_type_key, 0) + 1
            difficulty_counts[difficulty_key] = difficulty_counts.get(difficulty_key, 0) + 1

        # 워크시트 상태 업데이트
        worksheet.status = WorksheetStatus.COMPLETED
        worksheet.actual_korean_type_distribution = korean_type_counts
        worksheet.actual_question_type_distribution = question_type_counts
        worksheet.actual_difficulty_distribution = difficulty_counts

        # 생성 세션 업데이트
        generation_session.status = 'completed'
        generation_session.total_generated = len(saved_problems)
        generation_session.actual_korean_type_distribution = korean_type_counts
        generation_session.actual_question_type_distribution = question_type_counts
        generation_session.actual_difficulty_distribution = difficulty_counts

        db.commit()

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': '완료!'}
        )

        return {
            "worksheet_id": worksheet.id,
            "generation_id": generation_id,
            "total_problems": len(saved_problems),
            "korean_type_distribution": korean_type_counts,
            "question_type_distribution": question_type_counts,
            "difficulty_distribution": difficulty_counts
        }

    except Exception as e:
        # 오류 발생 시 세션 상태 업데이트
        try:
            generation_session.status = 'failed'
            db.commit()
        except:
            pass

        db.close()
        raise Exception(f"국어 문제 생성 중 오류: {str(e)}")

    finally:
        db.close()


@celery_app.task(bind=True)
def grade_korean_problems_task(self, worksheet_id: int, image_data: bytes = None,
                              multiple_choice_answers: dict = None, user_id: int = 1):
    """국어 문제 채점 태스크"""
    try:
        db = SessionLocal()
        ai_service = AIService()

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '채점 준비 중...'}
        )

        # 워크시트와 문제들 조회
        from .models.worksheet import Worksheet
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
        if not worksheet:
            raise Exception("워크시트를 찾을 수 없습니다.")

        problems = db.query(Problem).filter(Problem.worksheet_id == worksheet_id).order_by(Problem.sequence_order).all()

        # 채점 세션 생성
        from .models.grading_result import KoreanGradingSession, KoreanProblemGradingResult

        grading_session = KoreanGradingSession(
            worksheet_id=worksheet_id,
            graded_by=user_id,
            total_problems=len(problems),
            max_possible_score=float(len(problems) * 100),
            points_per_problem=100.0,
            input_method="manual" if multiple_choice_answers else "ocr",
            multiple_choice_answers=multiple_choice_answers,
            celery_task_id=self.request.id
        )

        if image_data:
            # OCR 처리
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 30, 'total': 100, 'status': 'OCR 처리 중...'}
            )
            ocr_text = ai_service.ocr_handwriting(image_data)
            grading_session.ocr_text = ocr_text

        db.add(grading_session)
        db.flush()

        # 문제별 채점
        total_score = 0
        correct_count = 0

        for idx, problem in enumerate(problems):
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'current': 30 + int((idx / len(problems)) * 60),
                    'total': 100,
                    'status': f'{idx + 1}/{len(problems)} 문제 채점 중...'
                }
            )

            # 학생 답안 추출
            if multiple_choice_answers and str(problem.id) in multiple_choice_answers:
                student_answer = multiple_choice_answers[str(problem.id)]
                input_method = "manual"
            else:
                student_answer = ""  # OCR에서 추출해야 함
                input_method = "ocr"

            # AI 채점
            grading_result = ai_service.grade_korean_answer(
                question=problem.question,
                correct_answer=problem.correct_answer,
                student_answer=student_answer,
                explanation=problem.explanation,
                question_type=problem.problem_type.value if hasattr(problem.problem_type, 'value') else str(problem.problem_type)
            )

            # 채점 결과 저장
            problem_result = KoreanProblemGradingResult(
                grading_session_id=grading_session.id,
                problem_id=problem.id,
                user_answer=student_answer,
                correct_answer=problem.correct_answer,
                is_correct=grading_result['is_correct'],
                score=float(grading_result['score']),
                points_per_problem=100.0,
                problem_type=problem.problem_type.value if hasattr(problem.problem_type, 'value') else str(problem.problem_type),
                input_method=input_method,
                ai_score=grading_result.get('score'),
                ai_feedback=grading_result.get('ai_feedback', ''),
                strengths=grading_result.get('strengths', ''),
                improvements=grading_result.get('improvements', ''),
                keyword_score_ratio=grading_result.get('keyword_score_ratio', 0.0),
                explanation=problem.explanation
            )
            db.add(problem_result)

            total_score += grading_result['score']
            if grading_result['is_correct']:
                correct_count += 1

        # 채점 세션 결과 업데이트
        grading_session.total_score = float(total_score)
        grading_session.correct_count = correct_count

        db.commit()

        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': '채점 완료!'}
        )

        return {
            "grading_session_id": grading_session.id,
            "total_problems": len(problems),
            "correct_count": correct_count,
            "total_score": total_score,
            "average_score": total_score / len(problems) if problems else 0
        }

    except Exception as e:
        db.close()
        raise Exception(f"국어 문제 채점 중 오류: {str(e)}")

    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.regenerate_korean_problem_task")
def regenerate_korean_problem_task(self, problem_id: int, requirements: str, current_problem: dict):
    """국어 문제 재생성 태스크"""
    try:
        db = SessionLocal()

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '문제 재생성 준비 중...'}
        )

        # 기존 문제 조회
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            raise Exception(f"문제를 찾을 수 없습니다: {problem_id}")

        # 워크시트 정보 조회
        worksheet = db.query(Worksheet).filter(Worksheet.id == problem.worksheet_id).first()
        if not worksheet:
            raise Exception("워크시트를 찾을 수 없습니다.")

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': '새 문제 생성 중...'}
        )

        # 빠른 재생성을 위한 AI 서비스 사용
        from .services.ai_service import AIService
        ai_service = AIService()

        # 기존 문제와 요구사항을 포함한 프롬프트 생성
        enhanced_prompt = f"""
다음 문제를 개선해주세요:

기존 문제:
질문: {current_problem.get('question', '')}
선택지: {current_problem.get('choices', [])}
정답: {current_problem.get('correct_answer', '')}
해설: {current_problem.get('explanation', '')}

개선 요구사항:
{requirements}

위 요구사항을 반영하여 더 나은 문제로 재생성해주세요.
"""

        # 빠른 재생성 메서드 사용 (복잡한 파이프라인 없이)
        new_problem_data = ai_service.regenerate_single_problem(
            current_problem=current_problem,
            requirements=enhanced_prompt
        )

        if not new_problem_data:
            raise Exception("새 문제 생성에 실패했습니다.")

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': '문제 업데이트 중...'}
        )

        # 기존 문제 업데이트
        problem.question = new_problem_data.get('question', problem.question)
        problem.choices = json.dumps(new_problem_data.get('choices'), ensure_ascii=False) if new_problem_data.get('choices') else problem.choices
        problem.correct_answer = new_problem_data.get('correct_answer', problem.correct_answer)
        problem.explanation = new_problem_data.get('explanation', problem.explanation)
        problem.source_text = new_problem_data.get('source_text', problem.source_text)
        problem.source_title = new_problem_data.get('source_title', problem.source_title)
        problem.source_author = new_problem_data.get('source_author', problem.source_author)

        db.commit()

        # 진행 상황 업데이트
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': '재생성 완료!'}
        )

        return {
            'success': True,
            'problem_id': problem_id,
            'updated_problem': {
                'question': problem.question,
                'choices': json.loads(problem.choices) if problem.choices else None,
                'correct_answer': problem.correct_answer,
                'explanation': problem.explanation,
                'source_text': problem.source_text,
                'source_title': problem.source_title,
                'source_author': problem.source_author
            }
        }

    except Exception as e:
        # 오류 로깅
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        db.close()
        raise Exception(f"국어 문제 재생성 중 오류: {str(e)}")

    finally:
        db.close()