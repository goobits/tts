"""Interactive voice browser UI module for TTS CLI.

This module provides a comprehensive curses-based user interface for browsing,
filtering, and previewing TTS voices across multiple providers. It features:

- Three-panel layout with filters, voice list, and preview
- Real-time voice preview with background audio playback
- Advanced filtering by provider, language, gender, quality
- Mouse and keyboard navigation support
- Voice quality analysis and metadata extraction
- Interactive voice selection and configuration

The voice browser is launched via the 'tts voices' command and provides
an intuitive way to explore and test available TTS voices before use.
"""

from .browser_commands import (
    handle_voices_command,
    interactive_voice_browser,
    show_browser_snapshot,
)
from .browser_ui import VoiceBrowser
from .voice_analyzer import analyze_voice

__all__ = [
    # Voice analysis
    "analyze_voice",
    # Browser UI
    "VoiceBrowser",
    # Command handlers
    "interactive_voice_browser",
    "show_browser_snapshot",
    "handle_voices_command",
]
