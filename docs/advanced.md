# Advanced Usage

Beyond basic text-to-speech, Goobits TTS supports pipeline integration, document processing, emotion detection, and SSML generation.

## Pipeline Integration

Goobits TTS works seamlessly with other command-line tools through standard input/output.

### Basic Piping

```bash
# Pipe text to TTS
echo "Hello world" | tts

# Read from file
cat document.txt | tts

# Process then speak
cat essay.txt | tts @edge
```

### Integration with Goobits Suite

**STT → TTS** (Speech-to-Text → Text-to-Speech):
```bash
# Transcribe audio, then speak it back
stt recording.wav | tts @edge
```

**TTT → TTS** (Text-to-Text → Text-to-Speech):
```bash
# Fix grammar, then speak
ttt "fix grammar" < essay.txt | tts

# Translate and speak
echo "Hello" | ttt "translate to Spanish" | tts @google --voice es-ES-Neural2-A

# Summarize document, then speak summary
cat long_article.txt | ttt "summarize in 3 sentences" | tts
```

**Full Pipeline** (STT → TTT → TTS):
```bash
# Transcribe, translate, then speak
stt audio.mp3 | ttt "translate to French" | tts @google
```

### Integration with Standard Tools

**With `jq` for JSON processing**:
```bash
curl https://api.example.com/data | jq -r '.message' | tts
```

**With `grep` for filtering**:
```bash
cat logs.txt | grep "ERROR" | tts
```

**With `sed` for text transformation**:
```bash
cat document.txt | sed 's/foo/bar/g' | tts
```

## Document Processing

Convert structured documents to speech with intelligent processing.

### Supported Formats

- HTML
- JSON
- Markdown

### Basic Usage

```bash
# Process HTML document
tts document report.html

# Process JSON data
tts document api_response.json

# Process Markdown
tts document README.md
```

### Save Processed Audio

```bash
tts document report.html --save
tts document report.html -o report.mp3
```

### HTML Processing

TTS converts HTML to speech by:

1. Extracting text content
2. Removing script and style tags
3. Converting common HTML entities
4. Preserving semantic structure

```bash
# Basic HTML conversion
tts document webpage.html

# With specific provider
tts document webpage.html @openai
```

### JSON Processing

For JSON files, TTS extracts string values and converts them to speech:

```bash
# Process JSON file
tts document data.json

# Useful for API responses
curl https://api.example.com/data | tts document --format json
```

### Markdown Processing

Markdown documents are converted to speech while preserving structure:

```bash
# Process Markdown file
tts document README.md

# Process with emotion detection
tts document article.md --emotion-profile narrative
```

## Emotion Detection

Goobits TTS includes context-aware emotion detection to make synthesized speech sound more natural.

### Emotion Profiles

Choose a profile based on your content type:

**Technical** - For documentation, code, technical writing:
```bash
tts document api_docs.md --emotion-profile technical
```

Characteristics:
- Neutral, professional tone
- Emphasis on clarity
- Minimal emotional inflection

**Marketing** - For promotional content, product descriptions:
```bash
tts document product_page.html --emotion-profile marketing
```

Characteristics:
- Enthusiastic tone
- Emphasis on key benefits
- Engaging delivery

**Narrative** - For stories, articles, creative content:
```bash
tts document story.md --emotion-profile narrative
```

Characteristics:
- Dynamic emotional range
- Natural storytelling pace
- Contextual emphasis

**Tutorial** - For how-to guides, educational content:
```bash
tts document guide.md --emotion-profile tutorial
```

Characteristics:
- Clear, instructional tone
- Emphasis on steps and actions
- Patient pacing

### How Emotion Detection Works

The emotion detection system:

1. Analyzes document structure and content
2. Identifies emotional cues (exclamation marks, questions, emphasis)
3. Adjusts speech parameters (pitch, rate, emphasis)
4. Applies profile-specific rules

### Combining with Providers

Different providers respond differently to emotion profiles:

```bash
# Edge TTS with emotion detection
tts document story.md --emotion-profile narrative @edge

# OpenAI with marketing profile
tts document product.html --emotion-profile marketing @openai
```

## SSML Generation

Speech Synthesis Markup Language (SSML) provides fine-grained control over speech output.

### Platform Support

Generate SSML optimized for specific platforms:

**Azure (Edge TTS)**:
```bash
tts document content.html --ssml-platform azure
```

**Google Cloud TTS**:
```bash
tts document content.html --ssml-platform google
```

**Amazon Polly**:
```bash
tts document content.html --ssml-platform amazon
```

### SSML Features

The SSML generator supports:

- **Breaks**: Pauses between sentences and paragraphs
- **Emphasis**: Highlighting important words
- **Prosody**: Control rate, pitch, and volume
- **Say-as**: Format numbers, dates, and special content

