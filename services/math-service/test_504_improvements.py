#!/usr/bin/env python3
"""
504 Timeout 개선사항 테스트 스크립트

이 스크립트는 다음 개선사항들이 올바르게 적용되었는지 확인합니다:
1. API 요청 temperature 값 조정 (0.1로 설정)
2. 최종 프롬프트 로깅
3. 난이도별 분리 요청 전략
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_temperature_setting():
    """Temperature 설정 테스트"""
    print("1. Temperature 설정 테스트")
    try:
        from app.services.problem_generator import ProblemGenerator
        generator = ProblemGenerator()

        # 모델 설정 확인
        config = generator.model._generation_config
        temp = config.temperature if hasattr(config, 'temperature') else "설정되지 않음"

        print(f"   - 현재 Temperature: {temp}")
        if temp == 0.1:
            print("   ✅ Temperature가 올바르게 설정됨 (0.1)")
        else:
            print("   ❌ Temperature 설정 확인 필요")

        return temp == 0.1
    except Exception as e:
        print(f"   ❌ Temperature 테스트 실패: {e}")
        return False

def test_logging_setup():
    """로깅 설정 테스트"""
    print("\n2. 로깅 설정 테스트")
    try:
        from app.services.problem_generator import ProblemGenerator
        generator = ProblemGenerator()

        # 로거 존재 확인
        if hasattr(generator, 'logger'):
            print("   ✅ 로거가 올바르게 설정됨")
            print(f"   - 로거 이름: {generator.logger.name}")
            print(f"   - 로거 레벨: {generator.logger.level}")
            return True
        else:
            print("   ❌ 로거가 설정되지 않음")
            return False
    except Exception as e:
        print(f"   ❌ 로깅 테스트 실패: {e}")
        return False

def test_difficulty_separation_method():
    """난이도별 분리 메서드 존재 확인"""
    print("\n3. 난이도별 분리 메서드 테스트")
    try:
        from app.services.math_generation_service import MathGenerationService
        service = MathGenerationService()

        # 새로운 메서드들 존재 확인
        methods_to_check = [
            '_generate_problems_by_difficulty',
            '_generate_single_difficulty_batch'
        ]

        missing_methods = []
        for method_name in methods_to_check:
            if not hasattr(service, method_name):
                missing_methods.append(method_name)

        if not missing_methods:
            print("   ✅ 모든 난이도 분리 메서드가 존재함")
            for method in methods_to_check:
                print(f"     - {method}: 존재")
            return True
        else:
            print("   ❌ 일부 메서드가 누락됨:")
            for method in missing_methods:
                print(f"     - {method}: 누락")
            return False

    except Exception as e:
        print(f"   ❌ 메서드 존재 테스트 실패: {e}")
        return False

def test_ai_service_temperature():
    """AI 서비스의 temperature 설정 테스트"""
    print("\n4. AI 서비스 Temperature 설정 테스트")
    try:
        from app.services.ai_service import AIService
        ai_service = AIService()

        # 모델 설정 확인
        config = ai_service.model._generation_config
        temp = config.temperature if hasattr(config, 'temperature') else "설정되지 않음"

        print(f"   - AI 서비스 Temperature: {temp}")
        if temp == 0.1:
            print("   ✅ AI 서비스 Temperature가 올바르게 설정됨 (0.1)")
        else:
            print("   ❌ AI 서비스 Temperature 설정 확인 필요")

        return temp == 0.1
    except Exception as e:
        print(f"   ❌ AI 서비스 Temperature 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("=== 504 Timeout 개선사항 검증 ===\n")

    tests = [
        test_temperature_setting,
        test_logging_setup,
        test_difficulty_separation_method,
        test_ai_service_temperature
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"테스트 실행 중 오류: {e}")
            results.append(False)

    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약:")
    print("="*50)

    test_names = [
        "Temperature 설정",
        "로깅 설정",
        "난이도별 분리 메서드",
        "AI 서비스 Temperature"
    ]

    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
        if result:
            passed += 1

    print(f"\n총 {len(results)}개 테스트 중 {passed}개 통과")

    if passed == len(results):
        print("🎉 모든 504 timeout 개선사항이 올바르게 적용되었습니다!")
    else:
        print("⚠️ 일부 개선사항에 문제가 있습니다. 위 결과를 확인해주세요.")

    return passed == len(results)

if __name__ == "__main__":
    main()