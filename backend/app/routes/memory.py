"""Memory management routes for RAG storage."""
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    StoreMemoryRequest,
    StoreMemoryResponse,
    QueryMemoryRequest,
    QueryMemoryResponse,
    MemoryStatsResponse
)
from app.memory.store import MemoryStore
from app.config import get_settings, Settings

router = APIRouter(prefix="/api/memory", tags=["memory"])

# Global instance (will be initialized in main.py)
memory_store: MemoryStore = None


def get_memory_store() -> MemoryStore:
    """Get memory store instance."""
    if memory_store is None:
        raise HTTPException(status_code=500, detail="Memory store not initialized")
    return memory_store


@router.post("/store", response_model=StoreMemoryResponse)
async def store_memory(request: StoreMemoryRequest):
    """Store an interaction in memory.

    Args:
        request: Memory storage request

    Returns:
        Storage response with entry ID
    """
    try:
        store = get_memory_store()
        entry_id = store.store(
            url=request.url,
            analysis=request.analysis,
            instruction=request.instruction,
            metadata=request.metadata
        )

        return StoreMemoryResponse(
            entry_id=entry_id,
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryMemoryResponse)
async def query_memory(request: QueryMemoryRequest):
    """Query memory for relevant interactions.

    Args:
        request: Query request

    Returns:
        Query results
    """
    try:
        store = get_memory_store()
        results = store.query(
            query_text=request.query,
            url_filter=request.url_filter,
            limit=request.limit
        )

        return QueryMemoryResponse(
            results=results,
            count=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entry_id}")
async def delete_memory(entry_id: str):
    """Delete a memory entry.

    Args:
        entry_id: ID of entry to delete

    Returns:
        Success status
    """
    try:
        store = get_memory_store()
        success = store.delete(entry_id)

        if not success:
            raise HTTPException(status_code=404, detail="Entry not found")

        return {"success": True, "message": "Entry deleted"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(settings: Settings = Depends(get_settings)):
    """Get memory statistics.

    Args:
        settings: Application settings

    Returns:
        Memory statistics
    """
    try:
        store = get_memory_store()
        count = store.get_count()

        return MemoryStatsResponse(
            total_entries=count,
            storage_path=settings.chroma_persist_dir
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_memory():
    """Clear all memory entries.

    Returns:
        Success status
    """
    try:
        store = get_memory_store()
        success = store.clear_all()

        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear memory")

        return {"success": True, "message": "All memory cleared"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
