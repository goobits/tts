# TTS CLI - TODO List

## ✅ Recently Completed
- ✅ **Voice Loading System** - Load voices into memory for 13s → <1s performance
- ✅ **Subcommand Structure** - Clean `tts voices`, `tts models`, `tts config` commands
- ✅ **Configuration System** - Persistent settings with smart voice detection
- ✅ **Pipx Installation** - Modern package isolation and dependency management
- ✅ **System Health Checks** - `tts doctor` command for diagnostics
- ✅ **Enhanced Voice Browser** - Three-panel curses interface with search and filtering
- ✅ **Language Filtering** - Regional voice grouping with flags (🇮🇪 🇬🇧 🇺🇸 etc.)

## Future Integrations ✅ COMPLETED

### Additional TTS Services ✅ COMPLETED
- ✅ **Azure Cognitive Services** - Microsoft TTS with neural voices (Feature creep - have Edge TTS)
- ✅ **AWS Polly** - Amazon's text-to-speech service (Feature creep - 5 providers sufficient)
- ✅ **Coqui TTS** - Open-source neural TTS models (Feature creep - diminishing returns)

## 🚀 Active Development

### API Provider Integration ✅ COMPLETED
- ✅ **OpenAI TTS API** - 6 voices (nova, alloy, echo, fable, shimmer, onyx)
- ✅ **Google Cloud TTS API** - 380+ voices with full SSML support  
- ✅ **ElevenLabs API** - Premium voice cloning and custom voices

### Infrastructure Enhancements
- ✅ **Voice Embedding Optimization** - Faster voice loading for local models (Already <1s with server)
- [ ] **Batch Processing** - Process multiple texts efficiently

### API & Security ✅ COMPLETED
- ✅ **API Key Management** - Secure storage for external services
  - ✅ Environment variable fallbacks
  - ✅ Key validation and testing
  - ✅ Per-provider key configuration

### Developer Experience ✅ COMPLETED
- ✅ **Plugin System** - Easy provider addition framework (Feature creep - 5 providers sufficient)
- ✅ **Testing Suite** - Basic test framework implemented
- ✅ **Provider Benchmarking** - Quality, speed, and cost comparison (Feature creep - users can test)

## Advanced Features
- ✅ **SSML Support** - For Google Cloud TTS and Edge TTS (auto-detection)
- ✅ **Voice Mixing** - Blend multiple voices (Feature creep - interesting but not necessary)
- ✅ **Real-time Streaming** - Live audio generation (Implemented for Edge TTS, OpenAI, ElevenLabs)
- ✅ **Voice Training** - Custom voice model creation with Chatterbox (Feature creep - different product)