#!/usr/bin/env python3
"""
Hooks module for TTS CLI business logic.

This module provides all hook handlers for the CLI commands:
- core: on_speak, on_save (main synthesis handlers)
- providers: on_voices, on_providers, on_install, on_info
- voice: on_voice_load, on_voice_unload, on_voice_status
- system: on_status, on_config
- document: on_document
- utils: helper functions and registries
"""

from .utils import (
    PROVIDERS_REGISTRY,
    PROVIDER_SHORTCUTS,
    parse_provider_shortcuts,
    handle_provider_shortcuts,
    get_engine,
)
from .core import on_speak, on_save
from .providers import on_voices, on_providers, on_install, on_info
from .voice import on_voice_load, on_voice_unload, on_voice_status
from .system import on_status, on_config
from .document import on_document

__all__ = [
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
]
