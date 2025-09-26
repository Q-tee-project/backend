-- Add total_revenue column to market_products table
ALTER TABLE market_service.market_products
ADD COLUMN total_revenue INTEGER DEFAULT 0;

-- Update existing products with calculated revenue
UPDATE market_service.market_products
SET total_revenue = (
    SELECT COALESCE(SUM(p.purchase_price), 0)
    FROM market_service.market_purchases p
    WHERE p.product_id = market_products.id
);