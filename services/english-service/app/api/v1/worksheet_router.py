from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import json
import uuid

from app.database import get_db
from app.core.config import get_settings
from app.schemas.schemas import (
    QuestionGenerationRequest, WorksheetSaveRequest, 
    WorksheetResponse, WorksheetSummary
)
from app.models.models import (
    GradingResult, QuestionResult, Worksheet, Passage, Example, Question
)
from app.services.question_generator import PromptGenerator

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini 라이브러리가 설치되지 않았습니다.")

router = APIRouter(tags=["Worksheets"])
settings = get_settings()

@router.post("/question-options")
async def receive_question_options(request: QuestionGenerationRequest, db: Session = Depends(get_db)):
    """사용자로부터 문제 생성 옵션을 입력받습니다."""
    print("🚨 함수 시작 - 요청이 서버에 도달했습니다!")
    
    try:
        print("\n" + "="*80)
        print("🎯 문제 생성 옵션 입력 받음!")
        print("="*80)
        
        print(f"🏫 학교급: {request.school_level}")
        print(f"📚 학년: {request.grade}학년")
        print(f"📊 총 문제 수: {request.total_questions}개")
        
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
            prompt = generator.generate_prompt(request_dict, db=db)
            print("✅ 프롬프트 생성 성공!")
            
        except Exception as prompt_error:
            print(f"❌ 프롬프트 생성 오류: {prompt_error}")
            raise prompt_error
        
        # LLM에 프롬프트 전송 및 응답 받기
        llm_response = None
        answer_sheet = None
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
                answer_sheet = llm_response # 호환성을 위해 동일 데이터 할당
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
        parsed_answer_sheet = None
        
        if llm_response:
            try:
                # 통합 JSON 파싱
                parsed_llm_response = json.loads(llm_response)
                parsed_answer_sheet = parsed_llm_response # 동일 객체 할당
                print("✅ 통합 JSON 파싱 완료!")
            except json.JSONDecodeError as e:
                print(f"⚠️ 통합 JSON 파싱 실패: {e}")
                parsed_llm_response = None
                parsed_answer_sheet = None
        
        # 백엔드에서 결과 출력
        print("=" * 80)
        print("🎉 문제지 및 답안지 생성 완료!")
        print("=" * 80)
        if parsed_llm_response:
            print(f"📄 문제지 ID: {parsed_llm_response.get('worksheet_id', 'N/A')}")
            print(f"📝 문제지 제목: {parsed_llm_response.get('worksheet_name', 'N/A')}")
            print(f"📊 총 문제 수: {parsed_llm_response.get('total_questions', 'N/A')}개")
        if parsed_answer_sheet:
            passages_count = len(parsed_answer_sheet.get("answer_sheet", {}).get("passages", []))
            examples_count = len(parsed_answer_sheet.get("answer_sheet", {}).get("examples", []))
            questions_count = len(parsed_answer_sheet.get("answer_sheet", {}).get("questions", []))
            print(f"📖 지문 수: {passages_count}개 (한글 번역 포함)")
            print(f"📝 예문 수: {examples_count}개 (한글 번역 포함)")
            print(f"🔍 정답 및 해설: {questions_count}개")
        print("=" * 80)

        return {
            "message": "문제지와 답안지 생성이 완료되었습니다!" if llm_response else "프롬프트가 생성되었습니다!",
            "status": "success",
            "request_data": request.dict(),
            "distribution_summary": distribution_summary,
            "prompt": prompt,
            "llm_response": parsed_llm_response,  # 파싱된 객체 전달
            "answer_sheet": parsed_answer_sheet,  # 파싱된 객체 전달
            "llm_error": llm_error,
            "subject_types_validation": {
                "reading_types": subject_details.get('reading_types', []),
                "grammar_categories": subject_details.get('grammar_categories', []),
                "grammar_topics": subject_details.get('grammar_topics', []),
                "vocabulary_categories": subject_details.get('vocabulary_categories', [])
            }
        }
        
    except Exception as e:
        print(f"❌ 옵션 입력 오류: {str(e)}")
        return {
            "message": f"옵션 입력 중 오류가 발생했습니다: {str(e)}",
            "status": "error"
        }

