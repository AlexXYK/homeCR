"""Simple script to run just the Dashboard."""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🎨 Starting Dashboard")
    print("=" * 60)
    print("🌐 Dashboard: http://localhost:8080")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "dashboard.api:dashboard_app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )

