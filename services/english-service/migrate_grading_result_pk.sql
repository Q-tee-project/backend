-- GradingResult 테이블의 기본키를 result_id로 변경하는 마이그레이션

-- 1. 외래키 제약조건 삭제
ALTER TABLE english_service.question_results 
DROP CONSTRAINT IF EXISTS question_results_grading_result_id_fkey;

-- 2. question_results 테이블의 grading_result_id 컬럼 타입 변경
ALTER TABLE english_service.question_results 
ALTER COLUMN grading_result_id TYPE VARCHAR(50);

-- 3. question_results 데이터 업데이트 (id -> result_id 매핑)
UPDATE english_service.question_results 
SET grading_result_id = (
    SELECT result_id 
    FROM english_service.grading_results 
    WHERE grading_results.id = question_results.grading_result_id::integer
);

-- 4. grading_results 테이블의 기본키 변경
ALTER TABLE english_service.grading_results DROP CONSTRAINT IF EXISTS grading_results_pkey;
ALTER TABLE english_service.grading_results DROP COLUMN IF EXISTS id;
ALTER TABLE english_service.grading_results ADD PRIMARY KEY (result_id);

-- 5. 외래키 제약조건 다시 추가
ALTER TABLE english_service.question_results 
ADD CONSTRAINT question_results_grading_result_id_fkey 
FOREIGN KEY (grading_result_id) REFERENCES english_service.grading_results(result_id) ON DELETE CASCADE;

-- 6. 인덱스 재생성
CREATE INDEX IF NOT EXISTS idx_question_results_grading_result_id 
ON english_service.question_results(grading_result_id);
