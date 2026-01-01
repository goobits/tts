# Deprecations

This document tracks deprecated features and their removal timeline for Matilda Voice.

## Scheduled for Removal

### v4.0.0 (next major release)

- [ ] **`play_audio_with_ffplay()` function** - Legacy audio playback function in `src/matilda_voice/audio_utils.py:508`. Use `AudioPlaybackManager` instead for consistent audio playback management.

- [ ] **Legacy format cache (`.pkl` files)** - Pickle-based document cache files in the document processing cache directory. The cache system now uses JSON format (`.json` files). Legacy `.pkl` files are automatically cleaned up during `clear_cache()` operations but will not be read.

## Already Removed

*No features have been fully removed yet.*

## Migration Guide

### Migrating from `play_audio_with_ffplay()` to `AudioPlaybackManager`

The legacy `play_audio_with_ffplay()` function is a thin wrapper that internally uses `AudioPlaybackManager`. Direct usage of `AudioPlaybackManager` is recommended for better control and consistency.

**Old usage:**
```python
from matilda_voice.audio_utils import play_audio_with_ffplay

# Play audio with optional cleanup and timeout
play_audio_with_ffplay("audio.mp3", logger=my_logger, cleanup=True, timeout=30)
```

**New usage:**
```python
from matilda_voice.audio_utils import AudioPlaybackManager, get_audio_manager

# Option 1: Use the global singleton manager (recommended for most cases)
manager = get_audio_manager()
manager.play_and_forget("audio.mp3", cleanup=True, timeout=30)

# Option 2: Create a dedicated manager with custom logger
manager = AudioPlaybackManager(logger=my_logger)
manager.play_and_forget("audio.mp3", cleanup=True, timeout=30)
```

**Benefits of `AudioPlaybackManager`:**
- Singleton pattern for resource efficiency (`get_audio_manager()`)
- Consistent behavior across all Voice providers
- Background playback management
- Built-in cleanup handling
- Better error reporting and logging

### Migrating from `.pkl` to `.json` document cache

The document processing cache (`src/matilda_voice/document_processing/performance_cache.py`) has moved from pickle (`.pkl`) to JSON (`.json`) format.

**No action required** - the cache system automatically:
1. Creates new cache entries in JSON format
2. Cleans up legacy `.pkl` files during `clear_cache()` operations

If you have important cached documents:
1. Run your document processing workflow once to regenerate caches
2. Call `cache.clear_cache()` to remove any legacy `.pkl` files

**Why JSON?**
- Security: Pickle files can execute arbitrary code when loaded
- Interoperability: JSON is human-readable and works across languages
- Debugging: Easy to inspect cache contents
