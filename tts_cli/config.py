"""Configuration management for TTS CLI with TOML support.

This module provides flexible configuration management supporting multiple sources:

**Configuration Sources (highest to lowest precedence):**
1. Environment variables (TTS_<SECTION>_<KEY>)
2. Local config.toml file (current directory)  
3. User config.toml file (~/.config/tts/config.toml)
4. Global config.toml file (/etc/tts/config.toml)
5. Built-in defaults

**TOML Configuration Format:**
The configuration uses a structured TOML format with sections for different
aspects of the application:

```toml
[network]
chatterbox_server_port = 12345
http_streaming_chunk_size = 1024

[timeouts]  
ffplay_timeout = 5
server_startup_timeout = 30

[providers.elevenlabs]
default_stability = 0.5
api_key_length = 32
```

**Environment Variable Override:**
Any configuration value can be overridden using environment variables:
- Format: TTS_<SECTION>_<KEY>=<value>
- Example: TTS_NETWORK_CHATTERBOX_SERVER_PORT=8080
- Supports: strings, integers, floats, booleans

**Usage Examples:**
```bash
# Override server port via environment
export TTS_NETWORK_CHATTERBOX_SERVER_PORT=8080

# Override timeout settings
export TTS_TIMEOUTS_FFPLAY_TIMEOUT=10

# Override provider defaults  
export TTS_PROVIDERS_ELEVENLABS_DEFAULT_STABILITY=0.8
```

**Migration from Hardcoded Values:**
The Config class now loads values dynamically, maintaining backwards
compatibility while enabling flexible deployment configuration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, Union, List
import logging

# Import TOML library (tomllib in Python 3.11+, fallback to toml)
try:
    import tomllib
    TOML_AVAILABLE = True
except ImportError:
    try:
        import toml as tomllib
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False
        tomllib = None

logger = logging.getLogger(__name__)

# Legacy JSON configuration for backwards compatibility
DEFAULT_CONFIG = {
    "version": "1.0",
    "default_action": "stream", 
    "voice": "edge_tts:en-IE-EmilyNeural",
    "rate": "+0%",
    "pitch": "+0Hz",
    "output_dir": "~/Downloads",
    "log_level": "info"
}

# Default TOML configuration structure
DEFAULT_TOML_CONFIG = {
    "general": {
        "version": "1.0",
        "default_action": "stream",
        "log_level": "info",
        "output_dir": "~/Downloads"
    },
    "voice": {
        "default_voice": "edge_tts:en-IE-EmilyNeural",
        "default_rate": "+0%", 
        "default_pitch": "+0Hz"
    },
    "network": {
        "chatterbox_server_port": 12345,
        "socket_recv_buffer_size": 4096,
        "http_streaming_chunk_size": 1024
    },
    "timeouts": {
        "server_startup_timeout": 30,
        "server_poll_interval": 1,
        "socket_connection_timeout": 1,
        "voice_loading_timeout": 30,
        "audio_check_timeout": 2,
        "ffprobe_timeout": 5,
        "ffmpeg_validation_timeout": 5,
        "ffplay_timeout": 5,
        "ffplay_termination_timeout": 2,
        "ffmpeg_conversion_timeout": 30
    },
    "ui": {
        "double_click_time": 0.8,
        "filter_panel_width": 20,
        "preview_panel_width": 18,
        "status_display_time": 1000,
        "click_feedback_time": 500,
        "success_message_time": 1500,
        "page_scroll_amount": 10,
        "printable_char_range_start": 32,
        "printable_char_range_end": 126
    },
    "audio": {
        "audio_16bit_scale": 32767,
        "audio_amplitude_limit": 0.95,
        "audio_channels": 1,
        "audio_sample_width": 2,
        "audio_cards_min_size": 0
    },
    "providers": {
        "elevenlabs": {
            "default_stability": 0.5,
            "default_similarity_boost": 0.5,
            "default_style": 0.0,
            "voice_id_length": 32,
            "api_key_length": 32
        },
        "google_tts": {
            "default_speaking_rate": 1.0,
            "default_pitch": 0.0,
            "api_key_length": 39,
            "oauth_token_min_length": 50,
            "service_account_json_min_length": 100
        },
        "openai": {
            "api_key_min_length": 40
        },
        "chatterbox": {
            "default_exaggeration": 0.5,
            "default_cfg_weight": 0.5,
            "default_temperature": 0.8,
            "default_min_p": 0.05
        }
    },
    "http": {
        "unauthorized": 401,
        "forbidden": 403,
        "rate_limit": 429,
        "payment_errors": [402, 409],
        "server_error_range_start": 500,
        "server_error_range_end": 600,
        "error_message_max_length": 100
    },
    "streaming": {
        "progress_interval": 10,
        "playback_start_threshold": 3
    },
    "voices": {
        "provider_sample_voices_count": 5,
        "voice_list_max_display": 15,
        "voice_name_display_length": 25,
        "voice_name_truncation_offset": 18
    },
    "system": {
        "thread_pool_max_workers": 1,
        "memory_gb_conversion_factor": 1024
    },
    "api_keys": {}
}


class ConfigManager:
    """Manages configuration loading from TOML files and environment variables.
    
    Configuration precedence (highest to lowest):
    1. Environment variables (TTS_<SECTION>_<KEY>)
    2. Local config.toml file (current directory)
    3. User config.toml file (~/.config/tts/config.toml)
    4. Global config.toml file (/etc/tts/config.toml)
    5. Built-in defaults
    """
    
    def __init__(self):
        self._config = None
        self._config_paths = self._get_config_paths()
    
    def _get_config_paths(self) -> List[Path]:
        """Get list of configuration file paths in order of precedence."""
        paths = []
        
        # Local config file (highest precedence)
        paths.append(Path.cwd() / "config.toml")
        
        # User config file (XDG standard)
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            config_dir = Path(xdg_config) / "tts"
        else:
            config_dir = Path.home() / ".config" / "tts"
        paths.append(config_dir / "config.toml")
        
        # Global config file (lowest precedence)
        paths.append(Path("/etc/tts/config.toml"))
        
        return paths
    
    def _load_toml_file(self, path: Path) -> Dict[str, Any]:
        """Load TOML configuration from file."""
        if not path.exists() or not TOML_AVAILABLE:
            return {}
        
        try:
            # Always use binary mode for tomllib (Python 3.11+)
            with open(path, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            logger.warning(f"Failed to load TOML config from {path}: {e}")
            return {}
    
    def _get_env_value(self, section: str, key: str) -> Optional[Union[str, int, float, bool]]:
        """Get configuration value from environment variable."""
        env_key = f"TTS_{section.upper()}_{key.upper()}"
        env_value = os.environ.get(env_key)
        
        if env_value is None:
            return None
        
        # Try to parse as appropriate type
        if env_value.lower() in ('true', 'false'):
            return env_value.lower() == 'true'
        
        try:
            # Try integer first
            if '.' not in env_value:
                return int(env_value)
        except ValueError:
            pass
        
        try:
            # Try float
            return float(env_value)
        except ValueError:
            pass
        
        # Return as string
        return env_value
    
    def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries."""
        result = {}
        
        for config in configs:
            for section, values in config.items():
                if section not in result:
                    result[section] = {}
                
                if isinstance(values, dict):
                    result[section].update(values)
                else:
                    result[section] = values
        
        return result
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from all sources with proper precedence."""
        if self._config is not None:
            return self._config
        
        # Start with defaults
        config = DEFAULT_TOML_CONFIG.copy()
        
        # Load TOML files (reverse order for proper precedence)
        for path in reversed(self._config_paths):
            toml_config = self._load_toml_file(path)
            if toml_config:
                logger.debug(f"Loaded config from {path}")
                config = self._merge_configs(config, toml_config)
        
        # Apply environment variable overrides
        for section in config:
            if isinstance(config[section], dict):
                # Handle nested sections (e.g., providers.elevenlabs)
                for key in config[section]:
                    if isinstance(config[section][key], dict):
                        # This is a nested section like providers.elevenlabs
                        for nested_key in config[section][key]:
                            env_value = self._get_env_value(f"{section}_{key}", nested_key)
                            if env_value is not None:
                                config[section][key][nested_key] = env_value
                                logger.debug(f"Override from env: {section}.{key}.{nested_key} = {env_value}")
                    else:
                        # Regular key-value pair
                        env_value = self._get_env_value(section, key)
                        if env_value is not None:
                            config[section][key] = env_value
                            logger.debug(f"Override from env: {section}.{key} = {env_value}")
        
        self._config = config
        return config
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        config = self.load_config()
        return config.get(section, {}).get(key, default)
    
    def reload(self):
        """Reload configuration from files."""
        self._config = None


# Global configuration manager instance
_config_manager = ConfigManager()


class Config:
    """Dynamic configuration class that loads values from TOML and environment."""
    
    @classmethod
    def _get(cls, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback to default."""
        return _config_manager.get_value(section, key, default)
    
    # Network & Communication
    @property
    def CHATTERBOX_SERVER_PORT(self) -> int:
        return self._get("network", "chatterbox_server_port", 12345)
    
    @property
    def SOCKET_RECV_BUFFER_SIZE(self) -> int:
        return self._get("network", "socket_recv_buffer_size", 4096)
    
    @property
    def HTTP_STREAMING_CHUNK_SIZE(self) -> int:
        return self._get("network", "http_streaming_chunk_size", 1024)
    
    # Timeout Values
    @property
    def SERVER_STARTUP_TIMEOUT(self) -> int:
        return self._get("timeouts", "server_startup_timeout", 30)
    
    @property
    def SERVER_POLL_INTERVAL(self) -> int:
        return self._get("timeouts", "server_poll_interval", 1)
    
    @property
    def SOCKET_CONNECTION_TIMEOUT(self) -> int:
        return self._get("timeouts", "socket_connection_timeout", 1)
    
    @property
    def VOICE_LOADING_TIMEOUT(self) -> int:
        return self._get("timeouts", "voice_loading_timeout", 30)
    
    @property
    def AUDIO_CHECK_TIMEOUT(self) -> int:
        return self._get("timeouts", "audio_check_timeout", 2)
    
    @property
    def FFPROBE_TIMEOUT(self) -> int:
        return self._get("timeouts", "ffprobe_timeout", 5)
    
    @property
    def FFMPEG_VALIDATION_TIMEOUT(self) -> int:
        return self._get("timeouts", "ffmpeg_validation_timeout", 5)
    
    @property
    def FFPLAY_TIMEOUT(self) -> int:
        return self._get("timeouts", "ffplay_timeout", 5)
    
    @property
    def FFPLAY_TERMINATION_TIMEOUT(self) -> int:
        return self._get("timeouts", "ffplay_termination_timeout", 2)
    
    @property
    def FFMPEG_CONVERSION_TIMEOUT(self) -> int:
        return self._get("timeouts", "ffmpeg_conversion_timeout", 30)
    
    # User Interface
    @property
    def UI_DOUBLE_CLICK_TIME(self) -> float:
        return self._get("ui", "double_click_time", 0.8)
    
    @property
    def UI_FILTER_PANEL_WIDTH(self) -> int:
        return self._get("ui", "filter_panel_width", 20)
    
    @property
    def UI_PREVIEW_PANEL_WIDTH(self) -> int:
        return self._get("ui", "preview_panel_width", 18)
    
    @property
    def UI_STATUS_DISPLAY_TIME(self) -> int:
        return self._get("ui", "status_display_time", 1000)
    
    @property
    def UI_CLICK_FEEDBACK_TIME(self) -> int:
        return self._get("ui", "click_feedback_time", 500)
    
    @property
    def UI_SUCCESS_MESSAGE_TIME(self) -> int:
        return self._get("ui", "success_message_time", 1500)
    
    @property
    def UI_PAGE_SCROLL_AMOUNT(self) -> int:
        return self._get("ui", "page_scroll_amount", 10)
    
    @property
    def UI_PRINTABLE_CHAR_RANGE(self) -> Tuple[int, int]:
        start = self._get("ui", "printable_char_range_start", 32)
        end = self._get("ui", "printable_char_range_end", 126)
        return (start, end)
    
    # Audio Processing
    @property
    def AUDIO_16BIT_SCALE(self) -> int:
        return self._get("audio", "audio_16bit_scale", 32767)
    
    @property
    def AUDIO_AMPLITUDE_LIMIT(self) -> float:
        return self._get("audio", "audio_amplitude_limit", 0.95)
    
    @property
    def AUDIO_CHANNELS(self) -> int:
        return self._get("audio", "audio_channels", 1)
    
    @property
    def AUDIO_SAMPLE_WIDTH(self) -> int:
        return self._get("audio", "audio_sample_width", 2)
    
    @property
    def AUDIO_CARDS_MIN_SIZE(self) -> int:
        return self._get("audio", "audio_cards_min_size", 0)
    
    # Provider Defaults
    @property
    def ELEVENLABS_DEFAULT_STABILITY(self) -> float:
        return self._get("providers", "elevenlabs", {}).get("default_stability", 0.5)
    
    @property
    def ELEVENLABS_DEFAULT_SIMILARITY_BOOST(self) -> float:
        return self._get("providers", "elevenlabs", {}).get("default_similarity_boost", 0.5)
    
    @property
    def ELEVENLABS_DEFAULT_STYLE(self) -> float:
        return self._get("providers", "elevenlabs", {}).get("default_style", 0.0)
    
    @property
    def ELEVENLABS_VOICE_ID_LENGTH(self) -> int:
        return self._get("providers", "elevenlabs", {}).get("voice_id_length", 32)
    
    @property
    def ELEVENLABS_API_KEY_LENGTH(self) -> int:
        return self._get("providers", "elevenlabs", {}).get("api_key_length", 32)
    
    @property
    def GOOGLE_TTS_DEFAULT_SPEAKING_RATE(self) -> float:
        return self._get("providers", "google_tts", {}).get("default_speaking_rate", 1.0)
    
    @property
    def GOOGLE_TTS_DEFAULT_PITCH(self) -> float:
        return self._get("providers", "google_tts", {}).get("default_pitch", 0.0)
    
    @property
    def GOOGLE_API_KEY_LENGTH(self) -> int:
        return self._get("providers", "google_tts", {}).get("api_key_length", 39)
    
    @property
    def OAUTH_TOKEN_MIN_LENGTH(self) -> int:
        return self._get("providers", "google_tts", {}).get("oauth_token_min_length", 50)
    
    @property
    def SERVICE_ACCOUNT_JSON_MIN_LENGTH(self) -> int:
        return self._get("providers", "google_tts", {}).get("service_account_json_min_length", 100)
    
    @property
    def OPENAI_API_KEY_MIN_LENGTH(self) -> int:
        return self._get("providers", "openai", {}).get("api_key_min_length", 40)
    
    @property
    def CHATTERBOX_DEFAULT_EXAGGERATION(self) -> float:
        return self._get("providers", "chatterbox", {}).get("default_exaggeration", 0.5)
    
    @property
    def CHATTERBOX_DEFAULT_CFG_WEIGHT(self) -> float:
        return self._get("providers", "chatterbox", {}).get("default_cfg_weight", 0.5)
    
    @property
    def CHATTERBOX_DEFAULT_TEMPERATURE(self) -> float:
        return self._get("providers", "chatterbox", {}).get("default_temperature", 0.8)
    
    @property
    def CHATTERBOX_DEFAULT_MIN_P(self) -> float:
        return self._get("providers", "chatterbox", {}).get("default_min_p", 0.05)
    
    # HTTP Status Codes
    @property
    def HTTP_UNAUTHORIZED(self) -> int:
        return self._get("http", "unauthorized", 401)
    
    @property
    def HTTP_FORBIDDEN(self) -> int:
        return self._get("http", "forbidden", 403)
    
    @property
    def HTTP_RATE_LIMIT(self) -> int:
        return self._get("http", "rate_limit", 429)
    
    @property
    def HTTP_PAYMENT_ERRORS(self) -> Tuple[int, ...]:
        errors = self._get("http", "payment_errors", [402, 409])
        return tuple(errors) if isinstance(errors, list) else (402, 409)
    
    @property
    def HTTP_SERVER_ERROR_RANGE(self) -> Tuple[int, int]:
        start = self._get("http", "server_error_range_start", 500)
        end = self._get("http", "server_error_range_end", 600)
        return (start, end)
    
    @property
    def ERROR_MESSAGE_MAX_LENGTH(self) -> int:
        return self._get("http", "error_message_max_length", 100)
    
    # Streaming & Progress
    @property
    def STREAMING_PROGRESS_INTERVAL(self) -> int:
        return self._get("streaming", "progress_interval", 10)
    
    @property
    def STREAMING_PLAYBACK_START_THRESHOLD(self) -> int:
        return self._get("streaming", "playback_start_threshold", 3)
    
    # Voice & Sample Management
    @property
    def PROVIDER_SAMPLE_VOICES_COUNT(self) -> int:
        return self._get("voices", "provider_sample_voices_count", 5)
    
    @property
    def VOICE_LIST_MAX_DISPLAY(self) -> int:
        return self._get("voices", "voice_list_max_display", 15)
    
    @property
    def VOICE_NAME_DISPLAY_LENGTH(self) -> int:
        return self._get("voices", "voice_name_display_length", 25)
    
    @property
    def VOICE_NAME_TRUNCATION_OFFSET(self) -> int:
        return self._get("voices", "voice_name_truncation_offset", 18)
    
    # System Resources
    @property
    def THREAD_POOL_MAX_WORKERS(self) -> int:
        return self._get("system", "thread_pool_max_workers", 1)
    
    @property
    def MEMORY_GB_CONVERSION_FACTOR(self) -> int:
        return self._get("system", "memory_gb_conversion_factor", 1024)


