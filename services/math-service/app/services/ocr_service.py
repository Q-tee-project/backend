"""
OCR 서비스 로직 분리 - 수학 필기체 답안 인식 최적화
"""
import os
import requests
import base64
from typing import Dict, Optional
import io
import re

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    

try:
    import numpy as np
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    


class OCRService:
    """OCR 전용 클래스 - 수학 필기체 답안 인식에 특화"""

    def __init__(self):
        self.vision_api_key = os.getenv("GOOGLE_VISION_API_KEY")
        if not self.vision_api_key:
            raise ValueError("GOOGLE_VISION_API_KEY environment variable is required")

        # 디버그 모드 설정
        self.debug_mode = os.getenv("OCR_DEBUG_MODE", "false").lower() == "true"
        self.debug_dir = os.getenv("OCR_DEBUG_DIR", "/tmp")

    def _log(self, message: str):
        """디버그 로그 출력"""
        if self.debug_mode:
            print(f"🔍 OCR: {message}")

    def extract_text_from_image(self, image_data: bytes) -> str:
        """
        Google Vision을 이용한 필기체 OCR

        Args:
            image_data: 이미지 바이너리 데이터 (PNG, JPG 등)

        Returns:
            인식된 텍스트 (수학 답안 형식)
        """
        try:
            self._log(f"image_data 타입: {type(image_data)}, 크기: {len(image_data) if image_data else 0} bytes")

            if not image_data or len(image_data) < 50:
                self._log(f"이미지 데이터가 비어있거나 너무 작음")
                return ""

            # 디버그 모드: 원본 이미지 저장
            if self.debug_mode:
                self._save_debug_image(image_data, "original")

            # 이미지 전처리
            processed_data = self._preprocess_image(image_data)
            if processed_data:
                image_data = processed_data
                if self.debug_mode:
                    self._save_debug_image(image_data, "processed")

            # Google Vision API 호출
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            result = self._call_vision_api(image_base64)

            if result:
                self._log(f"원본 인식 텍스트: {result[:100]}")
                cleaned_text = self._clean_math_text(result)
                self._log(f"후처리된 텍스트: {cleaned_text[:100]}")
                return cleaned_text

            return ""

        except Exception as e:
            print(f"❌ OCR 처리 오류: {str(e)}")
            if self.debug_mode:
                import traceback
                print(traceback.format_exc())
            return ""

    def _save_debug_image(self, image_data: bytes, suffix: str):
        """디버그용 이미지 저장"""
        try:
            import time
            timestamp = int(time.time() * 1000)
            debug_path = f"{self.debug_dir}/ocr_{suffix}_{timestamp}.png"
            with open(debug_path, 'wb') as f:
                f.write(image_data)
            self._log(f"디버그 이미지 저장: {debug_path}")
        except Exception as e:
            self._log(f"디버그 이미지 저장 실패: {e}")

    def _call_vision_api(self, image_base64: str) -> Optional[str]:
        """
        Google Vision API REST 호출
        - DOCUMENT_TEXT_DETECTION: 필기체 인식에 최적화
        - 언어 힌트 제거: 숫자와 수학 기호 인식 개선
        """
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
                            }
                        ]
                        # 언어 힌트 제거 - 숫자와 수학 기호는 언어 독립적
                    }
                ]
            }

            self._log("Google Vision API 호출 시작")
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
            self._log(f"응답 상태코드: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ Vision API 오류: {response.status_code} - {response.text}")
                return None

            result = response.json()

            if 'responses' in result and result['responses']:
                response_data = result['responses'][0]

                # DOCUMENT_TEXT_DETECTION 결과 확인
                if 'fullTextAnnotation' in response_data:
                    text = response_data['fullTextAnnotation'].get('text', '').strip()
                    if text:
                        return text

                # TEXT_DETECTION fallback
                if 'textAnnotations' in response_data and response_data['textAnnotations']:
                    text = response_data['textAnnotations'][0]['description'].strip()
                    if text:
                        return text

                self._log("텍스트 인식 결과 없음")

            return None

        except requests.RequestException as e:
            print(f"❌ Vision API 요청 오류: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Vision API 처리 오류: {str(e)}")
            return None

    def _preprocess_image(self, image_data: bytes) -> Optional[bytes]:
        """
        필기체 수학 답안 인식을 위한 이미지 전처리
        - OpenCV 우선 사용 (더 강력한 전처리)
        - PIL fallback
        """
        if CV2_AVAILABLE:
            return self._preprocess_with_cv2(image_data)
        elif PIL_AVAILABLE:
            return self._preprocess_with_pil(image_data)
        else:
            self._log("전처리 라이브러리 없음 - 원본 사용")
            return None

    def _preprocess_with_cv2(self, image_data: bytes) -> Optional[bytes]:
        """
        OpenCV 최소 전처리 - "API를 먼저 믿는 전략"
        실패 사례가 수집되면 추가 처리를 활성화
        """
        try:
            # bytes -> numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                self._log("OpenCV 이미지 디코딩 실패")
                return None

            self._log(f"원본 크기: {img.shape}")

            # 1. 그레이스케일 변환
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 2. 크기 조정 (작은 이미지는 확대)
            h, w = gray.shape
            min_size = 1000
            if h < min_size or w < min_size:
                scale = max(min_size / h, min_size / w, 2.0)  # 3.0 → 2.0으로 축소
                new_h, new_w = int(h * scale), int(w * scale)
                gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                self._log(f"크기 확대: {w}x{h} → {new_w}x{new_h} (x{scale:.1f})")

            # 3. 대비 향상 (CLAHE) - 어두운 이미지 대응
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # numpy array -> bytes (PNG)
            success, buffer = cv2.imencode('.png', enhanced, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            if not success:
                self._log("OpenCV 인코딩 실패")
                return None

            processed_data = buffer.tobytes()
            self._log(f"OpenCV 전처리 완료: {len(image_data)} → {len(processed_data)} bytes")
            return processed_data

            # ========================================
            # 🔪 필요시 활성화할 추가 처리 (현재 비활성화)
            # ========================================
            # # 노이즈 제거
            # denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            #
            # # 선명화
            # kernel = np.array([[-1, -1, -1],
            #                    [-1,  9, -1],
            #                    [-1, -1, -1]])
            # sharpened = cv2.filter2D(enhanced, -1, kernel)
            #
            # # Adaptive Thresholding (필기체 강조)
            # binary = cv2.adaptiveThreshold(
            #     sharpened,
            #     255,
            #     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            #     cv2.THRESH_BINARY,
            #     11,
            #     2
            # )
            #
            # # 모폴로지 연산 (필기 선 연결)
            # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            # morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        except Exception as e:
            self._log(f"OpenCV 전처리 실패: {e}")
            return None

    def _preprocess_with_pil(self, image_data: bytes) -> Optional[bytes]:
        """
        PIL 최소 전처리 (fallback) - "API를 먼저 믿는 전략"
        실패 사례가 수집되면 추가 처리를 활성화
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            self._log(f"원본 크기: {image.size}, 모드: {image.mode}")

            # RGB 변환
            if image.mode == 'RGBA':
                white_bg = Image.new('RGB', image.size, (255, 255, 255))
                white_bg.paste(image, mask=image.split()[-1])
                image = white_bg
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # 크기 조정
            w, h = image.size
            min_size = 1000
            if w < min_size or h < min_size:
                scale = max(min_size / w, min_size / h, 2.0)  # 3.0 → 2.0으로 축소
                new_w, new_h = int(w * scale), int(h * scale)
                image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self._log(f"크기 확대: {w}x{h} → {new_w}x{new_h}")

            # 대비 향상
            image = ImageEnhance.Contrast(image).enhance(1.5)  # 2.0 → 1.5로 축소

            # PNG로 저장
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', quality=100)
            processed_data = buffer.getvalue()

            self._log(f"PIL 전처리 완료: {len(image_data)} → {len(processed_data)} bytes")
            return processed_data

            # ========================================
            # 🔪 필요시 활성화할 추가 처리 (현재 비활성화)
            # ========================================
            # # 선명도 향상
            # image = ImageEnhance.Sharpness(image).enhance(2.0)
            #
            # # 밝기 조정
            # image = ImageEnhance.Brightness(image).enhance(1.1)

        except Exception as e:
            self._log(f"PIL 전처리 실패: {e}")
            return None

    def _clean_math_text(self, text: str) -> str:
        """
        수학 답안 텍스트 최소 정리 - "API를 먼저 믿는 전략"
        실패 사례가 수집되면 추가 처리를 활성화
        """
        if not text or not text.strip():
            return ""

        cleaned = text.strip()
        original = cleaned

        # 1. 비ASCII 문자 제거 (수학 답안은 ASCII만 필요)
        cleaned = re.sub(r'[^\x00-\x7F]', '', cleaned)

        # 2. OCR 오류 수정 (명백한 오인식만)
        cleaned = self._fix_ocr_errors(cleaned)

        # 3. 공백 정리
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        if cleaned != original:
            self._log(f"텍스트 정리: '{original}' → '{cleaned}'")

        return cleaned

        # ========================================
        # 🔪 필요시 활성화할 추가 처리 (현재 비활성화)
        # ========================================
        # # 분수 패턴 감지
        # fraction = self._detect_fraction(cleaned)
        # if fraction:
        #     self._log(f"분수 인식: '{original}' → '{fraction}'")
        #     return fraction

    def _detect_fraction(self, text: str) -> Optional[str]:
        """
        분수 패턴 감지 (현재 비활성화)
        필요시 _clean_math_text에서 활성화
        """
        # 패턴 1: "17\n4" (세로 분수)
        match = re.search(r'^(\d+)\s*[\n\r]+\s*(\d+)$', text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"

        # 패턴 2: "17/4" (슬래시 분수)
        match = re.search(r'^(\d+)\s*/\s*(\d+)$', text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"

        # 패턴 3: "17 4" (공백으로 분리된 두 숫자)
        match = re.search(r'^(\d+)\s+(\d+)$', text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"

        # 패턴 4: 문자와 숫자 혼합 (예: "E17" → "1/7")
        if re.search(r'[A-Za-z]', text):
            numbers = re.findall(r'\d+', text)
            if len(numbers) == 2:
                return f"{numbers[0]}/{numbers[1]}"
            elif len(numbers) == 1 and len(numbers[0]) == 2:
                # "17" in "E17" → "1/7"
                return f"{numbers[0][0]}/{numbers[0][1]}"

        return None

    def _fix_ocr_errors(self, text: str) -> str:
        """
        컨텍스트 기반 OCR 오인식 수정
        - 완전 매칭이 아닌 패턴 기반
        """
        # 숫자만 있는 경우는 수정하지 않음
        if re.match(r'^[\d\s\-+*/().=]+$', text):
            return text

        # 문자가 섞인 경우에만 수정
        replacements = {
            r'\bl\b': '1',      # 단어 경계의 소문자 l
            r'\bI\b': '1',      # 단어 경계의 대문자 I
            r'\bO\b': '0',      # 단어 경계의 대문자 O
            r'\bS\b': '5',      # 단어 경계의 S
            r'§': '5',          # 특수 문자
        }

        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        return text

    def extract_answer_from_text(self, ocr_text: str, problem_id: int, problem_number: int) -> str:
        """
        OCR 텍스트에서 특정 문제의 답안 추출 (현재 단순화)

        "API를 먼저 믿는 전략": 사용자가 한 문제씩 제출하는 것을 가정
        여러 문제를 한 번에 제출하는 경우가 생기면 로직 활성화

        Args:
            ocr_text: 전체 OCR 텍스트
            problem_id: 문제 ID (현재 미사용)
            problem_number: 문제 번호 (현재 미사용)

        Returns:
            추출된 답안 (현재는 전체 텍스트 반환)
        """
        if not ocr_text:
            return ""

        # 단순화: 전체 텍스트를 답안으로 반환
        return ocr_text.strip()

        # ========================================
        # 🔪 필요시 활성화할 추가 처리 (현재 비활성화)
        # ========================================
        # lines = ocr_text.split('\n')
        #
        # # 문제 번호로 답안 찾기
        # for i, line in enumerate(lines):
        #     # "1.", "1)", "1:" 등의 패턴
        #     pattern = rf'\b{problem_number}[\.\):]\s*(.+)'
        #     match = re.search(pattern, line)
        #     if match:
        #         answer = match.group(1).strip()
        #         self._log(f"문제 {problem_number} 답안 추출: {answer}")
        #         return answer
        #
        # # 패턴을 못 찾으면 전체 텍스트 반환
        # return ocr_text.strip()
