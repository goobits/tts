#!/usr/bin/env python3
"""
App hooks for TTS CLI - provides implementation for all TTS commands.

This module provides backward compatibility by re-exporting all hook
handlers from the hooks submodule.

The implementation has been split into:
- hooks/utils.py: Helper functions and provider registries
- hooks/core.py: on_speak, on_save handlers
- hooks/providers.py: on_voices, on_providers, on_install, on_info handlers
- hooks/voice.py: on_voice_load, on_voice_unload, on_voice_status handlers
- hooks/system.py: on_status, on_config handlers
- hooks/document.py: on_document handler
"""

# Re-export config functions for backward compatibility (used by tests)
from matilda_voice.config import load_config, save_config

# Re-export all hook handlers for backward compatibility
from .hooks import (
    PROVIDER_SHORTCUTS,
    # Registries
    PROVIDERS_REGISTRY,
    get_engine,
    handle_provider_shortcuts,
    on_config,
    # Document
    on_document,
    on_info,
    on_install,
    on_providers,
    on_save,
    # Core
    on_speak,
    # System
    on_status,
    # Voice
    on_voice_load,
    on_voice_status,
    on_voice_unload,
    # Providers
    on_voices,
    # Utils
    parse_provider_shortcuts,
)


def on_serve(host: str = "0.0.0.0", port: int = 8771, **kwargs):
    """Start the Voice HTTP server."""
    from .server import run_server
    run_server(host=host, port=port)


__all__ = [
    # Config (for backward compatibility)
    "load_config",
    "save_config",
    # Registries
    "PROVIDERS_REGISTRY",
    "PROVIDER_SHORTCUTS",
    # Utils
    "parse_provider_shortcuts",
    "handle_provider_shortcuts",
    "get_engine",
    # Core
    "on_speak",
    "on_save",
    # Providers
    "on_voices",
    "on_providers",
    "on_install",
    "on_info",
    # Voice
    "on_voice_load",
    "on_voice_unload",
    "on_voice_status",
    # System
    "on_status",
    "on_config",
    # Document
    "on_document",
    # Server
    "on_serve",
]
