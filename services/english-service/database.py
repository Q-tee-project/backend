from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 데이터베이스 URL 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/testdb")

# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 로컬 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (모델들이 상속받을 클래스)
Base = declarative_base()

# 데이터베이스 의존성 함수
def get_db():
    """
    데이터베이스 세션을 생성하고 반환하는 의존성 함수
    FastAPI의 Depends와 함께 사용됩니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 데이터베이스 초기화 함수
def init_db():
    """
    데이터베이스 테이블을 생성하는 함수
    애플리케이션 시작 시 호출됩니다.
    """
    # 모델들을 import해서 Base에 등록
    import models
    Base.metadata.create_all(bind=engine)
