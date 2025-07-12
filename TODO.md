# TTS CLI TODO

## High Priority

- [ ] **Error handling improvements**
  - Add proper exception handling for network failures
  - Handle audio device issues gracefully
  - Add provider-specific error handling

- [ ] **Logging system**
  - Add structured logging for debugging and monitoring TTS operations
  - Configure log levels and output destinations

## Medium Priority

- [ ] **Streaming optimization**
  - Implement true streaming for Edge TTS to reduce latency from ~2.4s to ~0.3-0.5s
  - Start playing audio chunks as they're generated instead of waiting for complete generation

- [x] **Voice discovery** ✅
  - [x] Add `--list-voices` command to show available voices per provider
  - [x] Add `--find-voice` to search voices by language/gender
  - [x] Validate voice names before synthesis to prevent failures
  - [ ] Show voice samples/previews

- [x] **Audio format options** ✅
  - [x] Support multiple output formats (WAV, OGG, FLAC) beyond just MP3
  - [x] Add quality/bitrate options
  - [x] Allow format selection via CLI parameter

- [ ] **SSML support**
  - Add Speech Synthesis Markup Language support for advanced voice control
  - Support pauses: `<break time="2s"/>`
  - Support emphasis: `<emphasis level="strong">text</emphasis>`
  - Support prosody: `<prosody rate="slow" pitch="high">text</prosody>`
  - Support pronunciation: `<phoneme>` tags
  - Support voice switching mid-sentence