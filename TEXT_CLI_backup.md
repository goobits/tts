# TTS CLI Command Checklist

This checklist contains all valid command line combinations for the TTS CLI tool.

## Direct Speech Synthesis (Main Command)

### Basic Usage
- [x] `tts "text"` *(Code verified - main command implemented)*
- [x] `tts text without quotes` *(Code verified - Click handles unquoted args)*
- [x] `echo "text" | tts` *(Code verified - stdin support implemented)*

### Provider Shortcuts
- [x] `tts @edge "text"` *(Code verified - PROVIDER_SHORTCUTS['edge'] = 'edge_tts')*
- [x] `tts @openai "text"` *(Code verified - PROVIDER_SHORTCUTS['openai'] = 'openai')*
- [x] `tts @elevenlabs "text"` *(Code verified - PROVIDER_SHORTCUTS['elevenlabs'] = 'elevenlabs')*
- [x] `tts @google "text"` *(Code verified - PROVIDER_SHORTCUTS['google'] = 'google')*
- [x] `tts @chatterbox "text"` *(Code verified - PROVIDER_SHORTCUTS['chatterbox'] = 'chatterbox')*

## Save Command

### Basic Save
- [x] `tts save "text"` *(Code verified - save command with TEXT argument)*
- [x] `tts save "text" -o output.mp3` *(Code verified - -o/--output option defined)*
- [x] `tts save "text" --output output.wav` *(Code verified - long form option)*

### Format Options
- [x] `tts save "text" -f mp3` *(Code verified - -f/--format option with choices=['mp3', 'wav', 'ogg', 'flac'])*
- [x] `tts save "text" -f wav` *(Code verified - format option supports wav)*
- [x] `tts save "text" -f ogg` *(Code verified - format option supports ogg)*
- [x] `tts save "text" -f flac` *(Code verified - format option supports flac)*
- [x] `tts save "text" --format mp3` *(Code verified - long form option)*
- [x] `tts save "text" --format wav` *(Code verified - long form option)*
- [x] `tts save "text" --format ogg` *(Code verified - long form option)*
- [x] `tts save "text" --format flac` *(Code verified - long form option)*

### Voice Selection
- [x] `tts save "text" -v en-US-JennyNeural` *(Code verified - -v/--voice option defined)*
- [x] `tts save "text" --voice en-GB-SoniaNeural` *(Code verified - long form option)*
- [x] `tts save "text" --clone voice.wav` (deprecated) *(Code verified - shows deprecation warning)*

### Audio Adjustments
- [x] `tts save "text" --rate +20%` *(Code verified - --rate option defined)*
- [x] `tts save "text" --rate -50%` *(Code verified - rate accepts percentage values)*
- [x] `tts save "text" --rate 150%` *(Code verified - rate accepts percentage values)*
- [x] `tts save "text" --pitch +5Hz` *(Code verified - --pitch option defined)*
- [x] `tts save "text" --pitch -10Hz` *(Code verified - pitch accepts Hz values)*

### Output Options
- [x] `tts save "text" --json` *(Code verified - --json flag defined)*
- [x] `tts save "text" --debug` *(Code verified - --debug flag defined)*

### Provider + Save
- [x] `tts save @edge "text"` *(Code verified - provider shortcuts work with save)*
- [x] `tts save @openai "text"` *(Code verified - provider shortcuts work with save)*
- [x] `tts save @elevenlabs "text"` *(Code verified - provider shortcuts work with save)*
- [x] `tts save @google "text"` *(Code verified - provider shortcuts work with save)*
- [x] `tts save @chatterbox "text"` *(Code verified - provider shortcuts work with save)*

### Combined Options
- [x] `tts save @edge "text" -o out.mp3 -v en-US-JennyNeural --rate -10%` *(Code verified - all options can be combined)*
- [x] `tts save "text" -o file.wav -f wav --pitch +5Hz --debug` *(Code verified - all options can be combined)*

## Document Command

### Basic Document Processing
- [x] `tts document file.html` *(Code verified - document command with DOCUMENT_PATH argument)*
- [x] `tts document file.md` *(Code verified - supports all file types)*
- [x] `tts document file.json` *(Code verified - supports all file types)*
- [x] `tts document file.txt` *(Code verified - supports all file types)*

### Save Options
- [x] `tts document file.html --save` *(Code verified - --save flag defined)*
- [x] `tts document file.html -o output.mp3` *(Code verified - -o/--output option defined)*
- [x] `tts document file.html --output output.wav` *(Code verified - long form option)*

