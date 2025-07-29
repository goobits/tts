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
- [Voice Discovery & Provider Management](#-voice-discovery--provider-management)
- [Voice Loading (Performance)](#-voice-loading-performance)
- [Voice Cloning Workflow](#-voice-cloning-workflow)
- [System Management](#-system-management)
- [Supported Engines](#-supported-engines)
- [Tech Stack & Architecture](#️-tech-stack--architecture)
- [Recent Improvements](#-recent-improvements)
- [Development](#-development)


## 📦 Installation

```bash
# Install from local source
git clone https://github.com/goobits/tts
cd tts
./setup.sh install         # Automatically handles all dependencies

# Verify installation
tts status                  # Check system health
```

## 🎯 Basic Usage

```bash
# Direct synthesis (streams to speakers by default)
tts "Hello world"                    # Stream with default voice
tts Hello world                      # Unquoted text works too
echo "Hello world" | tts             # Pipe input support

# Provider shortcuts for quick access
tts @edge "Hello world"              # Edge TTS (free, 300+ voices)
tts @openai "Hello world"            # OpenAI TTS (premium quality)
tts @elevenlabs "Hello world"        # ElevenLabs (voice cloning)
tts @google "Hello world"            # Google Cloud TTS
tts @chatterbox "Hello world"        # Local voice cloning

# Save to file
tts save "Hello world"               # Save to audio file
tts save @edge "Hello" -o speech.mp3 # Save with specific provider
```

## ⚙️ Configuration

TTS CLI now features an enhanced configuration display with organized sections:

```bash
tts config show                      # Rich display with emoji sections
tts config set openai_api_key YOUR_KEY   # Set API keys
tts config set voice en-IE-EmilyNeural   # Set default voice
tts config get voice                 # Get specific setting value
tts config edit                      # Interactive editor

# Enhanced config display shows:
# 🔑 API Keys: Status of all provider API keys
# 🎤 Defaults: Provider, voice, output format
# 🎛️ Audio Settings: Rate, pitch, streaming
# 💾 Paths: Config, cache, and log locations
# 💡 Tips: Quick help and usage examples
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

## 🎤 Voice Discovery & Provider Management

TTS CLI features an enhanced providers system with visual status indicators:

```bash
# Enhanced providers command with emoji status
tts providers                        # Rich display of all providers with status
tts providers @openai                # Setup instructions for specific provider
tts providers edge_tts               # Setup instructions using full name

# Traditional voice browsing
tts voices                           # Interactive voice browser
tts info                             # Show all providers and capabilities
tts info @edge                       # Detailed info for specific provider

# Quick status check
tts status                           # System health with provider status
tts version                          # Show version with suite branding
```

**Enhanced Provider Display:**
- 🏢 Visual provider listing with emojis
- ✅ ⚠️ ❌ Status indicators (Ready/API Key Required/Not Configured)
- 🔗 Provider shortcuts (@edge, @openai, etc.)
- 📋 Voice counts and capabilities
- 💡 Setup instructions with examples

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
tts status                           # Check system health
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
- **Automatic dependency management** via goobits extras
- **Automated setup scripts** with comprehensive dependency installation

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

## 🔗 Pipeline Integration

TTS CLI is designed to work seamlessly with other Goobits Audio Suite tools:

```bash
# Basic pipeline operations
echo "Hello world" | tts                     # Simple text-to-speech
cat document.txt | tts @edge                 # File input with provider

# Integration with TTT (Text-to-Text)
ttt "Fix grammar" < essay.txt | tts          # Fix grammar then speak
ttt "Summarize in 3 bullets" < report.md | tts @openai  # Summarize and speak

# Integration with STT (Speech-to-Text)  
stt recording.wav | tts @edge                # Transcribe and re-speak
stt meeting.mp3 | ttt "extract action items" | tts  # Meeting → actions → speech

# Advanced workflows
stt input.wav | ttt "translate to Spanish" | tts @google  # Translate pipeline
cat story.txt | ttt "simplify for kids" | tts @elevenlabs  # Accessibility
```

**Pipeline Features:**
- 🔄 **Seamless piping**: Works naturally with Unix pipes
- 🎯 **Provider selection**: Use shortcuts in any pipeline stage  
- 📝 **Text processing**: Perfect integration with TTT transformations
- 🎤 **Voice selection**: Automatic provider detection and voice selection
- ⚡ **Performance**: Optimized for real-time pipeline processing

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
mypy src/tts/               # Type checking
```

### Building
```bash
python -m build             # Build package
```

## 📄 License

MIT License - see LICENSE file for details.