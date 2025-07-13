# TTS CLI - TODO List

## High Priority Provider Integrations

### External TTS Services
- [ ] **ElevenLabs API** - Premium voice cloning and synthesis
  - Add API key configuration
  - Implement voice cloning workflows
  - Add voice library browsing

- [ ] **Google Cloud Text-to-Speech API** - Enterprise-grade TTS
  - Standard and WaveNet voices
  - SSML support for advanced speech control
  - Multi-language support

- [ ] **OpenAI TTS API** - Latest AI-powered speech synthesis
  - tts-1 and tts-1-hd models
  - Multiple voice options (alloy, echo, fable, nova, shimmer)
  - High-quality neural voices

## CLI Improvements

### Subcommand Structure
- [ ] Implement clean subcommand structure:
  - `tts voices` - List all voices from all providers
  - `tts voices edge_tts` - List voices for specific provider  
  - `tts voices search "irish"` - Search for voices
  - `tts voices preview en-IE-Emily` - Preview a voice
  - `tts models` - List available models

### Configuration Enhancements
- [ ] **API Key Management** - Secure storage and configuration
  - Support for multiple API keys per provider
  - Environment variable fallbacks
  - Key validation and testing

- [ ] **Provider Auto-Selection** - Smart provider choosing
  - Quality vs speed preferences
  - Cost optimization
  - Fallback chains for reliability

## Infrastructure

### Quality & Performance
- [ ] **Provider Benchmarking** - Compare quality, speed, and cost
- [ ] **Caching System** - Cache frequently used audio
- [ ] **Batch Processing** - Process multiple texts efficiently

### Developer Experience  
- [ ] **Plugin System** - Easy provider addition
- [ ] **Testing Suite** - Comprehensive provider testing
- [ ] **Documentation** - Provider integration guides