# 🗣️ TTS CLI - Smart Text-to-Speech

A lightning-fast, intelligent TTS system that automatically chooses the best engine based on your connectivity.

## ✨ Features

- 🔧 **Smart Configuration** - Set your preferred voice, provider, and default behavior
- 🎭 **Voice Cloning** - Clone any voice with a short audio sample
- ⚡ **Real-time Streaming** - No file creation, direct audio playback by default
- 🇮🇪 **Irish Voices** - High-quality Irish accents with en-IE-EmilyNeural
- 🚀 **Auto-Detection** - Smart provider selection based on voice format
- 🔧 **Simple CLI** - One command does everything

## 🚀 Quick Start

```bash
# Basic usage (streams by default)
tts "Hello, world!"

# Use specific voice
tts "Irish accent" --voice en-IE-EmilyNeural
tts "American voice" --voice en-US-JennyNeural

# Voice cloning with Chatterbox
tts "Clone my voice" --clone ~/my_voice.wav

# Save to file instead of streaming
tts "Save this" --save
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
# Text-to-Speech
tts "text"                    # Stream audio using configured voice
tts "text" --save             # Save to file instead of streaming
tts "text" --voice voice-name # Use specific voice
tts "text" --clone voice.wav  # Voice cloning with Chatterbox

# Configuration
tts config                    # Show current settings
tts config set voice en-IE-EmilyNeural        # Set default voice
tts config set default_action save            # Change default to save files
tts config edit               # Interactive configuration editor
tts config reset              # Reset to defaults

# Voice Discovery
tts --list-voices edge_tts    # List available voices
tts --find-voice "irish"      # Search for voices
tts --preview-voice en-IE-EmilyNeural  # Preview a voice
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

## ⚙️ Configuration System

The TTS CLI includes a powerful configuration system that remembers your preferences:

```bash
# Set your preferred voice (auto-detects provider)
tts config set voice en-IE-EmilyNeural

# Or specify provider explicitly
tts config set voice edge_tts:en-US-JennyNeural

# Change default behavior
tts config set default_action save    # Save files by default
tts config set output_dir ~/Audio     # Change save location

# View current settings
tts config

# Interactive editor
tts config edit
```

**Voice Auto-Detection:**
- `en-IE-EmilyNeural` → automatically uses Edge TTS
- `/path/to/voice.wav` → automatically uses Chatterbox for cloning
- `edge_tts:voice-name` → explicit provider specification

## 🌟 Why This Setup Rocks

- **Beats ElevenLabs** in blind tests (Chatterbox)
- **Free forever** - no API costs
- **Smart fallbacks** - always works online/offline  
- **Voice cloning** without training
- **Multiple accents** and languages

Built with ❤️ using cutting-edge open-source TTS models.