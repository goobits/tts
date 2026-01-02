"""
Security utilities for matilda-voice server.

Provides secure defaults for CORS configuration and other security-related functionality.
"""

import logging
import os
from typing import List

logger = logging.getLogger(__name__)


def get_allowed_origins() -> List[str]:
    """
    Get the list of allowed CORS origins.

    Security behavior:
    - If ALLOWED_ORIGINS env var is set, use those origins
    - If MATILDA_DEV_MODE=1/true/yes, fall back to localhost defaults for development
    - Otherwise, return empty list (secure default for production)

    Returns:
        List of allowed origin URLs, or empty list if none configured.
    """
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS")

    if allowed_origins_env:
        # Parse comma-separated origins, stripping whitespace
        origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
        return origins

    # Check for development mode
    dev_mode = os.getenv("MATILDA_DEV_MODE", "").lower() in ("1", "true", "yes")

    if dev_mode:
        # Development defaults - localhost origins for convenience
        return ["http://localhost:3000", "http://localhost:5173"]

    # Production: secure default is no origins allowed
    logger.warning(
        "ALLOWED_ORIGINS not set in production mode. "
        "CORS requests will be blocked. Set ALLOWED_ORIGINS environment variable "
        "to allow cross-origin requests, or set MATILDA_DEV_MODE=1 for development."
    )
    return []
