-- 1. submitted_at 컬럼 추가
ALTER TABLE math_service.assignment_deployments
ADD COLUMN submitted_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE english_service.assignment_deployments
ADD COLUMN submitted_at TIMESTAMP WITH TIME ZONE;

-- 2. 기존 completed_at 데이터를 submitted_at로 복사
UPDATE math_service.assignment_deployments
SET submitted_at = completed_at
WHERE completed_at IS NOT NULL;

UPDATE english_service.assignment_deployments
SET submitted_at = completed_at
WHERE completed_at IS NOT NULL;

-- 3. 완료된 상태인데 submitted_at이 NULL인 경우를 위한 안전장치
UPDATE math_service.assignment_deployments
SET submitted_at = deployed_at
WHERE status = 'completed' AND submitted_at IS NULL;

UPDATE english_service.assignment_deployments
SET submitted_at = deployed_at
WHERE status = 'completed' AND submitted_at IS NULL;

-- 국어 서비스는 이미 submitted_at이 있으므로 안전장치만
UPDATE korean_service.korean_assignment_deployments
SET submitted_at = deployed_at
WHERE status = 'completed' AND submitted_at IS NULL;