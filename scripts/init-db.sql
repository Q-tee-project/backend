-- 교육 플랫폼 데이터베이스 초기화 스크립트
-- This script runs automatically when PostgreSQL container starts

-- 메인 데이터베이스가 이미 생성되어 있으므로 추가 설정만 수행

-- 각 서비스별 스키마 생성 (선택사항)
CREATE SCHEMA IF NOT EXISTS math_service;
CREATE SCHEMA IF NOT EXISTS english_service;

-- 기본 권한 설정
GRANT ALL PRIVILEGES ON SCHEMA math_service TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA english_service TO postgres;

-- 확장 기능 활성화 (필요한 경우)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 테이블 생성은 각 서비스의 애플리케이션에서 자동으로 처리됩니다.
-- (SQLAlchemy의 Base.metadata.create_all()을 통해)

COMMENT ON SCHEMA math_service IS '수학 문제 생성 및 채점 서비스용 스키마';
COMMENT ON SCHEMA english_service IS '영어 문제 생성 서비스용 스키마';