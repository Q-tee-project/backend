"""
Custom exceptions for the Math Service.
"""

class MathServiceError(Exception):
    """Base exception class for the math service."""
    pass

class GenerationError(MathServiceError):
    """Exception raised for errors during problem generation."""
    pass

class AIResponseError(GenerationError):
    """Exception raised for malformed responses from the AI service."""
    pass

class GradingError(MathServiceError):
    """Exception raised for errors during grading."""
    pass

class OCRError(GradingError):
    """Exception raised for errors during OCR processing."""
    pass
