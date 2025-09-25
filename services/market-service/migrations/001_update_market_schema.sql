-- 마켓플레이스 DB 스키마 업데이트
-- 이미지 기반에서 미리보기 문제 기반으로 변경

-- 1. 기존 테이블 백업 (선택사항)
-- CREATE TABLE market_service.market_products_backup AS SELECT * FROM market_service.market_products;

-- 2. 기존 컬럼 제거 및 새 컬럼 추가
ALTER TABLE market_service.market_products
DROP COLUMN IF EXISTS images,
DROP COLUMN IF EXISTS main_image,
DROP COLUMN IF EXISTS status;

-- 3. 새로운 컬럼들 추가
ALTER TABLE market_service.market_products
ADD COLUMN worksheet_title VARCHAR(200) NOT NULL DEFAULT '',
ADD COLUMN worksheet_problems JSON NOT NULL DEFAULT '[]',
ADD COLUMN problem_count INTEGER NOT NULL DEFAULT 10,
ADD COLUMN school_level VARCHAR(20) NOT NULL DEFAULT '',
ADD COLUMN grade INTEGER NOT NULL DEFAULT 1,
ADD COLUMN semester VARCHAR(10),
ADD COLUMN unit_info VARCHAR(100),
ADD COLUMN preview_problems JSON NOT NULL DEFAULT '[]',
ADD COLUMN main_preview_problem_id INTEGER,
ADD COLUMN total_reviews INTEGER DEFAULT 0,
ADD COLUMN recommend_count INTEGER DEFAULT 0,
ADD COLUMN normal_count INTEGER DEFAULT 0,
ADD COLUMN not_recommend_count INTEGER DEFAULT 0,
ADD COLUMN satisfaction_rate FLOAT DEFAULT 0.0,
ADD COLUMN search_tags TEXT,
ADD COLUMN featured BOOLEAN DEFAULT FALSE,
ADD COLUMN trending_score FLOAT DEFAULT 0.0,
ADD COLUMN worksheet_metadata JSON;

-- 4. price 컬럼 타입 변경 (Decimal에서 Integer로)
ALTER TABLE market_service.market_products
ALTER COLUMN price TYPE INTEGER USING ROUND(price::numeric);

-- 5. 기존 tags 컬럼을 JSON으로 변경 (필요한 경우)
ALTER TABLE market_service.market_products
ALTER COLUMN tags TYPE JSON USING
CASE
    WHEN tags IS NULL THEN '[]'::json
    ELSE ('[' || '"' || replace(tags::text, ',', '","') || '"' || ']')::json
END;

-- 6. 리뷰 테이블 rating 컬럼 업데이트
ALTER TABLE market_service.market_reviews
ALTER COLUMN rating TYPE VARCHAR(20) USING
CASE
    WHEN rating::integer >= 4 THEN 'recommend'
    WHEN rating::integer = 3 THEN 'normal'
    ELSE 'not-recommend'
END;

-- 7. comment 컬럼 제거 (텍스트 리뷰 없음)
ALTER TABLE market_service.market_reviews
DROP COLUMN IF EXISTS comment;

-- 8. 고유 제약조건 추가 (워크시트 중복 등록 방지)
ALTER TABLE market_service.market_products
ADD CONSTRAINT unique_worksheet_product
UNIQUE (original_service, original_worksheet_id);

-- 9. 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_market_products_subject_type
ON market_service.market_products(subject_type);

CREATE INDEX IF NOT EXISTS idx_market_products_school_grade
ON market_service.market_products(school_level, grade);

CREATE INDEX IF NOT EXISTS idx_market_products_satisfaction
ON market_service.market_products(satisfaction_rate DESC);

CREATE INDEX IF NOT EXISTS idx_market_products_trending
ON market_service.market_products(trending_score DESC);

