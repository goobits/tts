# TTS CLI Configuration Guide

TTS CLI now supports flexible configuration through TOML files and environment variables, allowing you to customize settings without modifying source code.

## Configuration Sources

Configuration is loaded from multiple sources in this order (highest to lowest precedence):

1. **Environment Variables** (TTS_`<SECTION>`_`<KEY>`)
2. **Local config.toml** (current directory)
3. **User config.toml** (~/.config/tts/config.toml)
4. **Global config.toml** (/etc/tts/config.toml)
5. **Built-in defaults**

## TOML Configuration Format

Create a `config.toml` file with the following structure:

```toml
# Basic application settings
[general]
version = "1.0"
default_action = "stream"  # Options: "stream", "save"
log_level = "info"         # Options: "debug", "info", "warning", "error"
output_dir = "~/Downloads"

# Default voice settings
[voice]
default_voice = "edge_tts:en-IE-EmilyNeural"
default_rate = "+0%"
default_pitch = "+0Hz"

# Network and server settings
[network]
chatterbox_server_port = 12345
socket_recv_buffer_size = 4096
http_streaming_chunk_size = 1024

# Timeout values (in seconds)
[timeouts]
server_startup_timeout = 30
ffplay_timeout = 5
ffmpeg_conversion_timeout = 30

# User interface settings
[ui]
double_click_time = 0.8
filter_panel_width = 20
preview_panel_width = 18
page_scroll_amount = 10

# Audio processing settings
[audio]
audio_16bit_scale = 32767
audio_amplitude_limit = 0.95
audio_channels = 1
audio_sample_width = 2

# Provider-specific settings
[providers.elevenlabs]
default_stability = 0.5
default_similarity_boost = 0.5
default_style = 0.0
voice_id_length = 32
api_key_length = 32

[providers.google_tts]
default_speaking_rate = 1.0
default_pitch = 0.0
api_key_length = 39

[providers.openai]
api_key_min_length = 40

[providers.chatterbox]
default_exaggeration = 0.5
default_temperature = 0.8

# HTTP and error handling
[http]
unauthorized = 401
forbidden = 403
rate_limit = 429
payment_errors = [402, 409]
error_message_max_length = 100

# Streaming settings
[streaming]
progress_interval = 10
playback_start_threshold = 3

# Voice management
[voices]
provider_sample_voices_count = 5
voice_list_max_display = 15

# System resources
[system]
thread_pool_max_workers = 1
memory_gb_conversion_factor = 1024

# API keys (optional - can also use environment variables)
[api_keys]
# elevenlabs_api_key = "your_key_here"
# openai_api_key = "sk-your_key_here"
# google_api_key = "your_key_here"
```

## Environment Variable Overrides

Any configuration value can be overridden using environment variables with the format `TTS_<SECTION>_<KEY>`:

### Basic Settings
```bash
export TTS_NETWORK_CHATTERBOX_SERVER_PORT=8080
export TTS_TIMEOUTS_FFPLAY_TIMEOUT=10
export TTS_UI_FILTER_PANEL_WIDTH=25
```

### Provider Settings
```bash
export TTS_PROVIDERS_ELEVENLABS_DEFAULT_STABILITY=0.8
export TTS_PROVIDERS_GOOGLE_TTS_DEFAULT_SPEAKING_RATE=1.2
export TTS_PROVIDERS_OPENAI_API_KEY_MIN_LENGTH=50
```

### API Keys
```bash
export ELEVENLABS_API_KEY=your_elevenlabs_key
export OPENAI_API_KEY=sk-your_openai_key
export GOOGLE_API_KEY=your_google_key
```

## Common Use Cases

### Development Environment
```toml
[general]
log_level = "debug"

[timeouts]
ffplay_timeout = 15  # Longer for debugging
server_startup_timeout = 60

[providers.elevenlabs]
default_stability = 0.3  # More dynamic for testing
```

### Production Deployment
```toml
[general]
log_level = "warning"

[network]
chatterbox_server_port = 8080  # Production port

[timeouts]
server_startup_timeout = 120   # Allow more time for startup

[providers.elevenlabs]
default_stability = 0.8        # More stable for production
```

### Docker/Container Deployment
Use environment variables for dynamic configuration:
```bash
docker run -e TTS_NETWORK_CHATTERBOX_SERVER_PORT=8080 \
           -e TTS_GENERAL_LOG_LEVEL=info \
           -e ELEVENLABS_API_KEY=your_key \
           tts-cli
```

## Configuration File Locations

### User Configuration
Place your personal config at:
- Linux/macOS: `~/.config/tts/config.toml`
- Windows: `%APPDATA%/tts/config.toml`

### Project Configuration
Place a `config.toml` file in your project directory for project-specific settings.

### Global Configuration
System administrators can place global defaults at:
- Linux/macOS: `/etc/tts/config.toml`

## Migration from Hardcoded Values

The new TOML system is fully backwards compatible. Existing code will continue to work, but you can now override any setting:

**Before (hardcoded):**
```python
CHATTERBOX_SERVER_PORT = 12345  # Fixed value
```

**After (configurable):**
```toml
[network]
chatterbox_server_port = 12345  # Can be overridden
```

**Environment override:**
```bash
export TTS_NETWORK_CHATTERBOX_SERVER_PORT=8080
```

## Validation

The system automatically validates configuration values:
- Type checking (string, integer, float, boolean)
- Range validation where applicable
- API key format validation
- Fallback to defaults for invalid values

## Troubleshooting

### Debug Configuration Loading
Set debug logging to see configuration loading:
```bash
export TTS_GENERAL_LOG_LEVEL=debug
```

### Check Current Configuration
The system will log which configuration files are loaded and which environment variables are applied.

### Precedence Issues
Remember the precedence order:
1. Environment variables (highest)
2. Local config.toml
3. User config.toml
4. Global config.toml
5. Built-in defaults (lowest)

If a setting isn't taking effect, check if it's being overridden by a higher-precedence source.