@router.post("/worksheets", response_model=Dict[str, Any])
async def save_worksheet(request: WorksheetSaveRequest, db: Session = Depends(get_db)):
    """생성된 문제지와 답안지를 데이터베이스에 저장합니다."""
    try:
        worksheet_data = request.worksheet_data
        
        # 문제지 메타데이터 추출
        worksheet_id = str(uuid.uuid4())  # UUID로 자동 생성
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
                worksheet_id=db_worksheet.id,
                passage_id=passage_data.get('passage_id'),
                passage_type=passage_data.get('passage_type'),
                passage_content=passage_data.get('passage_content'),
                original_content=passage_data.get('original_content'),
                korean_translation=passage_data.get('korean_translation'),
                related_questions=passage_data.get('related_questions', [])
            )
            db.add(db_passage)
        
        # 3. Examples 저장
        examples_data = worksheet_data.get('examples', [])
        for example_data in examples_data:
            db_example = Example(
                worksheet_id=db_worksheet.id,
                example_id=example_data.get('example_id'),
                example_content=example_data.get('example_content'),
                original_content=example_data.get('original_content'),
                korean_translation=example_data.get('korean_translation'),
                related_questions=example_data.get('related_questions', [])
            )
            db.add(db_example)
        
        # 4. Questions 저장
        questions_data = worksheet_data.get('questions', [])
        for question_data in questions_data:
            db_question = Question(
                worksheet_id=db_worksheet.id,
                question_id=question_data.get('question_id'),
                question_text=question_data.get('question_text'),
                question_type=question_data.get('question_type'),
                question_subject=question_data.get('question_subject'),
                question_difficulty=question_data.get('question_difficulty'),
                question_detail_type=question_data.get('question_detail_type'),
                question_choices=question_data.get('question_choices'),
                passage_id=question_data.get('question_passage_id'),
                example_id=question_data.get('question_example_id'),
                correct_answer=question_data.get('correct_answer'),
                explanation=question_data.get('explanation'),
                learning_point=question_data.get('learning_point')
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
                id=worksheet.id,
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

@router.get("/worksheets/{worksheet_id}", response_model=WorksheetResponse)
async def get_worksheet(worksheet_id: int, db: Session = Depends(get_db)):
    """특정 문제지의 상세 정보를 조회합니다."""
    try:
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        return worksheet
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제지 조회 중 오류: {str(e)}")

@router.get("/worksheets/{worksheet_id}/edit")
async def get_worksheet_for_editing(worksheet_id: int, db: Session = Depends(get_db)):
    """문제지 편집용 워크시트를 조회합니다 (정답 및 해설 포함)."""
    try:
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
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
        
        # 지문 데이터 + 원본 내용 추가
        for passage in worksheet.passages:
            passage_data = {
                "passage_id": passage.passage_id,
                "passage_type": passage.passage_type,
                "passage_content": passage.passage_content,
                "related_questions": passage.related_questions
            }
            
            # 원본 지문 내용 추가 (답안 데이터에서)
            for answer_passage in worksheet.answer_passages:
                if answer_passage.passage_id == passage.passage_id:
                    passage_data["original_content"] = answer_passage.original_content
                    passage_data["text_type"] = answer_passage.text_type
                    break
            
            worksheet_data["passages"].append(passage_data)
        
        # 예문 데이터 + 원본 내용 추가
        for example in worksheet.examples:
            example_data = {
                "example_id": example.example_id,
                "example_content": example.example_content,
                "related_questions": example.related_questions
            }
            
            # 원본 예문 내용 추가 (답안 데이터에서)
            for answer_example in worksheet.answer_examples:
                if answer_example.example_id == example.example_id:
                    example_data["original_content"] = answer_example.original_content
                    break
            
            worksheet_data["examples"].append(example_data)
        
        # 문제 데이터 + 정답/해설 추가
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
                "question_example_id": question.example_id
            }
            
            # 정답/해설 데이터 추가
            answer_question = None
            for answer in worksheet.answer_questions:
                if answer.question_id == question.question_id:
                    answer_question = answer
                    break
            
            if answer_question:
                question_data.update({
                    "correct_answer": answer_question.correct_answer,
                    "explanation": answer_question.explanation,
                    "learning_point": answer_question.learning_point
                })
            else:
                question_data.update({
                    "correct_answer": "정답 정보 없음",
                    "explanation": None,
                    "learning_point": None
                })
            
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
async def get_worksheet_for_solving(worksheet_id: int, db: Session = Depends(get_db)):
    """문제 풀이용 문제지를 조회합니다 (답안 제외)."""
    try:
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
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
            worksheet_data["passages"].append({
                "passage_id": passage.passage_id,
                "passage_type": passage.passage_type,
                "passage_content": passage.passage_content,
                "related_questions": passage.related_questions
            })
        
        # 예문 데이터 추가
        for example in worksheet.examples:
            worksheet_data["examples"].append({
                "example_id": example.example_id,
                "example_content": example.example_content,
                "related_questions": example.related_questions
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
        
        return {
            "status": "success",
            "message": "문제 풀이용 문제지를 성공적으로 조회했습니다.",
            "worksheet_data": worksheet_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제지 조회 중 오류: {str(e)}")

@router.delete("/worksheets/{worksheet_id}", response_model=Dict[str, Any])
async def delete_worksheet(worksheet_id: int, db: Session = Depends(get_db)):
    """문제지와 관련된 모든 데이터를 삭제합니다."""
    try:
        # 문제지 존재 확인
        worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        worksheet_name = worksheet.worksheet_name
        
        # 관련된 채점 결과 삭제
        grading_results = db.query(GradingResult).filter(GradingResult.worksheet_id == worksheet_id).all()
        for result in grading_results:
            db.query(QuestionResult).filter(QuestionResult.grading_result_id == result.id).delete()
            db.delete(result)
        
        # 1. 답안 데이터 삭제 (worksheet.id 사용)
        db.query(AnswerQuestion).filter(AnswerQuestion.worksheet_id == worksheet_id).delete()
        db.query(AnswerPassage).filter(AnswerPassage.worksheet_id == worksheet_id).delete()
        db.query(AnswerExample).filter(AnswerExample.worksheet_id == worksheet_id).delete()
        
        # 2. 문제 삭제
        db.query(Question).filter(Question.worksheet_id == worksheet_id).delete()
        
        # 3. 지문 삭제
        db.query(Passage).filter(Passage.worksheet_id == worksheet_id).delete()
        
        # 4. 예문 삭제
        db.query(Example).filter(Example.worksheet_id == worksheet_id).delete()
        
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