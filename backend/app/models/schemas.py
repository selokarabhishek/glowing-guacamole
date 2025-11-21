"""Pydantic schemas for API requests and responses."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# VLM Schemas
class VLMRequest(BaseModel):
    """Request for VLM analysis."""
    image_base64: str = Field(..., description="Base64 encoded image data")
    prompt: str = Field(..., description="User's analysis prompt")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt override")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for response")
    provider: Optional[str] = Field(None, description="VLM provider override")


class VLMResponse(BaseModel):
    """Response from VLM analysis."""
    content: str = Field(..., description="Analysis result")
    provider: str = Field(..., description="VLM provider used")
    model: str = Field(..., description="Model used")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")


# Form Field Schemas
class FormField(BaseModel):
    """Detected form field."""
    field_type: str = Field(..., description="Input type (text, email, password, select, etc.)")
    label: str = Field(..., description="Field label or name")
    selector: str = Field(..., description="CSS selector to locate the field")
    required: bool = Field(False, description="Whether field is required")
    suggested_value: Optional[str] = Field(None, description="AI suggested value")
    placeholder: Optional[str] = Field(None, description="Placeholder text if available")


# Analysis Schemas
class AnalyzeRequest(BaseModel):
    """Request to analyze a screenshot."""
    image_base64: str = Field(..., description="Base64 encoded screenshot")
    prompt: str = Field(default="Analyze this page", description="User's analysis request")
    url: Optional[str] = Field(None, description="URL of the page being analyzed")
    use_memory: bool = Field(True, description="Whether to use memory context")
    provider: Optional[str] = Field(None, description="VLM provider override")


class AnalyzeResponse(BaseModel):
    """Response from page analysis."""
    analysis: str = Field(..., description="AI analysis of the page")
    form_fields: List[FormField] = Field(default_factory=list, description="Detected form fields")
    provider: str = Field(..., description="VLM provider used")
    model: str = Field(..., description="Model used")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")
    memory_context_used: bool = Field(False, description="Whether memory context was included")


# Memory Schemas
class StoreMemoryRequest(BaseModel):
    """Request to store interaction in memory."""
    url: str = Field(..., description="URL of the page")
    analysis: str = Field(..., description="AI analysis result")
    instruction: str = Field(..., description="User's original instruction")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class StoreMemoryResponse(BaseModel):
    """Response after storing memory."""
    entry_id: str = Field(..., description="ID of stored entry")
    success: bool = Field(..., description="Whether storage succeeded")


class QueryMemoryRequest(BaseModel):
    """Request to query memory."""
    query: str = Field(..., description="Query text")
    url_filter: Optional[str] = Field(None, description="Filter by URL")
    limit: int = Field(5, description="Maximum results to return")


class MemoryEntry(BaseModel):
    """Memory entry result."""
    entry_id: str = Field(..., description="Entry ID")
    url: str = Field(..., description="Page URL")
    analysis: str = Field(..., description="AI analysis")
    instruction: str = Field(..., description="User instruction")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    distance: Optional[float] = Field(None, description="Similarity distance")


class QueryMemoryResponse(BaseModel):
    """Response from memory query."""
    results: List[MemoryEntry] = Field(default_factory=list, description="Matching entries")
    count: int = Field(..., description="Number of results")


class MemoryStatsResponse(BaseModel):
    """Memory statistics."""
    total_entries: int = Field(..., description="Total entries in memory")
    storage_path: str = Field(..., description="ChromaDB storage path")


# Settings Schemas
class ProviderInfo(BaseModel):
    """VLM Provider information."""
    name: str = Field(..., description="Provider name")
    available: bool = Field(..., description="Whether provider is available")
    model: str = Field(..., description="Model being used")
    requires_api_key: bool = Field(..., description="Whether API key is required")
    api_key_configured: bool = Field(False, description="Whether API key is configured")


class SettingsResponse(BaseModel):
    """Application settings."""
    default_provider: str = Field(..., description="Default VLM provider")
    available_providers: List[ProviderInfo] = Field(..., description="All providers and their status")
    embedding_model: str = Field(..., description="Sentence transformer model")
    max_tokens: int = Field(..., description="Default max tokens")
