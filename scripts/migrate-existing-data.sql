-- 기존 public 스키마의 auth 관련 데이터를 auth_service 스키마로 이동하는 스크립트
-- 이 스크립트는 데이터가 있는 상태에서 실행해야 합니다.

-- 1. 기존 public 스키마의 테이블들을 auth_service 스키마로 이동
DO $$ 
BEGIN
    -- Auth service 테이블들 이동 (데이터와 함께)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'teachers') THEN
        RAISE NOTICE 'Moving teachers table from public to auth_service schema...';
        ALTER TABLE public.teachers SET SCHEMA auth_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'students') THEN
        RAISE NOTICE 'Moving students table from public to auth_service schema...';
        ALTER TABLE public.students SET SCHEMA auth_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'classrooms') THEN
        RAISE NOTICE 'Moving classrooms table from public to auth_service schema...';
        ALTER TABLE public.classrooms SET SCHEMA auth_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'student_join_requests') THEN
        RAISE NOTICE 'Moving student_join_requests table from public to auth_service schema...';
        ALTER TABLE public.student_join_requests SET SCHEMA auth_service;
    END IF;

    -- Math service 테이블들 이동
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'worksheets') THEN
        RAISE NOTICE 'Moving worksheets table from public to math_service schema...';
        ALTER TABLE public.worksheets SET SCHEMA math_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'problems') THEN
        RAISE NOTICE 'Moving problems table from public to math_service schema...';
        ALTER TABLE public.problems SET SCHEMA math_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'math_problem_generations') THEN
        RAISE NOTICE 'Moving math_problem_generations table from public to math_service schema...';
        ALTER TABLE public.math_problem_generations SET SCHEMA math_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'grading_sessions') THEN
        RAISE NOTICE 'Moving grading_sessions table from public to math_service schema...';
        ALTER TABLE public.grading_sessions SET SCHEMA math_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'problem_grading_results') THEN
        RAISE NOTICE 'Moving problem_grading_results table from public to math_service schema...';
        ALTER TABLE public.problem_grading_results SET SCHEMA math_service;
    END IF;

    -- English service 테이블들 이동  
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'grammar_categories') THEN
        RAISE NOTICE 'Moving grammar_categories table from public to english_service schema...';
        ALTER TABLE public.grammar_categories SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'grammar_topics') THEN
        RAISE NOTICE 'Moving grammar_topics table from public to english_service schema...';
        ALTER TABLE public.grammar_topics SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'vocabulary_categories') THEN
        RAISE NOTICE 'Moving vocabulary_categories table from public to english_service schema...';
        ALTER TABLE public.vocabulary_categories SET SCHEMA english_service;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'words') THEN
        RAISE NOTICE 'Moving words table from public to english_service schema...';
        ALTER TABLE public.words SET SCHEMA english_service;
    END IF;

    RAISE NOTICE 'Schema migration completed successfully!';
    
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Error during schema migration: %', SQLERRM;
END $$;