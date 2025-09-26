-- 미리보기 관련 컬럼 제거 마이그레이션
-- 프론트엔드에서 subject, grade, title로 이미지 생성하므로 미리보기 컬럼 불필요

-- 1. 미리보기 관련 컬럼 제거
ALTER TABLE market_service.market_products
DROP COLUMN IF EXISTS preview_problems,
DROP COLUMN IF EXISTS main_preview_problem_id;

-- 2. 불필요한 메타데이터 컬럼들도 정리 (선택사항)
ALTER TABLE market_service.market_products
DROP COLUMN IF EXISTS search_tags,
DROP COLUMN IF EXISTS featured,
DROP COLUMN IF EXISTS trending_score,
DROP COLUMN IF EXISTS worksheet_metadata;

-- 3. 인덱스 정리
DROP INDEX IF EXISTS market_service.idx_market_products_trending;

-- 4. 주석 업데이트
COMMENT ON TABLE market_service.market_products IS '마켓플레이스 상품 - 워크시트 복사본 기반 (프론트엔드에서 subject, grade, title로 이미지 생성)';

-- 5. 기존 함수/트리거는 그대로 유지 (리뷰 통계 관련)
-- update_satisfaction_rate() 함수와 trigger_update_review_stats 트리거는 유지

COMMENT ON COLUMN market_service.market_products.subject_type IS '과목 (국어, 수학, 영어) - 프론트엔드 이미지 생성용';
COMMENT ON COLUMN market_service.market_products.grade IS '학년 - 프론트엔드 이미지 생성용';
COMMENT ON COLUMN market_service.market_products.title IS '상품명 - 프론트엔드 이미지 생성용';