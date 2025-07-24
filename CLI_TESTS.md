# TTS CLI Command Checklist

## Basic Commands
- [ ] `tts "Hello world"` - Implicit speak (default command)
- [ ] `tts Hello world` - Unquoted text (implicit speak)
- [ ] `echo "Hello world" | tts` - Pipe input to speak
- [ ] `tts --version` - Show version information
- [ ] `tts --help` - Show main help menu

## Core Speech Commands

### Speak Command
- [ ] `tts speak "Hello world"` - Basic speak command
- [ ] `tts speak "Hello world" --voice en-US-JennyNeural` - Speak with specific voice
- [ ] `tts speak "Hello world" -v en-GB-SoniaNeural` - Short voice flag
- [ ] `tts speak "Hello world" --rate +20%` - Adjust speech rate (faster)
- [ ] `tts speak "Hello world" --rate -50%` - Adjust speech rate (slower)
- [ ] `tts speak "Hello world" --rate 150%` - Absolute rate setting
- [ ] `tts speak "Hello world" --pitch +5Hz` - Adjust pitch (higher)
- [ ] `tts speak "Hello world" --pitch -10Hz` - Adjust pitch (lower)
- [ ] `tts speak "Hello world" --debug` - Debug mode
- [ ] `tts speak "Hello world" --voice en-US-AriaNeural --rate +10% --pitch +2Hz` - Multiple options
- [ ] `echo "Piped text" | tts speak` - Speak piped input
- [ ] `tts speak` - Speak from stdin (interactive)

### Save Command
- [ ] `tts save "Hello world"` - Save with default filename (output.mp3)
- [ ] `tts save "Hello world" -o test.mp3` - Save to specific file
- [ ] `tts save "Hello world" --output audio.wav` - Long output flag
- [ ] `tts save "Hello world" -f wav` - Specify format (wav)
- [ ] `tts save "Hello world" --format mp3` - Specify format (mp3)
- [ ] `tts save "Hello world" --format ogg` - Specify format (ogg)
- [ ] `tts save "Hello world" --format flac` - Specify format (flac)
- [ ] `tts save "Hello world" -v en-US-JennyNeural` - Save with specific voice
- [ ] `tts save "Hello world" --voice edge_tts:en-GB-SoniaNeural` - Provider-specific voice
- [ ] `tts save "Hello world" --rate +20%` - Save with rate adjustment
- [ ] `tts save "Hello world" --pitch +5Hz` - Save with pitch adjustment
- [ ] `tts save "Hello world" --json` - JSON output mode
- [ ] `tts save "Hello world" --debug` - Debug mode
- [ ] `tts save "Hello world" -o out.mp3 -v en-US-AriaNeural --rate +10% --debug` - Multiple options
- [ ] `echo "Save this" | tts save -o piped.mp3` - Save piped input

## Provider Shortcuts

### Edge TTS (Free)
- [ ] `tts @edge "Hello world"` - Use Edge TTS provider
- [ ] `tts speak @edge "Hello world"` - Explicit speak with Edge
- [ ] `tts save @edge "Hello world" -o edge.mp3` - Save with Edge TTS
- [ ] `tts @edge "Hello world" --voice en-US-JennyNeural` - Edge with specific voice

### OpenAI TTS
- [ ] `tts @openai "Hello world"` - Use OpenAI TTS provider
- [ ] `tts speak @openai "Hello world"` - Explicit speak with OpenAI
- [ ] `tts save @openai "Hello world" -o openai.mp3` - Save with OpenAI TTS

### ElevenLabs
- [ ] `tts @elevenlabs "Hello world"` - Use ElevenLabs provider
- [ ] `tts speak @elevenlabs "Hello world"` - Explicit speak with ElevenLabs
- [ ] `tts save @elevenlabs "Hello world" -o eleven.mp3` - Save with ElevenLabs

### Google TTS
- [ ] `tts @google "Hello world"` - Use Google TTS provider
- [ ] `tts speak @google "Hello world"` - Explicit speak with Google
- [ ] `tts save @google "Hello world" -o google.mp3` - Save with Google TTS

### Chatterbox (Local Voice Cloning)
- [ ] `tts @chatterbox "Hello world"` - Use Chatterbox provider
- [ ] `tts speak @chatterbox "Hello world"` - Explicit speak with Chatterbox
- [ ] `tts save @chatterbox "Hello world" -o chatterbox.mp3` - Save with Chatterbox

## Provider Management

