"""
Test Pass 3 prompts in isolation.

This lets you iterate on prompts quickly without re-running OCR.
Save OCR outputs once, then test different prompts/models rapidly.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
from PIL import Image
from ocr_pipeline.intelligent_pipeline import IntelligentOCRPipeline, DocumentAnalysis


async def save_ocr_outputs(image_path: str, output_file: str):
    """Run OCR once and save outputs for reuse."""
    print("=" * 70)
    print("💾 SAVING OCR OUTPUTS")
    print("=" * 70)
    print(f"Image: {image_path}")
    print(f"Output: {output_file}")
    print()
    
    img = Image.open(image_path)
    pipeline = IntelligentOCRPipeline(use_gemini_vision=True, use_hybrid_ocr=True)
    
    # Run Pass 1 & 2
    print("Running Pass 1: Analysis...")
    analysis = await pipeline.pass1_analyze_document(img)
    
    print("Running Pass 2: Dual OCR...")
    tesseract_text, surya_text, engines = await pipeline.pass2_dual_extract(img, analysis)
    
    # Save everything
    data = {
        'image_path': str(image_path),
        'analysis': {
            'document_type': analysis.document_type,
            'complexity': analysis.complexity,
            'has_tables': analysis.has_tables,
            'has_handwriting': analysis.has_handwriting,
            'language': analysis.language,
            'recommended_engine': analysis.recommended_engine,
            'raw_analysis': analysis.raw_analysis
        },
        'tesseract_output': tesseract_text,
        'surya_output': surya_text,
        'engines_used': engines
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print()
    print(f"✅ Saved OCR outputs to {output_file}")
    print(f"   Tesseract: {len(tesseract_text or '')} chars")
    print(f"   Surya: {len(surya_text or '')} chars")
    print()


async def test_pass3_prompt(
    ocr_data_file: str,
    vision_provider: str = "ollama",
    custom_prompt: str = None
):
    """Test Pass 3 with saved OCR data and custom prompt."""
    print("=" * 70)
    print(f"🧪 TESTING PASS 3 ({vision_provider.upper()})")
    print("=" * 70)
    
    # Load saved data
    with open(ocr_data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    image_path = data['image_path']
    img = Image.open(image_path)
    
    # Reconstruct analysis
    analysis_dict = data['analysis']
    analysis = DocumentAnalysis(analysis_dict)
    
    tesseract_text = data['tesseract_output']
    surya_text = data['surya_output']
    engines = data['engines_used']
    
    print(f"Image: {image_path}")
    print(f"OCR outputs loaded: {len(tesseract_text or '')} + {len(surya_text or '')} chars")
    print()
    
    # Create pipeline
    pipeline = IntelligentOCRPipeline(
        vision_provider=vision_provider,
        use_hybrid_ocr=True
    )
    
    # Run Pass 3
    if custom_prompt:
        print("Using CUSTOM prompt")
        # TODO: Implement custom prompt injection
    
    print("Running Pass 3...")
    result = await pipeline.pass3_vision_guided_fusion(
        img, tesseract_text, surya_text, analysis, engines
    )
    
    print()
    print("=" * 70)
    print("📄 RESULT")
    print("=" * 70)
    print(result[:1000])
    if len(result) > 1000:
        print(f"\n... ({len(result) - 1000} more characters)")
    print()
    
    return result


async def compare_prompts(ocr_data_file: str):
    """Compare different approaches to Pass 3."""
    print("=" * 70)
    print("🔬 COMPARING PASS 3 APPROACHES")
    print("=" * 70)
    print()
    
    # Test 1: Ollama (current)
    print("\n" + "=" * 70)
    print("1️⃣  OLLAMA (Current Prompt)")
    print("=" * 70)
    result_ollama = await test_pass3_prompt(ocr_data_file, vision_provider="ollama")
    
    # Test 2: Gemini (current)
    print("\n" + "=" * 70)
    print("2️⃣  GEMINI 2.5 Pro (Current Prompt)")
    print("=" * 70)
    result_gemini = await test_pass3_prompt(ocr_data_file, vision_provider="gemini")
    
    # Compare
    print("\n" + "=" * 70)
    print("📊 COMPARISON")
    print("=" * 70)
    print(f"Ollama length: {len(result_ollama)} chars")
    print(f"Gemini length: {len(result_gemini)} chars")
    print()
    
    # Key differences
    print("Key differences to investigate:")
    print("  - Does Ollama get addresses wrong? (e.g., '4961' vs '1961')")
    print("  - Does Ollama properly format tables?")
    print("  - Does Ollama capture handwritten notes?")
    print()


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Save OCR outputs:")
        print("    py test_pass3_prompts.py save <image_path> <output.json>")
        print()
        print("  Test saved outputs:")
        print("    py test_pass3_prompts.py test <output.json> [ollama|gemini]")
        print()
        print("  Compare approaches:")
        print("    py test_pass3_prompts.py compare <output.json>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'save':
        if len(sys.argv) < 4:
            print("Usage: py test_pass3_prompts.py save <image_path> <output.json>")
            sys.exit(1)
        
        image_path = sys.argv[2]
        output_file = sys.argv[3]
        await save_ocr_outputs(image_path, output_file)
    
    elif command == 'test':
        if len(sys.argv) < 3:
            print("Usage: py dev_tools/test_pass3_prompts.py test <output.json> [ollama|gemini|openai|anthropic]")
            sys.exit(1)
        
        ocr_data_file = sys.argv[2]
        vision_provider = sys.argv[3] if len(sys.argv) > 3 else 'ollama'
        await test_pass3_prompt(ocr_data_file, vision_provider=vision_provider)
    
    elif command == 'compare':
        if len(sys.argv) < 3:
            print("Usage: py test_pass3_prompts.py compare <output.json>")
            sys.exit(1)
        
        ocr_data_file = sys.argv[2]
        await compare_prompts(ocr_data_file)
    
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: save, test, compare")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

