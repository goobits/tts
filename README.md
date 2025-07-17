# 🗣️ Goobits TTS

A modern command-line text-to-speech tool with pluggable provider architecture, real-time streaming, and voice cloning capabilities. Features smart auto-selection, interactive voice browser, and comprehensive configuration management with support for multiple TTS providers.

## 🔗 Related Projects

This project is part of the Goobits ecosystem:

- **[Goobits TTS](https://github.com/goobits/tts)** - Text-to-Speech engine (this project)
- **[Goobits STT](https://github.com/goobits/stt)** - Speech-to-Text engine with real-time transcription
- **[Goobits TTT](https://github.com/goobits/ttt)** - Text-to-Text processing and transformation tools
- **[Matilda](https://github.com/goobits/matilda)** - AI assistant for conversational interactions

## 📋 Table of Contents

- [Installation](#-installation)
- [Basic Usage](#-basic-usage)
- [Configuration](#️-configuration)
- [Voice Discovery](#-voice-discovery)
- [Voice Loading (Performance)](#-voice-loading-performance)
- [Voice Cloning Workflow](#-voice-cloning-workflow)
- [System Management](#-system-management)
- [Supported Engines](#-supported-engines)
- [Tech Stack & Architecture](#️-tech-stack--architecture)
- [Recent Improvements](#-recent-improvements)
- [Development](#-development)


## 📦 Installation

**⚠️ Important: Always use pipx for installation, never pip directly:**

```bash
# Install from source (currently only option)
# pipx install goobits-tts-cli  # TODO: Will be available when published

# Install from local source
git clone https://github.com/goobits/tts
cd tts
./setup.sh install         # Uses pipx automatically

# Verify installation
tts doctor                  # Check system health
tts install chatterbox gpu  # Add voice cloning (optional)
```

## 🎯 Basic Usage

```bash
tts "Hello world"                    # Stream with default voice
tts "Hello world" --save             # Save to file instead
tts "Hello world" --voice en-IE-EmilyNeural  # Use specific voice
tts "Hello world" --voice voice.wav  # Voice cloning
```

## ⚙️ Configuration

```bash
tts config                           # Show current settings
tts config voice en-IE-EmilyNeural  # Set default voice
tts config default_action save   # Save files by default
tts config edit                      # Interactive editor
```

## 🎤 Voice Discovery

```bash
tts voices                           # Interactive voice browser
tts models edge_tts                  # List voices for specific provider
tts voices en-GB                     # Filter by language/region
tts models                           # List providers and capabilities
```

## 🚀 Voice Loading (Performance)

```bash
tts load voice.wav voice2.wav        # Load voices into memory
tts status                           # Show loaded voices and system status
tts unload voice.wav                 # Remove specific voice from memory
tts unload all                       # Remove all voices
```

**Performance:** First call 13s (loading), subsequent calls <1s (cached).

## 🎭 Voice Cloning Workflow

```bash
# 1. Record your voice
arecord -f cd -t wav -d 30 ~/my_voice.wav

# 2. Load for fast access
tts load ~/my_voice.wav

# 3. Use instantly
tts "This sounds like me!" --voice ~/my_voice.wav
```

## 🔧 System Management

```bash
tts doctor                           # Check system health
tts install chatterbox gpu           # Install provider with GPU support
```

## 🎯 Supported Engines

| Engine | Speed | Quality | Offline | Voice Cloning | API Required |
|--------|-------|---------|---------|---------------|--------------|
| **Edge TTS** | ⚡ Instant | 🌟 Excellent | ❌ No | ❌ No | ❌ No |
| **Chatterbox** | 🔥 Fast | 🏆 Best-in-class | ✅ Yes | ✅ Yes | ❌ No |
| **OpenAI TTS** | ⚡ Fast | 🌟 Excellent | ❌ No | ❌ No | ✅ Yes |
| **Google Cloud TTS** | ⚡ Fast | 🌟 Excellent | ❌ No | ❌ No | ✅ Yes |
| **ElevenLabs** | 🔥 Fast | 🏆 Premium | ❌ No | ✅ Yes | ✅ Yes |

Choose from free offline options or premium cloud services based on your needs.

## 🛠️ Tech Stack & Architecture

### Core Framework
- **Python 3.8+** with Click CLI framework
- **Pluggable provider architecture** with dynamic loading
- **Type-safe codebase** with comprehensive TypedDict definitions
- **Shared utilities** for audio processing and error handling

### Audio Processing
- **FFmpeg/FFplay** for format conversion and real-time streaming
- **Chunked streaming** with configurable buffer sizes
- **Multiple audio formats** (MP3, WAV, OGG, FLAC)
- **Automatic format detection** and conversion

### TTS Providers
- **Edge TTS**: Microsoft Azure Neural Voices (free, 400+ voices)
- **Chatterbox**: PyTorch voice cloning (local, GPU/CPU)
- **OpenAI TTS**: Premium API with 6 high-quality voices
- **Google Cloud TTS**: Neural voices with dual authentication
- **ElevenLabs**: Advanced voice synthesis and cloning

### Configuration & Storage
- **XDG-compliant** paths (`~/.config/tts/`)
- **JSON** configuration with validation
- **Environment variable** support
- **API key management** with secure storage

### Development Quality
- **Comprehensive type hints** with mypy enforcement
- **Code formatting** with Black (100-char line length)
- **Linting** with Ruff
- **No code duplication** - shared utilities pattern
- **Comprehensive error handling** with custom exception hierarchy

### Installation & Dependencies
- **pipx isolation** for clean package management
- **Optional dependencies** per provider
- **Automated setup scripts** with dependency checking

## 🚀 Recent Improvements

### Code Quality Enhancements
- **Eliminated code duplication**: Extracted shared audio utilities (~120 lines saved)
- **Complete type coverage**: Added comprehensive type hints and TypedDict definitions
- **Standardized error handling**: Unified patterns across all providers
- **Improved maintainability**: Centralized common operations

### Performance Optimizations
- **Shared audio utilities**: Consistent ffplay process management
- **Voice caching system**: Fast repeated access to loaded voices
- **Chunked streaming**: Real-time audio with minimal latency
- **Optimized provider loading**: Dynamic imports with error recovery

## 🧪 Development

### Running Tests
```bash
./test.sh                   # Main test runner
python -m pytest tests/ -v  # Direct pytest execution
```

### Code Quality
```bash
black .                      # Format code (line-length 100)
ruff check .                 # Lint code 
mypy tts_cli/               # Type checking
```

### Building
```bash
python -m build             # Build package
```

## 📄 License

MIT License - see LICENSE file for details.