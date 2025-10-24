"""OCR evaluation metrics calculation."""
import Levenshtein
from typing import Dict


class OCRMetrics:
    """Calculate various OCR quality metrics."""
    
    @staticmethod
    def character_error_rate(ground_truth: str, predicted: str) -> float:
        """
        Calculate Character Error Rate (CER).
        
        CER = (insertions + deletions + substitutions) / length of ground truth
        """
        if not ground_truth:
            return 1.0 if predicted else 0.0
        
        distance = Levenshtein.distance(ground_truth, predicted)
        return distance / len(ground_truth)
    
    @staticmethod
    def word_error_rate(ground_truth: str, predicted: str) -> float:
        """
        Calculate Word Error Rate (WER).
        
        Similar to CER but at word level.
        """
        gt_words = ground_truth.split()
        pred_words = predicted.split()
        
        if not gt_words:
            return 1.0 if pred_words else 0.0
        
        distance = Levenshtein.distance(' '.join(gt_words), ' '.join(pred_words))
        return distance / len(gt_words)
    
    @staticmethod
    def accuracy(ground_truth: str, predicted: str) -> float:
        """
        Calculate accuracy (1 - CER).
        """
        return 1.0 - OCRMetrics.character_error_rate(ground_truth, predicted)
    
    @staticmethod
    def calculate_all(ground_truth: str, predicted: str) -> Dict[str, float]:
        """
        Calculate all metrics at once.
        
        Returns:
            Dictionary with CER, WER, and accuracy
        """
        cer = OCRMetrics.character_error_rate(ground_truth, predicted)
        wer = OCRMetrics.word_error_rate(ground_truth, predicted)
        
        return {
            "character_error_rate": cer,
            "word_error_rate": wer,
            "accuracy": 1.0 - cer,
            "character_count_gt": len(ground_truth),
            "character_count_pred": len(predicted),
            "word_count_gt": len(ground_truth.split()),
            "word_count_pred": len(predicted.split())
        }

