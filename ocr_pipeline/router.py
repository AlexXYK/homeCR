"""Intelligent OCR engine router based on document type and confidence."""
from typing import List, Optional
from PIL import Image
from .classifier import DocumentClassifier, DocumentType
from .engines.base_engine import BaseOCREngine, OCRResult
from .engines.tesseract_engine import TesseractEngine
from .engines.surya_engine import SuryaEngine
from .engines.vision_local import VisionLocalEngine
from config import settings


class OCRRouter:
    """Routes documents to the best OCR engine(s) based on classification."""
    
    def __init__(self):
        self.classifier = DocumentClassifier()
        
        # Initialize engines
        self.tesseract = TesseractEngine()
        self.surya = SuryaEngine()
        self.vision = VisionLocalEngine()
        
        # Check availability
        self.available_engines = {}
        if self.tesseract.is_available():
            self.available_engines['tesseract'] = self.tesseract
        if self.surya.is_available():
            self.available_engines['surya'] = self.surya
        if self.vision.is_available():
            self.available_engines['vision'] = self.vision
    
    def _select_engines(self, doc_type: DocumentType) -> List[BaseOCREngine]:
        """Select appropriate engines based on document type."""
        engines = []
        
        if doc_type == DocumentType.PRINTED_TEXT:
            # Tesseract is best for clean printed text
            if 'tesseract' in self.available_engines:
                engines.append(self.available_engines['tesseract'])
            if 'vision' in self.available_engines:
                engines.append(self.available_engines['vision'])
        
        elif doc_type == DocumentType.HANDWRITING:
            # Surya and vision models for handwriting
            if 'surya' in self.available_engines:
                engines.append(self.available_engines['surya'])
            if 'vision' in self.available_engines:
                engines.append(self.available_engines['vision'])
        
        elif doc_type == DocumentType.MIXED:
            # Use all available engines
            if 'vision' in self.available_engines:
                engines.append(self.available_engines['vision'])
            if 'surya' in self.available_engines:
                engines.append(self.available_engines['surya'])
            if 'tesseract' in self.available_engines:
                engines.append(self.available_engines['tesseract'])
        
        elif doc_type == DocumentType.SCREENSHOT:
            # Vision models and Tesseract
            if 'vision' in self.available_engines:
                engines.append(self.available_engines['vision'])
            if 'tesseract' in self.available_engines:
                engines.append(self.available_engines['tesseract'])
        
        elif doc_type == DocumentType.TABLE_HEAVY:
            # Vision models are best for tables
            if 'vision' in self.available_engines:
                engines.append(self.available_engines['vision'])
        
        elif doc_type == DocumentType.LOW_QUALITY:
            # Try all engines, pick best
            engines = list(self.available_engines.values())
        
        return engines
    
    async def route_and_process(
        self,
        image: Image.Image,
        force_engine: Optional[str] = None
    ) -> OCRResult:
        """
        Route document to appropriate engine(s) and return best result.
        
        Args:
            image: PIL Image to process
            force_engine: Optional engine name to force use of specific engine
            
        Returns:
            Best OCRResult from selected engines
        """
        # If forcing specific engine
        if force_engine:
            if force_engine in self.available_engines:
                return await self.available_engines[force_engine].process(image)
            else:
                raise ValueError(f"Engine '{force_engine}' not available")
        
        # Classify document type
        doc_type = await self.classifier.classify(image)
        
        # Select appropriate engines
        engines = self._select_engines(doc_type)
        
        if not engines:
            raise RuntimeError("No OCR engines available")
        
        # Process with selected engines
        results = []
        for engine in engines[:2]:  # Limit to 2 engines to save resources
            try:
                result = await engine.process(image)
                results.append(result)
            except Exception as e:
                print(f"Error with {engine.name}: {e}")
                continue
        
        if not results:
            raise RuntimeError("All OCR engines failed")
        
        # Return result with highest confidence
        best_result = max(results, key=lambda r: r.confidence)
        best_result.metadata["document_type"] = doc_type.value
        best_result.metadata["engines_tried"] = [r.engine_name for r in results]
        
        return best_result

