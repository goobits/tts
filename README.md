# 🗣️ TTS CLI - Smart Text-to-Speech

A lightning-fast, intelligent TTS system that automatically chooses the best engine based on your connectivity.

## ✨ Features

- 🌐 **Smart Auto-Selection** - Edge TTS when online, Chatterbox when offline
- 🎭 **Voice Cloning** - Clone any voice with a short audio sample
- ⚡ **Real-time Streaming** - No file creation, direct audio playback
- 🇬🇧 **High-Quality Voices** - British female default, multiple accents available
- 🚀 **GPU Accelerated** - CUDA support for local generation
- 🔧 **Simple CLI** - One command does everything

## 🚀 Quick Start

```bash
# Basic usage (auto-selects best engine)
tts "Hello, world!"

# Use specific engine
tts "British accent" -e edge_tts
tts "High quality local" -e chatterbox

# Voice cloning
tts "Clone my voice" --clone ~/my_voice.wav

# Different accents
tts "American voice" -e edge_tts -v en-US-JennyNeural
tts "Australian voice" -e edge_tts -v en-AU-NatashaNeural
```

## 📦 Installation

Already installed! The `tts` command is available system-wide.

## 🎯 Engines

| Engine | Speed | Quality | Offline | Voice Cloning |
|--------|-------|---------|---------|---------------|
| **Edge TTS** | ⚡ Instant | 🌟 Excellent | ❌ No | ❌ No |
| **Chatterbox** | 🔥 Fast | 🏆 Best-in-class | ✅ Yes | ✅ Yes |

## 🛠️ Commands

```bash
tts "text"                    # Auto-select engine
tts "text" -e edge_tts        # Force Edge TTS  
tts "text" -e chatterbox      # Force Chatterbox
tts "text" --clone voice.wav  # Voice cloning
tts --start-server            # Start TTS server
tts --status                  # Check server status
```

## 🎤 Voice Cloning

1. Record your voice:
```bash
arecord -f cd -t wav -d 30 ~/my_voice.wav
```

2. Use it:
```bash
tts "This is my cloned voice!" --clone ~/my_voice.wav
```

## 🔧 Server Management

```bash
# Start persistent server (faster Chatterbox)
tts --start-server

# Check if running
tts --status
```

## 🌟 Why This Setup Rocks

- **Beats ElevenLabs** in blind tests (Chatterbox)
- **Free forever** - no API costs
- **Smart fallbacks** - always works online/offline  
- **Voice cloning** without training
- **Multiple accents** and languages

Built with ❤️ using cutting-edge open-source TTS models.