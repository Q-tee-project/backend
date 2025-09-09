#!/usr/bin/env python3
"""
지문 유형 초기 데이터 생성 스크립트

각 지문 유형별 JSON 형식 예시를 데이터베이스에 저장합니다.
"""

from sqlalchemy.orm import sessionmaker
from database import engine
from models import TextType
from datetime import datetime

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_text_types():
    """지문 유형 초기 데이터를 생성합니다."""
    db = SessionLocal()
    
    try:
        # 기존 데이터 확인
        existing_count = db.query(TextType).count()
        if existing_count > 0:
            print(f"이미 {existing_count}개의 지문 유형이 존재합니다.")
            return
        
        # 지문 유형별 데이터 정의
        text_types_data = [
            {
                "type_name": "article",
                "display_name": "일반 글",
                "description": "설명문, 논설문, 기사, 연구 보고서, 블로그 포스트, 책의 한 부분 등 가장 기본적인 '만능' 유형",
                "json_format": {
                    "content": {
                        "title": "글 제목",
                        "paragraphs": [
                            {"text": "첫 번째 문단 내용"},
                            {"text": "두 번째 문단 내용"},
                            {"text": "세 번째 문단 내용"}
                        ]
                    }
                }
            },
            {
                "type_name": "correspondence",
                "display_name": "서신/소통",
                "description": "이메일, 편지, 메모, 사내 공지 등",
                "json_format": {
                    "metadata": {
                        "sender": "발신자 이름",
                        "recipient": "수신자 이름",
                        "subject": "제목/주제",
                        "date": "날짜"
                    },
                    "content": {
                        "paragraphs": [
                            {"text": "본문 첫 번째 문단"},
                            {"text": "본문 두 번째 문단"}
                        ]
                    }
                }
            },
            {
                "type_name": "dialogue",
                "display_name": "대화문",
                "description": "문자 메시지, 채팅, 인터뷰, 연극 대본 등",
                "json_format": {
                    "metadata": {
                        "participants": ["화자1", "화자2", "화자3"]
                    },
                    "content": [
                        {"speaker": "화자1", "line": "첫 번째 대사"},
                        {"speaker": "화자2", "line": "두 번째 대사"},
                        {"speaker": "화자1", "line": "세 번째 대사"}
                    ]
                }
            },
            {
                "type_name": "informational",
                "display_name": "정보성 양식",
                "description": "광고, 안내문, 포스터, 일정표, 메뉴판, 영수증 등",
                "json_format": {
                    "content": {
                        "title": "정보 제목",
                        "paragraphs": [
                            {"text": "설명 문단"}
                        ],
                        "lists": [
                            {"text": "항목 1"},
                            {"text": "항목 2"},
                            {"text": "항목 3"}
                        ],
                        "key_values": [
                            {"key": "장소", "value": "시청 앞"},
                            {"key": "시간", "value": "오후 2시"},
                            {"key": "연락처", "value": "02-1234-5678"}
                        ]
                    }
                }
            },
            {
                "type_name": "review",
                "display_name": "리뷰/후기",
                "description": "상품 후기, 영화 평점, 식당 리뷰 등",
                "json_format": {
                    "metadata": {
                        "rating": 4.5,
                        "product_name": "상품/서비스명",
                        "reviewer": "리뷰어 이름"
                    },
                    "content": {
                        "title": "리뷰 제목",
                        "paragraphs": [
                            {"text": "리뷰 내용 첫 번째 문단"},
                            {"text": "리뷰 내용 두 번째 문단"}
                        ]
                    }
                }
            },
            {
                "type_name": "social_media",
                "display_name": "SNS",
                "description": "트위터, 인스타그램 게시물, 페이스북 포스트 등",
                "json_format": {
                    "content": {
                        "text": "SNS 게시물 내용",
                        "hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"]
                    }
                }
            }
        ]
        
        # 데이터베이스에 저장
        for data in text_types_data:
            text_type = TextType(
                type_name=data["type_name"],
                display_name=data["display_name"],
                description=data["description"],
                json_format=data["json_format"],
                created_at=datetime.now()
            )
            db.add(text_type)
        
        db.commit()
        print(f"✅ {len(text_types_data)}개의 지문 유형이 성공적으로 생성되었습니다!")
        
        # 생성된 데이터 확인
        print("\n📋 생성된 지문 유형들:")
        text_types = db.query(TextType).all()
        for tt in text_types:
            print(f"  - {tt.type_name} ({tt.display_name}): {tt.description}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 지문 유형 초기 데이터 생성을 시작합니다...")
    init_text_types()
    print("✨ 완료!")