### Format Options
- [x] `tts document file.html -f mp3` *(Code verified - -f/--format with choices=['mp3', 'wav', 'ogg', 'flac'])*
- [x] `tts document file.html -f wav` *(Code verified - format supports wav)*
- [x] `tts document file.html -f ogg` *(Code verified - format supports ogg)*
- [x] `tts document file.html -f flac` *(Code verified - format supports flac)*
- [x] `tts document file.html --format mp3` *(Code verified - long form option)*
- [x] `tts document file.html --format wav` *(Code verified - long form option)*

### Voice Selection
- [x] `tts document file.html -v en-US-AriaNeural` *(Code verified - -v/--voice option defined)*
- [x] `tts document file.html --voice en-GB-RyanNeural` *(Code verified - long form option)*
- [x] `tts document file.html --clone voice.wav` (deprecated) *(Code verified - shows deprecation warning)*

### Audio Adjustments
- [x] `tts document file.html --rate +15%` *(Code verified - --rate option defined)*
- [x] `tts document file.html --rate -30%` *(Code verified - rate accepts percentage values)*
- [x] `tts document file.html --pitch +10Hz` *(Code verified - --pitch option defined)*
- [x] `tts document file.html --pitch -5Hz` *(Code verified - pitch accepts Hz values)*

### Document Processing Options
- [x] `tts document file.html --doc-format auto` *(Code verified - --doc-format with choices=['auto', 'markdown', 'html', 'json'])*
- [x] `tts document file.html --doc-format markdown` *(Code verified - doc-format supports markdown)*
- [x] `tts document file.html --doc-format html` *(Code verified - doc-format supports html)*
- [x] `tts document file.html --doc-format json` *(Code verified - doc-format supports json)*

### SSML Platform Options
- [x] `tts document file.html --ssml-platform azure` *(Code verified - --ssml-platform with choices=['azure', 'google', 'amazon', 'generic'])*
- [x] `tts document file.html --ssml-platform google` *(Code verified - ssml-platform supports google)*
- [x] `tts document file.html --ssml-platform amazon` *(Code verified - ssml-platform supports amazon)*
- [x] `tts document file.html --ssml-platform generic` *(Code verified - ssml-platform supports generic)*

### Emotion Profile Options
- [x] `tts document file.html --emotion-profile auto` *(Code verified - --emotion-profile with choices=['auto', 'technical', 'marketing', 'narrative', 'tutorial'])*
- [x] `tts document file.html --emotion-profile technical` *(Code verified - emotion-profile supports technical)*
- [x] `tts document file.html --emotion-profile marketing` *(Code verified - emotion-profile supports marketing)*
- [x] `tts document file.html --emotion-profile narrative` *(Code verified - emotion-profile supports narrative)*
- [x] `tts document file.html --emotion-profile tutorial` *(Code verified - emotion-profile supports tutorial)*

### Output Options
- [x] `tts document file.html --json` *(Code verified - --json flag defined)*
- [x] `tts document file.html --debug` *(Code verified - --debug flag defined)*

### Provider + Document
- [x] `tts document @edge file.md` *(Code verified - provider shortcuts work with document)*
- [x] `tts document @openai file.html` *(Code verified - provider shortcuts work with document)*
- [x] `tts document @elevenlabs file.json` *(Code verified - provider shortcuts work with document)*
- [x] `tts document @google file.txt` *(Code verified - provider shortcuts work with document)*
- [x] `tts document @chatterbox file.md` *(Code verified - provider shortcuts work with document)*

### Combined Document Options
- [x] `tts document @edge file.md --save -o out.mp3 --emotion-profile technical` *(Code verified - all options can be combined)*
- [x] `tts document file.html --ssml-platform azure --save --debug` *(Code verified - all options can be combined)*

## Voice Management Commands

### Voice Loading
- [x] `tts voice load voice.wav` *(Code verified - voice load command with VOICE_FILES argument)*
- [x] `tts voice load voice1.wav voice2.mp3` *(Code verified - nargs=-1 for multiple files)*
- [x] `tts voice load /path/to/voice.wav` *(Code verified - accepts any file path)*

### Voice Unloading
- [x] `tts voice unload voice.wav` *(Code verified - voice unload command with VOICE_FILES argument)*
- [x] `tts voice unload voice1.wav voice2.mp3` *(Code verified - nargs=-1 for multiple files)*
- [x] `tts voice unload --all` *(Code verified - --all flag defined)*

