"""
Quick verification that the system is working after cleanup.
"""
import sys


def verify_imports():
    """Verify all critical imports work."""
    print("=" * 70)
    print("🔍 VERIFYING IMPORTS")
    print("=" * 70)
    
    imports = [
        ("config.settings", "Settings configuration"),
        ("ocr_pipeline.intelligent_pipeline", "Intelligent pipeline"),
        ("ocr_pipeline.engines.vision_providers", "Vision providers"),
        ("ocr_pipeline.engines.tesseract_engine", "Tesseract engine"),
        ("ocr_pipeline.engines.surya_engine", "Surya engine"),
        ("app", "FastAPI app"),
    ]
    
    all_ok = True
    for module, desc in imports:
        try:
            __import__(module)
            print(f"  ✅ {desc}: {module}")
        except Exception as e:
            print(f"  ❌ {desc}: {module}")
            print(f"     Error: {e}")
            all_ok = False
    
    return all_ok


def verify_providers():
    """Verify provider system."""
    print("\n" + "=" * 70)
    print("🌐 VERIFYING PROVIDERS")
    print("=" * 70)
    
    try:
        from ocr_pipeline.engines.vision_providers import get_vision_provider
        from config import settings
        
        providers = ["ollama", "gemini", "openai", "anthropic", "openrouter"]
        
        for provider in providers:
            try:
                p = get_vision_provider(provider)
                status = "✅ Available" if p.is_available() else "⚠️  Not configured"
                print(f"  {status}: {provider} ({p.model_name})")
            except Exception as e:
                print(f"  ❌ {provider}: {e}")
        
        return True
    except Exception as e:
        print(f"  ❌ Provider system error: {e}")
        return False


def verify_config():
    """Verify configuration."""
    print("\n" + "=" * 70)
    print("⚙️  VERIFYING CONFIGURATION")
    print("=" * 70)
    
    try:
        from config import settings
        
        print(f"  Vision Provider: {settings.vision_provider}")
        print(f"  Ollama Host: {settings.ollama_host}")
        print(f"  Hybrid OCR: {settings.use_hybrid_ocr}")
        print(f"  Perfect Tables: {settings.perfect_tables}")
        print(f"  Gemini Model: {settings.gemini_model}")
        print(f"  Gemini API Key: {'✅ Set' if settings.gemini_api_key else '❌ Not set'}")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def verify_engines():
    """Verify OCR engines."""
    print("\n" + "=" * 70)
    print("🔧 VERIFYING OCR ENGINES")
    print("=" * 70)
    
    try:
        from ocr_pipeline.engines.tesseract_engine import TesseractEngine
        from ocr_pipeline.engines.surya_engine import SuryaEngine
        
        tesseract = TesseractEngine()
        surya = SuryaEngine()
        
        print(f"  {'✅' if tesseract.is_available() else '⚠️ '} Tesseract: {tesseract.name}")
        print(f"  ✅ Surya: {surya.name}")
        
        return True
    except Exception as e:
        print(f"  ❌ Engine error: {e}")
        return False


def main():
    """Run all verifications."""
    print("\n" + "=" * 70)
    print("🧪 SYSTEM VERIFICATION")
    print("=" * 70)
    print()
    
    results = {
        "Imports": verify_imports(),
        "Providers": verify_providers(),
        "Configuration": verify_config(),
        "OCR Engines": verify_engines()
    }
    
    print("\n" + "=" * 70)
    print("📊 VERIFICATION RESULTS")
    print("=" * 70)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check}")
    
    all_passed = all(results.values())
    
    print()
    if all_passed:
        print("🎉 ALL CHECKS PASSED - System is ready!")
        print()
        print("Next steps:")
        print("  1. Test OCR: python dev_tools/test_perfect_tables.py image.jpg")
        print("  2. Start API: python run_api.py")
        print("  3. Deploy: docker-compose up -d")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

