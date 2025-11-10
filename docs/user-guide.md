# User Guide

Complete reference for Goobits TTS command-line tool.

## Overview

Goobits TTS converts text to natural speech using multiple providers. Switch between Edge TTS, OpenAI, ElevenLabs, Google Cloud, and Chatterbox without changing your workflow.

## Basic Commands

### Stream Audio

Play synthesized speech directly through your speakers:

```bash
tts "Hello world"
tts "This is a longer sentence with multiple words"
echo "Pipe input also works" | tts
```

### Save to File

Save synthesized audio instead of playing:

```bash
tts save "Hello world"                          # Saves to output.mp3
tts save "Hello world" -o greeting.mp3          # Specify filename
tts save "Hello world" -o greeting.wav --format wav
```

### Provider Selection

Use specific TTS providers with the `@provider` syntax:

```bash
tts @edge "Hello from Microsoft"
tts @openai "Hello from OpenAI"
tts @elevenlabs "Hello from ElevenLabs"
tts @google "Hello from Google"
tts @chatterbox "Hello from local processing"
```

### Voice Selection

Specify voices for providers:

```bash
tts @edge "Hello" --voice en-US-AriaNeural
tts @openai "Hello" --voice alloy
tts @google "Hello" --voice en-US-Neural2-A
```

## Input Methods

### Command-Line Argument

```bash
tts "Your text here"
tts Your text here without quotes also works
```

### Standard Input (Pipe)

```bash
echo "Hello world" | tts
cat document.txt | tts
curl https://example.com/api | jq -r '.text' | tts
```

### File Input

```bash
cat file.txt | tts
tts < file.txt
```

## Output Options

### Audio Formats

Supported formats: MP3, WAV, OGG

```bash
tts save "Hello" --format mp3
tts save "Hello" --format wav
tts save "Hello" --format ogg
```

### Output Location

```bash
tts save "Hello" -o /path/to/output.mp3
tts save "Hello" --output ~/audio/greeting.mp3
```

### Streaming vs. Saving

By default, `tts` streams audio to speakers:

```bash
tts "Hello"              # Plays immediately
```

Use `save` subcommand to write to file:

```bash
tts save "Hello"         # Saves to file
```

## Provider Management

### Check Provider Status

```bash
tts providers            # List all providers and their status
tts providers @openai    # Get setup instructions for OpenAI
tts providers @google    # Get setup instructions for Google
```

### Set Default Provider

```bash
tts config set default_provider edge_tts
```

Valid provider names:
- `edge_tts` - Microsoft Edge TTS
- `openai` - OpenAI TTS
- `elevenlabs` - ElevenLabs
- `google` - Google Cloud TTS
- `chatterbox` - Local Chatterbox

### Provider Installation

Install only the providers you need:

```bash
# All providers
pip install goobits-tts[all]

# Individual providers
pip install goobits-tts[openai]
pip install goobits-tts[google]
pip install goobits-tts[elevenlabs]
pip install goobits-tts[chatterbox]

# Cloud providers only
pip install goobits-tts[cloud]

# Local providers only
pip install goobits-tts[local]
```

## Voice Management

### Browse Voices

Launch interactive voice browser:

```bash
tts voices
```

Features:
- Filter by language
- Filter by gender
- Preview voices in real-time
- See voice metadata

### List Voices (Non-Interactive)

```bash
tts @edge --list-voices
tts @openai --list-voices
tts @google --list-voices
```

### Preload Voices (Chatterbox)

For faster synthesis with Chatterbox:

```bash
# Load voice into memory
tts voice load /path/to/voice.wav

# Check loaded voices
tts voice status

# Use loaded voice
tts @chatterbox "Hello" --voice my_voice
```

## Configuration

### View Configuration

```bash
tts config show
```

Displays:
- API keys (masked)
- Default settings
- Audio configuration
- File paths

### Edit Configuration

```bash
tts config edit
```

Opens configuration file in your default editor.

### Set Configuration Values

```bash
tts config set KEY VALUE
```

Examples:

```bash
# Set API keys
tts config set openai_api_key sk-...
tts config set elevenlabs_api_key ...
tts config set google_api_key ...

# Set defaults
tts config set default_provider openai
tts config set audio_format mp3
tts config set default_voice edge_tts:en-US-AriaNeural
```

### Configuration File

Configuration is stored at:
- **Linux/macOS**: `~/.config/tts/config.toml`
- **Windows**: `%APPDATA%\tts\config.toml`

### Configuration Options

| Option | Description | Example |
|--------|-------------|---------|
| `default_provider` | Default TTS provider | `edge_tts` |
| `default_voice` | Default voice | `edge_tts:en-US-AriaNeural` |
| `audio_format` | Output format | `mp3`, `wav`, `ogg` |
| `openai_api_key` | OpenAI API key | `sk-...` |
| `elevenlabs_api_key` | ElevenLabs API key | `...` |
| `google_api_key` | Google Cloud API key | `...` |

## Document Processing

Convert structured documents to speech.

### Supported Formats

- HTML
- JSON
- Markdown

### Basic Usage

```bash
tts document file.html
tts document data.json
tts document README.md
```

### Save Processed Output

```bash
tts document file.html --save
tts document file.html -o output.mp3
```

### Emotion Profiles

Apply context-aware emotion detection:

```bash
tts document tech_doc.md --emotion-profile technical
tts document product.html --emotion-profile marketing
tts document story.md --emotion-profile narrative
tts document guide.md --emotion-profile tutorial
```

