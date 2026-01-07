# Integration Tests

Real provider integration tests (requires API keys).

## Setup

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_TTS_API_KEY="your-google-api-key"
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
```

## Run

```bash
python -m pytest tests/integration/ -v
python -m pytest tests/integration/providers/test_openai_integration.py -v
```
