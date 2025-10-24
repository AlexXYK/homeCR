"""
Script to run OCR benchmarks.
Usage: python run_tests.py [--dataset DATASET] [--engine ENGINE] [--max-samples N]
"""
import asyncio
import argparse
from testing.orchestrator import TestOrchestrator


async def main():
    parser = argparse.ArgumentParser(description="Run OCR benchmarks")
    parser.add_argument(
        "--dataset",
        help="Dataset to test (handwriting, print, tables, mixed, screenshots, edge_cases)",
        default=None
    )
    parser.add_argument(
        "--engine",
        help="Force specific engine (tesseract, surya, vision)",
        default=None
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Maximum number of samples to test",
        default=None
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics instead of running tests"
    )
    
    args = parser.parse_args()
    
    orchestrator = TestOrchestrator()
    
    if args.summary:
        # Show summary statistics
        stats = await orchestrator.get_summary_stats(
            dataset=args.dataset,
            engine=args.engine
        )
        
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        if stats['total_tests'] > 0:
            print(f"Total Tests: {stats['total_tests']}")
            print(f"Average Accuracy: {stats['avg_accuracy']:.1%}")
            print(f"Average CER: {stats['avg_cer']:.3f}")
            print(f"Average WER: {stats['avg_wer']:.3f}")
            print(f"Accuracy Range: {stats['min_accuracy']:.1%} - {stats['max_accuracy']:.1%}")
            print(f"Avg Processing Time: {stats['avg_processing_time']:.2f}s")
        else:
            print("No test results found")
        
        print("=" * 60)
    else:
        # Run benchmark
        dataset_names = [args.dataset] if args.dataset else None
        
        results = await orchestrator.run_benchmark(
            dataset_names=dataset_names,
            force_engine=args.engine,
            max_samples=args.max_samples
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("BENCHMARK COMPLETE")
        print("=" * 60)
        print(f"Total tests: {len(results)}")
        
        # Calculate overall metrics
        results_with_metrics = [r for r in results if r.metrics]
        if results_with_metrics:
            avg_accuracy = sum(r.metrics['accuracy'] for r in results_with_metrics) / len(results_with_metrics)
            avg_cer = sum(r.metrics['character_error_rate'] for r in results_with_metrics) / len(results_with_metrics)
            avg_time = sum(r.processing_time for r in results) / len(results)
            
            print(f"Average Accuracy: {avg_accuracy:.1%}")
            print(f"Average CER: {avg_cer:.3f}")
            print(f"Average Processing Time: {avg_time:.2f}s")
        
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

