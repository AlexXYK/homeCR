"""Surya OCR Engine - optimized for handwriting."""
from functools import lru_cache
from PIL import Image
from .base_engine import BaseOCREngine, OCRResult


class SuryaEngine(BaseOCREngine):
    """Surya engine for handwriting recognition."""
    
    def __init__(self):
        super().__init__("surya")
        self._foundation = None
        self._det = None
        self._rec = None
    
    @lru_cache(maxsize=1)
    def _get_foundation(self):
        """Lazy load foundation predictor."""
        from surya.foundation import FoundationPredictor
        return FoundationPredictor()
    
    @lru_cache(maxsize=1)
    def _get_det(self):
        """Lazy load detection predictor."""
        from surya.detection import DetectionPredictor
        return DetectionPredictor()
    
    @lru_cache(maxsize=1)
    def _get_rec(self):
        """Lazy load recognition predictor."""
        from surya.recognition import RecognitionPredictor
        return RecognitionPredictor(self._get_foundation())
    
    def is_available(self) -> bool:
        """Check if Surya is available."""
        try:
            import surya
            return True
        except ImportError:
            return False
    
    async def process(self, image: Image.Image) -> OCRResult:
        """Process image with Surya."""
        # Convert to RGB
        img_rgb = image.convert("RGB")
        
        # Get predictors
        rec = self._get_rec()
        det = self._get_det()
        
        # Run prediction
        preds = rec([img_rgb], det_predictor=det)[0]
        
        # Extract text lines
        lines = []
        if hasattr(preds, "text_lines"):
            for ln in getattr(preds, "text_lines", []):
                text = getattr(ln, "text", "") or ""
                if text:
                    lines.append(text)
        
        text = "\n".join(lines)
        
        # Surya doesn't provide confidence, use heuristic
        confidence = 0.8 if text.strip() else 0.0
        
        return OCRResult(
            text=text,
            confidence=confidence,
            engine_name=self.name,
            metadata={"lines_detected": len(lines)}
        )