### Voice Status
- [x] `tts voice status` *(Code verified - voice status command defined)*

## Configuration Commands

### View Configuration
- [x] `tts config` *(Code verified - config command defaults to 'show' action)*
- [x] `tts config show` *(Code verified - 'show' is a valid action choice)*

### Interactive Configuration
- [x] `tts config voice` *(Code verified - 'voice' is a valid action choice)*
- [x] `tts config provider` *(Code verified - 'provider' is a valid action choice)*
- [x] `tts config format` *(Code verified - 'format' is a valid action choice)*

### Get/Set Configuration
- [x] `tts config get default_voice` *(Code verified - 'get' is a valid action with KEY argument)*
- [x] `tts config get default_provider` *(Code verified - 'get' action supports any key)*
- [x] `tts config get default_format` *(Code verified - 'get' action supports any key)*
- [x] `tts config get openai_api_key` *(Code verified - 'get' action supports any key)*
- [x] `tts config get elevenlabs_api_key` *(Code verified - 'get' action supports any key)*
- [x] `tts config get google_api_key` *(Code verified - 'get' action supports any key)*
- [x] `tts config get google_credentials_path` *(Code verified - 'get' action supports any key)*

- [x] `tts config set default_voice en-US-JennyNeural` *(Code verified - 'set' action with KEY and VALUE arguments)*
- [x] `tts config set default_provider edge_tts` *(Code verified - 'set' action supports any key/value)*
- [x] `tts config set default_format wav` *(Code verified - 'set' action supports any key/value)*
- [x] `tts config set openai_api_key YOUR_KEY` *(Code verified - 'set' action supports any key/value)*
- [x] `tts config set elevenlabs_api_key YOUR_KEY` *(Code verified - 'set' action supports any key/value)*
- [x] `tts config set google_api_key YOUR_KEY` *(Code verified - 'set' action supports any key/value)*
- [x] `tts config set google_credentials_path /path/to/creds.json` *(Code verified - 'set' action supports any key/value)*

### Edit Configuration
- [x] `tts config edit` *(Code verified - 'edit' is a valid action choice)*

## Information Commands

### Provider Information
- [x] `tts info` *(Code verified - info command with optional PROVIDER argument)*
- [x] `tts info edge_tts` *(Code verified - info accepts provider names)*
- [x] `tts info openai` *(Code verified - info accepts provider names)*
- [x] `tts info elevenlabs` *(Code verified - info accepts provider names)*
- [x] `tts info google` *(Code verified - info accepts provider names)*
- [x] `tts info chatterbox` *(Code verified - info accepts provider names)*

### Provider Information (Shortcuts)
- [x] `tts info @edge` *(Code verified - info command handles @provider shortcuts)*
- [x] `tts info @openai` *(Code verified - info command handles @provider shortcuts)*
- [x] `tts info @elevenlabs` *(Code verified - info command handles @provider shortcuts)*
- [x] `tts info @google` *(Code verified - info command handles @provider shortcuts)*
- [x] `tts info @chatterbox` *(Code verified - info command handles @provider shortcuts)*

## Provider Commands

### List Providers
- [x] `tts providers` *(Code verified - providers command with optional PROVIDER_NAME argument)*

### Provider Setup Instructions
- [x] `tts providers edge_tts` *(Code verified - providers accepts provider names)*
- [x] `tts providers openai` *(Code verified - providers accepts provider names)*
- [x] `tts providers elevenlabs` *(Code verified - providers accepts provider names)*
- [x] `tts providers google` *(Code verified - providers accepts provider names)*
- [x] `tts providers chatterbox` *(Code verified - providers accepts provider names)*

### Provider Setup Instructions (Shortcuts)
- [x] `tts providers @edge` *(Code verified - providers handles @provider shortcuts)*
- [x] `tts providers @openai` *(Code verified - providers handles @provider shortcuts)*
- [x] `tts providers @elevenlabs` *(Code verified - providers handles @provider shortcuts)*
- [x] `tts providers @google` *(Code verified - providers handles @provider shortcuts)*
- [x] `tts providers @chatterbox` *(Code verified - providers handles @provider shortcuts)*

## Voice Browser Commands

### Browse All Voices
- [x] `tts voices` *(Code verified - voices command with optional ARGS)*

