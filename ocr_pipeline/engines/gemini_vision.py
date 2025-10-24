"""
Gemini Vision Engine - Uses Google's Gemini 2.5 Pro for multimodal vision tasks.
"""
import base64
import io
from typing import Optional
from PIL import Image
import google.generativeai as genai
from config import settings
from .base_engine import BaseOCREngine, OCRResult


class GeminiVisionEngine(BaseOCREngine):
    """
    Vision engine using Google Gemini 2.5 Pro.
    
    Gemini 2.5 Pro is a state-of-the-art multimodal model excellent for:
    - Document analysis and classification
    - Vision-guided OCR correction
    - Complex layout understanding
    - Table extraction and formatting
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize Gemini API.
        
        Args:
            model_name: Gemini model to use. Options:
                - "gemini-2.0-flash-exp" (default, fastest, free in preview)
                - "gemini-1.5-flash" (fast, cheap: ~$0.01/1K images)
                - "gemini-1.5-pro" (best quality, expensive: ~$0.10/1K images)
        """
        model_name = model_name or settings.gemini_model or "gemini-2.0-flash-exp"
        super().__init__(name=model_name)
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.max_image_size = (2048, 2048)  # Gemini can handle larger images
    
    def is_available(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key-here")
    
    def _prepare_image(self, image: Image.Image) -> Image.Image:
        """Prepare image for Gemini (resize if needed)."""
        # Gemini can handle larger images than Ollama
        if max(image.size) > self.max_image_size[0]:
            image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
        return image
    
    async def process(self, image: Image.Image) -> OCRResult:
        """
        Process image with Gemini for OCR.
        
        Note: This is typically slower than Tesseract/Surya for pure OCR,
        but better for understanding complex layouts and tables.
        """
        prepared_image = self._prepare_image(image)
        
        prompt = """Extract all text from this image accurately. 
Preserve the layout, structure, and formatting as much as possible.
If there are tables, format them clearly.
Return only the extracted text, no commentary."""
        
        response = self.model.generate_content([prompt, prepared_image])
        
        return OCRResult(
            text=response.text,
            confidence=0.95,  # Gemini is very reliable
            engine_name="gemini-2.0-flash-exp",
            metadata={"model": "gemini-2.0-flash-exp"}
        )
    
    async def analyze_document(self, image: Image.Image, prompt: str) -> str:
        """
        Use Gemini for document analysis with custom prompt.
        
        Perfect for Pass 1 (classification) and Pass 3 (correction).
        """
        prepared_image = self._prepare_image(image)
        response = self.model.generate_content([prompt, prepared_image])
        return response.text

