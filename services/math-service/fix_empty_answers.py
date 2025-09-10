#!/usr/bin/env python3
"""
비어있는 correct_answer 필드를 수정하는 스크립트

이 스크립트는 기존 문제들 중에서 correct_answer가 비어있는 문제들을
찾아서 explanation에서 정답을 추출하여 업데이트합니다.
"""

import os
import sys
import re
import psycopg2
from psycopg2.extras import RealDictCursor

# 환경변수에서 DB 설정 가져오기
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "qt_project_db"
DB_USER = "root"
DB_PASSWORD = "1234"

def connect_db():
    """데이터베이스 연결"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        sys.exit(1)

def extract_answer_from_explanation(explanation, problem_type):
    """explanation에서 정답 추출"""
    if not explanation:
        return None
        
    # 단답형 문제: 숫자나 간단한 식 찾기
    if problem_type == "short_answer":
        # LaTeX 형식의 답 찾기 ($x = 2$ 형태)
        latex_answer = re.search(r'\$[^$]*=[^$]*\$', explanation)
        if latex_answer:
            return latex_answer.group()
            
        # 단순 숫자 답 찾기
        number_answer = re.search(r'답은?\s*(\d+)', explanation)
        if number_answer:
            return number_answer.group(1)
            
        # 분수나 소수 찾기
        fraction_answer = re.search(r'답은?\s*(\$[^$]+\$)', explanation)
        if fraction_answer:
            return fraction_answer.group(1)
    
    # 서술형 문제: 전체 설명을 답안으로 사용
    elif problem_type in ["essay", "subjective"]:
        # 설명의 첫 번째 문장이나 핵심 부분 추출
        if len(explanation) > 300:
            # 너무 긴 경우 첫 두 문장만 사용
            sentences = explanation.split('. ')[:2]
            return '. '.join(sentences) + '.'
        else:
            return explanation
    
    return None

def fix_empty_answers():
    """비어있는 correct_answer 수정"""
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 비어있는 correct_answer 문제들 조회
        cur.execute("""
            SELECT id, problem_type, question, explanation, correct_answer
            FROM math_service.problems 
            WHERE correct_answer = '' OR correct_answer IS NULL
            ORDER BY id
        """)
        
        empty_problems = cur.fetchall()
        print(f"비어있는 답안을 가진 문제: {len(empty_problems)}개")
        
        updated_count = 0
        
        for problem in empty_problems:
            print(f"\n문제 ID {problem['id']} ({problem['problem_type']}):")
            print(f"질문: {problem['question'][:100]}...")
            print(f"현재 답안: '{problem['correct_answer']}'")
            
            # explanation에서 답안 추출 시도
            extracted_answer = extract_answer_from_explanation(
                problem['explanation'], 
                problem['problem_type']
            )
            
            if extracted_answer:
                print(f"추출된 답안: {extracted_answer[:100]}...")
                
                # 사용자 확인
                response = input("이 답안으로 업데이트하시겠습니까? (y/n/s=skip): ").lower()
                
                if response == 'y':
                    # 답안 업데이트
                    cur.execute("""
                        UPDATE math_service.problems 
                        SET correct_answer = %s 
                        WHERE id = %s
                    """, (extracted_answer, problem['id']))
                    
                    updated_count += 1
                    print("✅ 업데이트 완료")
                    
                elif response == 's':
                    print("⏭️ 건너뜀")
                    continue
                else:
                    print("❌ 업데이트 취소")
            else:
                print("❌ 답안을 추출할 수 없습니다.")
                
                # 수동 입력 옵션
                manual_answer = input("수동으로 답안을 입력하세요 (Enter=건너뜀): ").strip()
                if manual_answer:
                    cur.execute("""
                        UPDATE math_service.problems 
                        SET correct_answer = %s 
                        WHERE id = %s
                    """, (manual_answer, problem['id']))
                    
                    updated_count += 1
                    print("✅ 수동 업데이트 완료")
        
        # 커밋
        conn.commit()
        print(f"\n총 {updated_count}개 문제의 답안이 업데이트되었습니다.")
        
    except Exception as e:
        conn.rollback()
        print(f"오류 발생: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("비어있는 correct_answer 수정 스크립트")
    print("=" * 50)
    
    response = input("계속 진행하시겠습니까? (y/n): ").lower()
    if response != 'y':
        print("취소되었습니다.")
        sys.exit(0)
    
    fix_empty_answers()