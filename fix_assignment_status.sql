-- 기존 'submitted' 상태를 'completed'로 업데이트

-- 수학 서비스
UPDATE math_service.assignment_deployments
SET status = 'completed'
WHERE status = 'submitted';

-- 국어 서비스
UPDATE korean_service.assignment_deployments
SET status = 'completed'
WHERE status = 'submitted';

-- 영어 서비스
UPDATE english_service.assignment_deployments
SET status = 'completed'
WHERE status = 'submitted';

-- 업데이트된 레코드 수 확인
SELECT 'math_service' as service, COUNT(*) as updated_count
FROM math_service.assignment_deployments
WHERE status = 'completed'
UNION ALL
SELECT 'korean_service' as service, COUNT(*) as updated_count
FROM korean_service.assignment_deployments
WHERE status = 'completed'
UNION ALL
SELECT 'english_service' as service, COUNT(*) as updated_count
FROM english_service.assignment_deployments
WHERE status = 'completed';