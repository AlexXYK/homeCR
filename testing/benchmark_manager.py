"""Manage test datasets and ground truth data."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image


class BenchmarkDataset:
    """Represents a single benchmark dataset."""
    
    def __init__(self, name: str, root_path: Path):
        self.name = name
        self.root_path = root_path
        self.images_path = root_path / "images"
        self.ground_truth_path = root_path / "ground_truth"
        
        # Create directories if they don't exist
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.ground_truth_path.mkdir(parents=True, exist_ok=True)
    
    def get_samples(self) -> List[Dict]:
        """Get all samples in this dataset."""
        samples = []
        
        for img_file in self.images_path.glob("*.*"):
            if img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                continue
            
            # Look for corresponding ground truth
            gt_file = self.ground_truth_path / f"{img_file.stem}.txt"
            
            sample = {
                "id": img_file.stem,
                "image_path": str(img_file),
                "ground_truth_path": str(gt_file) if gt_file.exists() else None,
                "dataset": self.name
            }
            samples.append(sample)
        
        return samples
    
    def add_sample(self, image: Image.Image, ground_truth: str, sample_id: str) -> None:
        """Add a new sample to the dataset."""
        # Save image
        img_path = self.images_path / f"{sample_id}.png"
        image.save(img_path)
        
        # Save ground truth
        gt_path = self.ground_truth_path / f"{sample_id}.txt"
        gt_path.write_text(ground_truth, encoding='utf-8')


class BenchmarkManager:
    """Manages all benchmark datasets."""
    
    def __init__(self, base_path: str = "data/test_datasets"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize standard datasets
        self.datasets = {
            "handwriting": BenchmarkDataset("handwriting", self.base_path / "handwriting"),
            "print": BenchmarkDataset("print", self.base_path / "print"),
            "tables": BenchmarkDataset("tables", self.base_path / "tables"),
            "mixed": BenchmarkDataset("mixed", self.base_path / "mixed"),
            "screenshots": BenchmarkDataset("screenshots", self.base_path / "screenshots"),
            "edge_cases": BenchmarkDataset("edge_cases", self.base_path / "edge_cases"),
        }
    
    def get_dataset(self, name: str) -> Optional[BenchmarkDataset]:
        """Get a specific dataset by name."""
        return self.datasets.get(name)
    
    def get_all_samples(self, dataset_names: Optional[List[str]] = None) -> List[Dict]:
        """
        Get samples from specified datasets (or all if not specified).
        
        Args:
            dataset_names: List of dataset names to include, or None for all
            
        Returns:
            List of sample dictionaries
        """
        samples = []
        
        if dataset_names is None:
            dataset_names = list(self.datasets.keys())
        
        for name in dataset_names:
            if name in self.datasets:
                samples.extend(self.datasets[name].get_samples())
        
        return samples
    
    def add_sample_to_dataset(
        self,
        dataset_name: str,
        image: Image.Image,
        ground_truth: str,
        sample_id: Optional[str] = None
    ) -> None:
        """Add a sample to a specific dataset."""
        if dataset_name not in self.datasets:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        if sample_id is None:
            # Generate unique ID
            import time
            sample_id = f"sample_{int(time.time() * 1000)}"
        
        self.datasets[dataset_name].add_sample(image, ground_truth, sample_id)
    
    def get_statistics(self) -> Dict:
        """Get statistics about all datasets."""
        stats = {}
        
        for name, dataset in self.datasets.items():
            samples = dataset.get_samples()
            with_gt = sum(1 for s in samples if s['ground_truth_path'])
            stats[name] = {
                "total_samples": len(samples),
                "with_ground_truth": with_gt,
                "without_ground_truth": len(samples) - with_gt
            }
        
        return stats