Profiles:
- **technical** - Neutral, clear, professional
- **marketing** - Enthusiastic, engaging
- **narrative** - Dynamic, storytelling
- **tutorial** - Instructional, patient

### SSML Generation

Generate Speech Synthesis Markup Language:

```bash
tts document content.html --ssml-platform azure
tts document content.html --ssml-platform google
tts document content.html --ssml-platform amazon
```

Platforms:
- **azure** - Microsoft Azure SSML
- **google** - Google Cloud SSML
- **amazon** - Amazon Polly SSML

## System Status

### Health Check

```bash
tts status
```

Shows:
- Provider availability
- API key status
- Audio output devices
- System information
- Dependency status

### Version Information

```bash
tts --version
```

## Command Reference

### Main Commands

| Command | Description |
|---------|-------------|
| `tts TEXT` | Synthesize text and stream to speakers |
| `tts save TEXT` | Synthesize text and save to file |
| `tts document FILE` | Process document and convert to speech |
| `tts voices` | Launch interactive voice browser |
| `tts voice load FILE` | Load voice for Chatterbox |
| `tts voice status` | Show loaded voices |
| `tts config show` | Display configuration |
| `tts config edit` | Edit configuration file |
| `tts config set KEY VALUE` | Set configuration value |
| `tts providers` | Show provider status |
| `tts status` | System health check |
| `tts --version` | Show version |
| `tts --help` | Show help |

### Common Options

| Option | Description |
|--------|-------------|
| `--voice VOICE` | Specify voice |
| `--format FORMAT` | Audio format (mp3, wav, ogg) |
| `-o, --output PATH` | Output file path |
| `--save` | Save to file (for document command) |
| `--emotion-profile PROFILE` | Emotion detection profile |
| `--ssml-platform PLATFORM` | SSML platform |

### Provider Shortcuts

| Shortcut | Provider |
|----------|----------|
| `@edge` | Microsoft Edge TTS |
| `@openai` | OpenAI TTS |
| `@elevenlabs` | ElevenLabs |
| `@google` | Google Cloud TTS |
| `@chatterbox` | Chatterbox (local) |

## Common Workflows

### Quick Text-to-Speech

```bash
# Simple text
tts "Hello world"

# From clipboard (Linux)
xclip -o | tts

# From clipboard (macOS)
pbpaste | tts
```

### Content Creation

```bash
# Convert article to audio
tts document article.md --emotion-profile narrative -o article.mp3

# Process blog post
tts document post.html --emotion-profile marketing -o post.mp3
```

### Documentation to Audio

```bash
# Technical documentation
tts document API.md --emotion-profile technical -o docs.mp3

# Tutorial
tts document tutorial.md --emotion-profile tutorial -o lesson.mp3
```

### Pipeline Integration

```bash
# Transcribe and echo back
stt recording.wav | tts

# Translate and speak
echo "Hello" | ttt "translate to Spanish" | tts @google

# Summarize and speak
cat article.txt | ttt "summarize" | tts
```

### Batch Processing

```bash
# Process multiple files
for file in *.md; do
  tts document "$file" -o "${file%.md}.mp3"
done

# Convert text files
for file in *.txt; do
  cat "$file" | tts save -o "${file%.txt}.mp3"
done
```

## Tips and Best Practices

### Choosing a Provider

**For development**: Use Edge TTS (free, no setup)

**For production**: Use OpenAI or ElevenLabs (better quality, streaming)

**For multilingual**: Use Google Cloud (best language support)

**For privacy**: Use Chatterbox (local processing)

**For custom voices**: Use ElevenLabs or Chatterbox (voice cloning)

### Optimizing Quality

1. **Use appropriate voice** - Match voice to content language and tone
2. **Choose emotion profile** - Use profile matching your content type
3. **Consider provider** - Different providers excel at different content
4. **Use HD voices** - When available and quality is critical

### Performance Tips

1. **Use streaming** - OpenAI and ElevenLabs support real-time streaming
2. **Preload voices** - For Chatterbox, preload voices for faster synthesis
3. **Cache results** - Document processing automatically caches
4. **Choose local processing** - Chatterbox avoids network latency

### Cost Management

1. **Use Edge TTS for testing** - Free tier for development
2. **Monitor usage** - Check provider dashboards regularly
3. **Set budgets** - Configure spending limits in provider accounts
4. **Use Chatterbox when possible** - Free local processing

## Troubleshooting

### No Audio Output

1. Check system volume and audio device
2. Run `tts status` to verify audio setup
3. Try saving to file: `tts save "test" -o test.mp3`
4. Verify file plays: `mpv test.mp3` or `vlc test.mp3`

### Provider Errors

1. Check API key: `tts config show`
2. Verify provider status: `tts providers`
3. Get setup help: `tts providers @openai`
4. Test with Edge TTS: `tts @edge "test"`

### Installation Issues

1. Verify Python version: `python3 --version` (3.8+ required)
2. Try setup script: `./setup.sh install`
3. Install specific provider: `pip install goobits-tts[openai]`
4. Check dependencies: `pip list | grep tts`

### Performance Issues

1. Use faster provider (OpenAI for speed)
2. Enable GPU for Chatterbox (if available)
3. Clear cache: `rm -rf ~/.cache/tts/`
4. Check network latency for cloud providers

## Next Steps

- [Getting Started](getting-started.md) - Quick start guide
- [Provider Guide](providers.md) - Detailed provider information
- [Advanced Usage](advanced.md) - Pipelines and document processing
