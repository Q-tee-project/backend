from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.schemas.schemas import (
    QuestionGenerationRequest, CategoriesResponse,
    TextTypeCreate, TextTypeUpdate, TextTypeResponse,
    WorksheetSaveRequest, WorksheetResponse, WorksheetSummary,
    GradingResultResponse, GradingResultSummary, ReviewRequest, SubmissionRequest
)
from app.models.models import (
    GrammarCategory, GrammarTopic, VocabularyCategory, ReadingType, TextType,
    Worksheet, Passage, Example, Question, GradingResult, QuestionResult
)
from sqlalchemy import text
from typing import List, Dict, Any
from datetime import datetime
from app.services.question_generator import PromptGenerator
from app.services.grading_service import perform_grading
import os
import json
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini 라이브러리가 설치되지 않았습니다.")

# 라우터 생성
router = APIRouter()

# 헬스체크 엔드포인트 (데이터베이스 연결 확인 포함)
@router.get("/health")
async def health_check():
    try:
        # 데이터베이스 연결 테스트
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "message": "서버와 데이터베이스가 정상적으로 작동 중입니다.", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": "데이터베이스 연결에 문제가 있습니다.", "database": "disconnected", "error": str(e)}

# 문제 생성 옵션 입력받기 엔드포인트
@router.post("/question-options")
async def receive_question_options(request: QuestionGenerationRequest, db: Session = Depends(get_db)):
    """
    사용자로부터 문제 생성 옵션을 입력받습니다.
    """
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
            # 재시도 로직 제거 (내부에서 DB 처리하므로 불필요)
            raise prompt_error
        
        # LLM에 프롬프트 전송 및 응답 받기
        llm_response = None
        answer_sheet = None
        llm_error = None
        
        if GEMINI_AVAILABLE:
            try:
                print("🤖 Gemini API 호출 시작...")
                
                # Gemini API 키 설정 (환경변수 또는 하드코딩)
                api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBkqKJGKjGJKjGJKjGJKjGJKjGJKjGJKjG")  # 실제 API 키로 교체 필요
                genai.configure(api_key=api_key)
                
                # Gemini 모델 생성 (최신 모델명 사용)
                model = genai.GenerativeModel('gemini-2.5-pro')
                
                # 1단계: 문제지 생성
                print("📝 1단계: 문제지 생성 중...")
                response = model.generate_content(prompt)
                llm_response = response.text
                print("✅ 문제지 생성 완료!")
                
                # 2단계: 답안지 생성 (문제지가 성공적으로 생성된 경우에만)
                if llm_response:
                    try:
                        print("📋 2단계: 답안지 생성 중...")
                        
                        # JSON 파싱을 위한 전처리
                        clean_response = llm_response.strip()
                        if clean_response.startswith('```json'):
                            clean_response = clean_response.replace('```json', '').replace('```', '').strip()
                        elif clean_response.startswith('```'):
                            clean_response = clean_response.replace('```', '').strip()
                        
                        # 문제지 JSON 파싱
                        worksheet_json = json.loads(clean_response)
                        
                        # 답안지 프롬프트 생성
                        answer_prompt = generator.generate_answer_sheet_prompt(worksheet_json)
                        
                        # 답안지 생성 API 호출
                        answer_response = model.generate_content(answer_prompt)
                        answer_sheet = answer_response.text
                        print("✅ 답안지 생성 완료!")
                        
                    except json.JSONDecodeError as json_error:
                        print(f"⚠️ 답안지 생성 실패 - JSON 파싱 오류: {json_error}")
                        answer_sheet = None
                    except Exception as answer_error:
                        print(f"⚠️ 답안지 생성 실패: {answer_error}")
                        answer_sheet = None
                
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
        
        return {
            "message": "문제지와 답안지 생성이 완료되었습니다!" if llm_response else "프롬프트가 생성되었습니다!",
            "status": "success",
            "request_data": request.dict(),
            "distribution_summary": distribution_summary,
            "prompt": prompt,
            "llm_response": llm_response,
            "answer_sheet": answer_sheet,
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


# 카테고리 정보 조회 엔드포인트 (페이지에서 선택 옵션으로 사용)
@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """
    문법, 어휘, 독해 카테고리 정보를 조회하는 엔드포인트
    프론트엔드에서 선택 옵션을 만들 때 사용합니다.
    """
    try:
        # 문법 카테고리와 주제들 조회
        grammar_categories = db.query(GrammarCategory).all()
        grammar_data = []
        for category in grammar_categories:
            topics = [{"id": topic.id, "name": topic.name} for topic in category.topics]
            grammar_data.append({
                "id": category.id,
                "name": category.name,
                "topics": topics
            })
        
        # 어휘 카테고리 조회
        vocabulary_categories = db.query(VocabularyCategory).all()
        vocabulary_data = [{"id": cat.id, "name": cat.name} for cat in vocabulary_categories]
        
        # 독해 유형 조회
        reading_types = db.query(ReadingType).all()
        reading_data = [{"id": rt.id, "name": rt.name, "description": rt.description} for rt in reading_types]
        
        return {
            "grammar_categories": grammar_data,
            "vocabulary_categories": vocabulary_data,
            "reading_types": reading_data
        }
    except Exception as e:
        return {"error": f"카테고리 조회 중 오류 발생: {str(e)}"}

# ===========================================
# 지문 유형 관리 엔드포인트들 (간단 버전)
# ===========================================

# 지문 유형 목록 조회
@router.get("/text-types", response_model=List[TextTypeResponse])
async def get_text_types(db: Session = Depends(get_db)):
    """모든 지문 유형을 조회합니다."""
    try:
        text_types = db.query(TextType).all()
        return text_types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지문 유형 조회 중 오류: {str(e)}")

# 특정 지문 유형 조회
@router.get("/text-types/{text_type_id}", response_model=TextTypeResponse)
async def get_text_type(text_type_id: int, db: Session = Depends(get_db)):
    """특정 지문 유형을 조회합니다."""
    try:
        text_type = db.query(TextType).filter(TextType.id == text_type_id).first()
        if not text_type:
            raise HTTPException(status_code=404, detail="지문 유형을 찾을 수 없습니다.")
        return text_type
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지문 유형 조회 중 오류: {str(e)}")

# 지문 유형 생성
@router.post("/text-types", response_model=TextTypeResponse)
async def create_text_type(text_type: TextTypeCreate, db: Session = Depends(get_db)):
    """새로운 지문 유형을 생성합니다."""
    try:
        # 중복 이름 확인
        existing = db.query(TextType).filter(TextType.type_name == text_type.type_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 지문 유형 이름입니다.")
        
        db_text_type = TextType(
            type_name=text_type.type_name,
            display_name=text_type.display_name,
            description=text_type.description,
            json_format=text_type.json_format,
            created_at=datetime.now()
        )
        db.add(db_text_type)
        db.commit()
        db.refresh(db_text_type)
        return db_text_type
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"지문 유형 생성 중 오류: {str(e)}")

# 지문 유형 수정
@router.put("/text-types/{text_type_id}", response_model=TextTypeResponse)
async def update_text_type(text_type_id: int, text_type: TextTypeUpdate, db: Session = Depends(get_db)):
    """지문 유형을 수정합니다."""
    try:
        db_text_type = db.query(TextType).filter(TextType.id == text_type_id).first()
        if not db_text_type:
            raise HTTPException(status_code=404, detail="지문 유형을 찾을 수 없습니다.")
        
        # 수정할 필드들 업데이트
        if text_type.display_name is not None:
            db_text_type.display_name = text_type.display_name
        if text_type.description is not None:
            db_text_type.description = text_type.description
        if text_type.json_format is not None:
            db_text_type.json_format = text_type.json_format
        
        db.commit()
        db.refresh(db_text_type)
        return db_text_type
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"지문 유형 수정 중 오류: {str(e)}")