### Save SSML Output

```bash
# Generate and save SSML
tts document report.html --ssml-platform azure --save-ssml report.ssml

# Use SSML with provider
tts @google --ssml report.ssml
```

### Combining SSML and Emotion Profiles

```bash
tts document guide.md \
  --emotion-profile tutorial \
  --ssml-platform google \
  --save
```

## Voice Management

Preload voices for faster synthesis (Chatterbox provider).

### Load Voice

```bash
tts voice load /path/to/voice.wav
```

This loads the voice file into memory for quick access during synthesis.

### Check Loaded Voices

```bash
tts voice status
```

### Using Loaded Voices

```bash
# Load voice
tts voice load my_voice.wav

# Use in synthesis
tts @chatterbox "Hello" --voice my_voice
```

### Voice Quality Tips

For best Chatterbox voice cloning results:

1. **Use high-quality audio** (16kHz+ sample rate, 16-bit depth)
2. **Clear speech** without background noise
3. **Neutral emotion** in source audio
4. **5-30 seconds** of audio is typically sufficient
5. **Single speaker** only

## Performance Optimization

### Caching

Document processing results are automatically cached:

```bash
# First run: parses and caches
tts document large.html

# Subsequent runs: uses cache (much faster)
tts document large.html
```

Cache location: `~/.cache/tts/`

### Clear Cache

```bash
rm -rf ~/.cache/tts/
```

### Provider Performance

For fastest synthesis:

1. **OpenAI**: Best for real-time streaming
2. **Chatterbox**: Fast after voice loading (no network latency)
3. **Edge TTS**: Good balance of speed and quality
4. **ElevenLabs**: Fast with streaming enabled
5. **Google Cloud**: Good speed, may have latency for first request

## Interactive Voice Browser

Explore available voices with an interactive interface:

```bash
tts voices
```

### Features

- **Three-panel layout**: Filters, voice list, preview panel
- **Real-time preview**: Hear voices before using them
- **Filter by language**: Narrow down by language code
- **Filter by gender**: Male, female, or neutral voices
- **Quality analysis**: See voice metadata and ratings
- **Mouse support**: Click to select and preview
- **Keyboard navigation**: Arrow keys, Enter to select

### Keyboard Shortcuts

- **Arrow keys**: Navigate
- **Enter**: Select voice
- **Tab**: Switch between panels
- **q**: Quit
- **Space**: Preview voice
- **/** : Search/filter

## Configuration Management

### View Configuration

```bash
tts config show
```

### Edit Configuration

```bash
tts config edit
```

This opens your default editor with the configuration file.

### Set Individual Values

```bash
tts config set default_provider openai
tts config set audio_format mp3
tts config set openai_api_key YOUR_KEY
```

### Configuration Options

Available settings:

- `default_provider` - Default TTS provider
- `audio_format` - Output format (mp3, wav, ogg)
- `openai_api_key` - OpenAI API key
- `elevenlabs_api_key` - ElevenLabs API key
- `google_api_key` - Google Cloud API key
- `default_voice` - Default voice (format: `provider:voice_name`)

### Configuration File Location

Configuration is stored at:
- Linux/macOS: `~/.config/tts/config.toml`
- Windows: `%APPDATA%\tts\config.toml`

## System Health

### Check Status

```bash
tts status
```

This shows:
- Installed providers
- API key status
- Audio output devices
- System information

### Provider-Specific Status

```bash
tts providers           # All providers
tts providers @openai   # OpenAI setup instructions
tts providers @google   # Google setup instructions
```

## Troubleshooting

### Audio Issues

**No audio output**:
```bash
# Check system status
tts status

# Try saving to file instead
tts save "test" -o test.mp3

# Verify file was created
ls -lh test.mp3
```

**Audio stuttering**:
- Use a different provider with streaming support
- Try saving to file first, then playing
- Check system audio settings

### Provider Issues

**API key errors**:
```bash
# Verify configuration
tts config show

# Set key if missing
tts config set openai_api_key YOUR_KEY

# Test provider
tts providers @openai
```

**Rate limiting**:
- Edge TTS: Free tier has rate limits, try again later
- Paid providers: Check your quota and billing
- Use Chatterbox for unlimited local processing

### Performance Issues

**Slow synthesis**:
- Use OpenAI for fastest streaming
- Enable GPU for Chatterbox (CUDA)
- Check network latency for cloud providers

**High memory usage**:
- Clear document cache: `rm -rf ~/.cache/tts/`
- Use streaming providers (OpenAI, ElevenLabs)
- Process smaller documents

## Next Steps

- [Getting Started](getting-started.md) - Installation and basics
- [User Guide](user-guide.md) - Comprehensive documentation
- [Provider Guide](providers.md) - Provider comparison and setup
