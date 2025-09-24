"""
문제 재생성 API 테스트 예시
실제 테스트를 위해서는 서버를 실행하고 아래 예시를 참고하세요.
"""

import requests
import json

# 서버 URL (로컬 테스트용)
BASE_URL = "http://localhost:8002"

def test_regeneration_info():
    """재생성 정보 조회 테스트"""
    url = f"{BASE_URL}/api/english/worksheets/test-worksheet-123/questions/1/regeneration-info"

    response = requests.get(url)
    print("=== 재생성 정보 조회 ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()


def test_basic_regeneration():
    """기본 재생성 테스트 - 모든 조건 유지"""
    url = f"{BASE_URL}/api/english/worksheets/test-worksheet-123/questions/1/regenerate"

    payload = {
        "feedback": "문제를 더 쉽게 만들어주세요",
        "worksheet_context": {
            "school_level": "중학교",
            "grade": 1,
            "worksheet_type": "혼합형"
        },
        "current_question_type": "객관식",
        "current_subject": "독해",
        "current_detail_type": "제목 및 요지 추론",
        "current_difficulty": "상"
    }

    response = requests.post(url, json=payload)
    print("=== 기본 재생성 테스트 ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()


def test_difficulty_change():
    """난이도 변경 재생성 테스트"""
    url = f"{BASE_URL}/api/english/worksheets/test-worksheet-123/questions/2/regenerate"

    payload = {
        "feedback": "문제가 너무 어려워요. 중학교 1학년 수준으로 맞춰주세요",
        "keep_difficulty": False,
        "target_difficulty": "하",
        "worksheet_context": {
            "school_level": "중학교",
            "grade": 1,
            "worksheet_type": "문법"
        },
        "current_question_type": "객관식",
        "current_subject": "문법",
        "current_detail_type": "시제",
        "current_difficulty": "상",
        "additional_requirements": "기본적인 어휘만 사용하고, 예문을 일상생활 관련으로 만들어주세요"
    }

    response = requests.post(url, json=payload)
    print("=== 난이도 변경 재생성 테스트 ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()


def test_passage_regeneration():
    """지문과 함께 재생성 테스트"""
    url = f"{BASE_URL}/api/english/worksheets/test-worksheet-123/questions/3/regenerate"

    payload = {
        "feedback": "지문이 너무 길고 어려워요. 더 짧고 재미있는 내용으로 바꿔주세요",
        "keep_passage": False,
        "worksheet_context": {
            "school_level": "중학교",
            "grade": 1,
            "worksheet_type": "독해"
        },
        "current_question_type": "객관식",
        "current_subject": "독해",
        "current_detail_type": "내용 일치",
        "current_difficulty": "중",
        "additional_requirements": "스포츠나 취미 관련 주제로 만들어주세요"
    }

    response = requests.post(url, json=payload)
    print("=== 지문과 함께 재생성 테스트 ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()


def test_subject_change():
    """영역 변경 재생성 테스트"""
    url = f"{BASE_URL}/api/english/worksheets/test-worksheet-123/questions/4/regenerate"

    payload = {
        "feedback": "독해 문제 대신 어휘 문제로 바꿔주세요",
        "keep_subject": False,
        "keep_detail_type": False,
        "target_subject": "어휘",
        "target_detail_type": "빈칸 추론",
        "worksheet_context": {
            "school_level": "중학교",
            "grade": 1,
            "worksheet_type": "혼합형"
        },
        "current_question_type": "객관식",
        "current_subject": "독해",
        "current_detail_type": "제목 추론",
        "current_difficulty": "중"
    }

    response = requests.post(url, json=payload)
    print("=== 영역 변경 재생성 테스트 ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()


def test_validation_error():
    """유효성 검사 오류 테스트"""
    url = f"{BASE_URL}/api/english/worksheets/test-worksheet-123/questions/5/regenerate"

    # 잘못된 요청: keep_difficulty=True인데 target_difficulty 설정
    payload = {
        "feedback": "테스트",
        "keep_difficulty": True,
        "target_difficulty": "하",  # 이것은 오류를 발생시켜야 함
        "worksheet_context": {
            "school_level": "중학교",
            "grade": 1,
            "worksheet_type": "문법"
        },
        "current_question_type": "객관식",
        "current_subject": "문법",
        "current_detail_type": "시제",
        "current_difficulty": "상"
    }

    response = requests.post(url, json=payload)
    print("=== 유효성 검사 오류 테스트 ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()


if __name__ == "__main__":
    print("문제 재생성 API 테스트를 시작합니다...\n")
    print("⚠️  주의: 이 테스트를 실행하기 전에 다음을 확인하세요:")
    print("1. 영어 서비스가 http://localhost:8002에서 실행 중인지")
    print("2. 테스트용 워크시트와 문제가 데이터베이스에 존재하는지")
    print("3. Gemini API 키가 올바르게 설정되어 있는지\n")

    # 모든 테스트 실행
    try:
        test_regeneration_info()
        test_basic_regeneration()
        test_difficulty_change()
        test_passage_regeneration()
        test_subject_change()
        test_validation_error()
        print("✅ 모든 테스트가 완료되었습니다!")

    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 영어 서비스가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")