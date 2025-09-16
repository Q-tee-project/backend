-- Qt Project Database Schema Organization
-- 수학과 영어 관련 테이블을 스키마별로 분리하여 가독성 향상

-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS math_service;
CREATE SCHEMA IF NOT EXISTS english_service;
CREATE SCHEMA IF NOT EXISTS auth_service;
CREATE SCHEMA IF NOT EXISTS korean_service;

-- 스키마 권한 설정
GRANT USAGE ON SCHEMA math_service TO PUBLIC;
GRANT USAGE ON SCHEMA english_service TO PUBLIC;
GRANT USAGE ON SCHEMA auth_service TO PUBLIC;
GRANT USAGE ON SCHEMA korean_service TO PUBLIC;

-- 기존 public 스키마의 테이블들을 적절한 스키마로 이동
-- (테이블이 존재할 때만 실행)
DO $$ 
BEGIN
    -- Auth service 테이블들 이동
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'teachers') THEN
        ALTER TABLE public.teachers SET SCHEMA auth_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'students') THEN
        ALTER TABLE public.students SET SCHEMA auth_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'classrooms') THEN
        ALTER TABLE public.classrooms SET SCHEMA auth_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'student_join_requests') THEN
        ALTER TABLE public.student_join_requests SET SCHEMA auth_service;
    END IF;

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

    -- Korean service 테이블들 이동 (문제 생성/채점 관련만)
    -- 주의: 테이블명이 겹치지 않도록 스키마 우선순위에 따라 이동
    -- public 스키마에 korean 전용 테이블이 있다면 korean_service로 이동
END $$;

COMMENT ON SCHEMA math_service IS '수학 문제 생성 및 채점 관련 테이블들';
COMMENT ON SCHEMA english_service IS '영어 문법, 어휘, 독해 관련 테이블들';
COMMENT ON SCHEMA auth_service IS '사용자 인증 및 계정 관리 관련 테이블들';
COMMENT ON SCHEMA korean_service IS '국어 문제 생성 및 채점 관련 테이블들';