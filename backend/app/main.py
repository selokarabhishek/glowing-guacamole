"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.vlm.router import VLMRouter
from app.memory.store import MemoryStore
from app.memory.retriever import MemoryRetriever
from app.routes import analyze, memory, settings

# Initialize FastAPI app
app = FastAPI(
    title="Visual AI Assistant API",
    description="Backend API for Visual AI Assistant browser extension",
    version="1.0.0"
)

# Configure CORS for browser extension
# SECURITY: Restrict to extension only in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Chrome extensions
        "moz-extension://*",     # Firefox extensions
        "http://localhost:*",    # Development only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    settings_instance = get_settings()

    # Initialize VLM router
    vlm_router_instance = VLMRouter(settings_instance)
    analyze.vlm_router = vlm_router_instance
    settings.vlm_router = vlm_router_instance

    # Initialize memory store
    memory_store_instance = MemoryStore(
        persist_dir=settings_instance.chroma_persist_dir,
        embedding_model=settings_instance.embedding_model
    )
    memory.memory_store = memory_store_instance
    analyze.memory_store = memory_store_instance

    # Initialize memory retriever
    memory_retriever_instance = MemoryRetriever(memory_store_instance)
    analyze.memory_retriever = memory_retriever_instance

    print(f"✓ Visual AI Assistant API started")
    print(f"✓ Default VLM provider: {settings_instance.default_vlm_provider}")
    print(f"✓ Memory store: {settings_instance.chroma_persist_dir}")


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "service": "Visual AI Assistant API"}


# Include routers
app.include_router(analyze.router)
app.include_router(memory.router)
app.include_router(settings.router)
