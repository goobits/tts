# TTS CLI

A modular command-line interface for multiple text-to-speech engines.

## Installation

### From source

```bash
# Clone the repository
git clone https://github.com/yourusername/tts-cli.git
cd tts-cli

# Install in development mode
pip install -e .

# Or install specific providers
pip install -e ".[edge_tts]"
pip install -e ".[chatterbox]"
pip install -e ".[all]"  # Install all providers
```

### Install for development

```bash
pip install -e ".[dev]"  # Includes testing and linting tools
```

## Usage

Basic usage:
```bash
tts-cli "Your text here" -m edge_tts
```

With custom output file:
```bash
tts-cli "Your text here" -m edge_tts -o output.mp3
```

With provider-specific options:
```bash
tts-cli "Hello" -m edge_tts voice=en-GB-SoniaNeural rate=+20% pitch=+5Hz
```

Get provider information:
```bash
tts-cli "dummy" -m edge_tts info=true
```

## Available Providers

- **edge_tts**: Free Microsoft Edge TTS (no API key required)
- **chatterbox**: Voice cloning TTS with reference audio support
- **orpheus**: Fast ONNX-based TTS with multiple voices
- **naturalspeech**: Microsoft's high-quality TTS with emotion control
- **maskgct**: Masked Generative Codec Transformer for high-quality TTS

## Provider-Specific Options

### edge_tts
- `voice`: Voice name (default: en-US-JennyNeural)
- `rate`: Speech rate adjustment (e.g., +20%, -10%)
- `pitch`: Pitch adjustment (e.g., +5Hz, -10Hz)

### chatterbox
- `ref_audio`: Path to reference audio file for voice cloning
- `temperature`: Sampling temperature (default: 0.7)

### orpheus
- `voice`: Voice ID (default, alice, bob, charlie, diana)
- `speed`: Speech speed multiplier (default: 1.0)

### naturalspeech
- `emotion`: Emotion style (neutral, happy, sad, angry, surprised)
- `pitch`: Pitch shift in semitones (default: 0.0)
- `energy`: Energy/intensity multiplier (default: 1.0)

### maskgct
- `steps`: Number of denoising steps (default: 50)
- `guidance`: Guidance scale for classifier-free guidance (default: 3.0)
- `temperature`: Sampling temperature (default: 1.0)
- `seed`: Random seed for reproducibility

## Architecture

The CLI uses a plugin-based architecture with:
- Abstract `TTSProvider` base class
- Lazy loading of provider dependencies
- Simple dictionary-based provider registry
- Flexible key=value options system for provider-specific parameters