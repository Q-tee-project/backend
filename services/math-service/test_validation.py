#!/usr/bin/env python3
"""
AI 문제 검증 시스템 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.problem_validation_service import ProblemValidationService
import time

def test_basic_validation():
    """기본 검증 기능 테스트"""
    print("🧪 AI 문제 검증 시스템 테스트 시작\n")

    # 검증 서비스 초기화
    try:
        validator = ProblemValidationService()
        print("✅ ProblemValidationService 초기화 성공")
    except Exception as e:
        print(f"❌ 검증 서비스 초기화 실패: {e}")
        return False

    # 테스트 문제들
    test_problems = [
        {
            "name": "올바른 기본 문제",
            "problem": {
                "question": "$2 + 3 = ?$",
                "correct_answer": "5",
                "explanation": "2에 3을 더하면 5입니다.",
                "problem_type": "short_answer",
                "difficulty": "A"
            },
            "expected_valid": True
        },
        {
            "name": "수학적 오류가 있는 문제",
            "problem": {
                "question": "$2 + 3 = ?$",
                "correct_answer": "6",  # 틀린 정답
                "explanation": "2에 3을 더하면 6입니다.",
                "problem_type": "short_answer",
                "difficulty": "A"
            },
            "expected_valid": False
        },
        {
            "name": "LaTeX 오류가 있는 문제",
            "problem": {
                "question": "frac{1}{2} + frac{1}{3} = ?",  # 백슬래시 누락
                "correct_answer": "$\\frac{5}{6}$",
                "explanation": "분수의 덧셈입니다.",
                "problem_type": "short_answer",
                "difficulty": "B"
            },
            "expected_valid": False
        },
        {
            "name": "객관식 문제",
            "problem": {
                "question": "$x^2 - 4 = 0$을 만족하는 $x$의 값은?",
                "choices": ["$x = 2$", "$x = -2$", "$x = \\pm 2$", "$x = 4$"],
                "correct_answer": "$x = \\pm 2$",
                "explanation": "$x^2 = 4$이므로 $x = \\pm 2$입니다.",
                "problem_type": "multiple_choice",
                "difficulty": "B"
            },
            "expected_valid": True
        }
    ]

    # 테스트 실행
    results = []
    for i, test_case in enumerate(test_problems, 1):
        print(f"\n📝 테스트 {i}: {test_case['name']}")
        print("-" * 50)

        start_time = time.time()

        try:
            # 검증 수행
            validation_result = validator.validate_problem(test_case["problem"])

            end_time = time.time()
            duration = end_time - start_time

            # 결과 출력
            print(f"⏱️  검증 시간: {duration:.2f}초")
            print(f"✅ 검증 완료:")
            print(f"   - 유효성: {validation_result['is_valid']}")
            print(f"   - 수학적 정확성: {validation_result['math_accuracy']}")
            print(f"   - 정답 정확성: {validation_result['answer_correctness']}")
            print(f"   - 해설 품질: {validation_result['explanation_quality']}")
            print(f"   - LaTeX 문법: {validation_result['latex_syntax']}")
            print(f"   - 난이도 적절성: {validation_result['difficulty_appropriateness']}")
            print(f"   - 신뢰도: {validation_result['confidence_score']:.2f}")
            print(f"   - 자동 승인: {validation_result['auto_approve']}")

            if validation_result['issues']:
                print(f"   - 발견된 문제점: {validation_result['issues']}")

            if validation_result['suggestions']:
                print(f"   - 개선 제안: {validation_result['suggestions']}")

            # 예상 결과와 비교
            expected = test_case["expected_valid"]
            actual = validation_result["is_valid"]

            if expected == actual:
                print(f"🎯 예상 결과와 일치 (유효성: {actual})")
                result_status = "PASS"
            else:
                print(f"❌ 예상 결과와 불일치 (예상: {expected}, 실제: {actual})")
                result_status = "FAIL"

            results.append({
                "test_name": test_case["name"],
                "status": result_status,
                "duration": duration,
                "validation_result": validation_result
            })

        except Exception as e:
            print(f"❌ 검증 중 오류 발생: {e}")
            results.append({
                "test_name": test_case["name"],
                "status": "ERROR",
                "error": str(e)
            })

    # 전체 결과 요약
    print("\n" + "="*60)
    print("🏁 테스트 결과 요약")
    print("="*60)

    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = sum(1 for r in results if r.get("status") == "FAIL")
    errors = sum(1 for r in results if r.get("status") == "ERROR")

    print(f"총 테스트: {len(results)}")
    print(f"통과: {passed}")
    print(f"실패: {failed}")
    print(f"오류: {errors}")

    if errors == 0 and failed == 0:
        print("\n🎉 모든 테스트 통과! AI 검증 시스템이 정상적으로 작동합니다.")
        return True
    else:
        print(f"\n⚠️  일부 테스트 실패. 시스템 점검이 필요합니다.")
        return False

def test_batch_validation():
    """일괄 검증 기능 테스트"""
    print("\n\n🔄 일괄 검증 테스트")
    print("-" * 40)

    try:
        validator = ProblemValidationService()

        # 여러 문제 준비
        problems = [
            {
                "question": "$1 + 1 = ?$",
                "correct_answer": "2",
                "explanation": "기본 덧셈입니다.",
                "problem_type": "short_answer",
                "difficulty": "A"
            },
            {
                "question": "$x^2 + 2x + 1 = 0$의 해는?",
                "correct_answer": "$x = -1$",
                "explanation": "$(x+1)^2 = 0$이므로 $x = -1$입니다.",
                "problem_type": "short_answer",
                "difficulty": "B"
            },
            {
                "question": "잘못된 문제",
                "correct_answer": "틀린 답",
                "explanation": "이상한 해설",
                "problem_type": "short_answer",
                "difficulty": "C"
            }
        ]

        start_time = time.time()

        # 일괄 검증 수행
        validation_results = validator.validate_problem_batch(problems)

        end_time = time.time()
        total_duration = end_time - start_time

        # 요약 생성
        summary = validator.get_validation_summary(validation_results)

        print(f"✅ 일괄 검증 완료 ({total_duration:.2f}초)")
        print(f"📊 검증 요약:")
        print(f"   - 총 문제 수: {summary['total_problems']}")
        print(f"   - 유효한 문제: {summary['valid_problems']}")
        print(f"   - 무효한 문제: {summary['invalid_problems']}")
        print(f"   - 자동 승인: {summary['auto_approved']}")
        print(f"   - 수동 검토 필요: {summary['manual_review_needed']}")
        print(f"   - 유효율: {summary['validity_rate']}%")
        print(f"   - 자동 승인율: {summary['auto_approval_rate']}%")

        if summary['common_issues']:
            print(f"   - 자주 발견되는 문제점:")
            for issue, count in summary['common_issues'].items():
                print(f"     * {issue}: {count}회")

        return True

    except Exception as e:
        print(f"❌ 일괄 검증 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AI 문제 검증 시스템 종합 테스트")
    print("=" * 60)

    # 기본 검증 테스트
    basic_success = test_basic_validation()

    # 일괄 검증 테스트
    batch_success = test_batch_validation()

    # 최종 결과
    print("\n" + "="*60)
    print("🏆 최종 테스트 결과")
    print("="*60)

    if basic_success and batch_success:
        print("🎉 모든 테스트 통과! AI 검증 시스템이 완전히 작동합니다.")
        print("\n📋 사용 가능한 기능:")
        print("  ✅ 단일 문제 검증")
        print("  ✅ 일괄 문제 검증")
        print("  ✅ 수학적 정확성 검사")
        print("  ✅ LaTeX 문법 검증")
        print("  ✅ 난이도 적절성 검증")
        print("  ✅ 자동 승인 판정")
        print("  ✅ 검증 요약 및 통계")

        print("\n🔗 다음 단계:")
        print("  1. FastAPI 서버 실행: python math_main.py")
        print("  2. API 엔드포인트 테스트: http://localhost:8000/docs")
        print("  3. 실제 문제 생성 및 검증 테스트")

        exit(0)
    else:
        print("❌ 일부 테스트 실패. 시스템 점검 후 다시 테스트하세요.")
        exit(1)