"""Simple script to run just the OCR API."""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting OCR API")
    print("=" * 60)
    print("📡 API: http://localhost:5000")
    print("📖 Docs: http://localhost:5000/docs")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        log_level="info"
    )

