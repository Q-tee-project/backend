from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import json
import uuid

from app.database import get_db
from app.core.config import get_settings
from app.schemas.generation import WorksheetGenerationRequest
from app.schemas.worksheet import (
    WorksheetSaveRequest, WorksheetResponse, WorksheetSummary
)
from app.models import (
    GradingResult, QuestionResult, Worksheet, Passage, Question
)
from app.services.generation.question_generator import PromptGenerator

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini 라이브러리가 설치되지 않았습니다.")

router = APIRouter(tags=["Worksheets"])
settings = get_settings()

@router.post("/worksheet-generate")
async def worksheet_generate(request: WorksheetGenerationRequest, db: Session = Depends(get_db)):
    """사용자로부터 문제 생성 옵션을 입력받습니다."""
    print("🚨 함수 시작 - 요청이 서버에 도달했습니다!")
    
    try:
        print("\n" + "="*80)
        print("🎯 문제 생성 옵션 입력 받음!")
        
        print(f" 학교급: {request.school_level}")
        print(f" 학년: {request.grade}학년")
        print(f" 총 문제 수: {request.total_questions}개")
        
        print(f"\n🎯 선택된 영역: {', '.join(request.subjects)}")
        
        # 세부 영역 정보 출력
        if request.subject_details:
            print("\n📋 세부 영역 선택:")
            
            if request.subject_details.reading_types:
                print(f"  📖 독해 유형: {', '.join(request.subject_details.reading_types)}")
            
            if request.subject_details.grammar_categories:
                print(f"  📝 문법 카테고리: {', '.join(request.subject_details.grammar_categories)}")
                
            if request.subject_details.grammar_topics:
                print(f"  📝 문법 토픽: {', '.join(request.subject_details.grammar_topics)}")
            
            if request.subject_details.vocabulary_categories:
                print(f"  📚 어휘 카테고리: {', '.join(request.subject_details.vocabulary_categories)}")
        
        # 영역별 비율 출력
        if request.subject_ratios:
            print("\n⚖️ 영역별 비율:")
            for ratio in request.subject_ratios:
                print(f"  {ratio.subject}: {ratio.ratio}%")
        
        # 문제 형식 출력
        print(f"\n📋 문제 형식: {request.question_format}")
        if request.format_ratios:
            print("📊 형식별 비율:")
            for format_ratio in request.format_ratios:
                print(f"  {format_ratio.format}: {format_ratio.ratio}%")
        
        # 난이도 분배 출력
        if request.difficulty_distribution:
            print("\n🎯 난이도 분배:")
            for diff in request.difficulty_distribution:
                print(f"  {diff.difficulty}: {diff.ratio}%")
        
        # 추가 요구사항 출력
        if request.additional_requirements:
            print(f"\n📝 추가 요구사항:")
            print(f"  {request.additional_requirements}")
        
        print("="*80)
        
        # 프롬프트 생성기 초기화 및 실행
        print("\n🎯 프롬프트 생성 시작...")
        generator = PromptGenerator()
        
        # 요청 데이터를 딕셔너리로 변환
        request_dict = request.dict()
        
        # 분배 요약 생성
        distribution_summary = generator.get_distribution_summary(request_dict)
        
        print("📊 분배 결과:")
        print(f"  총 문제 수: {distribution_summary['total_questions']}")
        print("  영역별 분배:")
        for item in distribution_summary['subject_distribution']:
            print(f"    {item['subject']}: {item['count']}문제 ({item['ratio']}%)")
        print("  형식별 분배:")
        for item in distribution_summary['format_distribution']:
            print(f"    {item['format']}: {item['count']}문제 ({item['ratio']}%)")
        print("  난이도별 분배:")
        for item in distribution_summary['difficulty_distribution']:
            print(f"    {item['difficulty']}: {item['count']}문제 ({item['ratio']}%)")
        print(f"  검증 통과: {distribution_summary['validation_passed']}")
        
        # 프롬프트 생성
        try:
            print("🔍 프롬프트 생성 시도 중...")
            
            # 디버깅: difficulty_distribution 데이터 확인
            print(f"\n🔍 디버깅 - request_dict['difficulty_distribution']: {request_dict.get('difficulty_distribution', 'NOT_FOUND')}")
            if 'difficulty_distribution' in request_dict:
                for i, diff in enumerate(request_dict['difficulty_distribution']):
                    print(f"  [{i}] difficulty: '{diff.get('difficulty')}', ratio: {diff.get('ratio')} (type: {type(diff.get('ratio'))})")
            
            prompt = generator.generate_prompt(request_dict, db=db)
            print("✅ 프롬프트 생성 성공!")
            print(f"🔍 프롬프트: {prompt}")
        except Exception as prompt_error:
            print(f"❌ 프롬프트 생성 오류: {prompt_error}")
            raise prompt_error
        
        # LLM에 프롬프트 전송 및 응답 받기
        llm_response = None
        llm_error = None
        
        if GEMINI_AVAILABLE:
            try:
                print("🤖 Gemini API 호출 시작...")

                # Gemini API 키 설정
                if not settings.gemini_api_key:
                    raise Exception("GEMINI_API_KEY가 설정되지 않았습니다.")
                
                genai.configure(api_key=settings.gemini_api_key)
                
                # Gemini 모델 생성
                model = genai.GenerativeModel(settings.gemini_model)
                
                # 통합 프롬프트로 API 한 번만 호출 (JSON 응답 요청)
                print("📝 통합 문제지/답안지 생성 중...")
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                llm_response = response.text
                print("✅ 통합 생성 완료!")
                
            except Exception as api_error:
                print(f"❌ Gemini API 호출 오류: {api_error}")
                llm_error = str(api_error)
        else:
            llm_error = "Gemini 라이브러리가 설치되지 않았습니다."
        
        print("\n🎯 영역별 출제 유형 확인:")
        subject_details = request_dict.get('subject_details', {})
        print(f"  독해 유형: {subject_details.get('reading_types', [])}")
        print(f"  문법 카테고리: {subject_details.get('grammar_categories', [])}")
        print(f"  문법 토픽: {subject_details.get('grammar_topics', [])}")
        print(f"  어휘 카테고리: {subject_details.get('vocabulary_categories', [])}")
        
        print("\n✅ 프롬프트 생성 완료!")
        print("="*80)
        
        # JSON 파싱 처리
        parsed_llm_response = None
        
        if llm_response:
            try:
                # 통합 JSON 파싱
                parsed_llm_response = json.loads(llm_response)
                print("✅ 통합 JSON 파싱 완료!")
            except json.JSONDecodeError as e:
                print(f"⚠️ 통합 JSON 파싱 실패: {e}")
                parsed_llm_response = None
        
        # 백엔드에서 결과 출력
        print("=" * 80)
        print("🎉 문제지 및 답안지 생성 완료!")
        print("=" * 80)
        if parsed_llm_response:
            print(f"📄 문제지 ID: {parsed_llm_response.get('worksheet_id', 'N/A')}")
            print(f"📝 문제지 제목: {parsed_llm_response.get('worksheet_name', 'N/A')}")
            print(f"📊 총 문제 수: {parsed_llm_response.get('total_questions', 'N/A')}개")
        print("=" * 80)

        return {
            "message": "문제지와 답안지 생성이 완료되었습니다!" if llm_response else "프롬프트가 생성되었습니다!",
            "status": "success",
            "llm_response": parsed_llm_response,  # 파싱된 객체 전달
            "llm_error": llm_error,
        }
        
    except Exception as e:
        print(f"❌ 옵션 입력 오류: {str(e)}")
        return {
            "message": f"옵션 입력 중 오류가 발생했습니다: {str(e)}",
            "status": "error"
        }

