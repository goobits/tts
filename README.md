# 🎵 Goobits TTS

A comprehensive text-to-speech command-line tool with multiple provider support, voice cloning capabilities, and intelligent document processing. Features real-time streaming, interactive voice browsing, and advanced emotion detection for natural-sounding speech synthesis across various providers and use cases.

## 🔗 Related Projects

- **[Matilda](https://github.com/goobits/matilda)** - AI assistant
- **[Goobits STT](https://github.com/goobits/stt)** - Speech-to-Text engine
- **[Goobits TTS](https://github.com/goobits/tts)** - Text-to-Speech engine (this project)
- **[Goobits TTT](https://github.com/goobits/ttt)** - Text-to-Text processing

## 📋 Table of Contents

- [Installation](#-installation)
- [Basic Usage](#-basic-usage)
- [Configuration](#️-configuration)
- [Provider Support](#-provider-support)
- [Voice Management](#-voice-management)
- [Document Processing](#-document-processing)
- [Audio Features](#️-audio-features)
- [Testing & Development](#-testing--development)
- [Provider Comparison](#-provider-comparison)
- [Advanced Features](#-advanced-features)
- [Tech Stack](#️-tech-stack)

## 📦 Installation

```bash
# Use the setup script (recommended)
./setup.sh install                # Install from PyPI with all dependencies
./setup.sh install --dev          # Install in development mode (editable)

# Or manually with pipx/pip
pipx install goobits-tts[all]     # Install globally with all providers
pip install -e .[dev]             # Install editable with dev tools
tts --version                      # Verify installation
tts "Hello world"                  # Test basic functionality
```

## 🎯 Basic Usage

```bash
tts "Hello world"                  # Stream audio (default behavior)
tts save "Hello world"             # Save to file
tts @edge "Hello world"            # Use specific provider
echo "Hello world" | tts           # Pipe input support
tts voices                         # Interactive voice browser
```

## ⚙️ Configuration

```bash
# Edit main configuration
tts config edit

# Set API keys
tts config set openai_api_key YOUR_KEY
tts config set elevenlabs_api_key YOUR_KEY

# View current settings
tts config show

# Provider status
tts providers                      # Enhanced provider display
tts providers @openai              # Provider-specific setup
```

## 🎤 Provider Support

```bash
# Provider shortcuts
tts @edge "Hello world"            # Edge TTS (free)
tts @openai "Hello world"          # OpenAI TTS
tts @elevenlabs "Hello world"      # ElevenLabs
tts @google "Hello world"          # Google Cloud TTS
tts @chatterbox "Hello world"      # Local voice cloning

# Save with specific provider
tts save @edge "text" -o audio.mp3
tts save @openai "text" --format wav

# System status
tts status                         # System health check
tts providers                      # Provider availability
```

## 🗣️ Voice Management

```bash
# Interactive voice browser
tts voices                         # Browse and preview voices

# Voice loading (Chatterbox)
tts voice load voice.wav           # Preload voice for fast access
tts voice status                   # Show loaded voices

# Voice specification
tts @edge "text" --voice en-US-AriaNeural
tts @openai "text" --voice alloy
```

## 📄 Document Processing

```bash
# Multi-format support
tts document report.html           # Convert HTML to speech
tts document api.json              # Process JSON data
tts document README.md             # Markdown conversion

# Advanced document options
tts document report.html --emotion-profile technical
tts document story.md --emotion-profile narrative
tts document guide.md --emotion-profile tutorial

# SSML generation
tts document content.html --ssml-platform azure
tts document content.html --ssml-platform google --save
```

## 🎵 Audio Features

- **Real-time streaming**: Direct audio playback to speakers with minimal latency
- **Multiple formats**: MP3, WAV, OGG support with automatic conversion
- **Voice cloning**: Local voice synthesis with Chatterbox integration
- **Background playback**: Non-blocking audio with concurrent processing
- **Quality control**: Configurable bitrates and sample rates

## 🧪 Testing & Development

```bash
# Run test suite (recommended)
./test.sh                          # Main test runner with coverage
python -m pytest tests/ -v        # Direct pytest execution

# Specific test categories
pytest tests/unit/ -v              # Pure unit tests
pytest tests/integration/ -v       # Integration tests
pytest tests/e2e/ -v               # End-to-end workflows

# Code quality
ruff check .                       # Linting
ruff check . --fix                 # Auto-fix issues
black .                           # Code formatting
mypy src/tts/                     # Type checking

# Quick CLI validation
python test_cli.py                 # CLI smoke test
```

## 🔧 Provider Comparison

| Provider | Cost | Quality | Speed | Voice Cloning | Best For |
|----------|------|---------|-------|---------------|----------|
| **Edge TTS** | 🆓 Free | 🌟🌟🌟 Good | ⚡ Fast | ❌ No | General use, development |
| **OpenAI TTS** | 💰 Paid | 🌟🌟🌟🌟 Great | 🔥 Very Fast | ❌ No | Production, real-time |
| **ElevenLabs** | 💰 Paid | 🏆 Excellent | 🔥 Fast | ✅ Yes | Premium quality, cloning |
| **Google Cloud** | 💰 Paid | 🌟🌟🌟🌟 Great | ⚡ Fast | ❌ No | Enterprise, multilingual |
| **Chatterbox** | 🆓 Free | 🌟🌟🌟 Variable | 🔥 Fast | ✅ Yes | Local processing, privacy |

Choose based on your quality requirements, budget, and privacy needs.

## 🚀 Advanced Features

```bash
# Pipeline integration
echo "Hello world" | tts                    # Simple pipe
ttt "Fix grammar" < essay.txt | tts         # Fix then speak
stt recording.wav | tts @edge              # Transcribe and speak

# Emotion detection
tts document technical.md --emotion-profile technical
tts document story.txt --emotion-profile narrative

# Performance caching
tts document large.html                     # Automatic caching
tts document large.html                     # Fast repeat processing

# Configuration profiles
tts config set default_provider edge_tts
tts config set audio_format mp3
```

## 🛠️ Tech Stack

### Core Technologies
- **🧠 AI/TTS**: Edge TTS, OpenAI API, ElevenLabs, Google Cloud TTS
- **🎙️ Audio**: FFmpeg, soundfile, PyAudio for streaming and processing
- **🗣️ Voice Cloning**: Chatterbox TTS with PyTorch/GPU acceleration

### Document Processing
- **📝 Parsing**: BeautifulSoup (HTML), JSON, Markdown processors
- **🎭 Emotion**: Advanced emotion detection with context-aware profiling
- **📊 SSML**: Platform-optimized speech synthesis markup generation
- **💾 Caching**: Performance optimization for repeated document processing

### Development & Testing
- **🧪 Testing**: pytest with comprehensive integration and E2E tests
- **📊 Quality**: ruff (linting), black (formatting), mypy (typing)
- **🏗️ Build**: Goobits CLI framework with automated script generation
- **📦 Dependencies**: Automatic provider dependency management

### User Interface
- **🖥️ CLI**: Rich-click with emoji-enhanced interface and provider shortcuts
- **🎛️ Interactive**: Curses-based voice browser with real-time preview
- **⚙️ Configuration**: XDG-compliant with interactive editing and validation
- **📈 Monitoring**: Structured logging with health checks and status reporting
- **🔧 Management**: Voice loading/caching system for optimized performance