### Providers Command
- [ ] `tts providers` - List all available providers
- [ ] `tts providers edge_tts` - Show specific provider info
- [ ] `tts providers @edge` - Show provider info via shortcut

### Info Command
- [ ] `tts info` - Show general provider information
- [ ] `tts info edge_tts` - Get detailed info about Edge TTS
- [ ] `tts info @edge` - Get info via provider shortcut
- [ ] `tts info @openai` - Get OpenAI provider info
- [ ] `tts info @elevenlabs` - Get ElevenLabs provider info
- [ ] `tts info @google` - Get Google TTS provider info
- [ ] `tts info @chatterbox` - Get Chatterbox provider info

### Install Command
- [ ] `tts install` - Show installation help
- [ ] `tts install edge-tts` - Install Edge TTS dependencies
- [ ] `tts install openai` - Install OpenAI dependencies
- [ ] `tts install elevenlabs` - Install ElevenLabs dependencies
- [ ] `tts install google-tts` - Install Google TTS dependencies
- [ ] `tts install chatterbox` - Install Chatterbox dependencies (PyTorch, etc.)

## Configuration Management

### Config Commands
- [ ] `tts config` - Show all configuration
- [ ] `tts config show` - Explicit show command
- [ ] `tts config get voice` - Get specific config value
- [ ] `tts config set voice edge_tts:en-US-JennyNeural` - Set default voice
- [ ] `tts config set openai_api_key YOUR_KEY` - Set OpenAI API key
- [ ] `tts config set elevenlabs_api_key YOUR_KEY` - Set ElevenLabs API key
- [ ] `tts config set google_api_key YOUR_KEY` - Set Google API key
- [ ] `tts config set google_credentials_path /path/to/creds.json` - Set Google service account
- [ ] `tts config voice` - Voice-related configuration
- [ ] `tts config provider` - Provider-related configuration
- [ ] `tts config format` - Format-related configuration
- [ ] `tts config edit` - Interactive configuration editor

### Status Command
- [ ] `tts status` - System and provider status check

## Voice Management

### Voices Browser
- [ ] `tts voices` - Interactive voice browser

### Voice Loading (Chatterbox)
- [ ] `tts voice status` - Show loaded voices and system status
- [ ] `tts voice load voice.wav` - Load single voice file
- [ ] `tts voice load voice1.wav voice2.wav` - Load multiple voice files
- [ ] `tts voice load *.wav` - Load all WAV files in directory
- [ ] `tts voice unload voice.wav` - Unload specific voice file
- [ ] `tts voice unload voice1.wav voice2.wav` - Unload multiple voices
- [ ] `tts voice unload --all` - Unload all loaded voices

## Document Processing

### Document Command
- [ ] `tts document document.md` - Convert markdown document (stream)
- [ ] `tts document document.html` - Convert HTML document
- [ ] `tts document data.json` - Convert JSON document
- [ ] `tts document document.md --save` - Save document audio to file
- [ ] `tts document document.md -o document.mp3` - Save to specific file
- [ ] `tts document document.md --output audio.wav -f wav` - Save with format
- [ ] `tts document document.md -v en-US-JennyNeural` - Use specific voice
- [ ] `tts document document.md --doc-format markdown` - Explicit format
- [ ] `tts document document.html --doc-format html` - HTML format
- [ ] `tts document data.json --doc-format json` - JSON format
- [ ] `tts document file.txt --doc-format auto` - Auto-detect format
- [ ] `tts document document.md --ssml-platform azure` - Azure SSML
- [ ] `tts document document.md --ssml-platform google` - Google SSML
- [ ] `tts document document.md --ssml-platform amazon` - Amazon SSML
- [ ] `tts document document.md --ssml-platform generic` - Generic SSML
- [ ] `tts document document.md --emotion-profile technical` - Technical emotion
- [ ] `tts document document.md --emotion-profile marketing` - Marketing emotion
- [ ] `tts document document.md --emotion-profile narrative` - Narrative emotion
- [ ] `tts document document.md --emotion-profile tutorial` - Tutorial emotion
- [ ] `tts document document.md --emotion-profile auto` - Auto emotion detection
- [ ] `tts document document.md --rate +20% --pitch +5Hz` - Rate and pitch
- [ ] `tts document document.md --json` - JSON output
- [ ] `tts document document.md --debug` - Debug mode

## Complex Combinations

### Provider + Options
- [ ] `tts @edge "Hello world" --voice en-GB-SoniaNeural --rate +20%` - Provider with voice and rate
- [ ] `tts save @openai "Hello world" -o openai.mp3 --voice alloy` - OpenAI save with voice
- [ ] `tts @elevenlabs "Hello world" --debug` - ElevenLabs with debug
- [ ] `tts speak @google "Hello world" --pitch +10Hz` - Google with pitch adjustment