@router.post("/worksheets", response_model=Dict[str, Any])
async def save_worksheet(request: WorksheetSaveRequest, db: Session = Depends(get_db)):
    """생성된 문제지를 데이터베이스에 저장합니다."""
    print("🚨 저장 요청 시작!")
    try:
        worksheet_data = request.worksheet_data
        
        # 문제지 메타데이터 추출
        worksheet_id = str(uuid.uuid4())  # UUID로 자동 생성
        teacher_id = worksheet_data.get('teacher_id')
        worksheet_name = worksheet_data.get('worksheet_name')
        school_level = worksheet_data.get('worksheet_level')
        grade = str(worksheet_data.get('worksheet_grade'))
        subject = worksheet_data.get('worksheet_subject', '영어')
        total_questions = worksheet_data.get('total_questions')
        duration = worksheet_data.get('worksheet_duration')
        
        print(f"🆔 생성된 워크시트 UUID: {worksheet_id}")
        
        # 중복 확인 (UUID는 거의 중복될 가능성이 없지만 안전장치로 유지)
        existing = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if existing:
            # 만약 UUID가 중복되면 새로 생성
            worksheet_id = str(uuid.uuid4())
            print(f"🔄 UUID 중복으로 재생성: {worksheet_id}")
        
        # 1. Worksheet 생성
        db_worksheet = Worksheet(
            worksheet_id=worksheet_id,
            worksheet_name=worksheet_name,
            school_level=school_level,
            grade=grade,
            subject=subject,
            total_questions=total_questions,
            duration=int(duration) if duration else None,
            created_at=datetime.now()
        )
        db.add(db_worksheet)
        db.flush()
        
        # 2. Passages 저장
        passages_data = worksheet_data.get('passages', [])
        for passage_data in passages_data:
            db_passage = Passage(
                worksheet_id=db_worksheet.worksheet_id,
                passage_id=passage_data.get('passage_id'),
                passage_type=passage_data.get('passage_type'),
                passage_content=passage_data.get('passage_content'),
                original_content=passage_data.get('original_content'),
                korean_translation=passage_data.get('korean_translation'),
                related_questions=passage_data.get('related_questions', []),
                created_at=datetime.now()
            )
            db.add(db_passage)
        
        # 3. Examples는 이제 Question 모델에 포함됨 (별도 저장 불필요)
        
        # 4. Questions 저장
        questions_data = worksheet_data.get('questions', [])
        for question_data in questions_data:
            db_question = Question(
                worksheet_id=db_worksheet.worksheet_id,
                question_id=question_data.get('question_id'),
                question_text=question_data.get('question_text'),
                question_type=question_data.get('question_type'),
                question_subject=question_data.get('question_subject'),
                question_difficulty=question_data.get('question_difficulty'),
                question_detail_type=question_data.get('question_detail_type'),
                question_choices=question_data.get('question_choices'),
                passage_id=question_data.get('question_passage_id'),
                correct_answer=question_data.get('correct_answer'),
                example_content=question_data.get('example_content', ''),
                example_original_content=question_data.get('example_original_content'),
                example_korean_translation=question_data.get('example_korean_translation'),
                explanation=question_data.get('explanation'),
                learning_point=question_data.get('learning_point'),
                created_at=datetime.now()
            )
            db.add(db_question)
        
        # 커밋
        db.commit()
        db.refresh(db_worksheet)
        
        return {
            "message": "문제지가 성공적으로 저장되었습니다.",
            "worksheet_id": worksheet_id,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 문제지 저장 오류 상세:")
        print(f"   오류 타입: {type(e).__name__}")
        print(f"   오류 메시지: {str(e)}")
        print(f"   오류 위치: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
        import traceback
        print(f"   전체 스택 트레이스:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"문제지 저장 중 오류: {str(e)}")

@router.get("/worksheets", response_model=List[WorksheetSummary])
async def get_worksheets(db: Session = Depends(get_db)):
    """저장된 문제지 목록을 조회합니다."""
    try:
        worksheets = db.query(Worksheet).order_by(Worksheet.created_at.desc()).all()
        return [
            WorksheetSummary(
                id=worksheet.worksheet_id,
                worksheet_id=worksheet.worksheet_id,
                worksheet_name=worksheet.worksheet_name,
                school_level=worksheet.school_level,
                grade=worksheet.grade,
                subject=worksheet.subject,
                total_questions=worksheet.total_questions,
                duration=worksheet.duration,
                created_at=worksheet.created_at
            )
            for worksheet in worksheets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제지 목록 조회 중 오류: {str(e)}")

@router.get("/worksheets/{worksheet_id}/edit")
async def get_worksheet_for_editing(worksheet_id: str, db: Session = Depends(get_db)):
    """문제지 편집용 워크시트를 조회합니다 (정답 및 해설 포함)."""
    try:
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        # 문제지 데이터를 딕셔너리로 변환
        worksheet_data = {
            "worksheet_id": worksheet.worksheet_id,
            "worksheet_name": worksheet.worksheet_name,
            "worksheet_level": worksheet.school_level,
            "worksheet_grade": worksheet.grade,
            "worksheet_subject": worksheet.subject,
            "total_questions": worksheet.total_questions,
            "worksheet_duration": worksheet.duration,
            "passages": [],
            "examples": [],
            "questions": []
        }
        
        # 지문 데이터 추가
        for passage in worksheet.passages:
            passage_data = {
                "passage_id": passage.passage_id,
                "passage_type": passage.passage_type,
                "passage_content": passage.passage_content,
                "original_content": passage.original_content,
                "korean_translation": passage.korean_translation,
                "related_questions": passage.related_questions
            }
            worksheet_data["passages"].append(passage_data)
        
        # 예문 데이터 추가
        for example in worksheet.examples:
            example_data = {
                "example_id": example.example_id,
                "example_content": example.example_content,
                "original_content": example.original_content,
                "korean_translation": example.korean_translation,
                "related_question": example.related_question
            }
            worksheet_data["examples"].append(example_data)
        
        # 문제 데이터 추가 (정답/해설 포함)
        for question in worksheet.questions:
            question_data = {
                "question_id": question.question_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "question_subject": question.question_subject,
                "question_difficulty": question.question_difficulty,
                "question_detail_type": question.question_detail_type,
                "question_choices": question.question_choices,
                "question_passage_id": question.passage_id,
                "question_example_id": question.example_id,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "learning_point": question.learning_point
            }
            worksheet_data["questions"].append(question_data)
        
        return {
            "status": "success",
            "message": "편집용 문제지를 성공적으로 조회했습니다.",
            "worksheet_data": worksheet_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"편집용 문제지 조회 중 오류: {str(e)}")

@router.get("/worksheets/{worksheet_id}/solve")
async def get_worksheet_for_solving(worksheet_id: str, db: Session = Depends(get_db)):
    """문제 풀이용 문제지를 조회합니다 (답안 제외)."""
    try:
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        # 문제지 데이터를 딕셔너리로 변환
        worksheet_data = {
            "worksheet_id": worksheet.worksheet_id,
            "worksheet_name": worksheet.worksheet_name,
            "worksheet_level": worksheet.school_level,
            "worksheet_grade": worksheet.grade,
            "worksheet_subject": worksheet.subject,
            "total_questions": worksheet.total_questions,
            "worksheet_duration": worksheet.duration,
            "passages": [],
            "examples": [],
            "questions": []
        }
        
        # 지문 데이터 추가 (한글 번역 포함)
        for passage in worksheet.passages:
            worksheet_data["passages"].append({
                "passage_id": passage.passage_id,
                "passage_type": passage.passage_type,
                "passage_content": passage.passage_content,
                "original_content": passage.original_content,
                "korean_translation": passage.korean_translation,
                "related_questions": passage.related_questions
            })
        
        # 예문 데이터 추가 (한글 번역 포함)
        for example in worksheet.examples:
            worksheet_data["examples"].append({
                "example_id": example.example_id,
                "example_content": example.example_content,
                "original_content": example.original_content,
                "korean_translation": example.korean_translation,
                "related_question": example.related_question
            })
        
        # 문제 데이터 추가 (답안 제외)
        for question in worksheet.questions:
            worksheet_data["questions"].append({
                "question_id": question.question_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "question_subject": question.question_subject,
                "question_difficulty": question.question_difficulty,
                "question_detail_type": question.question_detail_type,
                "question_choices": question.question_choices,
                "question_passage_id": question.passage_id,
                "question_example_id": question.example_id
            })
        
        # 응답 데이터 구조 통일 (채점 결과 호환성)
        return {
            "worksheet_id": worksheet_data["worksheet_id"],
            "worksheet_name": worksheet_data["worksheet_name"],
            "worksheet_level": worksheet_data["worksheet_level"],
            "worksheet_grade": worksheet_data["worksheet_grade"],
            "worksheet_subject": worksheet_data["worksheet_subject"],
            "total_questions": worksheet_data["total_questions"],
            "worksheet_duration": worksheet_data["worksheet_duration"],
            "passages": worksheet_data["passages"],
            "examples": worksheet_data["examples"],
            "questions": worksheet_data["questions"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제지 조회 중 오류: {str(e)}")

@router.put("/worksheets/{worksheet_id}/questions/{question_id}/text")
async def update_question_text(worksheet_id: str, question_id: int, request: Dict[str, str], db: Session = Depends(get_db)):
    """문제 텍스트를 업데이트합니다."""
    try:
        question = db.query(Question).filter(
            Question.worksheet_id == worksheet_id,
            Question.question_id == question_id
        ).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
        
        question.question_text = request.get("question_text")
        db.commit()
        
        return {"status": "success", "message": "문제 텍스트가 업데이트되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"문제 텍스트 업데이트 중 오류: {str(e)}")

@router.put("/worksheets/{worksheet_id}/questions/{question_id}/choice")
async def update_question_choice(worksheet_id: str, question_id: int, request: Dict[str, Any], db: Session = Depends(get_db)):
    """문제 선택지를 업데이트합니다."""
    try:
        question = db.query(Question).filter(
            Question.worksheet_id == worksheet_id,
            Question.question_id == question_id
        ).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
        
        choice_index = request.get("choice_index")
        choice_text = request.get("choice_text")
        
        if question.question_choices and isinstance(question.question_choices, list):
            if 0 <= choice_index < len(question.question_choices):
                question.question_choices[choice_index] = choice_text
                db.commit()
                
                return {"status": "success", "message": "선택지가 업데이트되었습니다."}
        
        raise HTTPException(status_code=400, detail="유효하지 않은 선택지 인덱스입니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"선택지 업데이트 중 오류: {str(e)}")

@router.put("/worksheets/{worksheet_id}/questions/{question_id}/answer")
async def update_question_answer(worksheet_id: str, question_id: int, request: Dict[str, str], db: Session = Depends(get_db)):
    """문제 정답을 업데이트합니다."""
    try:
        question = db.query(Question).filter(
            Question.worksheet_id == worksheet_id,
            Question.question_id == question_id
        ).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
        
        question.correct_answer = request.get("correct_answer")
        db.commit()
        
        return {"status": "success", "message": "정답이 업데이트되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"정답 업데이트 중 오류: {str(e)}")

@router.put("/worksheets/{worksheet_id}/passages/{passage_id}")
async def update_passage(worksheet_id: str, passage_id: int, request: Dict[str, Any], db: Session = Depends(get_db)):
    """지문을 업데이트합니다."""
    try:
        passage = db.query(Passage).filter(
            Passage.worksheet_id == worksheet_id,
            Passage.passage_id == passage_id
        ).first()
        
        if not passage:
            raise HTTPException(status_code=404, detail="지문을 찾을 수 없습니다.")
        
        # JSON 형식 유지하면서 업데이트
        passage_content = request.get("passage_content")
        if isinstance(passage_content, str):
            # 문자열인 경우 JSON으로 파싱 시도
            try:
                import json
                passage_content = json.loads(passage_content)
            except json.JSONDecodeError:
                # JSON이 아닌 경우 기존 구조 유지하면서 내용만 업데이트
                if isinstance(passage.passage_content, dict):
                    passage.passage_content["content"] = passage_content
                else:
                    passage.passage_content = {"content": passage_content}
        else:
            passage.passage_content = passage_content
        
        db.commit()
        
        return {"status": "success", "message": "지문이 업데이트되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"지문 업데이트 중 오류: {str(e)}")

@router.put("/worksheets/{worksheet_id}/examples/{example_id}")
# 예문 업데이트는 이제 Question 모델을 통해 처리됨

@router.put("/worksheets/{worksheet_id}/title")
async def update_worksheet_title(worksheet_id: str, request: Dict[str, str], db: Session = Depends(get_db)):
    """문제지 제목을 업데이트합니다."""
    try:
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        worksheet.worksheet_name = request.get("worksheet_name")
        db.commit()
        
        return {"status": "success", "message": "문제지 제목이 업데이트되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"문제지 제목 업데이트 중 오류: {str(e)}")

@router.delete("/worksheets/{worksheet_id}", response_model=Dict[str, Any])
async def delete_worksheet(worksheet_id: str, db: Session = Depends(get_db)):
    """문제지와 관련된 모든 데이터를 삭제합니다."""
    try:
        # 문제지 존재 확인
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        worksheet_name = worksheet.worksheet_name
        
        # 관련된 채점 결과 삭제
        grading_results = db.query(GradingResult).filter(GradingResult.worksheet_id == worksheet_id).all()
        for result in grading_results:
            db.query(QuestionResult).filter(QuestionResult.grading_result_id == result.result_id).delete()
            db.delete(result)
        
        # 2. 문제 삭제
        db.query(Question).filter(Question.worksheet_id == worksheet_id).delete()
        
        # 3. 지문 삭제
        db.query(Passage).filter(Passage.worksheet_id == worksheet_id).delete()
        
        # 4. 예문은 Question 모델에 포함되어 있으므로 별도 삭제 불필요
        
        # 5. 문제지 삭제
        db.delete(worksheet)
        
        # 변경사항 커밋
        db.commit()
        
        return {
            "status": "success",
            "message": f"문제지 '{worksheet_name}'이 성공적으로 삭제되었습니다.",
            "deleted_worksheet_id": worksheet_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"문제지 삭제 중 오류: {str(e)}")