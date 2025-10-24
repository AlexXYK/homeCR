"""
Test the intelligent multi-pass OCR pipeline.
Usage: py dev_tools/test_intelligent_pipeline.py path/to/image.jpg
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from PIL import Image
from ocr_pipeline.intelligent_pipeline import IntelligentOCRPipeline


async def test_pipeline(image_path: str):
    """Test the intelligent pipeline on an image."""
    print("=" * 70)
    print(f"🔍 Testing Intelligent Pipeline: {image_path}")
    print("=" * 70)
    
    # Load image
    img = Image.open(image_path)
    print(f"📐 Image size: {img.size}")
    print(f"🎨 Mode: {img.mode}")
    print()
    
    # Initialize pipeline
    pipeline = IntelligentOCRPipeline()
    
    # Process
    result = await pipeline.process(img)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    print(f"Pipeline: {result.metadata['pipeline']}")
    print(f"OCR Engines: {result.metadata.get('ocr_engines', result.metadata.get('ocr_engine', 'N/A'))}")
    print(f"Hybrid Mode: {result.metadata.get('hybrid_mode', False)}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Passes completed: {result.metadata['passes_completed']}")
    print()
    
    print("📋 Document Analysis:")
    analysis = result.metadata['analysis']
    print(f"  Type: {analysis['document_type']}")
    print(f"  Complexity: {analysis['complexity']}")
    print(f"  Has tables: {analysis['has_tables']}")
    print(f"  Has handwriting: {analysis['has_handwriting']}")
    print(f"  Language: {analysis.get('language', 'N/A')}")
    print()
    
    print("=" * 70)
    print("✨ VISION-CORRECTED & FORMATTED OUTPUT")
    print("=" * 70)
    print(result.text)
    print()
    
    # Show improvement
    raw_len = result.metadata.get('raw_text_length', 0)
    final_len = result.metadata.get('final_text_length', 0)
    if raw_len and final_len:
        change = ((final_len - raw_len) / raw_len) * 100
        print(f"📈 Text length change: {change:+.1f}% (formatting adjustment)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py test_intelligent_pipeline.py <image_path>")
        print("\nExample:")
        print("  py test_intelligent_pipeline.py test.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"❌ Error: Image not found: {image_path}")
        sys.exit(1)
    
    asyncio.run(test_pipeline(image_path))

