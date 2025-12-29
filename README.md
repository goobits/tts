# 🔊 Matilda Voice

Unified TTS CLI supporting multiple providers with streaming, file output, and voice cloning.

## ✨ Key Features

- **🎯 Simple Streaming** - Direct audio output to speakers with `voice "Hello"`
- **🔧 Multi-Provider** - Edge TTS, OpenAI, ElevenLabs, Google Cloud, Chatterbox
- **🎙️ Voice Cloning** - Clone voices locally with Chatterbox
- **🔄 Pipeline Ready** - Works with stdin/stdout for tool chaining
- **📄 Document Processing** - Convert HTML, JSON, Markdown to speech

## 🚀 Quick Start

```bash
# Install
./setup.sh install

# Stream to speakers
voice "Hello world"

# Save to file
voice save "Hello world" -o greeting.mp3

# Use specific provider
voice @edge "Hello from Microsoft"
voice @openai "Hello from OpenAI"
```

## 🎙️ Providers

| Provider | Cost | Quality | Speed | Voice Cloning |
|----------|------|---------|-------|---------------|
| Edge TTS | Free | Good | Fast | No |
| OpenAI | Paid | Excellent | Very Fast | No |
| ElevenLabs | Paid | Excellent | Fast | Yes |
| Google Cloud | Paid | Excellent | Fast | No |
| Chatterbox | Free | Variable | Fast | Yes |

```bash
# Provider shortcuts
voice @edge "text"        # Microsoft Edge TTS (free)
voice @openai "text"      # OpenAI TTS
voice @elevenlabs "text"  # ElevenLabs
voice @google "text"      # Google Cloud TTS
voice @chatterbox "text"  # Local voice cloning
```

## 📚 Python Library

```python
from matilda_voice.core import TTSEngine, initialize_tts_engine
from matilda_voice.app_hooks import PROVIDERS_REGISTRY

# Initialize engine with provider registry
engine = initialize_tts_engine(PROVIDERS_REGISTRY)

# Synthesize to file (returns output path)
output = engine.synthesize_text("Hello world", output_path="output.mp3", stream=False)

# Stream to speakers (returns None)
engine.synthesize_text("Hello world", provider_name="edge_tts", stream=True)
```

## ⚙️ Configuration

```bash
# Set API keys
voice config set openai_api_key YOUR_KEY
voice config set elevenlabs_api_key YOUR_KEY
voice config set google_api_key YOUR_KEY

# View configuration
voice config show

# Interactive editor
voice config edit
```

### Voice Selection

```bash
# Browse voices interactively
voice voices

# Use specific voice
voice @edge "Hello" --voice en-US-AriaNeural
voice @openai "Hello" --voice alloy
```

## 🔗 Pipeline Integration

```bash
# Pipe text to voice
echo "Hello world" | voice

# Text transformation → Speech (requires ttt installed)
echo "Hello" | ttt "translate to Spanish" | voice @google

# Document processing
voice document report.html --emotion-profile technical
```

## 🛠️ Installation Options

```bash
# Recommended (all providers)
./setup.sh install

# Development (editable)
./setup.sh install --dev

# Alternative methods
pipx install goobits-matilda-voice[all]
pip install goobits-matilda-voice[openai]    # Single provider
```

**Requirements**: Python 3.8+, FFmpeg, audio output device

## 📖 Documentation

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines, architecture overview, and advanced usage patterns.

## 🧪 Development

```bash
# Install dev dependencies
./setup.sh install --dev

# Run tests
./test.sh

# Code quality
ruff check . --fix
black .
mypy src/
```

## 🔗 Related Projects

Part of the Goobits AI toolkit:

- **[Matilda](https://github.com/goobits/matilda)** - AI assistant
- **[Matilda Ears](https://github.com/goobits/matilda-ears)** - Speech-to-Text
- **[Matilda Voice](https://github.com/goobits/matilda-voice)** - Text-to-Speech
- **[Matilda Brain](https://github.com/goobits/matilda-brain)** - Text-to-Text processing

## 📝 License

MIT License - See LICENSE file for details.

---

Contributions welcome. See [CLAUDE.md](CLAUDE.md) for development guidelines.
