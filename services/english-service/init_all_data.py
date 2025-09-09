#!/usr/bin/env python3
"""
English Service 전체 초기 데이터 생성 스크립트

data 폴더의 모든 JSON 파일들을 데이터베이스에 자동으로 import합니다.
"""

import json
import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from database import engine
from models import (
    GrammarCategory, GrammarTopic, GrammarAchievement,
    VocabularyCategory, Word, ReadingType, TextType
)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def load_json_data(filename):
    """JSON 파일을 읽어서 파이썬 객체로 반환합니다."""
    # .json 확장자가 없으면 자동으로 추가
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        print(f"❌ 파일을 찾을 수 없습니다: {filepath}")
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # vocabulary_categories 파일은 {}로 감싸져 있음
            if content.startswith('{') and content.endswith('}'):
                # {} 제거하고 내용만 추출
                content = content[1:-1].strip()
            
            if content.startswith('[') and content.endswith(']'):
                return json.loads(content)
            else:
                # JSON 배열이 아닌 경우 배열로 감싸기
                return json.loads(f'[{content}]')
                
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류 in {filename}: {e}")
        return []
    except Exception as e:
        print(f"❌ 파일 읽기 오류 in {filename}: {e}")
        return []

def init_grammar_categories(db):
    """문법 카테고리 데이터를 초기화합니다."""
    if db.query(GrammarCategory).count() > 0:
        existing_count = db.query(GrammarCategory).count()
        print(f"📚 Grammar Categories: 이미 {existing_count}개 데이터가 존재합니다.")
        return
        
    data = load_json_data("grammar_categories")
    if not data:
        print("❌ Grammar Categories: 데이터 파일이 비어있거나 로드할 수 없습니다.")
        return
    
    print(f"📚 Grammar Categories 데이터 import 시작... ({len(data)}개 항목)")
    
    for item in data:
        category = GrammarCategory(
            id=item.get("id"),
            name=item.get("name"),
            created_at=datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')) if item.get("created_at") else None
        )
        db.add(category)
        print(f"   - {item.get('name')} (ID: {item.get('id')})")
    
    db.commit()
    print(f"✅ Grammar Categories: {len(data)}개 항목이 성공적으로 생성되었습니다.")

def init_grammar_topics(db):
    """문법 주제 데이터를 초기화합니다."""
    if db.query(GrammarTopic).count() > 0:
        existing_count = db.query(GrammarTopic).count()
        print(f"📖 Grammar Topics: 이미 {existing_count}개 데이터가 존재합니다.")
        return
        
    data = load_json_data("grammar_topics")
    if not data:
        print("❌ Grammar Topics: 데이터 파일이 비어있거나 로드할 수 없습니다.")
        return
    
    print(f"📖 Grammar Topics 데이터 import 시작... ({len(data)}개 항목)")
    
    for item in data:
        topic = GrammarTopic(
            id=item.get("id"),
            category_id=item.get("category_id"),
            name=item.get("name"),
            learning_objective=item.get("learning_objective"),
            created_at=datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')) if item.get("created_at") else None
        )
        db.add(topic)
        print(f"   - {item.get('name')} (ID: {item.get('id')}, Category: {item.get('category_id')})")
    
    db.commit()
    print(f"✅ Grammar Topics: {len(data)}개 항목이 성공적으로 생성되었습니다.")

def init_grammar_achievements(db):
    """문법 성취도 데이터를 초기화합니다."""
    if db.query(GrammarAchievement).count() > 0:
        existing_count = db.query(GrammarAchievement).count()
        print(f"🏆 Grammar Achievements: 이미 {existing_count}개 데이터가 존재합니다.")
        return
        
    data = load_json_data("grammar_achievements")
    if not data:
        print("❌ Grammar Achievements: 데이터 파일이 비어있거나 로드할 수 없습니다.")
        return
    
    print(f"🏆 Grammar Achievements 데이터 import 시작... ({len(data)}개 항목)")
    
    level_counts = {}
    
    for item in data:
        achievement = GrammarAchievement(
            id=item.get("id"),
            topic_id=item.get("topic_id"),
            level=item.get("level"),
            description=item.get("description"),
            created_at=datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')) if item.get("created_at") else None
        )
        db.add(achievement)
        
        level = item.get("level", "unknown")
        level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"   - {item.get('level')}: {item.get('description')[:50]}... (Topic: {item.get('topic_id')})")
    
    db.commit()
    print(f"✅ Grammar Achievements: {len(data)}개 항목이 성공적으로 생성되었습니다.")
    print("   레벨별 분포:")
    for level, count in sorted(level_counts.items()):
        print(f"   - {level}: {count}개")