### Browse Provider Voices
- [x] `tts voices edge_tts` *(Code verified - voices accepts provider names)*
- [x] `tts voices openai` *(Code verified - voices accepts provider names)*
- [x] `tts voices elevenlabs` *(Code verified - voices accepts provider names)*
- [x] `tts voices google` *(Code verified - voices accepts provider names)*
- [x] `tts voices chatterbox` *(Code verified - voices accepts provider names)*

### Browse Provider Voices (Shortcuts)
- [x] `tts voices @edge` *(Code verified - voices handles @provider shortcuts)*
- [x] `tts voices @openai` *(Code verified - voices handles @provider shortcuts)*
- [x] `tts voices @elevenlabs` *(Code verified - voices handles @provider shortcuts)*
- [x] `tts voices @google` *(Code verified - voices handles @provider shortcuts)*
- [x] `tts voices @chatterbox` *(Code verified - voices handles @provider shortcuts)*

## System Commands

### Health Check
- [x] `tts status` *(Code verified - status command defined)*

### Installation
- [x] `tts install edge_tts` *(Code verified - install command with ARGS)*
- [x] `tts install chatterbox cpu` *(Code verified - install handles multiple args)*
- [x] `tts install chatterbox gpu` *(Code verified - install handles multiple args)*

### Version Information
- [x] `tts version` *(Code verified - version command defined)*
- [x] `tts --version` *(Code verified - Click built-in --version flag)*

### Help
- [x] `tts --help` *(Code verified - Click provides --help for all commands)*
- [x] `tts save --help` *(Code verified - save command has help)*
- [x] `tts document --help` *(Code verified - document command has help)*
- [x] `tts voice --help` *(Code verified - voice group has help)*
- [x] `tts config --help` *(Code verified - config command has help)*
- [x] `tts info --help` *(Code verified - info command has help)*
- [x] `tts providers --help` *(Code verified - providers command has help)*
- [x] `tts voices --help` *(Code verified - voices command has help)*
- [x] `tts status --help` *(Code verified - status command has help)*
- [x] `tts install --help` *(Code verified - install command has help)*
- [x] `tts version --help` *(Code verified - version command has help)*

## Pipeline Examples

### Basic Pipelines
- [x] `echo "Hello world" | tts` *(Code verified - stdin support via click.get_text_stream)*
- [x] `cat file.txt | tts` *(Code verified - stdin support for any piped input)*
- [x] `echo "Hello" | tts @edge` *(Code verified - stdin + provider shortcuts)*
- [x] `echo "Hello" | tts @openai` *(Code verified - stdin + provider shortcuts)*
- [x] `cat document.txt | tts save -o output.mp3` *(Code verified - stdin works with save command)*

### Advanced Pipelines (with other tools)
- [x] `stt recording.wav | tts` *(Code verified - accepts any piped text input)*
- [x] `stt recording.wav | tts @edge` *(Code verified - piped input + provider shortcuts)*
- [x] `ttt "Fix grammar" < essay.txt | tts` *(Code verified - accepts any piped text input)*
- [x] `ttt "Translate to Spanish" < file.txt | tts @google` *(Code verified - piped input + provider shortcuts)*

## Edge Cases and Special Options

### Empty/Special Input
- [x] `tts ""` *(Code verified - handles empty strings)*
- [x] `tts " "` *(Code verified - handles whitespace-only strings)*
- [x] `echo "" | tts` *(Code verified - handles empty piped input)*

### Invalid Provider Shortcuts
- [x] `tts @invalid "text"` (should show error) *(Code verified - proper error handling for unknown shortcuts)*
- [x] `tts info @nonexistent` (should show error) *(Code verified - shows "Unknown provider shortcut" error)*
- [x] `tts voices @unknown` (should show error) *(Code verified - shows "Unknown provider shortcut" error)*

### Deprecated Options
- [x] `tts save "text" --clone voice.wav` (should show deprecation warning) *(Code verified - click.echo shows deprecation message)*
- [x] `tts document file.html --clone voice.wav` (should show deprecation warning) *(Code verified - click.echo shows deprecation message)*

## Notes

- Provider shortcuts (`@edge`, `@openai`, etc.) can be used with most commands that accept text or provider names
- Rate can be specified as percentages: `+20%`, `-50%`, `150%`
- Pitch can be specified in Hz: `+5Hz`, `-10Hz`
- Audio formats supported: `mp3` (default), `wav`, `ogg`, `flac`
- Document formats: `auto` (default), `markdown`, `html`, `json`
- SSML platforms: `azure`, `google`, `amazon`, `generic`
- Emotion profiles: `auto` (default), `technical`, `marketing`, `narrative`, `tutorial`