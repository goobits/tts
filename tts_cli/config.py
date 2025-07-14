"""Configuration management for TTS CLI."""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "version": "1.0",
    "default_action": "stream",
    "voice": "edge_tts:en-IE-EmilyNeural",
    "rate": "+0%",
    "pitch": "+0Hz",
    "output_dir": "~/Downloads",
    "log_level": "info"
}


def get_config_path() -> Path:
    """Get the configuration file path, using XDG standard with fallback."""
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config:
        config_dir = Path(xdg_config) / "tts"
    else:
        config_dir = Path.home() / ".config" / "tts"
    
    config_file = config_dir / "config.json"
    
    # Fallback to old location for backwards compatibility
    fallback_file = Path.home() / ".tts.json"
    
    # If new location doesn't exist but old one does, use old one
    if not config_file.exists() and fallback_file.exists():
        return fallback_file
    
    return config_file


def get_default_config() -> Dict[str, Any]:
    """Get the default configuration."""
    return DEFAULT_CONFIG.copy()


def load_config() -> Dict[str, Any]:
    """Load configuration from file, returning defaults if file doesn't exist or is corrupt."""
    config_path = get_config_path()
    
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys are present
            default_config = get_default_config()
            default_config.update(config)
            return default_config
        else:
            logger.debug(f"Config file not found at {config_path}, using defaults")
            return get_default_config()
    
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")
        return get_default_config()


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file atomically."""
    config_path = get_config_path()
    
    try:
        # Ensure config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first, then rename (atomic operation)
        temp_path = config_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Atomic rename
        temp_path.rename(config_path)
        logger.info(f"Configuration saved to {config_path}")
        return True
    
    except (IOError, OSError) as e:
        logger.error(f"Failed to save config to {config_path}: {e}")
        return False


def parse_voice_setting(voice_str: str) -> Tuple[Optional[str], str]:
    """Parse voice setting, returning (provider, voice) tuple.
    
    Handles both explicit provider:voice format and auto-detection.
    
    Args:
        voice_str: Voice string like "edge_tts:en-IE-EmilyNeural" or "en-IE-EmilyNeural"
    
    Returns:
        (provider, voice) tuple. Provider may be None for auto-detection.
    """
    if ':' in voice_str:
        # Explicit provider format: "openai:nova", "google:en-US-Neural2-A", etc.
        provider, voice = voice_str.split(':', 1)
        return provider, voice
    else:
        # Auto-detect provider based on voice characteristics
        if '/' in voice_str or voice_str.endswith(('.wav', '.mp3', '.flac', '.ogg')):
            # File path - likely chatterbox voice cloning
            return 'chatterbox', voice_str
        elif voice_str in ['alloy', 'echo', 'fable', 'nova', 'onyx', 'shimmer']:
            # OpenAI voice names
            return 'openai', voice_str
        elif voice_str.startswith(('en-', 'es-', 'fr-', 'de-', 'it-', 'pt-', 'ja-', 'ko-', 'zh-')) and ('Neural2' in voice_str or 'Wavenet' in voice_str):
            # Google Cloud TTS format like "en-US-Neural2-A" or "en-US-Wavenet-A"
            return 'google', voice_str
        elif voice_str in ['rachel', 'domi', 'bella', 'antoni', 'elli', 'josh', 'arnold', 'adam', 'sam']:
            # ElevenLabs default voice names
            return 'elevenlabs', voice_str
        elif 'Neural' in voice_str or '-' in voice_str:
            # Standard Azure/Edge TTS format like "en-US-JennyNeural"
            return 'edge_tts', voice_str
        else:
            # Unknown format, let current provider handle it
            return None, voice_str


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean configuration values."""
    validated = config.copy()
    
    # Validate default_action
    if validated.get('default_action') not in ['stream', 'save']:
        validated['default_action'] = 'stream'
    
    # Validate log_level
    valid_levels = ['debug', 'info', 'warning', 'error']
    if validated.get('log_level') not in valid_levels:
        validated['log_level'] = 'info'
    
    # Expand output_dir tilde
    if 'output_dir' in validated:
        validated['output_dir'] = str(Path(validated['output_dir']).expanduser())
    
    return validated


def get_setting(key: str, default: Any = None) -> Any:
    """Get a single setting from configuration."""
    config = load_config()
    return config.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """Set a single setting in configuration."""
    config = load_config()
    config[key] = value
    validated_config = validate_config(config)
    return save_config(validated_config)


def validate_api_key(provider: str, api_key: str) -> bool:
    """Validate API key format for different providers."""
    if not api_key or not isinstance(api_key, str):
        return False
    
    if provider == "openai":
        # OpenAI keys start with sk- and are ~50 chars
        return api_key.startswith("sk-") and len(api_key) >= 40
    
    elif provider == "google":
        # Google API keys are 39 chars, start with AIza or can be OAuth token
        return (api_key.startswith("AIza") and len(api_key) == 39) or \
               (api_key.startswith("ya29.") and len(api_key) > 50) or \
               len(api_key) > 100  # Service account JSON string
    
    elif provider == "elevenlabs":
        # ElevenLabs keys are 32 char hex strings
        return len(api_key) == 32 and all(c in '0123456789abcdef' for c in api_key.lower())
    
    else:
        # Unknown provider, assume valid if non-empty
        return len(api_key.strip()) > 0


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider, checking config and environment."""
    # Check config first
    config_key = f"{provider}_api_key"
    api_key = get_setting(config_key)
    
    if api_key and validate_api_key(provider, api_key):
        return api_key
    
    # Fallback to environment variables
    env_key = f"{provider.upper()}_API_KEY"
    env_api_key = os.environ.get(env_key)
    
    if env_api_key and validate_api_key(provider, env_api_key):
        return env_api_key
    
    return None


def set_api_key(provider: str, api_key: str) -> bool:
    """Set and validate API key for a provider."""
    if not validate_api_key(provider, api_key):
        return False
    
    config_key = f"{provider}_api_key"
    return set_setting(config_key, api_key)


def is_ssml(text: str) -> bool:
    """Auto-detect if text contains SSML markup."""
    text = text.strip()
    return text.startswith('<speak') and text.endswith('</speak>')


def strip_ssml_tags(text: str) -> str:
    """Strip SSML tags from text, keeping only the content."""
    import re
    # Remove all XML tags but keep the content
    return re.sub(r'<[^>]+>', '', text)