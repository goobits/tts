# 🔊 Matilda Voice

One CLI for all TTS providers. Stream to speakers, save to files, or clone voices. Works with your text processing pipeline.

**Supported Providers**: Edge TTS • OpenAI • ElevenLabs • Google Cloud • Chatterbox

## Quick Start

1. **Install**: `./setup.sh install`
2. **Test**: `voice "Hello world"`
3. **Done**: You just synthesized speech

## Basic Usage

```bash
# Stream audio to speakers
voice "Hello world"
echo "Hello world" | tts

# Save to file
voice save "Hello world" -o greeting.mp3

# Use specific provider
voice @edge "Hello from Microsoft"
voice @openai "Hello from OpenAI"
voice @elevenlabs "Hello from ElevenLabs"
```

## Provider Comparison

| Provider | Cost | Quality | Speed | Voice Cloning | Best For |
|----------|------|---------|-------|---------------|----------|
| Edge TTS | Free | Good | Fast | No | Development, general use |
| OpenAI | Paid | Excellent | Very Fast | No | Production, real-time |
| ElevenLabs | Paid | Excellent | Fast | Yes | Premium quality, cloning |
| Google Cloud | Paid | Excellent | Fast | No | Enterprise, multilingual |
| Chatterbox | Free | Variable | Fast | Yes | Local processing, privacy |

## Configuration

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

## Voice Selection

```bash
# Browse voices interactively
voice voices

# Use specific voice
voice @edge "Hello" --voice en-US-AriaNeural
voice @openai "Hello" --voice alloy
```

## Pipeline Integration

Works seamlessly with other Goobits tools:

```bash
# Speech → Text → Speech
stt recording.wav | tts @edge

# Text transformation → Speech
echo "Hello" | ttt "translate to Spanish" | tts @google

# Document processing
voice document report.html --emotion-profile technical
```

## Documentation

- **[Getting Started](docs/getting-started.md)** - Installation and first steps
- **[User Guide](docs/user-guide.md)** - Complete reference
- **[Provider Guide](docs/providers.md)** - Provider comparison and setup
- **[Advanced Usage](docs/advanced.md)** - Pipelines and document processing

## Installation Options

**Recommended** (all providers):
```bash
./setup.sh install
```

**Alternative methods**:
```bash
pipx install goobits-matilda-voice[all]      # Global install
pip install goobits-matilda-voice[all]       # User install
pip install goobits-matilda-voice[openai]    # Single provider
```

**Development**:
```bash
./setup.sh install --dev
```

## System Requirements

- Python 3.8+
- FFmpeg (for audio processing)
- Audio output device

## Related Projects

Part of the Goobits AI toolkit:

- **[Matilda](https://github.com/goobits/matilda)** - AI assistant
- **[Matilda Ears](https://github.com/goobits/matilda-ears)** - Speech-to-Text
- **[Matilda Voice](https://github.com/goobits/matilda-voice)** - Text-to-Speech (this project)
- **[Matilda Brain](https://github.com/goobits/matilda-brain)** - Text-to-Text processing

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! See [CLAUDE.md](CLAUDE.md) for development setup and guidelines.
