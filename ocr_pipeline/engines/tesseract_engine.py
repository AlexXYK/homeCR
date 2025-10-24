"""Tesseract OCR Engine - optimized for printed text."""
import io
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageOps
from .base_engine import BaseOCREngine, OCRResult


class TesseractEngine(BaseOCREngine):
    """Tesseract engine with advanced preprocessing."""
    
    def __init__(self):
        super().__init__("tesseract")
    
    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def _preprocess(self, img: Image.Image) -> Image.Image:
        """Apply OpenCV preprocessing for better OCR."""
        img = ImageOps.exif_transpose(img)
        w, h = img.size
        long_side = max(w, h)
        if long_side > 2200:
            scale = 2200 / long_side
            img = img.resize((int(w * scale), int(h * scale)))
        
        arr = np.array(img)
        gray = arr if arr.ndim == 2 else cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        gray = cv2.bilateralFilter(gray, d=7, sigmaColor=40, sigmaSpace=40)
        
        std = float(gray.std())
        if std >= 32.0:
            _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            th = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 35, 15
            )
        
        th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        return Image.fromarray(th)
    
    def _get_text(self, img: Image.Image, psm: str) -> str:
        """Extract text with specific PSM mode."""
        cfg = f"--oem 1 --psm {psm} -l eng --dpi 300 -c preserve_interword_spaces=1"
        return pytesseract.image_to_string(img, config=cfg)
    
    def _get_confidence(self, img: Image.Image, psm: str) -> float:
        """Get average confidence score."""
        cfg = f"--oem 1 --psm {psm} -l eng --dpi 300"
        data = pytesseract.image_to_data(
            img, config=cfg, output_type=pytesseract.Output.DICT
        )
        confs = [int(c) for c in data.get("conf", []) if c not in ("-1", -1)]
        return float(sum(confs) / len(confs)) if confs else 0.0
    
    async def process(self, image: Image.Image) -> OCRResult:
        """Process image with Tesseract."""
        # Preprocess
        processed = self._preprocess(image)
        
        # Try multiple PSM modes and pick best
        best_text, best_conf = "", 0.0
        for psm in ("6", "4", "11"):
            text = self._get_text(processed, psm=psm).strip()
            conf = self._get_confidence(processed, psm=psm)
            if conf > best_conf and text:
                best_text, best_conf = text, conf
        
        return OCRResult(
            text=best_text,
            confidence=best_conf / 100.0,  # Normalize to 0-1
            engine_name=self.name,
            metadata={"psm_modes_tested": ["6", "4", "11"]}
        )