### Document + Provider
- [ ] `tts document @edge document.md` - Process document with Edge TTS
- [ ] `tts document @openai document.md --save -o openai_doc.mp3` - Document with OpenAI, save
- [ ] `tts document @chatterbox document.md --emotion-profile narrative` - Chatterbox with emotion

### Piped Input Combinations
- [ ] `echo "Test text" | tts @edge` - Pipe to provider shortcut
- [ ] `echo "Test text" | tts save -o piped.mp3 --voice en-US-AriaNeural` - Pipe to save with voice
- [ ] `cat document.txt | tts @openai --debug` - Cat file to provider with debug
- [ ] `echo "Test" | tts speak --rate +50% --pitch +10Hz` - Pipe with multiple options

### Error Conditions
- [ ] `tts @unknown "Hello world"` - Unknown provider shortcut (should error)
- [ ] `tts speak "Hello world" --voice NonexistentVoice` - Invalid voice (should error/warn)
- [ ] `tts save "Hello world" -f invalid_format` - Invalid format (should error)
- [ ] `tts document nonexistent.md` - Nonexistent document (should error)
- [ ] `tts info @invalid` - Invalid provider shortcut for info (should error)
- [ ] `tts install invalid-provider` - Invalid provider for install (should error)

## JSON Output Mode

### JSON with Core Commands
- [ ] `tts save "Hello world" --json` - Save with JSON output
- [ ] `tts document document.md --json` - Document processing with JSON output

### JSON with Info Commands
- [ ] `tts status --json` - Status in JSON format (if supported)
- [ ] `tts providers --json` - Providers list in JSON format (if supported)
- [ ] `tts config --json` - Configuration in JSON format (if supported)

## Integration Testing

### Real Provider Testing (Requires API Keys)
- [ ] `tts @edge "Hello world"` - Test Edge TTS (free, requires internet)
- [ ] `tts @openai "Hello world"` - Test OpenAI TTS (requires API key)  
- [ ] `tts @elevenlabs "Hello world"` - Test ElevenLabs (requires API key)
- [ ] `tts @google "Hello world"` - Test Google TTS (requires API key)
- [ ] `tts @chatterbox "Hello world"` - Test Chatterbox (requires local setup)

### Voice File Testing (Requires Audio Files)
- [ ] `tts voice load test_voice.wav` - Load actual voice file
- [ ] `tts voice status` - Check loaded voices
- [ ] `tts @chatterbox "Hello world"` - Use loaded voice
- [ ] `tts voice unload test_voice.wav` - Unload voice file

### Document Testing (Requires Test Documents)
- [ ] `tts document tests/fixtures/test_markdown.md` - Process real markdown
- [ ] `tts document tests/fixtures/test_html.html` - Process real HTML
- [ ] `tts document tests/fixtures/test_data.json` - Process real JSON

## Testing Summary

### ✅ Expected Working Commands
Based on Phase 2 implementation, these should work:
- All basic speech commands (speak, save)
- Provider shortcuts (@edge, @openai, @elevenlabs, @google, @chatterbox)
- Configuration management (config show/get/set)
- Provider information (info, providers, status)
- Installation system (install)
- Voice management (voice load/unload/status)
- Document processing (document with various formats)
- Debug and JSON output modes

### 🔧 Dependencies Required for Full Testing
- **Audio playback**: ffplay (for streaming audio)
- **Audio conversion**: ffmpeg (for format conversion)
- **API keys**: OpenAI, ElevenLabs, Google Cloud for respective providers
- **Local setup**: Chatterbox server for voice cloning features
- **Test files**: Sample documents, voice files for comprehensive testing

### 📊 Test Categories
1. **Unit Tests**: CLI argument parsing, hook implementations
2. **Integration Tests**: Real provider API calls (costs money)
3. **Audio Tests**: Actual audio generation and playback
4. **Error Handling**: Invalid inputs, missing dependencies
5. **Performance Tests**: Large documents, multiple voice loading

### 💡 Testing Strategy
1. Run unit tests first (no API costs)
2. Test with Edge TTS (free, requires internet)
3. Test premium providers with minimal API calls
4. Test advanced features (voice loading, document processing)
5. Test error conditions and edge cases

The CLI should maintain 100% functional parity with the original implementation while providing enhanced provider shortcut support and robust error handling.