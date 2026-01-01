"""
Hook implementations for Matilda Voice - Text to Speech.

This file re-exports hook implementations from the hooks package.
The CLI imports hooks from here, which delegates to the real implementations.
"""

# Re-export all hooks from the hooks package
from matilda_voice.hooks import (
    # Registries
    PROVIDERS_REGISTRY,
    PROVIDER_SHORTCUTS,
    # Utils
    parse_provider_shortcuts,
    handle_provider_shortcuts,
    get_engine,
    # Core
    on_speak,
    on_save,
    # Providers
    on_voices,
    on_providers,
    on_install,
    on_info,
    # Voice
    on_voice_load,
    on_voice_unload,
    on_voice_status,
    # System
    on_status,
    on_config,
    # Document
    on_document,
)

# Re-export config functions for backwards compatibility
from matilda_voice.config import load_config, save_config

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
    # Config
    "load_config",
    "save_config",
]