# 지문 유형 삭제
@router.delete("/text-types/{text_type_id}")
async def delete_text_type(text_type_id: int, db: Session = Depends(get_db)):
    """지문 유형을 삭제합니다."""
    try:
        db_text_type = db.query(TextType).filter(TextType.id == text_type_id).first()
        if not db_text_type:
            raise HTTPException(status_code=404, detail="지문 유형을 찾을 수 없습니다.")
        
        db.delete(db_text_type)
        db.commit()
        return {"message": "지문 유형이 성공적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"지문 유형 삭제 중 오류: {str(e)}")

# ====================================
# 문제지 저장 관련 엔드포인트
# ====================================

@router.post("/worksheets", response_model=Dict[str, Any])
async def save_worksheet(request: WorksheetSaveRequest, db: Session = Depends(get_db)):
    """생성된 문제지와 답안지를 데이터베이스에 저장합니다."""
    try:
        worksheet_data = request.worksheet_data
        answer_data = request.answer_data
        
        # 문제지 메타데이터 추출
        worksheet_id = worksheet_data.get('worksheet_id')
        worksheet_name = worksheet_data.get('worksheet_name')
        school_level = worksheet_data.get('worksheet_level')
        grade = str(worksheet_data.get('worksheet_grade'))  # 문자열로 변환
        subject = worksheet_data.get('worksheet_subject', '영어')
        total_questions = worksheet_data.get('total_questions')
        duration = worksheet_data.get('worksheet_duration')
        
        # 중복 확인
        existing = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"이미 존재하는 문제지 ID입니다: {worksheet_id}")
        
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
        db.flush()  # ID 생성을 위해 flush
        
        # 2. Passages 저장
        passages_data = worksheet_data.get('passages', [])
        for passage_data in passages_data:
            db_passage = Passage(
                worksheet_id=db_worksheet.id,
                passage_id=passage_data.get('passage_id'),
                passage_type=passage_data.get('passage_type'),
                passage_content=passage_data.get('passage_content'),
                related_questions=passage_data.get('related_questions', []),
                created_at=datetime.now()
            )
            db.add(db_passage)
        
        # 3. Examples 저장
        examples_data = worksheet_data.get('examples', [])
        for example_data in examples_data:
            db_example = Example(
                worksheet_id=db_worksheet.id,
                example_id=example_data.get('example_id'),
                example_content=example_data.get('example_content'),
                related_questions=example_data.get('related_questions', []),
                created_at=datetime.now()
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
                created_at=datetime.now()
            )
            db.add(db_question)
        
        # 5. Answer Data 정규화해서 저장
        if answer_data:
            # 5-1. Answer Questions 저장
            questions_data = answer_data.get("questions", [])
            for question_data in questions_data:
                db_answer_question = Question(
                    worksheet_id=db_worksheet.id,
                    question_id=question_data.get("question_id"),
                    correct_answer=question_data.get("correct_answer"),
                    explanation=question_data.get("explanation"),
                    learning_point=question_data.get("learning_point"),
                    created_at=datetime.now()
                )
                db.add(db_answer_question)
            
            # 5-2. Answer Passages 저장
            passages_data = answer_data.get("passages", [])
            for passage_data in passages_data:
                db_answer_passage = Passage(
                    worksheet_id=db_worksheet.id,
                    passage_id=passage_data.get("passage_id"),
                    text_type=passage_data.get("text_type"),
                    original_content=passage_data.get("original_content"),
                    related_questions=passage_data.get("related_questions"),
                    created_at=datetime.now()
                )
                db.add(db_answer_passage)
            
            # 5-3. Answer Examples 저장
            examples_data = answer_data.get("examples", [])
            for example_data in examples_data:
                db_answer_example = Example(
                    worksheet_id=db_worksheet.id,
                    example_id=example_data.get("example_id"),
                    original_content=example_data.get("original_content"),
                    related_questions=example_data.get("related_questions"),
                    created_at=datetime.now()
                )
                db.add(db_answer_example)
        
        # 커밋
        db.commit()
        db.refresh(db_worksheet)
        
        return {
            "message": "문제지가 성공적으로 저장되었습니다.",
            "worksheet_id": worksheet_id,
            "database_id": db_worksheet.id,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"문제지 저장 중 오류: {str(e)}")

