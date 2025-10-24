"""
Test the perfect_tables flag.

Shows the simple use case: default (fast, free) vs perfect tables.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from PIL import Image
from ocr_pipeline.intelligent_pipeline import IntelligentOCRPipeline


async def compare_table_modes(image_path: str):
    """Compare default vs perfect_tables mode."""
    print("=" * 70)
    print("📊 TABLE QUALITY COMPARISON")
    print("=" * 70)
    print(f"Image: {image_path}")
    print()
    
    img = Image.open(image_path)
    
    # Mode 1: Default (Local, fast, free)
    print("\n" + "=" * 70)
    print("1️⃣  DEFAULT MODE (Local, Fast, Free)")
    print("=" * 70)
    print("Settings: vision_provider=ollama, perfect_tables=False")
    print("Cost: $0")
    print()
    
    pipeline_default = IntelligentOCRPipeline(
        vision_provider="ollama",
        use_hybrid_ocr=True,
        perfect_tables=False
    )
    
    result_default = await pipeline_default.process(img)
    
    print()
    print("📄 OUTPUT:")
    print("-" * 70)
    print(result_default.text[:800])
    print(f"\n... ({len(result_default.text)} total characters)")
    
    # Mode 2: Perfect Tables
    print("\n\n" + "=" * 70)
    print("2️⃣  PERFECT TABLES MODE (Hybrid: Local + Gemini for Tables)")
    print("=" * 70)
    print("Settings: vision_provider=ollama, perfect_tables=True")
    print("Cost: ~$0.005/doc (only if document has tables)")
    print()
    
    pipeline_perfect = IntelligentOCRPipeline(
        vision_provider="ollama",
        use_hybrid_ocr=True,
        perfect_tables=True  # ← The magic flag!
    )
    
    result_perfect = await pipeline_perfect.process(img)
    
    print()
    print("📄 OUTPUT:")
    print("-" * 70)
    print(result_perfect.text[:800])
    print(f"\n... ({len(result_perfect.text)} total characters)")
    
    # Comparison
    print("\n\n" + "=" * 70)
    print("📊 COMPARISON")
    print("=" * 70)
    print(f"Default mode:")
    print(f"  Length: {len(result_default.text)} chars")
    print(f"  Has markdown tables (|): {result_default.text.count('|') > 10}")
    print(f"  Cost: $0")
    print()
    print(f"Perfect tables mode:")
    print(f"  Length: {len(result_perfect.text)} chars")
    print(f"  Has markdown tables (|): {result_perfect.text.count('|') > 10}")
    print(f"  Cost: ~$0.005")
    print()
    
    if result_perfect.text.count('|') > result_default.text.count('|'):
        print("✅ Perfect tables mode successfully formatted tables as markdown!")
    else:
        print("⚠️  No significant table improvement detected")
    
    print()
    print("💡 USAGE:")
    print("  Fast/Free:      pipeline = IntelligentOCRPipeline(vision_provider='ollama')")
    print("  Perfect Tables: pipeline = IntelligentOCRPipeline(vision_provider='ollama', perfect_tables=True)")
    print("  Full Cloud:     pipeline = IntelligentOCRPipeline(vision_provider='gemini')")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_perfect_tables.py <image_path>")
        print()
        print("Example:")
        print("  python test_perfect_tables.py vettest.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"❌ Error: Image not found: {image_path}")
        sys.exit(1)
    
    asyncio.run(compare_table_modes(image_path))

