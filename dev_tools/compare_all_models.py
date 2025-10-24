"""Compare all vision models: Gemma3, Qwen2.5vl, Gemini"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from dev_tools.test_pass3_prompts import test_pass3_prompt


async def compare_all(ocr_data_file: str):
    """Compare Gemma3, Qwen2.5vl, and Gemini."""
    import os
    
    print("=" * 70)
    print("🔬 COMPARING ALL MODELS")
    print("=" * 70)
    print()
    
    # Test 1: Gemma3 (original)
    print("\n" + "=" * 70)
    print("1️⃣  GEMMA 3 12B-IT-QAT (Small, quantized)")
    print("=" * 70)
    os.environ['OLLAMA_VISION_MODEL'] = 'gemma3:12b-it-qat'
    result_gemma = await test_pass3_prompt(ocr_data_file, use_gemini=False)
    
    # Test 2: Qwen2.5vl (document-specialized)
    print("\n" + "=" * 70)
    print("2️⃣  QWEN 2.5 VL 7B (Document-optimized)")
    print("=" * 70)
    os.environ['OLLAMA_VISION_MODEL'] = 'qwen2.5vl:7b'
    result_qwen = await test_pass3_prompt(ocr_data_file, use_gemini=False)
    
    # Test 3: Gemini (SOTA cloud)
    print("\n" + "=" * 70)
    print("3️⃣  GEMINI 2.5 PRO (Cloud SOTA)")
    print("=" * 70)
    result_gemini = await test_pass3_prompt(ocr_data_file, use_gemini=True)
    
    # Compare
    print("\n" + "=" * 70)
    print("📊 COMPARISON")
    print("=" * 70)
    print(f"Gemma3 length:  {len(result_gemma):5} chars")
    print(f"Qwen2.5 length: {len(result_qwen):5} chars")
    print(f"Gemini length:  {len(result_gemini):5} chars")
    print()
    
    # Check for key features
    print("Key Features:")
    print(f"  Address '1961' correct:")
    print(f"    Gemma3:  {'1961' in result_gemma}")
    print(f"    Qwen2.5: {'1961' in result_qwen}")
    print(f"    Gemini:  {'1961' in result_gemini}")
    print()
    
    print(f"  Markdown table format (|):")
    print(f"    Gemma3:  {result_gemma.count('|') > 10}")
    print(f"    Qwen2.5: {result_qwen.count('|') > 10}")
    print(f"    Gemini:  {result_gemini.count('|') > 10}")
    print()
    
    print(f"  Handwritten 'Testing' captured:")
    print(f"    Gemma3:  {'Testing' in result_gemma or 'testing' in result_gemma.lower()}")
    print(f"    Qwen2.5: {'Testing' in result_qwen or 'testing' in result_qwen.lower()}")
    print(f"    Gemini:  {'Testing' in result_gemini or 'testing' in result_gemini.lower()}")
    print()
    
    # Word overlap comparison
    gemma_words = set(result_gemma.lower().split())
    qwen_words = set(result_qwen.lower().split())
    gemini_words = set(result_gemini.lower().split())
    
    gemma_vs_gemini = len(gemma_words & gemini_words) / len(gemma_words | gemini_words) * 100
    qwen_vs_gemini = len(qwen_words & gemini_words) / len(qwen_words | gemini_words) * 100
    
    print(f"Similarity to Gemini (word overlap):")
    print(f"  Gemma3:  {gemma_vs_gemini:.1f}%")
    print(f"  Qwen2.5: {qwen_vs_gemini:.1f}%")
    print()
    
    print("💡 RECOMMENDATION:")
    if qwen_vs_gemini > gemma_vs_gemini + 5:
        print(f"  ✅ Qwen2.5vl is {qwen_vs_gemini - gemma_vs_gemini:.1f}% better than Gemma3!")
        print("  ✅ Use Qwen2.5vl as your local model")
    elif qwen_vs_gemini > 90:
        print(f"  ✅ Qwen2.5vl matches Gemini quality! ({qwen_vs_gemini:.1f}%)")
        print("  ✅ You don't need Gemini for most documents")
    else:
        print(f"  ⚠️  Both local models good but Gemini still better")
        print("  💡 Consider hybrid: local by default, Gemini for complex docs")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_all_models.py <ocr_data.json>")
        sys.exit(1)
    
    ocr_data_file = sys.argv[1]
    asyncio.run(compare_all(ocr_data_file))

