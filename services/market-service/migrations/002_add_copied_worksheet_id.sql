-- Add copied_worksheet_id column to market_purchases table
ALTER TABLE market_service.market_purchases
ADD COLUMN copied_worksheet_id INTEGER;