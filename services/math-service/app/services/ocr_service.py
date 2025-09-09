"""
OCR 서비스 로직 분리
"""
import os
import requests
import base64
from typing import Dict, Optional

class OCRService:
    """OCR 전용 클래스"""
    
    def __init__(self):
        self.vision_api_key = os.getenv("GOOGLE_VISION_API_KEY")
        if not self.vision_api_key:
            raise ValueError("GOOGLE_VISION_API_KEY environment variable is required")
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """Google Vision을 이용한 손글씨 OCR"""
        try:
            print(f"🔍 OCR 디버그: image_data 타입: {type(image_data)}")
            print(f"🔍 OCR 디버그: image_data 크기: {len(image_data) if image_data else 'None'}")
            
            if not image_data:
                print("🔍 OCR 디버그: image_data가 비어있음")
                return ""
            
            # 이미지 데이터를 base64로 인코딩
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Google Vision API 호출
            result = self._call_vision_api(image_base64)
            
            if result:
                detected_text = result.strip()
                print(f"🔍 OCR 디버그: 인식된 텍스트: {detected_text[:50]}...")
                return detected_text
            else:
                print("🔍 OCR 디버그: 텍스트 인식 실패")
                return ""
                
        except Exception as e:
            import traceback
            print(f"OCR 처리 오류: {str(e)}")
            print(f"OCR 오류 상세: {traceback.format_exc()}")
            return ""
    
    def _call_vision_api(self, image_base64: str) -> Optional[str]:
        """Google Vision API REST 호출"""
        try:
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.vision_api_key}"
            
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 1
                            }
                        ]
                    }
                ]
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            print(f"🔍 OCR 디버그: Google Vision API 호출 시작")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"🔍 OCR 디버그: 응답 상태코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"🔍 OCR 디버그: 응답 데이터: {str(result)[:200]}...")
                
                if 'responses' in result and result['responses']:
                    response_data = result['responses'][0]
                    if 'textAnnotations' in response_data and response_data['textAnnotations']:
                        return response_data['textAnnotations'][0]['description']
                    else:
                        print("🔍 OCR 디버그: textAnnotations가 비어있음")
                        return None
                else:
                    print("🔍 OCR 디버그: responses가 비어있음")
                    return None
            else:
                error_msg = response.text
                print(f"❌ OCR API 오류: {response.status_code} - {error_msg}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ OCR API 요청 오류: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ OCR API 처리 오류: {str(e)}")
            return None
    
    def extract_answer_from_text(self, ocr_text: str, problem_id: int, problem_number: int) -> str:
        """OCR 텍스트에서 특정 문제의 답안 추출"""
        # OCR 후처리: 일반적인 오인식 패턴 수정
        cleaned_text = self.clean_ocr_text(ocr_text)
        
        lines = cleaned_text.split('\n')
        
        # 문제 번호 패턴 찾기
        for i, line in enumerate(lines):
            if f"{problem_number}." in line or f"{problem_number})" in line:
                # 해당 줄에서 답안 부분 추출
                answer_part = line.split(f"{problem_number}.")[-1].split(f"{problem_number})")[-1]
                return answer_part.strip()
        
        # 패턴을 찾지 못한 경우 전체 텍스트 반환
        return cleaned_text.strip()
    
    def clean_ocr_text(self, text: str) -> str:
        """OCR 텍스트의 일반적인 오인식 패턴을 수정"""
        import re
        
        # 공통 오인식 패턴 수정
        replacements = {
            # 숫자 오인식 패턴
            r'\.\.+': '1',  # .. -> 1
            r'l': '1',      # l -> 1 (소문자 엘)
            r'I': '1',      # I -> 1 (대문자 아이)
            r'O': '0',      # O -> 0 (대문자 오)
            r'o': '0',      # o -> 0 (소문자 오)
            r'S': '5',      # S -> 5 
            r'§': '5',      # § -> 5
            r'Z': '2',      # Z -> 2
            r'g': '9',      # g -> 9
            r'b': '6',      # b -> 6
            # 연속된 공백을 하나로
            r'\s+': ' ',
            # 특수문자 정리
            r'[^\w\s,./\-+()=]': '',
        }
        
        cleaned = text
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        
        print(f"🔍 OCR 후처리: '{text[:30]}...' -> '{cleaned[:30]}...'")
        return cleaned.strip()