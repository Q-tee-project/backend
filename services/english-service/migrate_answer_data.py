#!/usr/bin/env python3
"""
답안지 데이터 마이그레이션 스크립트
기존 JSON 구조 → 새로운 정규화된 테이블 구조로 변환
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.models import Worksheet, AnswerQuestion, AnswerPassage, AnswerExample
from sqlalchemy import text

def migrate_answer_data():
    """기존 JSON 답안지 데이터를 정규화된 테이블로 마이그레이션"""
    db = SessionLocal()
    
    try:
        print("🚀 답안지 데이터 마이그레이션을 시작합니다...")
        
        # 1. 기존 answer_sheets 테이블에서 데이터 조회
        result = db.execute(text("""
            SELECT worksheet_id, answer_data 
            FROM english_service.answer_sheets
        """))
        
        old_answer_sheets = result.fetchall()
        print(f"📊 마이그레이션할 답안지: {len(old_answer_sheets)}개")
        
        if not old_answer_sheets:
            print("❌ 마이그레이션할 답안지가 없습니다.")
            return
        
        # 2. 각 답안지 데이터를 정규화된 구조로 변환
        for worksheet_id, answer_data in old_answer_sheets:
            print(f"\n📝 워크시트 ID {worksheet_id} 마이그레이션 중...")
            
            # answer_data가 중첩 구조인지 확인
            actual_data = answer_data
            if isinstance(answer_data, dict) and "answer_sheet" in answer_data:
                actual_data = answer_data["answer_sheet"]
            
            # 2-1. Answer Questions 마이그레이션
            questions_data = actual_data.get("questions", [])
            if isinstance(questions_data, list):
                for question_data in questions_data:
                    # 기존 데이터가 있는지 확인
                    existing = db.query(AnswerQuestion).filter(
                        AnswerQuestion.worksheet_id == worksheet_id,
                        AnswerQuestion.question_id == question_data.get("question_id")
                    ).first()
                    
                    if not existing:
                        db_answer_question = AnswerQuestion(
                            worksheet_id=worksheet_id,
                            question_id=question_data.get("question_id"),
                            correct_answer=question_data.get("correct_answer", ""),
                            explanation=question_data.get("explanation", ""),
                            learning_point=question_data.get("learning_point", ""),
                            created_at=datetime.now()
                        )
                        db.add(db_answer_question)
                        print(f"  ✅ 문제 {question_data.get('question_id')} 추가")
                    else:
                        print(f"  ⏭️ 문제 {question_data.get('question_id')} 이미 존재")
            
            # 2-2. Answer Passages 마이그레이션
            passages_data = actual_data.get("passages", [])
            if isinstance(passages_data, list):
                for passage_data in passages_data:
                    # 기존 데이터가 있는지 확인
                    existing = db.query(AnswerPassage).filter(
                        AnswerPassage.worksheet_id == worksheet_id,
                        AnswerPassage.passage_id == passage_data.get("passage_id")
                    ).first()
                    
                    if not existing:
                        db_answer_passage = AnswerPassage(
                            worksheet_id=worksheet_id,
                            passage_id=passage_data.get("passage_id"),
                            text_type=passage_data.get("text_type", ""),
                            original_content=passage_data.get("original_content", ""),
                            related_questions=passage_data.get("related_questions", []),
                            created_at=datetime.now()
                        )
                        db.add(db_answer_passage)
                        print(f"  ✅ 지문 {passage_data.get('passage_id')} 추가")
                    else:
                        print(f"  ⏭️ 지문 {passage_data.get('passage_id')} 이미 존재")
            
            # 2-3. Answer Examples 마이그레이션
            examples_data = actual_data.get("examples", [])
            if isinstance(examples_data, list):
                for example_data in examples_data:
                    # 기존 데이터가 있는지 확인
                    existing = db.query(AnswerExample).filter(
                        AnswerExample.worksheet_id == worksheet_id,
                        AnswerExample.example_id == example_data.get("example_id")
                    ).first()
                    
                    if not existing:
                        db_answer_example = AnswerExample(
                            worksheet_id=worksheet_id,
                            example_id=example_data.get("example_id"),
                            original_content=example_data.get("original_content", ""),
                            related_questions=example_data.get("related_questions", []),
                            created_at=datetime.now()
                        )
                        db.add(db_answer_example)
                        print(f"  ✅ 예문 {example_data.get('example_id')} 추가")
                    else:
                        print(f"  ⏭️ 예문 {example_data.get('example_id')} 이미 존재")
        
        # 3. 변경사항 커밋
        db.commit()
        print(f"\n🎉 마이그레이션이 완료되었습니다!")
        
        # 4. 결과 확인
        answer_questions = db.query(AnswerQuestion).count()
        answer_passages = db.query(AnswerPassage).count()
        answer_examples = db.query(AnswerExample).count()
        
        print(f"\n📊 마이그레이션 결과:")
        print(f"  - 답안 문제: {answer_questions}개")
        print(f"  - 답안 지문: {answer_passages}개")
        print(f"  - 답안 예문: {answer_examples}개")
        
    except Exception as e:
        print(f"❌ 마이그레이션 중 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_migration():
    """마이그레이션 결과 검증"""
    db = SessionLocal()
    
    try:
        print("\n🔍 마이그레이션 결과 검증 중...")
        
        # 워크시트별 답안 데이터 확인
        worksheets = db.query(Worksheet).all()
        
        for worksheet in worksheets:
            print(f"\n📋 워크시트: {worksheet.worksheet_id}")
            
            answer_questions = db.query(AnswerQuestion).filter(
                AnswerQuestion.worksheet_id == worksheet.id
            ).count()
            
            answer_passages = db.query(AnswerPassage).filter(
                AnswerPassage.worksheet_id == worksheet.id
            ).count()
            
            answer_examples = db.query(AnswerExample).filter(
                AnswerExample.worksheet_id == worksheet.id
            ).count()
            
            print(f"  - 답안 문제: {answer_questions}개")
            print(f"  - 답안 지문: {answer_passages}개")
            print(f"  - 답안 예문: {answer_examples}개")
            
            if answer_questions == 0:
                print(f"  ⚠️ 경고: 답안 문제가 없습니다!")
        
    finally:
        db.close()

if __name__ == "__main__":
    try:
        migrate_answer_data()
        verify_migration()
        print("\n✨ 모든 작업이 완료되었습니다!")
        
    except Exception as e:
        print(f"\n💥 오류 발생: {e}")
        sys.exit(1)
