-- 답지 테이블 재생성 스크립트 (개발환경 전용)
-- 주의: 기존 답지 데이터가 모두 삭제됩니다!

-- 기존 테이블 삭제 (FK 제약조건 때문에 순서 중요)
DROP TABLE IF EXISTS english_service.answer_questions CASCADE;
DROP TABLE IF EXISTS english_service.answer_passages CASCADE;
DROP TABLE IF EXISTS english_service.answer_examples CASCADE;

-- 확인용 메시지
SELECT '답지 테이블 삭제 완료. 서버를 재시작하면 새로운 스키마로 테이블이 재생성됩니다.' as message;
