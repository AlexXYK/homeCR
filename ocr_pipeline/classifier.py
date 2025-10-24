"""Document type classifier for intelligent routing."""
import io
import base64
import httpx
from enum import Enum
from PIL import Image
import numpy as np
from config import settings


class DocumentType(Enum):
    """Document type classifications."""
    PRINTED_TEXT = "printed_text"
    HANDWRITING = "handwriting"
    MIXED = "mixed"
    SCREENSHOT = "screenshot"
    TABLE_HEAVY = "table_heavy"
    LOW_QUALITY = "low_quality"


class DocumentClassifier:
    """Classifies document type for optimal OCR routing."""
    
    def __init__(self):
        self.ollama_host = settings.ollama_host
        self.vision_model = settings.ollama_vision_model
    
    async def classify(self, image: Image.Image) -> DocumentType:
        """
        Classify the document type.
        
        For now, uses vision model for classification.
        TODO: Add lightweight CNN classifier for faster classification.
        """
        # Quick heuristic checks first
        if self._is_low_quality(image):
            return DocumentType.LOW_QUALITY
        
        # Use vision model for classification
        doc_type = await self._classify_with_vision(image)
        return doc_type
    
    def _is_low_quality(self, image: Image.Image) -> bool:
        """Quick check for low quality images."""
        # Check if image is very small
        if image.width < 100 or image.height < 100:
            return True
        
        # Check if image is very blurry (using variance of Laplacian)
        arr = np.array(image.convert('L'))
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        variance = np.var(np.abs(np.convolve(arr.flatten(), laplacian.flatten(), mode='same')))
        
        if variance < 100:  # Arbitrary threshold for blur
            return True
        
        return False
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64."""
        buffered = io.BytesIO()
        # Resize for faster classification
        img_small = image.copy()
        img_small.thumbnail((800, 800))
        img_small.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    async def _classify_with_vision(self, image: Image.Image) -> DocumentType:
        """Use vision model to classify document type."""
        img_b64 = self._image_to_base64(image)
        
        prompt = """Analyze this document image and classify it into ONE of these categories:
1. printed_text - Clean, machine-printed text (books, documents, PDFs)
2. handwriting - Handwritten notes or text
3. mixed - Contains both printed text and handwriting
4. screenshot - Screenshot of digital content (websites, apps)
5. table_heavy - Document with significant tables or structured data

Respond with ONLY the category name, nothing else."""
        
        payload = {
            "model": self.vision_model,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 2048
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            result = data.get("response", "").strip().lower()
            
            # Parse result
            if "printed" in result or "print" in result:
                return DocumentType.PRINTED_TEXT
            elif "handwrit" in result:
                return DocumentType.HANDWRITING
            elif "mixed" in result:
                return DocumentType.MIXED
            elif "screenshot" in result or "screen" in result:
                return DocumentType.SCREENSHOT
            elif "table" in result:
                return DocumentType.TABLE_HEAVY
            else:
                # Default to printed text
                return DocumentType.PRINTED_TEXT
                
        except Exception as e:
            print(f"Classification error: {e}, defaulting to PRINTED_TEXT")
            return DocumentType.PRINTED_TEXT

