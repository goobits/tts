# TTS CLI TODO

## High Priority

- [x] **Error handling improvements** ✅
  - [x] Add proper exception handling for network failures
  - [x] Handle audio device issues gracefully  
  - [x] Add provider-specific error handling
  - [x] File permission checks before synthesis

- [x] **Logging system** ✅
  - [x] Add structured logging for debugging and monitoring TTS operations
  - [x] Configure log levels and output destinations
  - [x] Create ./logs/tts.log with INFO/WARNING/ERROR levels
  - [x] Log synthesis attempts, errors, timing, and file operations

## Medium Priority

- [ ] **Streaming optimization**
  - Implement true streaming for Edge TTS to reduce latency from ~2.4s to ~0.3-0.5s
  - Start playing audio chunks as they're generated instead of waiting for complete generation

- [x] **Voice discovery** ✅
  - [x] Add `--list-voices` command to show available voices per provider (322 voices for edge_tts)
  - [x] Add `--find-voice` to search voices by language/gender
  - [x] Validate voice names before synthesis to prevent failures
  - [x] Set edge_tts as default model (no -m required)
  - [x] Show voice samples/previews with `--preview-voice` command

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