def init_vocabulary_categories(db):
    """어휘 카테고리 데이터를 초기화합니다."""
    if db.query(VocabularyCategory).count() > 0:
        existing_count = db.query(VocabularyCategory).count()
        print(f"📝 Vocabulary Categories: 이미 {existing_count}개 데이터가 존재합니다.")
        return
        
    data = load_json_data("vocabulary_categories")
    if not data:
        print("❌ Vocabulary Categories: 데이터 파일이 비어있거나 로드할 수 없습니다.")
        return
    
    print(f"📝 Vocabulary Categories 데이터 import 시작... ({len(data)}개 항목)")
    
    for item in data:
        category = VocabularyCategory(
            id=item.get("id"),
            name=item.get("name"),
            learning_objective=item.get("learning_objective"),
            created_at=datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')) if item.get("created_at") else None
        )
        db.add(category)
        print(f"   - {item.get('name')} (ID: {item.get('id')})")
    
    db.commit()
    print(f"✅ Vocabulary Categories: {len(data)}개 항목이 성공적으로 생성되었습니다.")

def init_words(db):
    """단어 데이터를 초기화합니다."""
    if db.query(Word).count() > 0:
        existing_count = db.query(Word).count()
        print(f"💬 Words: 이미 {existing_count}개 데이터가 존재합니다.")
        return
        
    data = load_json_data("words")
    if not data:
        print("❌ Words: 데이터 파일이 비어있거나 로드할 수 없습니다.")
        return
    
    print(f"💬 Words 데이터 import 시작... ({len(data)}개 항목)")
    
    # 레벨별 카운트를 위한 딕셔너리
    level_counts = {}
    
    for i, item in enumerate(data):
        word = Word(
            id=item.get("id"),
            word=item.get("word"),
            level=item.get("level"),
            created_at=datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')) if item.get("created_at") else None
        )
        db.add(word)
        
        # 레벨별 카운트 증가
        level = item.get("level", "unknown")
        level_counts[level] = level_counts.get(level, 0) + 1
        
        # 처음 10개만 개별 출력, 이후는 100개마다 진행상황 출력
        if i < 10:
            print(f"   - {item.get('word')} ({item.get('level')}) (ID: {item.get('id')})")
        elif (i + 1) % 100 == 0:
            print(f"   ... {i + 1}/{len(data)} 개 처리됨")
    
    db.commit()
    
    # 레벨별 요약 출력
    print(f"✅ Words: {len(data)}개 항목이 성공적으로 생성되었습니다.")
    print("   레벨별 분포:")
    for level, count in sorted(level_counts.items()):
        print(f"   - {level}: {count}개")

def init_reading_types(db):
    """독해 유형 데이터를 초기화합니다."""
    if db.query(ReadingType).count() > 0:
        existing_count = db.query(ReadingType).count()
        print(f"📚 Reading Types: 이미 {existing_count}개 데이터가 존재합니다.")
        return
        
    data = load_json_data("reading_types")
    if not data:
        print("❌ Reading Types: 데이터 파일이 비어있거나 로드할 수 없습니다.")
        return
    
    print(f"📚 Reading Types 데이터 import 시작... ({len(data)}개 항목)")
    
    for item in data:
        reading_type = ReadingType(
            id=item.get("id"),
            name=item.get("name"),
            description=item.get("description"),
            created_at=datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')) if item.get("created_at") else None
        )
        db.add(reading_type)
        print(f"   - {item.get('name')} (ID: {item.get('id')})")
        print(f"     {item.get('description')}")
    
    db.commit()
    print(f"✅ Reading Types: {len(data)}개 항목이 성공적으로 생성되었습니다.")

def init_text_types(db):
    """텍스트 유형 데이터를 초기화합니다."""
    if db.query(TextType).count() > 0:
        existing_count = db.query(TextType).count()
        print(f"📄 Text Types: 이미 {existing_count}개 데이터가 존재합니다.")
        return
        
    data = load_json_data("text_types")
    if not data:
        print("❌ Text Types: 데이터 파일이 비어있거나 로드할 수 없습니다.")
        return
    
    print(f"📄 Text Types 데이터 import 시작... ({len(data)}개 항목)")
    
    for item in data:
        text_type = TextType(
            id=item.get("id"),
            type_name=item.get("type_name"),
            display_name=item.get("display_name"),
            description=item.get("description"),
            json_format=item.get("json_format"),
            created_at=datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')) if item.get("created_at") else None
        )
        db.add(text_type)
        print(f"   - {item.get('display_name')} ({item.get('type_name')}) (ID: {item.get('id')})")
        print(f"     {item.get('description')}")
    
    db.commit()
    print(f"✅ Text Types: {len(data)}개 항목이 성공적으로 생성되었습니다.")

def init_all_data():
    """모든 초기 데이터를 데이터베이스에 생성합니다."""
    print("\n" + "="*80)
    print("🚀 English Service 초기 데이터 생성을 시작합니다...")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # 순서대로 데이터 초기화 (외래키 관계 고려)
        init_grammar_categories(db)
        init_grammar_topics(db)
        init_grammar_achievements(db)
        init_vocabulary_categories(db)
        init_words(db)
        init_reading_types(db)
        init_text_types(db)
        
        print("\n" + "="*80)
        print("✨ 모든 초기 데이터 생성이 완료되었습니다!")
        print("="*80)
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_all_data()
