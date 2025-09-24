-- 수학 서비스: completed_at -> submitted_at 마이그레이션
-- 기존 completed_at 데이터가 있다면 submitted_at로 복사
UPDATE math_service.assignment_deployments
SET submitted_at = completed_at
WHERE completed_at IS NOT NULL AND submitted_at IS NULL;

-- 영어 서비스: completed_at -> submitted_at 마이그레이션
-- 기존 completed_at 데이터가 있다면 submitted_at로 복사
UPDATE english_service.assignment_deployments
SET submitted_at = completed_at
WHERE completed_at IS NOT NULL AND submitted_at IS NULL;

-- 완료된 상태인데 submitted_at이 NULL인 경우를 위한 안전장치
-- 수학 서비스
UPDATE math_service.assignment_deployments
SET submitted_at = deployed_at
WHERE status = 'completed' AND submitted_at IS NULL;

-- 영어 서비스
UPDATE english_service.assignment_deployments
SET submitted_at = deployed_at
WHERE status = 'completed' AND submitted_at IS NULL;

-- 국어 서비스도 동일한 안전장치
UPDATE korean_service.korean_assignment_deployments
SET submitted_at = deployed_at
WHERE status = 'completed' AND submitted_at IS NULL;