from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from schemas import (
    QuestionGenerationRequest, CategoriesResponse,
    TextTypeCreate, TextTypeUpdate, TextTypeResponse
)
from models import GrammarCategory, GrammarTopic, VocabularyCategory, ReadingType
from sqlalchemy import text
from typing import List
from datetime import datetime
from question_generator import PromptGenerator
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
            prompt = generator.generate_prompt(request_dict)
            print("✅ 프롬프트 생성 성공!")
            
        except Exception as prompt_error:
            print(f"❌ 프롬프트 생성 오류: {prompt_error}")
            # 재시도 로직 제거 (내부에서 DB 처리하므로 불필요)
            raise prompt_error
        
        # LLM에 프롬프트 전송 및 응답 받기
        llm_response = None
        llm_error = None
        
        if GEMINI_AVAILABLE:
            try:
                print("🤖 Gemini API 호출 시작...")
                
                # Gemini API 키 설정 (환경변수 또는 하드코딩)
                api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBkqKJGKjGJKjGJKjGJKjGJKjGJKjGJKjG")  # 실제 API 키로 교체 필요
                genai.configure(api_key=api_key)
                
                # Gemini 모델 생성 (최신 모델명 사용)
                model = genai.GenerativeModel('gemini-2.5-pro')
                
                # Gemini API 호출
                response = model.generate_content(prompt)
                
                llm_response = response.text
                print("✅ Gemini API 호출 성공!")
                
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
            "message": "문제 생성이 완료되었습니다!" if llm_response else "프롬프트가 생성되었습니다!",
            "status": "success",
            "request_data": request.dict(),
            "distribution_summary": distribution_summary,
            "prompt": prompt,
            "llm_response": llm_response,
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

