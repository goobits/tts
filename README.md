# Goobits TTS

One CLI for all TTS providers. Stream to speakers, save to files, or clone voices. Works with your text processing pipeline.

**Supported Providers**: Edge TTS • OpenAI • ElevenLabs • Google Cloud • Chatterbox

## Quick Start

1. **Install**: `./setup.sh install`
2. **Test**: `tts "Hello world"`
3. **Done**: You just synthesized speech

## Basic Usage

```bash
# Stream audio to speakers
tts "Hello world"
echo "Hello world" | tts

# Save to file
tts save "Hello world" -o greeting.mp3

# Use specific provider
tts @edge "Hello from Microsoft"
tts @openai "Hello from OpenAI"
tts @elevenlabs "Hello from ElevenLabs"
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
tts config set openai_api_key YOUR_KEY
tts config set elevenlabs_api_key YOUR_KEY
tts config set google_api_key YOUR_KEY

# View configuration
tts config show

# Interactive editor
tts config edit
```

## Voice Selection

```bash
# Browse voices interactively
tts voices

# Use specific voice
tts @edge "Hello" --voice en-US-AriaNeural
tts @openai "Hello" --voice alloy
```

## Pipeline Integration

Works seamlessly with other Goobits tools:

```bash
# Speech → Text → Speech
stt recording.wav | tts @edge

# Text transformation → Speech
echo "Hello" | ttt "translate to Spanish" | tts @google

# Document processing
tts document report.html --emotion-profile technical
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
pipx install goobits-tts[all]      # Global install
pip install goobits-tts[all]       # User install
pip install goobits-tts[openai]    # Single provider
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
- **[Goobits STT](https://github.com/goobits/stt)** - Speech-to-Text
- **[Goobits TTS](https://github.com/goobits/tts)** - Text-to-Speech (this project)
- **[Goobits TTT](https://github.com/goobits/ttt)** - Text-to-Text processing

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! See [CLAUDE.md](CLAUDE.md) for development setup and guidelines.
