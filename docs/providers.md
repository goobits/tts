# Provider Guide

Supported Voice providers and basic setup.

## Providers

- Edge Voice (free)
- OpenAI
- ElevenLabs
- Google Cloud
- Chatterbox (local)

## Setup

```bash
voice config set openai_api_key YOUR_KEY
voice config set elevenlabs_api_key YOUR_KEY
voice config set google_api_key YOUR_KEY
```

## Use a Provider

```bash
voice @edge "Hello"
voice @openai "Hello"
voice @elevenlabs "Hello"
voice @google "Hello"
voice @chatterbox "Hello"
```

## Install Extras

```bash
pip install goobits-matilda-voice[all]
pip install goobits-matilda-voice[openai]
pip install goobits-matilda-voice[google]
pip install goobits-matilda-voice[elevenlabs]
pip install goobits-matilda-voice[chatterbox]
```
