"""Base OCR Engine interface."""
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any
from PIL import Image


class OCRResult:
    """Standardized OCR result."""
    
    def __init__(
        self,
        text: str,
        confidence: float,
        engine_name: str,
        metadata: Dict[str, Any] = None
    ):
        self.text = text
        self.confidence = confidence
        self.engine_name = engine_name
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"OCRResult(engine={self.engine_name}, confidence={self.confidence:.2f}, chars={len(self.text)})"


class BaseOCREngine(ABC):
    """Abstract base class for OCR engines."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def process(self, image: Image.Image) -> OCRResult:
        """
        Process an image and return OCR result.
        
        Args:
            image: PIL Image to process
            
        Returns:
            OCRResult with text, confidence, and metadata
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available and ready to use."""
        pass

