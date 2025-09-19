import io
import base64
import google.generativeai as genai
from PIL import Image
from typing import Optional

class OCRService:
    def __init__(self):
        # Gemini 모델은 이미 ai_service에서 설정됨
        pass

    def extract_text_from_image(self, image_data: bytes) -> str:
        """이미지에서 텍스트 추출"""
        try:
            # 이미지 로드
            image = Image.open(io.BytesIO(image_data))

            # Gemini Vision API를 사용한 OCR
            model = genai.GenerativeModel('gemini-2.5-pro')

            prompt = """
이 이미지에서 한글 텍스트를 추출해주세요.
손글씨나 인쇄된 글자를 모두 인식하여 정확히 텍스트로 변환해주세요.
텍스트만 반환하고 다른 설명은 포함하지 마세요.
"""

            response = model.generate_content([prompt, image])
            return response.text.strip()

        except Exception as e:
            print(f"OCR 처리 오류: {e}")
            return "텍스트 인식에 실패했습니다."