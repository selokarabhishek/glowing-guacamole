"""Run the FastAPI application."""
import uvicorn
from app.config import get_settings


if __name__ == "__main__":
    settings = get_settings()

    print("=" * 60)
    print("Visual AI Assistant Backend")
    print("=" * 60)
    print(f"Starting server on {settings.host}:{settings.port}")
    print(f"API docs available at http://{settings.host}:{settings.port}/docs")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
