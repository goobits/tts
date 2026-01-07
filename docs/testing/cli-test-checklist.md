# CLI Test Checklist

Minimal manual checklist for CLI validation.

## Basic
- `voice "Hello world"`
- `echo "Hello world" | voice`
- `voice --version`
- `voice --help`

## Providers
- `voice @edge "Hello"`
- `voice @openai "Hello"`
- `voice @elevenlabs "Hello"`
- `voice @google "Hello"`
- `voice @chatterbox "Hello"`

## Save
- `voice save "Hello world" -o test.mp3`
- `voice save "Hello world" --format wav -o test.wav`

## Config
- `voice config show`
- `voice config set default_provider edge_tts`

## Document
- `voice document tests/fixtures/technical_document.md --save`
