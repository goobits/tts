# 🗣️ Goobits TTS CLI

A command-line text-to-speech tool that supports multiple TTS providers with automatic voice selection and voice cloning capabilities. Stream audio directly to speakers or save to files with support for various formats. Features an interactive voice browser, smart provider detection, and comprehensive configuration management for seamless deployment across different environments.

## 📦 Installation

```bash
./setup-pipx.sh install    # Install with pipx
tts doctor                 # Check system health
tts install chatterbox gpu # Add voice cloning (optional)
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
tts config set voice en-IE-EmilyNeural  # Set default voice
tts config set default_action save   # Save files by default
tts config edit                      # Interactive editor
```

## 🎤 Voice Discovery

```bash
tts voices                           # List all available voices
tts voices edge_tts                  # List voices for specific provider
tts voices find "irish"              # Search voices
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
| **Edge TTS** | ⚡ Instant | 🌟 Excellent | ❌ No | ❌ No | ❌ Free |
| **Chatterbox** | 🔥 Fast | 🏆 Best-in-class | ✅ Yes | ✅ Yes | ❌ Free |
| **OpenAI TTS** | ⚡ Fast | 🌟 Excellent | ❌ No | ❌ No | ✅ Paid |
| **Google Cloud TTS** | ⚡ Fast | 🌟 Excellent | ❌ No | ❌ No | ✅ Paid |
| **ElevenLabs** | 🔥 Fast | 🏆 Premium | ❌ No | ✅ Yes | ✅ Paid |

Choose from free offline options or premium cloud services based on your needs.