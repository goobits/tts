# TTS Provider Guide

Goobits TTS supports five TTS providers, each with different strengths and trade-offs.

## Provider Comparison

| Provider | Cost | Quality | Speed | Voice Cloning | Streaming | Best For |
|----------|------|---------|-------|---------------|-----------|----------|
| Edge TTS | Free | Good | Fast | No | No | Development, testing, general use |
| OpenAI | Paid | Excellent | Very Fast | No | Yes | Production, real-time applications |
| ElevenLabs | Paid | Excellent | Fast | Yes | Yes | Custom voices, premium quality |
| Google Cloud | Paid | Excellent | Fast | No | No | Enterprise, multilingual support |
| Chatterbox | Free | Variable | Fast | Yes | No | Local processing, privacy, offline use |

## Edge TTS

**Provider**: Microsoft Azure Cognitive Services
**Cost**: Free
**Setup**: None required (works out of the box)

### Usage

```bash
tts @edge "Hello world"
tts @edge "Text" --voice en-US-AriaNeural
```

### Available Voices

Browse voices interactively:
```bash
tts voices
```

Or list voices programmatically:
```bash
tts @edge --list-voices
```

### Characteristics

- No API key required
- Good quality neural voices
- Wide language support (75+ languages)
- No streaming support (downloads complete file first)
- Rate limits apply (Microsoft's free tier)

### Best For

- Development and testing
- Personal projects
- Applications where cost is a concern
- Quick prototyping

## OpenAI TTS

**Provider**: OpenAI API
**Cost**: $15 per 1 million characters
**Setup**: Requires API key

### Configuration

```bash
tts config set openai_api_key YOUR_KEY
```

Get an API key at: https://platform.openai.com/api-keys

### Usage

```bash
tts @openai "Hello world"
tts @openai "Text" --voice alloy
```

### Available Voices

- `alloy` - Neutral, balanced
- `echo` - Male, clear
- `fable` - Expressive, British accent
- `onyx` - Deep, male
- `nova` - Warm, female
- `shimmer` - Soft, female

### Characteristics

- High-quality neural voices
- Real-time streaming support
- Low latency (ideal for interactive applications)
- Multiple voice personalities
- HD quality option available

### Best For

- Production applications
- Real-time streaming scenarios
- Applications requiring consistent quality
- Integration with OpenAI ecosystem

## ElevenLabs

**Provider**: ElevenLabs API
**Cost**: Paid plans starting at $5/month
**Setup**: Requires API key

### Configuration

```bash
tts config set elevenlabs_api_key YOUR_KEY
```

Get an API key at: https://elevenlabs.io

### Usage

```bash
tts @elevenlabs "Hello world"
tts @elevenlabs "Text" --voice adam
```

### Characteristics

- Exceptional voice quality
- Voice cloning capabilities
- Emotional range and expressiveness
- Real-time streaming support
- Custom voice creation (paid plans)

### Voice Cloning

ElevenLabs supports cloning voices from audio samples (requires paid plan):

1. Upload voice sample to ElevenLabs dashboard
2. Create custom voice
3. Use voice ID with TTS CLI

### Best For

- Premium quality requirements
- Custom voice cloning
- Content creation (podcasts, audiobooks)
- Character voices for games/apps

## Google Cloud TTS

**Provider**: Google Cloud Platform
**Cost**: $4 per 1 million characters (Neural2), $16 per 1 million characters (Studio)
**Setup**: Requires API key or service account

### Configuration

**Option 1: API Key** (simpler):
```bash
tts config set google_api_key YOUR_KEY
```

**Option 2: Service Account** (more secure):
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

Get credentials at: https://console.cloud.google.com/apis/credentials

### Usage

```bash
tts @google "Hello world"
tts @google "Text" --voice en-US-Neural2-A
```

### Characteristics

- Multiple quality tiers (Standard, Neural2, Studio)
- Extensive language support (220+ voices, 40+ languages)
- WaveNet technology for natural speech
- SSML support for fine-grained control
- Integration with Google Cloud ecosystem

### Best For

- Enterprise applications
- Multilingual support requirements
- Google Cloud Platform integration
- Applications requiring SSML

## Chatterbox

**Provider**: Local processing (chatterbox-tts)
**Cost**: Free
**Setup**: Automatic (installed with `goobits-matilda-voice[chatterbox]`)

### Usage

```bash
tts @chatterbox "Hello world"
```

### Voice Cloning

Chatterbox supports local voice cloning from audio files:

```bash
# Load a voice for future use
tts voice load /path/to/voice.wav

# Check loaded voices
tts voice status

# Use loaded voice
tts @chatterbox "Hello world" --voice my_voice
```

### Characteristics

- Runs entirely locally (no API calls)
- GPU acceleration support (CUDA)
- Voice cloning from short audio samples
- No internet required after setup
- Privacy-focused (data never leaves your machine)
- Quality varies based on voice sample

### Hardware Recommendations

- **CPU only**: Works, but slower synthesis
- **GPU (CUDA)**: Significantly faster (5-10x speedup)
- **Memory**: 4GB+ RAM recommended
- **Disk**: ~2GB for model files

### Best For

- Privacy-sensitive applications
- Offline environments
- Custom voice cloning without cloud APIs
- Development without API costs

## Provider Selection

### Automatic Provider Selection

TTS automatically selects the best available provider based on:

1. Configured API keys
2. Voice specification (if provided)
3. Default provider setting

### Manual Provider Selection

Use the `@provider` shortcut:

```bash
tts @edge "text"
tts @openai "text"
tts @elevenlabs "text"
tts @google "text"
tts @chatterbox "text"
```

### Set Default Provider

```bash
tts config set default_provider edge_tts
```

Valid values: `edge_tts`, `openai`, `elevenlabs`, `google`, `chatterbox`

## Provider Status

Check which providers are available:

```bash
tts providers           # Show all provider status
tts providers @openai   # Show OpenAI-specific setup
tts status              # System health check
```

## Installation by Provider

Install only the providers you need:

```bash
# All providers
pip install goobits-matilda-voice[all]

# Cloud providers only
pip install goobits-matilda-voice[cloud]

# Local providers only
pip install goobits-matilda-voice[local]

# Individual providers
pip install goobits-matilda-voice[openai]
pip install goobits-matilda-voice[google]
pip install goobits-matilda-voice[elevenlabs]
pip install goobits-matilda-voice[chatterbox]
```

## Cost Comparison

Based on synthesizing a 1000-word article (~5000 characters):

| Provider | Cost per Article | Notes |
|----------|------------------|-------|
| Edge TTS | Free | Subject to rate limits |
| OpenAI | $0.075 | Standard voices |
| Google Cloud | $0.02 - $0.08 | Varies by voice tier |
| ElevenLabs | Varies | Character quota based on plan |
| Chatterbox | Free | Local processing only |

## Quality Considerations

**Edge TTS**: Consistent good quality, suitable for most use cases.

**OpenAI**: Excellent quality with low latency, best for real-time applications.

**ElevenLabs**: Highest quality with emotional range, best for content where voice quality is critical.

**Google Cloud**: Excellent quality with best multilingual support, ideal for international applications.

**Chatterbox**: Quality depends on voice sample used for cloning. Best when you have high-quality reference audio.

## Next Steps

- [Getting Started](getting-started.md) - Installation and first steps
- [User Guide](user-guide.md) - Comprehensive usage documentation
- [Advanced Usage](advanced.md) - Pipelines and document processing
