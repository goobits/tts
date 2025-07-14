# TTS CLI - TODO List

## ✅ Recently Completed
- ✅ **Voice Loading System** - Load voices into memory for 13s → <1s performance
- ✅ **Subcommand Structure** - Clean `tts voices`, `tts models`, `tts config` commands
- ✅ **Configuration System** - Persistent settings with smart voice detection
- ✅ **Pipx Installation** - Modern package isolation and dependency management
- ✅ **System Health Checks** - `tts doctor` command for diagnostics

## Future Integrations

### Additional TTS Services
- [ ] **Azure Cognitive Services** - Microsoft TTS with neural voices
- [ ] **AWS Polly** - Amazon's text-to-speech service
- [ ] **Coqui TTS** - Open-source neural TTS models

## 🚀 Active Development

### API Provider Integration (In Progress)
- [ ] **OpenAI TTS API** - 6 voices (nova, alloy, echo, fable, shimmer, onyx)
- [ ] **Google Cloud TTS API** - 380+ voices with full SSML support  
- [ ] **ElevenLabs API** - Premium voice cloning and custom voices

### Infrastructure Enhancements
- [ ] **Voice Embedding Optimization** - Faster voice loading for local models
- [ ] **Batch Processing** - Process multiple texts efficiently

### API & Security
- [ ] **API Key Management** - Secure storage for external services
  - Environment variable fallbacks
  - Key validation and testing
  - Per-provider key configuration

### Developer Experience
- [ ] **Plugin System** - Easy provider addition framework
- [ ] **Testing Suite** - Comprehensive provider testing
- [ ] **Provider Benchmarking** - Quality, speed, and cost comparison

## Advanced Features
- [ ] **SSML Support** - For Google Cloud TTS and Edge TTS (auto-detection)
- [ ] **Voice Mixing** - Blend multiple voices
- [ ] **Real-time Streaming** - Live audio generation
- [ ] **Voice Training** - Custom voice model creation with Chatterbox