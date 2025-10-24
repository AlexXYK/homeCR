"""Test orchestration and execution."""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from PIL import Image
import aiosqlite

from .benchmark_manager import BenchmarkManager
from .metrics import OCRMetrics
from ocr_pipeline.router import OCRRouter


class TestResult:
    """Represents a single test result."""
    
    def __init__(
        self,
        sample_id: str,
        dataset: str,
        engine: str,
        predicted_text: str,
        ground_truth: Optional[str],
        metrics: Optional[Dict],
        processing_time: float,
        timestamp: datetime
    ):
        self.sample_id = sample_id
        self.dataset = dataset
        self.engine = engine
        self.predicted_text = predicted_text
        self.ground_truth = ground_truth
        self.metrics = metrics or {}
        self.processing_time = processing_time
        self.timestamp = timestamp


class TestOrchestrator:
    """Orchestrates automated testing of OCR system."""
    
    def __init__(self, db_path: str = "data/test_results.db"):
        self.db_path = db_path
        self.benchmark_manager = BenchmarkManager()
        self.ocr_router = OCRRouter()
        self.metrics_calculator = OCRMetrics()
    
    async def initialize_database(self):
        """Initialize the results database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_id TEXT NOT NULL,
                    dataset TEXT NOT NULL,
                    engine TEXT NOT NULL,
                    predicted_text TEXT,
                    ground_truth TEXT,
                    cer REAL,
                    wer REAL,
                    accuracy REAL,
                    processing_time REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_dataset_timestamp 
                ON test_results(dataset, timestamp)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_engine_timestamp 
                ON test_results(engine, timestamp)
            """)
            await db.commit()
    
    async def run_test_on_sample(
        self,
        sample: Dict,
        force_engine: Optional[str] = None
    ) -> TestResult:
        """Run OCR test on a single sample."""
        import time
        
        # Load image
        image = Image.open(sample['image_path'])
        
        # Load ground truth if available
        ground_truth = None
        if sample['ground_truth_path']:
            ground_truth = Path(sample['ground_truth_path']).read_text(encoding='utf-8')
        
        # Run OCR
        start_time = time.time()
        result = await self.ocr_router.route_and_process(image, force_engine=force_engine)
        processing_time = time.time() - start_time
        
        # Calculate metrics if we have ground truth
        metrics = None
        if ground_truth:
            metrics = self.metrics_calculator.calculate_all(ground_truth, result.text)
        
        return TestResult(
            sample_id=sample['id'],
            dataset=sample['dataset'],
            engine=result.engine_name,
            predicted_text=result.text,
            ground_truth=ground_truth,
            metrics=metrics,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
    
    async def save_result(self, result: TestResult):
        """Save test result to database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO test_results 
                (sample_id, dataset, engine, predicted_text, ground_truth, 
                 cer, wer, accuracy, processing_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.sample_id,
                result.dataset,
                result.engine,
                result.predicted_text,
                result.ground_truth,
                result.metrics.get('character_error_rate'),
                result.metrics.get('word_error_rate'),
                result.metrics.get('accuracy'),
                result.processing_time,
                result.timestamp
            ))
            await db.commit()
    
    async def run_benchmark(
        self,
        dataset_names: Optional[List[str]] = None,
        force_engine: Optional[str] = None,
        max_samples: Optional[int] = None
    ) -> List[TestResult]:
        """
        Run benchmark tests on specified datasets.
        
        Args:
            dataset_names: Datasets to test (all if None)
            force_engine: Force specific engine (auto-route if None)
            max_samples: Limit number of samples to test
            
        Returns:
            List of test results
        """
        # Initialize database
        await self.initialize_database()
        
        # Get samples
        samples = self.benchmark_manager.get_all_samples(dataset_names)
        
        if max_samples:
            samples = samples[:max_samples]
        
        if not samples:
            print("No samples found in test datasets")
            return []
        
        print(f"Running benchmark on {len(samples)} samples...")
        
        # Run tests
        results = []
        for i, sample in enumerate(samples, 1):
            try:
                print(f"Testing {i}/{len(samples)}: {sample['id']} ({sample['dataset']})")
                result = await self.run_test_on_sample(sample, force_engine)
                await self.save_result(result)
                results.append(result)
                
                # Print metrics if available
                if result.metrics:
                    print(f"  CER: {result.metrics['character_error_rate']:.3f}, "
                          f"Accuracy: {result.metrics['accuracy']:.3f}")
                
            except Exception as e:
                print(f"  Error: {e}")
                continue
        
        return results
    
    async def get_summary_stats(
        self,
        dataset: Optional[str] = None,
        engine: Optional[str] = None,
        limit_days: int = 30
    ) -> Dict:
        """
        Get summary statistics from test results.
        
        Args:
            dataset: Filter by dataset (all if None)
            engine: Filter by engine (all if None)
            limit_days: Only include results from last N days
            
        Returns:
            Dictionary with summary statistics
        """
        query = """
            SELECT 
                COUNT(*) as total_tests,
                AVG(cer) as avg_cer,
                AVG(wer) as avg_wer,
                AVG(accuracy) as avg_accuracy,
                AVG(processing_time) as avg_time,
                MIN(accuracy) as min_accuracy,
                MAX(accuracy) as max_accuracy
            FROM test_results
            WHERE timestamp > datetime('now', '-{} days')
        """.format(limit_days)
        
        conditions = []
        params = []
        
        if dataset:
            conditions.append("dataset = ?")
            params.append(dataset)
        
        if engine:
            conditions.append("engine = ?")
            params.append(engine)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                
                if row and row[0] > 0:
                    return {
                        "total_tests": row[0],
                        "avg_cer": row[1],
                        "avg_wer": row[2],
                        "avg_accuracy": row[3],
                        "avg_processing_time": row[4],
                        "min_accuracy": row[5],
                        "max_accuracy": row[6]
                    }
        
        return {"total_tests": 0}

