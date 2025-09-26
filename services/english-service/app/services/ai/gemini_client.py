from typing import Optional
from app.core.config import get_settings

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiClient:
    """Gemini AI 클라이언트 클래스"""

    def __init__(self):
        self.settings = get_settings()
        self.model = None

        if not GEMINI_AVAILABLE:
            print("Warning: Google Generative AI library not found. AI features will be disabled.")
            return

        if not self.settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")

        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel(self.settings.gemini_flash_model)

    def is_available(self) -> bool:
        """Gemini 서비스가 사용 가능한지 확인"""
        return GEMINI_AVAILABLE and self.model is not None

    async def generate_content(self, prompt: str) -> Optional[str]:
        """Gemini AI로 콘텐츠 생성"""
        if not self.is_available():
            return None

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API 호출 실패: {e}")
            return None