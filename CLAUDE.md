# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TTS CLI is a Python text-to-speech command-line tool that supports multiple TTS providers with smart auto-selection, voice cloning capabilities, and intelligent document processing. The project uses a pluggable provider architecture to support:

- **Edge TTS** (Microsoft Azure): Free, high-quality neural voices  
- **Chatterbox**: Local voice cloning with GPU/CPU support
- **OpenAI TTS**: API-based synthesis with premium voices
- **Google Cloud TTS**: Google's neural voices via REST API
- **ElevenLabs**: Advanced voice synthesis and cloning

Additionally, TTS CLI now includes advanced document-to-speech capabilities:
- **Multi-format support**: HTML, JSON, Markdown auto-conversion
- **Emotion detection**: Context-aware emotion profiles (technical, marketing, narrative, tutorial)
- **SSML generation**: Platform-optimized speech synthesis markup (Azure, Google, Amazon)
- **Performance caching**: Optimized document processing for repeated conversions

## Installation & Development Setup

**Use the setup script for installation**:

```bash
# Production install (for end users)
./setup.sh install

# Development install (editable) - RECOMMENDED FOR DEVELOPMENT  
./setup.sh install --dev

# Upgrade to latest version
./setup.sh upgrade

# Uninstall
./setup.sh uninstall
```

**IMPORTANT FOR DEVELOPMENT**: Always use `./setup.sh install --dev` for development work. This creates an editable installation where code changes are immediately reflected without needing to reinstall or upgrade.

## Common Development Commands

**Testing:**
```bash
./test.sh               # Main test runner with coverage
python -m pytest tests/ -v    # Direct pytest execution
```

**Code Quality:**
```bash
ruff check .                                              # Lint code 
ruff check . --fix                                        # Auto-fix linting issues
black .                                                   # Format code (line-length 100)
mypy tts_cli/                                            # Type checking
```

**Note:** If tools are installed via pipx, use the full path:
```bash
~/.local/share/pipx/venvs/goobits-tts/bin/ruff check .    # Lint code
~/.local/share/pipx/venvs/goobits-tts/bin/black .         # Format code  
~/.local/share/pipx/venvs/goobits-tts/bin/mypy tts_cli/   # Type checking
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
6. **tts_cli/document_processing/** - Document parsing (HTML, JSON, Markdown)
7. **tts_cli/speech_synthesis/** - Emotion detection and SSML generation

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
tts save "text"               # Save to file
tts voices                    # Interactive voice browser
tts config                    # Show/edit configuration  
tts doctor                    # System health check
tts voice load voice.wav      # Preload voice for fast access
tts install chatterbox gpu    # Install provider dependencies

# Document processing commands
tts document report.html           # Convert HTML to speech
tts document api.json --emotion-profile technical --save
tts document README.md --ssml-platform azure
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
- Document-to-speech processing with emotion detection
- Multi-format document support (HTML, JSON, Markdown)
- Platform-specific SSML generation (Azure, Google, Amazon)
- Context-aware emotion profiles for different document types

## Important Files to Understand

- `tts_cli/tts.py` - Main CLI entry point with provider registry
- `tts_cli/config.py` - Configuration management with voice parsing logic  
- `tts_cli/voice_browser.py` - Interactive voice browser implementation
- `tts_cli/providers/` - Provider implementations (Edge TTS, Chatterbox, etc.)
- `setup.sh` - Installation script (use this for all installs)
- `pyproject.toml` - Package configuration and dependencies

### Temporary Files
When creating temporary debug or test scripts, use `/tmp` directory to keep the project clean.