"""Analysis routes for screenshot processing."""
import re
import json
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    FormField,
    VLMRequest
)
from app.vlm.router import VLMRouter
from app.memory.store import MemoryStore
from app.memory.retriever import MemoryRetriever
from app.config import get_settings, Settings

router = APIRouter(prefix="/api/analyze", tags=["analyze"])

# Global instances (will be initialized in main.py)
vlm_router: VLMRouter = None
memory_store: MemoryStore = None
memory_retriever: MemoryRetriever = None


def get_vlm_router() -> VLMRouter:
    """Get VLM router instance."""
    if vlm_router is None:
        raise HTTPException(status_code=500, detail="VLM router not initialized")
    return vlm_router


def get_memory_retriever() -> MemoryRetriever:
    """Get memory retriever instance."""
    if memory_retriever is None:
        raise HTTPException(status_code=500, detail="Memory retriever not initialized")
    return memory_retriever


@router.post("/", response_model=AnalyzeResponse)
async def analyze_page(
    request: AnalyzeRequest,
    settings: Settings = Depends(get_settings)
):
    """Analyze a page screenshot.

    Args:
        request: Analysis request with screenshot and prompt
        settings: Application settings

    Returns:
        Analysis response with detected fields
    """
    try:
        # Build enhanced prompt with memory if requested
        enhanced_prompt = request.prompt
        memory_used = False

        if request.use_memory and memory_retriever:
            enhanced_prompt, memory_used = memory_retriever.build_enhanced_prompt(
                request.prompt,
                url=request.url,
                use_memory=True
            )

        # Create VLM request
        vlm_request = VLMRequest(
            image_base64=request.image_base64,
            prompt=enhanced_prompt,
            system_prompt=settings.system_prompt,
            max_tokens=settings.max_tokens,
            provider=request.provider
        )

        # Get VLM response
        router_instance = get_vlm_router()
        vlm_response = await router_instance.analyze(vlm_request)

        # Extract form fields from response
        form_fields = extract_form_fields(vlm_response.content)

        return AnalyzeResponse(
            analysis=vlm_response.content,
            form_fields=form_fields,
            provider=vlm_response.provider,
            model=vlm_response.model,
            tokens_used=vlm_response.tokens_used,
            memory_context_used=memory_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-fields", response_model=list[FormField])
async def extract_fields_only(
    request: AnalyzeRequest,
    settings: Settings = Depends(get_settings)
):
    """Extract form fields only from screenshot.

    Args:
        request: Analysis request with screenshot
        settings: Application settings

    Returns:
        List of detected form fields
    """
    # Use a focused prompt for field extraction
    field_prompt = """Analyze this page and extract all form input fields. For each field, provide:
- Field type (text, email, password, select, checkbox, textarea, etc.)
- Field label
- CSS selector (id, name, or other unique selector)
- Whether it's required
- Any placeholder text

Format your response as a structured list."""

    request.prompt = field_prompt
    response = await analyze_page(request, settings)
    return response.form_fields


def extract_form_fields(analysis_text: str) -> list[FormField]:
    """Extract structured form fields from analysis text.

    Args:
        analysis_text: AI analysis response

    Returns:
        List of detected form fields
    """
    fields = []

    # Try to find structured field information in the response
    # Look for patterns like:
    # - Field: <name> (type: <type>, selector: <selector>)
    # - <label>: <type> field, selector: <selector>

    # Pattern 1: JSON-like structure
    json_pattern = r'\{[^}]*"(?:type|field_type|label)"[^}]*\}'
    json_matches = re.finditer(json_pattern, analysis_text, re.IGNORECASE)

    for match in json_matches:
        try:
            field_data = json.loads(match.group())
            fields.append(FormField(
                field_type=field_data.get('type') or field_data.get('field_type', 'text'),
                label=field_data.get('label', 'Unknown'),
                selector=field_data.get('selector', ''),
                required=field_data.get('required', False),
                suggested_value=field_data.get('suggested_value'),
                placeholder=field_data.get('placeholder')
            ))
        except json.JSONDecodeError:
            continue

    # Pattern 2: Line-by-line description
    # Example: "Email field (required) - selector: #email"
    line_pattern = r'(?P<label>[\w\s]+):\s*(?P<type>text|email|password|select|checkbox|textarea|tel|url|number)(?:\s+field)?(?:\s*\((?P<required>required)\))?\s*[-–]\s*(?:selector|css):\s*(?P<selector>[^\n,]+)'
    line_matches = re.finditer(line_pattern, analysis_text, re.IGNORECASE)

    for match in line_matches:
        fields.append(FormField(
            field_type=match.group('type').lower(),
            label=match.group('label').strip(),
            selector=match.group('selector').strip(),
            required=match.group('required') is not None,
            suggested_value=None,
            placeholder=None
        ))

    return fields
