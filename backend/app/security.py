"""Security utilities for authentication and authorization."""
from fastapi import HTTPException, Header, Depends
from app.config import get_settings, Settings


async def verify_auth_token(
    authorization: str = Header(None),
    settings: Settings = Depends(get_settings)
):
    """Verify authentication token if required.

    Args:
        authorization: Authorization header value
        settings: Application settings

    Raises:
        HTTPException: If authentication is required and fails
    """
    # If auth is not required, allow all requests
    if not settings.require_auth:
        return

    # If auth is required but no token configured, warn but allow
    if not settings.api_token:
        print("⚠️  WARNING: REQUIRE_AUTH=true but no API_TOKEN configured!")
        return

    # Check authorization header
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Include 'Authorization: Bearer <token>' header."
        )

    # Verify Bearer token format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use 'Bearer <token>'"
        )

    # Extract and verify token
    token = authorization.replace("Bearer ", "")
    if token != settings.api_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )


def check_sensitive_url(url: str) -> dict:
    """Check if URL contains sensitive patterns.

    Args:
        url: URL to check

    Returns:
        Dict with is_sensitive flag and warnings
    """
    sensitive_patterns = [
        ("banking", ["bank", "chase", "wellsfargo", "bofa", "citibank"]),
        ("payment", ["paypal", "venmo", "cashapp", "stripe", "square"]),
        ("authentication", ["login", "signin", "auth", "password", "sso"]),
        ("checkout", ["checkout", "payment", "credit-card", "billing"]),
        ("medical", ["medical", "health", "patient", "prescription"]),
        ("tax/legal", ["ssn", "tax", "irs", "w2", "w9", "legal"]),
        ("email", ["mail.google", "outlook", "yahoo.mail", "proton"]),
    ]

    warnings = []
    is_sensitive = False

    url_lower = url.lower()

    for category, patterns in sensitive_patterns:
        if any(pattern in url_lower for pattern in patterns):
            warnings.append(f"Detected {category} page")
            is_sensitive = True

    return {
        "is_sensitive": is_sensitive,
        "warnings": warnings,
        "url": url
    }