-- 10. 함수: 만족도 자동 계산 트리거
CREATE OR REPLACE FUNCTION market_service.update_satisfaction_rate()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE market_service.market_products
    SET satisfaction_rate =
        CASE
            WHEN total_reviews = 0 THEN 0.0
            ELSE ROUND((recommend_count::float / total_reviews::float) * 100, 1)
        END
    WHERE id = COALESCE(NEW.product_id, OLD.product_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 11. 트리거 생성: 리뷰 추가/삭제 시 통계 자동 업데이트
DROP TRIGGER IF EXISTS trigger_update_review_stats ON market_service.market_reviews;
CREATE TRIGGER trigger_update_review_stats
    AFTER INSERT OR DELETE OR UPDATE ON market_service.market_reviews
    FOR EACH ROW
    EXECUTE FUNCTION market_service.update_satisfaction_rate();

-- 12. 기본 데이터 정리 (필요한 경우)
-- UPDATE market_service.market_products
-- SET tags = '[]'::json WHERE tags IS NULL;

-- UPDATE market_service.market_products
-- SET preview_problems = '[]'::json WHERE preview_problems IS NULL;

-- ==================== 포인트 시스템 테이블 생성 ====================

-- 13. 사용자 포인트 테이블
CREATE TABLE IF NOT EXISTS market_service.user_points (
    user_id INTEGER PRIMARY KEY,
    available_points INTEGER DEFAULT 0 NOT NULL,
    total_earned INTEGER DEFAULT 0 NOT NULL,
    total_spent INTEGER DEFAULT 0 NOT NULL,
    total_charged INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 14. 포인트 거래 내역 테이블
CREATE TABLE IF NOT EXISTS market_service.point_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    product_id INTEGER,
    description VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 15. 포인트 시스템 인덱스
CREATE INDEX IF NOT EXISTS idx_point_transactions_user_id ON market_service.point_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_point_transactions_type ON market_service.point_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_point_transactions_created_at ON market_service.point_transactions(created_at DESC);

-- 16. MarketPurchase 테이블 포인트 시스템 업데이트
ALTER TABLE market_service.market_purchases
ALTER COLUMN payment_method TYPE VARCHAR(20) USING 'points',
ALTER COLUMN payment_method SET DEFAULT 'points';

-- 포인트로 결제된 구매만 허용
UPDATE market_service.market_purchases SET payment_method = 'points';

-- 17. 포인트 관련 제약조건
ALTER TABLE market_service.user_points
ADD CONSTRAINT check_available_points_non_negative CHECK (available_points >= 0);

ALTER TABLE market_service.point_transactions
ADD CONSTRAINT check_valid_transaction_type
CHECK (transaction_type IN ('charge', 'purchase', 'earn', 'admin_adjust'));

-- 18. 초기 포인트 지급 함수 (선택사항)
CREATE OR REPLACE FUNCTION market_service.give_welcome_points(p_user_id INTEGER, p_amount INTEGER DEFAULT 5000)
RETURNS VOID AS $$
BEGIN
    INSERT INTO market_service.user_points (user_id, available_points, total_charged)
    VALUES (p_user_id, p_amount, p_amount)
    ON CONFLICT (user_id) DO UPDATE SET
        available_points = user_points.available_points + p_amount,
        total_charged = user_points.total_charged + p_amount;

    INSERT INTO market_service.point_transactions (user_id, transaction_type, amount, balance_after, description)
    VALUES (p_user_id, 'charge', p_amount, (SELECT available_points FROM market_service.user_points WHERE user_id = p_user_id), '웰컴 포인트 지급');
END;
$$ LANGUAGE plpgsql;

-- 댓글 및 문서화
COMMENT ON TABLE market_service.market_products IS '마켓플레이스 상품 - 워크시트 복사본 기반';
COMMENT ON COLUMN market_service.market_products.preview_problems IS '미리보기 문제 ID 배열 (최대 3개)';
COMMENT ON COLUMN market_service.market_products.main_preview_problem_id IS '대표 미리보기 문제 ID';
COMMENT ON COLUMN market_service.market_products.satisfaction_rate IS '만족도 (추천 비율 %)';

COMMENT ON TABLE market_service.user_points IS '사용자 포인트 관리';
COMMENT ON TABLE market_service.point_transactions IS '포인트 거래 내역';
COMMENT ON COLUMN market_service.point_transactions.amount IS '포인트 양 (+ 적립, - 차감)';