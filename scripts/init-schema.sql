-- Qt Project Database Schema Organization
-- 수학과 영어 관련 테이블을 스키마별로 분리하여 가독성 향상

-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS math_service;
CREATE SCHEMA IF NOT EXISTS english_service;
CREATE SCHEMA IF NOT EXISTS shared;

-- 스키마 권한 설정
GRANT USAGE ON SCHEMA math_service TO PUBLIC;
GRANT USAGE ON SCHEMA english_service TO PUBLIC;
GRANT USAGE ON SCHEMA shared TO PUBLIC;

-- 기존 public 스키마의 테이블들을 적절한 스키마로 이동
-- (테이블이 존재할 때만 실행)
DO $$ 
BEGIN
    -- Math service 테이블들 이동
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'worksheets') THEN
        ALTER TABLE public.worksheets SET SCHEMA math_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'problems') THEN
        ALTER TABLE public.problems SET SCHEMA math_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'math_problem_generations') THEN
        ALTER TABLE public.math_problem_generations SET SCHEMA math_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'grading_sessions') THEN
        ALTER TABLE public.grading_sessions SET SCHEMA math_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'problem_grading_results') THEN
        ALTER TABLE public.problem_grading_results SET SCHEMA math_service;
    END IF;
    
    -- English service 테이블들 이동
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'grammar_categories') THEN
        ALTER TABLE public.grammar_categories SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'grammar_topics') THEN
        ALTER TABLE public.grammar_topics SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'grammar_achievements') THEN
        ALTER TABLE public.grammar_achievements SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'vocabulary_categories') THEN
        ALTER TABLE public.vocabulary_categories SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'words') THEN
        ALTER TABLE public.words SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'reading_types') THEN
        ALTER TABLE public.reading_types SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'text_types') THEN
        ALTER TABLE public.text_types SET SCHEMA english_service;
    END IF;
END $$;

COMMENT ON SCHEMA math_service IS '수학 문제 생성 및 채점 관련 테이블들';
COMMENT ON SCHEMA english_service IS '영어 문법, 어휘, 독해 관련 테이블들';
COMMENT ON SCHEMA shared IS '서비스 간 공유되는 공통 테이블들';