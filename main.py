"""
Main entry point for the Universal OCR system.
Runs both the OCR API and the dashboard.
"""
import uvicorn
import asyncio
from multiprocessing import Process
from config import settings


def run_api():
    """Run the OCR API server."""
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=False,
        log_level="info"
    )


def run_dashboard():
    """Run the dashboard server."""
    uvicorn.run(
        "dashboard.api:dashboard_app",
        host="0.0.0.0",
        port=settings.dashboard_port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Universal OCR System")
    print("=" * 60)
    print(f"📡 OCR API will be available at: http://localhost:{settings.api_port}")
    print(f"🎨 Dashboard will be available at: http://localhost:{settings.dashboard_port}")
    print(f"🤖 Ollama endpoint: {settings.ollama_host}")
    print("=" * 60)
    print()
    
    # Start both servers in separate processes
    api_process = Process(target=run_api)
    dashboard_process = Process(target=run_dashboard)
    
    try:
        api_process.start()
        dashboard_process.start()
        
        api_process.join()
        dashboard_process.join()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
        api_process.terminate()
        dashboard_process.terminate()
        api_process.join()
        dashboard_process.join()
        print("✅ Shutdown complete")

