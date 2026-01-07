# User Guide

Core CLI usage for the Voice tool.

## Basic Usage

```bash
voice "Hello world"
echo "Hello world" | voice
voice save "Hello world" -o greeting.mp3
```

## Providers

```bash
voice @edge "Hello"
voice @openai "Hello"
voice @elevenlabs "Hello"
voice @google "Hello"
voice @chatterbox "Hello"
```

## Voices

```bash
voice voices
voice @edge --list-voices
voice @openai --list-voices
voice @google --list-voices
```

## Configuration

```bash
voice config show
voice config set default_provider edge_tts
voice config set default_voice edge_tts:en-US-AriaNeural
```

## Document Processing

```bash
voice document file.html
voice document file.md --emotion-profile technical
voice document file.json --save
```

## Status

```bash
voice status
voice providers
```
