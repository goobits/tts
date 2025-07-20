# 🗣️ Goobits TTS

A modern command-line text-to-speech tool with pluggable provider architecture, real-time streaming, voice cloning capabilities, and intelligent document processing. Features smart auto-selection, interactive voice browser, comprehensive configuration management, and advanced document-to-speech conversion with emotion detection and SSML generation.

## 🔗 Related Projects

This project is part of the Goobits ecosystem:

- **[Matilda](https://github.com/goobits/matilda)** - AI assistant for conversational interactions
- **[Goobits STT](https://github.com/goobits/stt)** - Speech-to-Text engine with real-time transcription
- **[Goobits TTS](https://github.com/goobits/tts)** - Text-to-Speech engine (this project)
- **[Goobits TTT](https://github.com/goobits/ttt)** - Text-to-Text processing and transformation tools

## 📋 Table of Contents

- [Installation](#-installation)
- [Basic Usage](#-basic-usage)
- [Document Processing](#-document-processing)
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
# pipx install goobits-tts  # TODO: Will be available when published

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
# New recommended syntax
tts "Hello world"                    # Stream with default voice
tts save "Hello world"               # Save to file
tts @edge "Hello world"              # Use Edge TTS provider
tts @openai "Hello world" --voice nova  # OpenAI with specific voice

# Provider shortcuts (recommended)
tts @edge "text"                     # Edge TTS
tts @openai "text"                   # OpenAI TTS
tts @elevenlabs "text"               # ElevenLabs
tts @google "text"                   # Google TTS
tts @chatterbox "text"               # Voice cloning
```

## ⚙️ Configuration

```bash
tts config                           # Show current settings
tts config voice en-IE-EmilyNeural  # Set default voice
tts config default_action save   # Save files by default
tts config edit                      # Interactive editor
```

## 📄 Document Processing

Convert documents to natural-sounding speech with intelligent formatting:

```bash
# New recommended syntax
tts document report.html             # Convert HTML to speech
tts document README.md --save        # Save markdown as audio file
tts document api.json @edge          # Use specific provider

# Advanced features  
tts document manual.pdf --emotion-profile technical
tts document story.html --emotion-profile narrative
tts document tutorial.md --emotion-profile tutorial

# Platform-specific SSML
tts document doc.html --ssml-platform azure    # Azure-optimized
tts document doc.html --ssml-platform google   # Google Cloud TTS
tts document doc.html --ssml-platform amazon   # Amazon Polly

# Auto-detection
tts document file.html --doc-format auto       # Auto-detect format
```

**Features:**
- 🎯 Multi-format support: HTML, JSON, Markdown
- 🎭 Context-aware emotion detection
- 🔊 Platform-optimized SSML generation
- ⚡ Performance caching for repeated conversions
- 🧠 Intelligent pause insertion and emphasis

## 🎤 Voice Discovery

```bash
tts voices                           # Interactive voice browser
tts models edge_tts                  # List voices for specific provider
tts voices en-GB                     # Filter by language/region
tts models                           # List providers and capabilities
```

## 🚀 Voice Loading (Performance)

```bash
# New recommended syntax
tts voice load voice.wav voice2.wav  # Load voices into memory
tts voice status                     # Show loaded voices and system status
tts voice unload voice.wav           # Remove specific voice from memory
tts voice unload all                 # Remove all voices
```

**Performance:** First call 13s (loading), subsequent calls <1s (cached).

## 🎭 Voice Cloning Workflow

```bash
# 1. Record your voice
arecord -f cd -t wav -d 30 ~/my_voice.wav

# 2. Load for fast access
tts voice load ~/my_voice.wav

# 3. Use instantly
tts @chatterbox "This sounds like me!" --clone ~/my_voice.wav
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

### Document Processing Features (NEW)
- **Intelligent document-to-speech**: Convert HTML, JSON, and Markdown to natural speech
- **Context-aware emotion detection**: Automatic emotion profiles for different document types
- **Platform-specific SSML**: Optimized output for Azure, Google, and Amazon TTS platforms
- **Markdown-first architecture**: 42% code reduction with unified processing pipeline

### Code Quality Enhancements
- **Eliminated code duplication**: Extracted shared audio utilities (~120 lines saved)
- **Complete type coverage**: Added comprehensive type hints and TypedDict definitions
- **Standardized error handling**: Unified patterns across all providers
- **Improved maintainability**: Centralized common operations

### Performance Optimizations
- **Shared audio utilities**: Consistent ffplay process management
- **Voice caching system**: Fast repeated access to loaded voices
- **Chunked streaming**: Real-time audio with minimal latency
- **Document caching**: Optimized repeated document conversions
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