@router.get("/worksheets", response_model=List[WorksheetSummary])
async def get_worksheets(db: Session = Depends(get_db)):
    """저장된 문제지 목록을 조회합니다."""
    try:
        worksheets = db.query(Worksheet).order_by(Worksheet.created_at.desc()).all()
        return worksheets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제지 목록 조회 중 오류: {str(e)}")

@router.get("/worksheets", response_model=List[WorksheetSummary])
async def get_worksheets_list(db: Session = Depends(get_db)):
    """저장된 모든 문제지 목록을 조회합니다."""
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
async def get_worksheet(worksheet_id: str, db: Session = Depends(get_db)):
    """특정 문제지의 상세 정보를 조회합니다."""
    try:
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        return worksheet
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제지 조회 중 오류: {str(e)}")

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
                # 답안 관련 정보는 제외
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

@router.post("/worksheets/{worksheet_id}/submit")
async def submit_answers_and_grade(
    worksheet_id: str,
    submission_data: SubmissionRequest,
    db: Session = Depends(get_db)
):
    """답안을 제출하고 자동 채점을 수행합니다."""
    try:
        # 문제지 조회
        worksheet = db.query(Worksheet).filter(Worksheet.worksheet_id == worksheet_id).first()
        if not worksheet:
            raise HTTPException(status_code=404, detail="문제지를 찾을 수 없습니다.")
        
        student_name = submission_data.student_name
        answers = submission_data.answers
        completion_time = submission_data.completion_time
        
        # 채점 수행
        grading_result = await perform_grading(worksheet, answers, db, student_name, completion_time)
        
        # 결과 반환
        return {
            "status": "success",
            "message": "답안이 제출되고 채점이 완료되었습니다.",
            "grading_result": {
                "result_id": grading_result["result_id"],
                "student_name": student_name,
                "completion_time": completion_time,
                "total_score": grading_result["total_score"],
                "max_score": grading_result["max_score"],
                "percentage": grading_result["percentage"],
                "needs_review": grading_result["needs_review"],
                "passage_groups": grading_result.get("passage_groups", []),      # 지문별 그룹
                "example_groups": grading_result.get("example_groups", []),      # 예문별 그룹  
                "standalone_questions": grading_result.get("standalone_questions", [])  # 독립 문제들
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답안 제출 및 채점 중 오류: {str(e)}")

@router.get("/grading-results", response_model=List[GradingResultSummary])
async def get_grading_results(db: Session = Depends(get_db)):
    """모든 채점 결과 목록을 조회합니다."""
    try:
        results = db.query(GradingResult).join(Worksheet).order_by(GradingResult.created_at.desc()).all()
        
        result_summaries = []
        for result in results:
            result_summaries.append(GradingResultSummary(
                id=result.id,
                result_id=result.result_id,
                worksheet_id=result.worksheet_id,
                student_name=result.student_name,
                completion_time=result.completion_time,
                total_score=result.total_score,
                max_score=result.max_score,
                percentage=result.percentage,
                needs_review=result.needs_review,
                is_reviewed=result.is_reviewed,
                created_at=result.created_at,
                worksheet_name=result.worksheet.worksheet_name if result.worksheet else None
            ))
        
        return result_summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채점 결과 조회 중 오류: {str(e)}")

@router.get("/grading-results/{result_id}", response_model=GradingResultResponse)
async def get_grading_result(result_id: str, db: Session = Depends(get_db)):
    """특정 채점 결과의 상세 정보를 조회합니다."""
    try:
        result = db.query(GradingResult).filter(GradingResult.result_id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="채점 결과를 찾을 수 없습니다.")
        
        # 지문과 예문 데이터도 함께 조회
        answer_passages = db.query(Passage).filter(
            Passage.worksheet_id == result.worksheet_id
        ).all()
        
        answer_examples = db.query(Example).filter(
            Example.worksheet_id == result.worksheet_id
        ).all()
        
        # 백엔드에서 미리 그룹핑 (grading_service와 동일한 로직)
        passage_groups = []
        example_groups = []
        standalone_questions = []
        
        
        # 문제별 결과를 딕셔너리로 변환 (그룹핑용)
        question_results = []
        processed_questions = set()
        
        for question_result in result.question_results:
            question_data = {
                "id": question_result.id,
                "question_id": question_result.question_id,
                "question_type": question_result.question_type,
                "student_answer": question_result.student_answer,
                "correct_answer": question_result.correct_answer,
                "score": question_result.score,
                "max_score": question_result.max_score,
                "is_correct": question_result.is_correct,
                "grading_method": question_result.grading_method,
                "ai_feedback": question_result.ai_feedback,
                "needs_review": question_result.needs_review,
                "reviewed_score": question_result.reviewed_score,
                "reviewed_feedback": question_result.reviewed_feedback,
                "is_reviewed": question_result.is_reviewed,
                "created_at": question_result.created_at,
                "passage_id": getattr(question_result, 'passage_id', None),
                "example_id": getattr(question_result, 'example_id', None)
            }
            question_results.append(question_data)
        
        # 지문별 문제 그룹핑 (related_questions 기준)
        for answer_passage in answer_passages:
            if answer_passage.related_questions:
                related_questions = []
                for question_id in answer_passage.related_questions:
                    matching_question = next((q for q in question_results if q["question_id"] == str(question_id)), None)
                    if matching_question:
                        related_questions.append(matching_question)
                        processed_questions.add(matching_question["question_id"])
                
                if related_questions:
                    passage_groups.append({
                        "passage": {
                            "passage_id": answer_passage.passage_id,
                            "original_content": answer_passage.original_content,
                            "text_type": getattr(answer_passage, 'text_type', None)
                        },
                        "questions": related_questions
                    })
        
        # 예문별 문제 그룹핑 (지문에 속하지 않은 것만)
        for answer_example in answer_examples:
            if answer_example.related_questions:
                related_questions = []
                
                # related_questions가 문자열인 경우 리스트로 변환
                if isinstance(answer_example.related_questions, str):
                    question_ids = [answer_example.related_questions]
                else:
                    question_ids = answer_example.related_questions
                    
                for question_id in question_ids:
                    if str(question_id) not in processed_questions:
                        matching_question = next((q for q in question_results if q["question_id"] == str(question_id)), None)
                        if matching_question:
                            related_questions.append(matching_question)
                            processed_questions.add(matching_question["question_id"])
                
                if related_questions:
                    example_groups.append({
                        "example": {
                            "example_id": answer_example.example_id,
                            "original_content": answer_example.original_content
                        },
                        "questions": related_questions
                    })
        
        # 독립 문제들
        standalone_questions = [q for q in question_results if q["question_id"] not in processed_questions]
        
        # 디버깅 로그
        print(f"🔍 API 디버깅 - result_id: {result.result_id}")
        print(f"📄 passage_groups 개수: {len(passage_groups)}")
        print(f"📝 example_groups 개수: {len(example_groups)}")
        print(f"📋 standalone_questions 개수: {len(standalone_questions)}")
        print(f"🗂️ answer_passages 개수: {len(answer_passages)}")
        print(f"🗂️ answer_examples 개수: {len(answer_examples)}")
        
        # 결과 객체 구성
        result_dict = {
            "id": result.id,
            "result_id": result.result_id,
            "worksheet_id": result.worksheet_id,
            "student_name": result.student_name,
            "completion_time": result.completion_time,
            "total_score": result.total_score,
            "max_score": result.max_score,
            "percentage": result.percentage,
            "needs_review": result.needs_review,
            "is_reviewed": result.is_reviewed,
            "reviewed_at": result.reviewed_at,
            "reviewed_by": result.reviewed_by,
            "created_at": result.created_at,
            "question_results": question_results,  # 호환성을 위해 유지
            "passage_groups": passage_groups,      # 지문별 그룹
            "example_groups": example_groups,      # 예문별 그룹  
            "standalone_questions": standalone_questions  # 독립 문제들
        }
        
        return result_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채점 결과 조회 중 오류: {str(e)}")

@router.put("/grading-results/{result_id}/review")
async def update_grading_review(
    result_id: str, 
    review_data: ReviewRequest, 
    db: Session = Depends(get_db)
):
    """채점 결과의 검수를 업데이트합니다."""
    try:
        # 채점 결과 조회
        grading_result = db.query(GradingResult).filter(GradingResult.result_id == result_id).first()
        if not grading_result:
            raise HTTPException(status_code=404, detail="채점 결과를 찾을 수 없습니다.")
        
        # 문제별 검수 결과 업데이트
        total_score = 0
        max_score = 0
        
        for question_result in grading_result.question_results:
            question_id = question_result.question_id
            max_score += question_result.max_score
            
            if question_id in review_data.question_results:
                review_info = review_data.question_results[question_id]
                
                # 검수된 점수와 피드백 업데이트
                if "score" in review_info:
                    question_result.reviewed_score = review_info["score"]
                    total_score += review_info["score"]
                else:
                    total_score += question_result.score
                
                if "feedback" in review_info:
                    question_result.reviewed_feedback = review_info["feedback"]
                
                question_result.is_reviewed = True
            else:
                total_score += question_result.score
        
        # 전체 채점 결과 업데이트
        grading_result.total_score = total_score
        grading_result.percentage = round((total_score / max_score * 100) if max_score > 0 else 0, 1)
        grading_result.is_reviewed = True
        grading_result.reviewed_at = datetime.now()
        grading_result.reviewed_by = review_data.reviewed_by
        grading_result.needs_review = False
        
        db.commit()
        
        return {
            "status": "success",
            "message": "검수가 완료되었습니다.",
            "result": {
                "result_id": result_id,
                "total_score": total_score,
                "max_score": max_score,
                "percentage": grading_result.percentage
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검수 업데이트 중 오류: {str(e)}")