# Create singleton instance that will be imported by other modules
Config = Config()


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
        return api_key.startswith("sk-") and len(api_key) >= Config.OPENAI_API_KEY_MIN_LENGTH
    
    elif provider == "google":
        # Google API keys are 39 chars, start with AIza or can be OAuth token
        return (api_key.startswith("AIza") and len(api_key) == Config.GOOGLE_API_KEY_LENGTH) or \
               (api_key.startswith("ya29.") and len(api_key) > Config.OAUTH_TOKEN_MIN_LENGTH) or \
               len(api_key) > Config.SERVICE_ACCOUNT_JSON_MIN_LENGTH  # Service account JSON string
    
    elif provider == "elevenlabs":
        # ElevenLabs keys are 32 char hex strings
        return len(api_key) == Config.ELEVENLABS_API_KEY_LENGTH and all(c in '0123456789abcdef' for c in api_key.lower())
    
    else:
        # Unknown provider, assume valid if non-empty
        return len(api_key.strip()) > 0


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider, checking TOML config, JSON config, and environment.
    
    Search order:
    1. Environment variables (PROVIDER_API_KEY)
    2. TOML configuration (api_keys.provider_api_key)
    3. Legacy JSON configuration (provider_api_key)
    
    Args:
        provider: Provider name (e.g., 'elevenlabs', 'openai', 'google')
        
    Returns:
        API key string if found and valid, None otherwise
    """
    # Check TOML configuration first
    toml_api_key = _config_manager.get_value("api_keys", f"{provider}_api_key")
    if toml_api_key and validate_api_key(provider, toml_api_key):
        return toml_api_key
    
    # Check legacy JSON config
    config_key = f"{provider}_api_key"
    json_api_key = get_setting(config_key)
    if json_api_key and validate_api_key(provider, json_api_key):
        return json_api_key
    
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