"""Local Vision Model Engine via Ollama."""
import io
import base64
import httpx
from PIL import Image
from config import settings
from .base_engine import BaseOCREngine, OCRResult


class VisionLocalEngine(BaseOCREngine):
    """Vision model via Ollama for complex documents."""
    
    def __init__(self, model_name: str = None):
        super().__init__("vision_local")
        self.model_name = model_name or settings.vision_model
        self.ollama_host = settings.ollama_host
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.ollama_host}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return any(self.model_name in m.get("name", "") for m in models)
        except Exception:
            pass
        return False
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    async def process(self, image: Image.Image) -> OCRResult:
        """Process image with Ollama vision model."""
        # Convert image to base64
        img_b64 = self._image_to_base64(image)
        
        # Craft prompt for OCR
        prompt = """Extract all text from this image. Preserve the layout and structure as much as possible.
If you see tables, format them as markdown tables.
If you see lists, use proper list formatting.
Output ONLY the extracted text, no commentary."""
        
        # Call Ollama API
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 4096
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_host}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        text = data.get("response", "").strip()
        
        # Estimate confidence based on response quality
        confidence = 0.85 if text else 0.0
        if len(text) > 50:
            confidence = 0.9
        
        return OCRResult(
            text=text,
            confidence=confidence,
            engine_name=self.name,
            metadata={
                "model": self.model_name,
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "response_tokens": data.get("eval_count", 0)
            }
        )

