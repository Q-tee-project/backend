-- 한글 번역 필드 추가 마이그레이션
-- 실행일: 2025-09-11
-- 목적: 답지에 한글 번역 기능 추가

-- Answer Passages 테이블에 korean_translation 컬럼 추가
ALTER TABLE english_service.answer_passages 
ADD COLUMN korean_translation TEXT;

-- Answer Examples 테이블에 korean_translation 컬럼 추가
ALTER TABLE english_service.answer_examples 
ADD COLUMN korean_translation TEXT;

-- 컬럼 추가 확인
COMMENT ON COLUMN english_service.answer_passages.korean_translation IS '지문의 한글 번역 (자연스럽고 읽기 쉬운 한국어)';
COMMENT ON COLUMN english_service.answer_examples.korean_translation IS '예문의 한글 번역 (자연스럽고 읽기 쉬운 한국어)';

-- 마이그레이션 완료 확인용 쿼리
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'english_service' 
  AND table_name IN ('answer_passages', 'answer_examples')
  AND column_name = 'korean_translation'
ORDER BY table_name, column_name;
