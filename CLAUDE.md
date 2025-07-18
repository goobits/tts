# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TTS CLI is a Python text-to-speech command-line tool that supports multiple TTS providers with smart auto-selection and voice cloning capabilities. The project uses a pluggable provider architecture to support:

- **Edge TTS** (Microsoft Azure): Free, high-quality neural voices  
- **Chatterbox**: Local voice cloning with GPU/CPU support
- **OpenAI TTS**: API-based synthesis with premium voices
- **Google Cloud TTS**: Google's neural voices via REST API
- **ElevenLabs**: Advanced voice synthesis and cloning

## Installation & Development Setup

**Use the setup script for installation**:

```bash
# Production install
./setup.sh install

# Development install (editable) - USE THIS FOR DEVELOPMENT  
./setup.sh install --dev

# Uninstall
./setup.sh uninstall
```

## Common Development Commands

**Testing:**
```bash
./test.sh               # Main test runner with coverage
python -m pytest tests/ -v    # Direct pytest execution
```

**Code Quality:**
```bash
black .                  # Format code (line-length 100)
ruff check .            # Lint code 
mypy tts_cli/           # Type checking
```

**Building:**
```bash
python -m build         # Build package
make build              # Alternative build command
```

## Architecture Overview

### Core Components

1. **tts_cli/tts.py** - Main CLI entry point with Click commands
2. **tts_cli/base.py** - Abstract `TTSProvider` base class
3. **tts_cli/config.py** - Configuration management with XDG compliance
4. **tts_cli/voice_manager.py** - Voice loading/caching for fast access
5. **tts_cli/providers/** - Provider implementations

### Provider Architecture

All providers inherit from `TTSProvider` and implement:
- `synthesize(text, output_path, **kwargs)` - Core synthesis method
- `get_info()` - Returns provider capabilities and sample voices

Provider loading is dynamic via the `PROVIDERS` dict in `tts.py:21-27`.

### Configuration System

- Default config in `config.py:11-19`
- XDG-compliant paths (`~/.config/tts/config.json`)
- Voice format: `provider:voice_name` (e.g., `edge_tts:en-IE-EmilyNeural`)
- Auto-detection of providers from voice strings in `parse_voice_setting()`

### Key CLI Commands

**Package name:** `goobits-tts` (installs as `tts` command)

**IMPORTANT: Always use the setup script for installation:**
```bash
./setup.sh install           # Install the package
```

```bash
tts "text"                    # Stream audio (default)
tts "text" --save             # Save to file
tts voices                    # Interactive voice browser
tts config                    # Show/edit configuration  
tts doctor                    # System health check
tts load voice.wav            # Preload voice for fast access
tts install chatterbox gpu    # Install provider dependencies
```

## Code Style & Standards

- **Line length**: 100 characters (Black + Ruff configured)
- **Type hints**: Required for all functions (`mypy` enforced)
- **Error handling**: Use custom exceptions from `exceptions.py`
- **Logging**: Structured logging to `logs/tts.log` + console

## Key Implementation Details

### Real-time Streaming
The CLI defaults to streaming audio directly to speakers. Providers should support `stream=true` in kwargs to enable this.

### Voice Cloning (Chatterbox)
Voice files can be loaded into memory for fast synthesis:
```python
voice_manager = VoiceManager()
voice_manager.load_voice("/path/to/voice.wav")  # Pre-load for speed
```

### Interactive Voice Browser
Advanced curses-based interface in `tts_cli/tts.py` with:
- Three-panel layout (filters, voices, preview)
- Mouse and keyboard navigation
- Real-time voice preview with background audio playback
- Quality analysis and metadata extraction

### Provider Installation
The `tts install` command handles complex dependency management, especially for Chatterbox which requires PyTorch with optional GPU support.

## Testing Notes

- Tests are in `tests/` directory
- Provider-specific tests check availability before running
- Use `pytest -v` for verbose output
- Mock external dependencies for unit tests

## Recent Features

- Real-time streaming support (OpenAI, ElevenLabs) 
- Enhanced curses voice browser with three-panel layout
- Dual authentication for Google Cloud TTS (API key + service account)
- Voice loading/caching system for performance
- Interactive configuration editor

## Important Files to Understand

- `tts_cli/tts.py` - Main CLI entry point with provider registry
- `tts_cli/config.py` - Configuration management with voice parsing logic  
- `tts_cli/voice_browser.py` - Interactive voice browser implementation
- `tts_cli/providers/` - Provider implementations (Edge TTS, Chatterbox, etc.)
- `setup.sh` - Installation script (use this for all installs)
- `pyproject.toml` - Package configuration and dependencies

### Temporary Files
When creating temporary debug or test scripts, use `/tmp` directory to keep the project clean.