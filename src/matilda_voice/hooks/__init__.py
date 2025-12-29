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

from .core import on_save, on_speak
from .document import on_document
from .providers import on_info, on_install, on_providers, on_voices
from .system import on_config, on_status
from .utils import (
    PROVIDER_SHORTCUTS,
    PROVIDERS_REGISTRY,
    get_engine,
    handle_provider_shortcuts,
    parse_provider_shortcuts,
)
from .voice import on_voice_load, on_voice_status, on_voice_unload

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
