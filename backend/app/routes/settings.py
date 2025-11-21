"""Settings and configuration routes."""
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import SettingsResponse, ProviderInfo
from app.vlm.router import VLMRouter
from app.config import get_settings, Settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Global instance (will be initialized in main.py)
vlm_router: VLMRouter = None


def get_vlm_router() -> VLMRouter:
    """Get VLM router instance."""
    if vlm_router is None:
        raise HTTPException(status_code=500, detail="VLM router not initialized")
    return vlm_router


@router.get("/", response_model=SettingsResponse)
async def get_app_settings(settings: Settings = Depends(get_settings)):
    """Get application settings and provider information.

    Args:
        settings: Application settings

    Returns:
        Settings response with provider info
    """
    try:
        router_instance = get_vlm_router()
        providers = router_instance.list_available_providers()

        return SettingsResponse(
            default_provider=settings.default_vlm_provider,
            available_providers=list(providers.values()),
            embedding_model=settings.embedding_model,
            max_tokens=settings.max_tokens
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=dict[str, ProviderInfo])
async def get_providers():
    """Get available VLM providers and their status.

    Returns:
        Dict of provider name to provider info
    """
    try:
        router_instance = get_vlm_router()
        return router_instance.list_available_providers()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
