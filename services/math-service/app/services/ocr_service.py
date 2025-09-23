"""
OCR 서비스 로직 분리
"""
import os
import requests
import base64
from typing import Dict, Optional
try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL/Pillow not available - image preprocessing disabled")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not available - advanced image processing disabled")

import io

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

            # 디버깅용: 이미지를 파일로 저장
            debug_path = f"/tmp/debug_ocr_{len(image_data)}.png"
            try:
                with open(debug_path, 'wb') as f:
                    f.write(image_data)
                print(f"🔍 OCR 디버그: 이미지 저장됨 - {debug_path}")
            except Exception as save_error:
                print(f"🔍 OCR 디버그: 이미지 저장 실패 - {save_error}")

            # 이미지 크기가 너무 작으면 스킵
            if len(image_data) < 50:  # 50 bytes 미만으로 크게 낮춤
                print(f"🔍 OCR 디버그: 이미지가 너무 작음 ({len(image_data)} bytes)")
                return ""

            # 이미지 전처리 시도 (PIL 사용 가능한 경우만)
            if PIL_AVAILABLE:
                try:
                    processed_image_data = self._preprocess_image(image_data)
                    if processed_image_data and len(processed_image_data) > len(image_data):
                        print(f"🔍 OCR 디버그: 이미지 전처리 완료 ({len(image_data)} → {len(processed_image_data)} bytes)")
                        image_data = processed_image_data
                except Exception as preprocess_error:
                    print(f"🔍 OCR 디버그: 이미지 전처리 실패 - {preprocess_error}")
                    # 원본 이미지 사용
            else:
                print(f"🔍 OCR 디버그: PIL 미설치로 이미지 전처리 건너뜀")
            
            # 이미지 데이터를 base64로 인코딩
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Google Vision API 호출
            result = self._call_vision_api(image_base64)
            
            if result:
                detected_text = result.strip()
                print(f"🔍 OCR 디버그: 원본 인식 텍스트: {detected_text[:50]}...")

                # 수학 답안 후처리: 비라틴 문자 제거
                cleaned_text = self._clean_math_text(detected_text)
                print(f"🔍 OCR 디버그: 후처리된 텍스트: {cleaned_text[:50]}...")

                return cleaned_text if cleaned_text else detected_text
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
                                "type": "DOCUMENT_TEXT_DETECTION",
                                "maxResults": 10
                            },
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 10
                            }
                        ],
                        "imageContext": {
                            "languageHints": ["en", "en-US"]  # 영어 우선 인식
                        }
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

                    # DOCUMENT_TEXT_DETECTION 결과 먼저 확인
                    if 'fullTextAnnotation' in response_data and response_data['fullTextAnnotation']:
                        text = response_data['fullTextAnnotation'].get('text', '').strip()
                        if text:
                            print(f"🔍 OCR 디버그: DOCUMENT_TEXT_DETECTION 성공: {text[:50]}...")
                            return text

                    # TEXT_DETECTION 결과 확인
                    if 'textAnnotations' in response_data and response_data['textAnnotations']:
                        text = response_data['textAnnotations'][0]['description'].strip()
                        if text:
                            print(f"🔍 OCR 디버그: TEXT_DETECTION 성공: {text[:50]}...")
                            return text

                    print("🔍 OCR 디버그: 모든 텍스트 인식 결과가 비어있음")
                    print(f"🔍 OCR 디버그: 전체 응답: {result}")
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

    def _preprocess_image(self, image_data: bytes) -> Optional[bytes]:
        """이미지 전처리로 OCR 인식률 향상"""
        if not PIL_AVAILABLE:
            return None

        try:
            # PIL Image로 변환
            image = Image.open(io.BytesIO(image_data))
            original_size = image.size
            print(f"🔍 OCR 디버그: 원본 이미지 크기: {original_size}")

            # RGBA를 RGB로 변환 (배경을 흰색으로)
            if image.mode == 'RGBA':
                # 흰색 배경 생성
                white_bg = Image.new('RGB', image.size, (255, 255, 255))
                white_bg.paste(image, mask=image.split()[-1])  # alpha 채널을 마스크로 사용
                image = white_bg
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # 작은 이미지의 경우 더 적극적으로 확대
            width, height = image.size
            min_size = 800  # 최소 크기를 800픽셀로 설정

            if width < min_size or height < min_size:
                # 더 큰 배율로 확대
                scale_factor = max(min_size/width, min_size/height, 4.0)  # 최소 4배 확대
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)

                # 고품질 리샘플링 사용
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"🔍 OCR 디버그: 이미지 크기 확대 {width}x{height} → {new_width}x{new_height} (배율: {scale_factor:.1f})")

            # 더 간단하고 안전한 처리 방식으로 변경
            # 직접 대비와 선명도만 조정

            # 더 강한 대비 향상
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)  # 1.5에서 2.0으로 증가

            # 더 강한 선명도 향상
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)  # 1.2에서 2.0으로 증가

            # 밝기 조정 (필기가 더 명확하게 보이도록)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)

            # 최종 이미지를 고품질로 저장
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', quality=100, optimize=False)
            processed_data = buffer.getvalue()

            # 전처리된 이미지도 디버그용으로 저장
            debug_processed_path = f"/tmp/debug_processed_{len(processed_data)}.png"
            try:
                with open(debug_processed_path, 'wb') as f:
                    f.write(processed_data)
                print(f"🔍 OCR 디버그: 전처리된 이미지 저장됨 - {debug_processed_path}")
            except Exception as save_error:
                print(f"🔍 OCR 디버그: 전처리된 이미지 저장 실패 - {save_error}")

            print(f"🔍 OCR 디버그: 이미지 전처리 완료 ({len(image_data)} → {len(processed_data)} bytes)")
            return processed_data

        except Exception as e:
            print(f"🔍 OCR 디버그: 이미지 전처리 중 오류 - {str(e)}")
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

    def _clean_math_text(self, text: str) -> str:
        """수학 답안용 텍스트 정리 - 비라틴 문자 제거 및 기본 정리"""
        import re

        if not text or not text.strip():
            return ""

        cleaned = text.strip()

        # 1. 비라틴 문자 제거 (한글, 일본어, 중국어 등)
        # 수학 답안은 영어, 숫자, 기본 기호만 있어야 함
        cleaned = re.sub(r'[^\x00-\x7F]', '', cleaned)

        # 2. "메ーン 5" 같은 패턴에서 숫자만 추출
        if re.search(r'\d+', cleaned):
            # 숫자가 포함된 경우, 의미있는 패턴 찾기
            # 공백으로 분리된 마지막 숫자를 분모로 가정
            parts = cleaned.split()
            numbers = [p for p in parts if re.match(r'^-?\d+\.?\d*$', p)]
            letters = [p for p in parts if re.match(r'^[a-zA-Z\-\+]+$', p)]

            if len(numbers) == 1 and len(letters) >= 1:
                # "x-y 5" 패턴으로 해석
                numerator = ''.join(letters).replace(' ', '')
                denominator = numbers[0]
                cleaned = f"{numerator}/{denominator}"
            elif len(numbers) == 1 and not letters:
                # 숫자만 남은 경우
                cleaned = numbers[0]

        # 3. 기본 정리
        cleaned = re.sub(r'\s+', ' ', cleaned)  # 연속 공백 제거
        cleaned = cleaned.strip()

        return cleaned