# Getting Started

Get up and running with Goobits TTS in under 60 seconds.

## Installation

### Quick Install (Recommended)

```bash
./setup.sh install
```

This installs the `tts` command with all dependencies handled automatically.

### Verify Installation

```bash
tts --version
tts "Hello world"
```

If you hear audio, you're done! The default provider (Edge TTS) requires no API keys.

### Alternative Installation Methods

**Global install with pipx**:
```bash
pipx install goobits-tts[all]
```

**User install with pip**:
```bash
pip install --user goobits-tts[all]
```

**Development install** (for contributors):
```bash
./setup.sh install --dev
```

## First Steps

### Stream Audio

By default, TTS streams audio directly to your speakers:

```bash
tts "Hello world"
tts "Welcome to Goobits TTS"
echo "Pipe input works too" | tts
```

### Save to File

```bash
tts save "Hello world" -o greeting.mp3
```

### Try Different Providers

Edge TTS (free) is the default, but you can try others:

```bash
tts @edge "Hello from Microsoft"
tts @google "Hello from Google"
tts @openai "Hello from OpenAI"
```

Note: OpenAI, Google Cloud, and ElevenLabs require API keys. See [Provider Setup](providers.md) for configuration.

## Configuration

### Set Your Default Provider

```bash
tts config set default_provider edge_tts
```

### Configure API Keys

```bash
tts config set openai_api_key YOUR_KEY
tts config set elevenlabs_api_key YOUR_KEY
tts config set google_api_key YOUR_KEY
```

### View Configuration

```bash
tts config show
```

### Edit Configuration Interactively

```bash
tts config edit
```

Configuration is stored at `~/.config/tts/config.toml`.

## Getting Help

```bash
tts --help              # General help
tts save --help         # Command-specific help
tts providers           # Check provider status
tts status              # System health check
```

## Common Issues

**No audio output?**
- Check your system volume
- Verify audio device: `tts status`
- Try saving to file first: `tts save "test" -o test.mp3`

**Provider errors?**
- Run `tts providers` to check provider status
- Verify API keys: `tts config show`
- Check provider-specific setup: `tts providers @openai`

**Installation issues?**
- Ensure Python 3.8+ is installed: `python3 --version`
- Try the setup script: `./setup.sh install`
- For development setup: `./setup.sh install --dev`

## Next Steps

- [User Guide](user-guide.md) - Comprehensive documentation
- [Provider Setup](providers.md) - Configure all TTS providers
- [Advanced Usage](advanced.md) - Pipelines and document processing
