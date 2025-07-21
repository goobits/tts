#!/usr/bin/env python3

import rich_click as click

# Configure rich-click to enable markup - MUST be first!
click.rich_click.USE_RICH_MARKUP = True

# Apply Dracula theme colors
click.rich_click.STYLE_OPTION = "#ff79c6"      # Dracula Pink - for option flags
click.rich_click.STYLE_ARGUMENT = "#8be9fd"    # Dracula Cyan - for argument types  
click.rich_click.STYLE_COMMAND = "#50fa7b"     # Dracula Green - for subcommands
click.rich_click.STYLE_USAGE = "#bd93f9"       # Dracula Purple - for "Usage:" line
click.rich_click.STYLE_HELPTEXT = "#b3b8c0"    # Light gray - for help descriptions

# Configure rich-click to sort commands alphabetically
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.COMMAND_GROUPS = {
    "tts": [
        {
            "name": "Commands",
            "commands": [],  # Empty list will include all commands
        }
    ]
}
click.rich_click.OPTION_GROUPS = {
    "tts": [],  # No custom option groups
}
# Sort commands alphabetically
click.rich_click.OPTIONS_PANEL_TITLE = "Options"
click.rich_click.COMMANDS_PANEL_TITLE = "Commands"
# Set max width to prevent wrapping issues
click.rich_click.MAX_WIDTH = 120
click.rich_click.STYLE_COMMANDS_TABLE_PADDING = (0, 1)

"""TTS CLI - Text-to-Speech Command Line Interface.

This module provides the main CLI entry point for the TTS CLI application,
which supports multiple TTS providers with smart auto-selection and voice
cloning capabilities. The CLI offers comprehensive functionality including:

**Core Features:**
- Text-to-speech synthesis with multiple providers
- Real-time audio streaming with minimal latency
- File output in various formats (MP3, WAV, etc.)
- Interactive voice browser with advanced filtering
- Provider-specific voice cloning (Chatterbox)
- Configuration management with XDG compliance

**Supported Providers:**
- Edge TTS (Microsoft Azure): Free, high-quality neural voices
- Chatterbox: Local voice cloning with GPU/CPU support
- OpenAI TTS: API-based synthesis with premium voices
- Google Cloud TTS: Google's neural voices via REST API
- ElevenLabs: Advanced voice synthesis and cloning

**Main Commands:**
- `tts "text"` - Synthesize and stream audio
- `tts "text" --save` - Save audio to file
- `tts voices` - Interactive voice browser
- `tts config` - Configuration management
- `tts status` - System health check

**Usage Examples:**
```bash
tts "Hello world"                    # Stream with default voice
tts "Hello" --voice edge_tts:en-US-JennyNeural --save
tts voices                           # Browse available voices
tts config voice edge_tts:en-US-AriaNeural
```

The CLI uses a pluggable provider architecture with dynamic loading,
centralized configuration, and comprehensive error handling.
"""

import importlib
import json
import logging
import signal
import subprocess  # Still needed for doctor command and other CLI operations
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

from .__version__ import __version__
from .base import TTSProvider
from .config import (
    get_default_config,
    load_config,
    parse_voice_setting,
    save_config,
    set_api_key,
    set_setting,
    validate_api_key,
)
from .core import get_tts_engine, initialize_tts_engine
from .exceptions import (
    DependencyError,
    ProviderLoadError,
    ProviderNotFoundError,
    TTSError,
)
from .voice_browser import (
    handle_voices_command,
)
from .voice_manager import VoiceManager

PROVIDERS: Dict[str, str] = {
    "chatterbox": ".providers.chatterbox.ChatterboxProvider",
    "edge_tts": ".providers.edge_tts.EdgeTTSProvider",
    "openai": ".providers.openai_tts.OpenAITTSProvider",
    "google": ".providers.google_tts.GoogleTTSProvider",
    "elevenlabs": ".providers.elevenlabs.ElevenLabsProvider",
}

# Provider shortcuts mapping for @provider syntax
PROVIDER_SHORTCUTS: Dict[str, str] = {
    "edge": "edge_tts",
    "openai": "openai",
    "elevenlabs": "elevenlabs",
    "google": "google",
    "chatterbox": "chatterbox"
}


class DefaultCommandGroup(click.RichGroup):
    """
    A custom Click group that handles direct text synthesis when no subcommand is specified.
    """
    def resolve_command(
        self, ctx: click.Context, args: List[str]
    ) -> Tuple[Optional[str], Optional[click.Command], List[str]]:
        # If no args, this could be stdin input or help request
        if not args:
            # Set flag for direct synthesis and let main() handle stdin detection
            ctx.meta['direct_synthesis'] = True
            ctx.meta['synthesis_args'] = []
            return None, self.callback, args

        # If the first arg is a known option (like --help or --list),
        # let default handling take over.
        if args[0].startswith('-'):
            return super().resolve_command(ctx, args)

        # Check if the first argument is a subcommand.
        command_names = self.list_commands(ctx)
        if args[0] in command_names:
            # It's a subcommand, let Click handle it normally.
            return super().resolve_command(ctx, args)

        # The first argument is not a subcommand, so we assume it's text for direct synthesis
        # Store args for direct synthesis handling
        ctx.meta['direct_synthesis'] = True
        ctx.meta['synthesis_args'] = args
        # Return the group's callback name so Click can invoke main()
        return None, self.callback, args


def parse_provider_shortcut(args: List[str]) -> Tuple[Optional[str], List[str]]:
    """Parse @provider shortcut from arguments and return (provider, remaining_args).

    The @provider shortcut is only recognized when it's the first argument after
    the main command or subcommand to avoid ambiguity with user text.

    Returns:
        Tuple of (provider_name, remaining_args) where provider_name is None if no shortcut found
    """
    if not args:
        return None, args

    # Check if first argument is a provider shortcut
    first_arg = args[0]
    if first_arg.startswith('@'):
        shortcut = first_arg[1:]
        if shortcut in PROVIDER_SHORTCUTS:
            provider_name = PROVIDER_SHORTCUTS[shortcut]
            return provider_name, args[1:]  # Return provider and remaining args
        else:
            # Unknown shortcut - show error
            click.echo(f"❌ Error: Unknown provider shortcut '@{shortcut}'", err=True)
            shortcuts = [f"@{s}" for s in PROVIDER_SHORTCUTS.keys()]
            click.echo(f"💡 Available providers: {', '.join(shortcuts)}", err=True)
            click.echo("💡 Use 'tts providers' to see detailed information.", err=True)
            sys.exit(1)

    return None, args


def setup_logging() -> logging.Logger:
    """Setup logging configuration for TTS CLI"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors on console
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(logs_dir / "tts.log")
    file_handler.setLevel(logging.INFO)  # Log everything to file
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.DEBUG,  # Capture everything
        handlers=[file_handler, console_handler]
    )

    # Get logger for this module
    return logging.getLogger(__name__)


def parse_input(text: str) -> Tuple[str, Dict]:
    """Parse input as JSON or plain text. Returns (text, params_dict)"""
    if text and text.strip().startswith('{'):
        try:
            data = json.loads(text)
            if 'text' in data and isinstance(data['text'], str):
                return data.pop('text'), data  # Extract text, return rest as params
        except json.JSONDecodeError:
            pass
    return text, {}  # Plain text input


def handle_direct_synthesis(args: List[str]) -> None:
    """Handle direct text synthesis without a subcommand.
    
    Enables commands like: tts "Hello world"
    """
    # Parse provider shortcuts from the arguments
    provider_from_shortcut = None
    final_text = None
    final_options = []

    # Handle case where args is empty (stdin input)
    if not args:
        final_text = None
        final_options = []
    else:
        # Check if first arg starts with @provider shortcut
        if args[0].startswith('@'):
            provider_from_shortcut, remaining_args = parse_provider_shortcut(args)
            if remaining_args:
                final_text = remaining_args[0] if remaining_args else None
                final_options = remaining_args[1:] if len(remaining_args) > 1 else []
            else:
                final_text = None
                final_options = []
        else:
            # First arg is text, check if second arg is @provider
            final_text = args[0]
            remaining_args = args[1:]
            
            if remaining_args and remaining_args[0].startswith('@'):
                provider_from_shortcut, options_after_provider = parse_provider_shortcut(remaining_args)
                final_options = options_after_provider
            else:
                final_options = remaining_args

    # If we have text and options that don't look like actual options, combine them
    # This handles the case: tts Hello world (without quotes)
    if final_text and final_options:
        # Check if the options look like plain text (not CLI options or key=value pairs)
        text_like_options = []
        remaining_options = []

        for opt in final_options:
            # If it doesn't start with - and doesn't contain =, it's likely part of the text
            if not opt.startswith('-') and '=' not in opt and not opt.startswith('@'):
                text_like_options.append(opt)
            else:
                # Once we hit a real option, collect the rest as options
                remaining_options.append(opt)
                remaining_options.extend(final_options[final_options.index(opt) + 1:])
                break

        if text_like_options:
            # Combine the text with the text-like options
            final_text = final_text + ' ' + ' '.join(text_like_options)
            final_options = remaining_options

    # Setup logging
    logger = setup_logging()

    # Initialize core TTS engine
    initialize_tts_engine(PROVIDERS)

    # Load configuration first
    user_config = load_config()

    # Use provider from shortcut if detected, otherwise fall back to config
    final_model = provider_from_shortcut

    # Apply configuration defaults where CLI args weren't provided
    if not final_model:
        config_voice = user_config.get('voice', 'edge_tts:en-IE-EmilyNeural')
        provider, _ = parse_voice_setting(config_voice)
        final_model = provider or 'edge_tts'

    # Handle voice configuration
    final_voice = None
    config_voice = user_config.get('voice')
    if config_voice:
        _, final_voice = parse_voice_setting(config_voice)

    # Validate model/provider early
    if final_model not in PROVIDERS:
        click.echo(f"❌ Error: Unknown provider: {final_model}", err=True)
        sys.exit(1)

    # Set default output and format
    output = "output.wav"
    output_format = user_config.get('format', 'mp3')

    # Check required arguments - try stdin if no text provided
    if not final_text:
        # Check if text is being piped in
        if not sys.stdin.isatty():
            # Read from stdin
            try:
                final_text = sys.stdin.read().strip()
                if not final_text:
                    # Show help when empty stdin is provided
                    click.echo("❌ Error: No text provided via stdin", err=True)
                    sys.exit(1)
                logger.debug(f"Read {len(final_text)} characters from stdin")
            except Exception as e:
                logger.error(f"Failed to read from stdin: {e}")
                click.echo("📥 Error: Failed to read text from stdin", err=True)
                sys.exit(1)
        else:
            # Error when no text is provided
            click.echo("❌ Error: You must provide text to synthesize", err=True)
            click.echo("💡 Usage: tts \"Hello world\" or echo \"text\" | tts", err=True)
            sys.exit(1)

    # Parse JSON input if provided and override parameters
    final_text, json_params = parse_input(final_text)
    if json_params:
        # Override CLI parameters with JSON values
        final_voice = json_params.get('voice', final_voice)
        output = json_params.get('output_path', output)
        output_format = json_params.get('format', output_format)

    # In streaming mode, display the text being spoken
    click.echo(final_text)

    # Handle main synthesis - direct synthesis is always streaming (save=False)
    handle_synthesize(
        final_text, final_model, output, False, final_voice, None, output_format,
        tuple(final_options), logger, False, False, None, None
    )


def format_output(
    success: bool,
    provider: Optional[str] = None,
    voice: Optional[str] = None,
    action: Optional[str] = None,
    duration: Optional[float] = None,
    output_path: Optional[str] = None,
    error: Optional[str] = None,
    error_code: Optional[str] = None,
    json_output: bool = False,
    debug: bool = False
) -> str:
    """Format output as JSON or human-readable text"""
    if json_output:
        if success:
            result: Dict[str, Any] = {"success": True}
            if provider:
                result["provider"] = provider
            if voice:
                result["voice"] = voice
            if action:
                result["action"] = action
            if duration is not None:
                result["duration_seconds"] = duration
            if output_path:
                result["output_path"] = output_path
        else:
            result: Dict[str, Any] = {"success": False}
            if error:
                result["error"] = error
            if error_code:
                result["error_code"] = error_code
        return json.dumps(result)
    else:
        if success:
            # In standard mode (not debug), only show output for saves
            if not debug and action == "stream":
                return ""  # Silent for streaming in standard mode
            elif action == "save" and output_path:
                return f"Saved to: {output_path}"
            elif debug:
                if action == "stream":
                    return f"✅ Streaming complete ({duration:.2f}s) with {provider}"
                else:
                    return f"✅ Saved to {output_path} ({duration:.2f}s) with {provider}"
            else:
                return ""  # Silent in standard mode
        else:
            return f"Error: {error}" if error else "Error occurred"


def load_provider(name: str) -> Type[TTSProvider]:
    if name not in PROVIDERS:
        raise ProviderNotFoundError(f"Unknown provider: {name}")

    try:
        module_path, class_name = PROVIDERS[name].rsplit(".", 1)
        module = importlib.import_module(module_path, package=__package__)
        provider_class: Type[TTSProvider] = getattr(module, class_name)

        if not issubclass(provider_class, TTSProvider):
            raise ProviderLoadError(f"{provider_class} is not a TTSProvider")

        return provider_class
    except ImportError as e:
        raise ProviderLoadError(f"Failed to load provider {name}: {e}") from e
    except AttributeError as e:
        raise ProviderLoadError(f"Provider class not found for {name}: {e}") from e



def handle_save_command(text: str, provider: Optional[str] = None, **kwargs: Any) -> None:
    """Handle the new 'tts save' subcommand"""
    # Extract common options from kwargs
    output = kwargs.get('output')
    voice = kwargs.get('voice')
    clone = kwargs.get('clone')
    output_format = kwargs.get('output_format')
    options = kwargs.get('options', ())
    json_output = kwargs.get('json_output', False)
    debug = kwargs.get('debug', False)
    rate = kwargs.get('rate')
    pitch = kwargs.get('pitch')

    # Load config to get default provider if not specified
    if not provider:
        config = load_config()
        config_voice = config.get('voice', 'edge_tts:en-IE-EmilyNeural')
        parsed_provider, _ = parse_voice_setting(config_voice)
        provider = parsed_provider or 'edge_tts'

    # Set default output if not provided
    if not output:
        config = load_config()
        output_dir = Path(config.get('output_dir', '~/Downloads')).expanduser()
        output = str(output_dir / "output.wav")

    # Ensure we're saving
    save = True

    # Setup logging
    logger = setup_logging()

    # Call the existing synthesis handler with save=True
    handle_synthesize(
        text, provider, output, save, voice or "", clone or "",
        output_format or "wav", options, logger, json_output, debug, rate, pitch
    )


def handle_document_command(document_path: str, provider: str = None, **kwargs) -> None:
    """Handle the new 'tts document' subcommand"""
    # Extract document processing options
    doc_format = kwargs.get('doc_format', 'auto')
    ssml_platform = kwargs.get('ssml_platform', 'generic')
    emotion_profile = kwargs.get('emotion_profile', 'auto')
    debug = kwargs.get('debug', False)
    save = kwargs.get('save', False)

    # Process the document
    text = handle_document_processing(
        document_path=document_path,
        doc_format=doc_format,
        ssml_platform=ssml_platform,
        emotion_profile=emotion_profile,
        debug=debug
    )

    if not text:
        click.echo("❌ Error: Failed to process document", err=True)
        sys.exit(1)

    # If save flag is set, synthesize the processed text
    if save or any(k in kwargs for k in ['output', 'output_format']):
        # Extract synthesis options
        output = kwargs.get('output')
        voice = kwargs.get('voice')
        clone = kwargs.get('clone')
        output_format = kwargs.get('output_format')
        options = kwargs.get('options', ())
        json_output = kwargs.get('json_output', False)
        rate = kwargs.get('rate')
        pitch = kwargs.get('pitch')

        # Load config to get default provider if not specified
        if not provider:
            config = load_config()
            config_voice = config.get('voice', 'edge_tts:en-IE-EmilyNeural')
            provider, _ = parse_voice_setting(config_voice)
            provider = provider or 'edge_tts'

        # Setup logging
        logger = setup_logging()

        # Call synthesis handler
        handle_synthesize(
            text, provider, output, save, voice, clone, output_format,
            options, logger, json_output, debug, rate, pitch
        )
    else:
        # Just output the processed text
        click.echo(text)


def handle_voice_subcommand(subcommand: str, args: tuple) -> None:
    """Handle voice subcommand group: load, unload, status"""
    if subcommand == "load":
        handle_load_command(args)
    elif subcommand == "unload":
        handle_unload_command(args)
    elif subcommand == "status":
        handle_status_command()
    else:
        click.echo(f"❌ Error: Unknown voice subcommand '{subcommand}'", err=True)
        click.echo("💡 Available voice commands: load, unload, status", err=True)
        sys.exit(1)


def handle_providers_command() -> None:
    """Enhanced providers command with emoji-rich display and status checking"""
    click.echo("🏢 Available TTS Providers:")
    click.echo()
    
    # Provider metadata with emojis and descriptions
    provider_info = {
        "edge_tts": {
            "emoji": "🌐",
            "name": "Edge TTS",
            "description": "Free Microsoft Azure voices",
            "shortcut": "@edge",
            "default_voice_count": "300+"
        },
        "openai": {
            "emoji": "🤖", 
            "name": "OpenAI",
            "description": "Premium AI voices",
            "shortcut": "@openai",
            "default_voice_count": "6"
        },
        "elevenlabs": {
            "emoji": "🎭",
            "name": "ElevenLabs", 
            "description": "Advanced voice cloning",
            "shortcut": "@elevenlabs",
            "default_voice_count": "30+"
        },
        "chatterbox": {
            "emoji": "🏠",
            "name": "Chatterbox",
            "description": "Local voice synthesis", 
            "shortcut": "@chatterbox",
            "default_voice_count": "Custom"
        },
        "google": {
            "emoji": "☁️",
            "name": "Google Cloud TTS",
            "description": "Google neural voices",
            "shortcut": "@google", 
            "default_voice_count": "200+"
        }
    }
    
    # Load config to check API keys
    config = load_config()
    
    for provider_name in PROVIDERS.keys():
        if provider_name not in provider_info:
            continue
            
        info = provider_info[provider_name]
        
        # Check provider status
        status_emoji = "❌"
        status_text = "Not available"
        voice_count = info["default_voice_count"]
        
        try:
            provider_class = load_provider(provider_name)
            provider = provider_class()
            
            # Get actual info if available
            try:
                provider_data = provider.get_info()
                if provider_data and 'sample_voices' in provider_data:
                    voice_count = str(len(provider_data['sample_voices']))
            except:
                pass  # Use default voice count
                
            # Check specific provider status
            if provider_name == "edge_tts":
                status_emoji = "✅"
                status_text = "Ready"
            elif provider_name == "openai":
                if config.get("openai_api_key"):
                    status_emoji = "✅"
                    status_text = "Ready"
                else:
                    status_emoji = "⚠️"
                    status_text = "API key required"
            elif provider_name == "elevenlabs":
                if config.get("elevenlabs_api_key"):
                    status_emoji = "✅"
                    status_text = "Ready"
                else:
                    status_emoji = "❌"
                    status_text = "Not configured"
            elif provider_name == "google":
                if config.get("google_api_key") or config.get("google_credentials_path"):
                    status_emoji = "✅"
                    status_text = "Ready"
                else:
                    status_emoji = "⚠️"
                    status_text = "API key required"
            elif provider_name == "chatterbox":
                # Check for PyTorch and voice files
                try:
                    provider._lazy_load()  # This will check dependencies
                    from pathlib import Path
                    voices_dir = Path("./voices/")
                    voice_files = []
                    if voices_dir.exists():
                        voice_files = list(voices_dir.glob("*.wav")) + list(voices_dir.glob("*.mp3"))
                    
                    if voice_files:
                        status_emoji = "✅"
                        status_text = "Ready"
                        voice_count = str(len(voice_files))
                    else:
                        status_emoji = "⚠️"
                        status_text = "No voice files"
                except:
                    status_emoji = "❌"
                    status_text = "Not installed"
                    
        except Exception:
            status_emoji = "❌"
            status_text = "Not available"
        
        # Display provider info
        click.echo(f"{info['emoji']} {info['name']}")
        click.echo(f"   {info['description']}")
        click.echo(f"   Shortcut: {info['shortcut']}")
        click.echo(f"   Voices: {voice_count}")
        click.echo(f"   Status: {status_emoji} {status_text}")
        click.echo()
    
    click.echo("💡 Run 'tts providers <name>' for setup instructions.")


def handle_provider_setup_instructions(provider_name: str) -> None:
    """Show setup instructions for a specific provider"""
    # Handle @provider shortcuts
    if provider_name.startswith('@'):
        shortcut = provider_name[1:]
        if shortcut in PROVIDER_SHORTCUTS:
            provider_name = PROVIDER_SHORTCUTS[shortcut]
        else:
            click.echo(f"❌ Unknown provider shortcut '@{shortcut}'", err=True)
            click.echo(f"Available providers: {', '.join('@' + s for s in PROVIDER_SHORTCUTS.keys())}", err=True)
            sys.exit(1)
    
    # Provider setup instructions
    setup_instructions = {
        "edge_tts": {
            "emoji": "🌐",
            "name": "Edge TTS",
            "status": "✅ Ready - No setup required",
            "instructions": [
                "Edge TTS is free and works out of the box!",
                "No API keys or installation needed.",
                "300+ voices available from Microsoft Azure."
            ],
            "examples": [
                "tts @edge \"Hello world\"",
                "tts @edge \"Hello\" --voice en-US-JennyNeural",
                "tts voices  # Browse available voices"
            ]
        },
        "openai": {
            "emoji": "🤖", 
            "name": "OpenAI",
            "status": "⚠️ Requires API key",
            "instructions": [
                "1. Get API key from https://platform.openai.com/api-keys",
                "2. Set your API key: tts config set openai_api_key YOUR_KEY",
                "3. Verify setup: tts @openai \"Hello world\""
            ],
            "examples": [
                "tts @openai \"Hello world\"",
                "tts @openai \"Hello\" --voice nova",
                "tts @openai \"Hello\" --voice alloy"
            ]
        },
        "elevenlabs": {
            "emoji": "🎭",
            "name": "ElevenLabs",
            "status": "❌ Requires API key and account",
            "instructions": [
                "1. Create account at https://elevenlabs.io",
                "2. Get API key from your profile settings",
                "3. Set your API key: tts config set elevenlabs_api_key YOUR_KEY",
                "4. Verify setup: tts @elevenlabs \"Hello world\""
            ],
            "examples": [
                "tts @elevenlabs \"Hello world\"",
                "tts @elevenlabs \"Hello\" --voice Rachel",
                "tts voices @elevenlabs  # Browse ElevenLabs voices"
            ]
        },
        "chatterbox": {
            "emoji": "🏠",
            "name": "Chatterbox",
            "status": "❌ Requires installation and voice files",
            "instructions": [
                "1. Install dependencies: tts install chatterbox gpu",
                "2. Place voice files (.wav/.mp3) in ./voices/ directory",
                "3. Load a voice: tts voice load voices/my_voice.wav",
                "4. Test synthesis: tts @chatterbox \"Hello world\""
            ],
            "examples": [
                "tts @chatterbox \"Hello world\"",
                "tts @chatterbox \"Hello\" --voice ./voices/my_voice.wav",
                "tts voice status  # Check loaded voices"
            ]
        },
        "google": {
            "emoji": "☁️",
            "name": "Google Cloud TTS",
            "status": "⚠️ Requires API key or service account",
            "instructions": [
                "Option 1 - API Key:",
                "  1. Enable Cloud TTS API in Google Cloud Console",
                "  2. Create API key with TTS permissions",
                "  3. Set key: tts config set google_api_key YOUR_KEY",
                "",
                "Option 2 - Service Account:",
                "  1. Create service account in Google Cloud Console",
                "  2. Download JSON credentials file",
                "  3. Set path: tts config set google_credentials_path /path/to/creds.json"
            ],
            "examples": [
                "tts @google \"Hello world\"",
                "tts @google \"Hello\" --voice en-US-Standard-A",
                "tts voices @google  # Browse Google voices"
            ]
        }
    }
    
    if provider_name not in setup_instructions:
        click.echo(f"❌ Unknown provider: {provider_name}", err=True)
        click.echo(f"Available providers: {', '.join(PROVIDERS.keys())}", err=True)
        sys.exit(1)
    
    info = setup_instructions[provider_name]
    
    click.echo(f"{info['emoji']} {info['name']} Setup")
    click.echo("━" * (len(info['name']) + 8))
    click.echo()
    click.echo(f"Status: {info['status']}")
    click.echo()
    click.echo("📋 Setup Instructions:")
    for instruction in info['instructions']:
        if instruction == "":
            click.echo()
        else:
            click.echo(f"   {instruction}")
    click.echo()
    click.echo("💡 Usage Examples:")
    for example in info['examples']:
        click.echo(f"   {example}")


def handle_config_commands(action: str, key: str = None, value: str = None) -> None:
    """Handle --config subcommands"""
    if action == "show":
        config = load_config()
        click.echo("⚙️  TTS Configuration:")
        click.echo()
        
        # API Keys section
        click.echo("🔑 API Keys:")
        api_keys = {
            'openai_api_key': 'OpenAI',
            'elevenlabs_api_key': 'ElevenLabs', 
            'google_api_key': 'Google Cloud',
            'google_credentials_path': 'Google Credentials'
        }
        
        for key, display_name in api_keys.items():
            value = config.get(key)
            if value:
                if key == 'google_credentials_path':
                    click.echo(f"  {display_name}: {value} (✅ set)")
                else:
                    # Mask API keys for security
                    masked = value[:8] + "..." + value[-3:] if len(value) > 11 else value[:3] + "..."
                    click.echo(f"  {display_name}: {masked} (✅ set)")
            else:
                click.echo(f"  {display_name}: ❌ not set")
        
        click.echo()
        click.echo("🎤 Defaults:")
        voice = config.get('voice', 'edge_tts:en-IE-EmilyNeural')
        provider, voice_name = voice.split(':', 1) if ':' in voice else (voice, 'default')
        click.echo(f"  provider: {provider}")
        click.echo(f"  voice: {voice_name}")
        click.echo(f"  output_format: {config.get('output_format', 'mp3')}")
        
        click.echo()
        click.echo("🎛️  Audio Settings:")
        click.echo(f"  rate: {config.get('rate', '+0%')}")
        click.echo(f"  pitch: {config.get('pitch', '+0Hz')}")
        click.echo(f"  streaming_enabled: {config.get('streaming_enabled', True)}")
        
        click.echo()
        click.echo("💾 Paths:")
        from pathlib import Path
        config_path = Path.home() / ".config" / "tts" / "config.json"
        cache_path = Path.home() / ".cache" / "tts"
        logs_path = Path.home() / ".local" / "share" / "tts" / "logs"
        click.echo(f"  config: {config_path}")
        click.echo(f"  cache: {cache_path}")
        click.echo(f"  logs: {logs_path}")
        
        click.echo()
        click.echo("💡 Tips:")
        click.echo("  • Set API keys: tts config set <key> <value>")
        click.echo("  • Edit config: tts config edit")
        click.echo("  • View specific: tts config get <key>")

    elif action == "set":
        if not key or not value:
            click.echo("❌ Error: config set requires both key and value", err=True)
            click.echo("💡 Usage: tts config voice en-IE-EmilyNeural", err=True)
            click.echo("         tts config openai_api_key sk-...", err=True)
            sys.exit(1)

        # Special handling for API keys
        if key.endswith("_api_key"):
            provider = key.replace("_api_key", "")
            if provider in ["openai", "google", "elevenlabs"]:
                if validate_api_key(provider, value):
                    if set_api_key(provider, value):
                        click.echo(f"✅ Set {provider} API key")
                    else:
                        click.echo(f"❌ Failed to save {provider} API key", err=True)
                        sys.exit(1)
                else:
                    click.echo(f"❌ Invalid {provider} API key format", err=True)
                    if provider == "openai":
                        click.echo(
                            "💡 OpenAI keys start with 'sk-' and are ~50 characters", err=True
                        )
                    elif provider == "google":
                        click.echo(
                            "💡 Google keys start with 'AIza' (39 chars) or 'ya29.' (OAuth)",
                            err=True
                        )
                    elif provider == "elevenlabs":
                        click.echo("💡 ElevenLabs keys are 32-character hex strings", err=True)
                    sys.exit(1)
            else:
                click.echo(f"❌ Unknown provider '{provider}' for API key", err=True)
                click.echo("💡 Supported providers: openai, google, elevenlabs", err=True)
                sys.exit(1)
        else:
            # Regular config setting
            if set_setting(key, value):
                click.echo(f"✅ Set {key} = {value}")
            else:
                click.echo("❌ Failed to save configuration", err=True)
                sys.exit(1)

    elif action == "reset":
        if save_config(get_default_config()):
            click.echo("✅ Configuration reset to defaults")
        else:
            click.echo("❌ Failed to reset configuration", err=True)
            sys.exit(1)

    elif action == "get":
        if not key:
            click.echo("❌ Error: config get requires a key", err=True)
            click.echo("💡 Usage: tts config get voice", err=True)
            sys.exit(1)

        config = load_config()
        if key in config:
            click.echo(config[key])
        else:
            click.echo(f"❌ Error: Configuration key '{key}' not found", err=True)
            click.echo(f"💡 Available keys: {', '.join(config.keys())}", err=True)
            sys.exit(1)

    elif action == "edit":
        config = load_config()
        click.echo("⚙️  Interactive configuration editor:")
        click.echo("💡 Press Enter to keep current value, or type new value")
        click.echo()

        new_config = {}
        for key, current_value in config.items():
            if key == "version":
                new_config[key] = current_value
                continue

            prompt = f"{key} ({current_value}): "
            new_value = click.prompt(prompt, default=current_value, show_default=False)
            new_config[key] = new_value

        if save_config(new_config):
            click.echo("✅ Configuration updated successfully")
        else:
            click.echo("❌ Failed to save configuration", err=True)
            sys.exit(1)

    else:
        click.echo("❌ Error: Unknown config action. Use: show, get, set, reset, or edit", err=True)
        sys.exit(1)


def _validate_provider_options(provider_name: str, kwargs: dict, logger: logging.Logger, debug: bool) -> None:
    """Validate options against provider capabilities and show warnings for invalid options"""
    try:
        from .core import get_tts_engine
        tts_engine = get_tts_engine()

        # Get provider info to see what options are supported
        provider_info = tts_engine.get_provider_info(provider_name)
        if not provider_info or 'options' not in provider_info:
            return  # Can't validate without provider info

        supported_options = set(provider_info['options'].keys())
        used_options = set(kwargs.keys())

        # Find invalid options
        invalid_options = used_options - supported_options

        if invalid_options:
            provider_name_display = provider_info.get('name', provider_name)
            click.echo(f"⚠️  Warning: {provider_name_display} doesn't support these options:", err=True)
            for invalid_opt in sorted(invalid_options):
                click.echo(f"   • {invalid_opt}={kwargs[invalid_opt]}", err=True)

            if supported_options:
                click.echo(f"   Supported options: {', '.join(sorted(supported_options))}", err=True)
            click.echo(f"   Use 'tts info {provider_name}' to see all available options", err=True)

        # Validate specific option values
        _validate_option_values(provider_name, kwargs, logger, debug)

    except Exception as e:
        if debug:
            logger.debug(f"Option validation failed: {e}")


def _validate_option_values(provider_name: str, kwargs: dict, logger: logging.Logger, debug: bool) -> None:
    """Validate specific option values for common parameters"""

    # Validate rate parameter
    if 'rate' in kwargs:
        rate = kwargs['rate']
        if not _is_valid_rate(rate):
            click.echo(f"⚠️  Warning: Invalid rate value '{rate}'. Expected format: +50%, -25%, 150%, etc.", err=True)

    # Validate pitch parameter
    if 'pitch' in kwargs:
        pitch = kwargs['pitch']
        if not _is_valid_pitch(pitch):
            click.echo(f"⚠️  Warning: Invalid pitch value '{pitch}'. Expected format: +5Hz, -10Hz, etc.", err=True)

    # Validate boolean parameters
    boolean_params = ['stream']
    for param in boolean_params:
        if param in kwargs:
            value = kwargs[param]
            if not _is_valid_boolean(value):
                click.echo(f"⚠️  Warning: Invalid {param} value '{value}'. Expected: true, false, 1, 0, yes, no", err=True)

    # Provider-specific validations
    if provider_name == 'elevenlabs':
        _validate_elevenlabs_options(kwargs)
    elif provider_name == 'google_tts':
        _validate_google_tts_options(kwargs)


def _is_valid_rate(rate: str) -> bool:
    """Check if rate value is valid"""
    import re
    # Allow formats: +50%, -25%, 150%, +0%, etc.
    return bool(re.match(r'^[+-]?\d+%$', rate))


def _is_valid_pitch(pitch: str) -> bool:
    """Check if pitch value is valid"""
    import re
    # Allow formats: +5Hz, -10Hz, +0Hz, etc.
    return bool(re.match(r'^[+-]?\d+(\.\d+)?Hz$', pitch))


def _is_valid_boolean(value: str) -> bool:
    """Check if value is a valid boolean representation"""
    return value.lower() in ('true', 'false', '1', '0', 'yes', 'no')


def _validate_elevenlabs_options(kwargs: dict) -> None:
    """Validate ElevenLabs-specific options"""

    # Validate stability (0.0-1.0)
    if 'stability' in kwargs:
        try:
            stability = float(kwargs['stability'])
            if not 0.0 <= stability <= 1.0:
                click.echo(f"⚠️  Warning: ElevenLabs stability must be between 0.0 and 1.0, got {stability}", err=True)
        except ValueError:
            click.echo(f"⚠️  Warning: ElevenLabs stability must be a number, got '{kwargs['stability']}'", err=True)

    # Validate similarity_boost (0.0-1.0)
    if 'similarity_boost' in kwargs:
        try:
            similarity = float(kwargs['similarity_boost'])
            if not 0.0 <= similarity <= 1.0:
                click.echo(f"⚠️  Warning: ElevenLabs similarity_boost must be between 0.0 and 1.0, got {similarity}", err=True)
        except ValueError:
            click.echo(
                f"⚠️  Warning: ElevenLabs similarity_boost must be a number, got '{kwargs['similarity_boost']}'",
                err=True
            )

    # Validate style (0.0-1.0)
    if 'style' in kwargs:
        try:
            style = float(kwargs['style'])
            if not 0.0 <= style <= 1.0:
                click.echo(f"⚠️  Warning: ElevenLabs style must be between 0.0 and 1.0, got {style}", err=True)
        except ValueError:
            click.echo(f"⚠️  Warning: ElevenLabs style must be a number, got '{kwargs['style']}'", err=True)


def _validate_google_tts_options(kwargs: dict) -> None:
    """Validate Google TTS-specific options"""

    # Validate speaking_rate (0.25-4.0)
    if 'speaking_rate' in kwargs:
        try:
            rate = float(kwargs['speaking_rate'])
            if not 0.25 <= rate <= 4.0:
                click.echo(f"⚠️  Warning: Google TTS speaking_rate must be between 0.25 and 4.0, got {rate}", err=True)
        except ValueError:
            click.echo(f"⚠️  Warning: Google TTS speaking_rate must be a number, got '{kwargs['speaking_rate']}'", err=True)

    # Validate pitch (-20.0 to 20.0)
    if 'pitch' in kwargs and not kwargs['pitch'].endswith('Hz'):  # Google uses numeric pitch, not Hz
        try:
            pitch = float(kwargs['pitch'])
            if not -20.0 <= pitch <= 20.0:
                click.echo(f"⚠️  Warning: Google TTS pitch must be between -20.0 and 20.0, got {pitch}", err=True)
        except ValueError:
            click.echo(f"⚠️  Warning: Google TTS pitch must be a number, got '{kwargs['pitch']}'", err=True)


def check_option_precedence(cli_rate: str, cli_pitch: str, options: tuple, logger: logging.Logger) -> None:
    """Check for option precedence conflicts and warn users"""
    # Parse key=value options to find conflicts
    kv_options = {}
    for opt in options:
        if "=" in opt:
            key, value = opt.split("=", 1)
            kv_options[key] = value

    # Check for conflicts between CLI flags and key=value options
    if cli_rate is not None and 'rate' in kv_options:
        click.echo(f"⚠️  Both --rate and rate= specified. Using --rate {cli_rate}", err=True)

    if cli_pitch is not None and 'pitch' in kv_options:
        click.echo(f"⚠️  Both --pitch and pitch= specified. Using --pitch {cli_pitch}", err=True)


def handle_synthesize(
    text: str, model: str, output: str, save: bool, voice: str,
    clone: str, output_format: str, options: tuple, logger: logging.Logger,
    json_output: bool = False, debug: bool = False,
    rate: str = None, pitch: str = None
) -> None:
    """Handle main synthesis command using the core TTS engine."""
    # Check for option precedence conflicts
    check_option_precedence(rate, pitch, options, logger)

    # Parse key=value options (filter out non key=value arguments)
    kwargs = {}
    for opt in options:
        if "=" in opt:
            key, value = opt.split("=", 1)
            kwargs[key] = value
        # Ignore non key=value options as they might be parsed by Click differently

    # Load default rate and pitch from config if not specified
    from .config import load_config
    config = load_config()

    # Use CLI options first, then kwargs, then config defaults
    if rate is not None:
        kwargs['rate'] = rate
    elif 'rate' not in kwargs:
        kwargs['rate'] = config.get('rate', '+0%')

    if pitch is not None:
        kwargs['pitch'] = pitch
    elif 'pitch' not in kwargs:
        kwargs['pitch'] = config.get('pitch', '+0Hz')

    # Validate options against provider capabilities
    _validate_provider_options(model, kwargs, logger, debug)

    if debug:
        logger.info(f"Using rate: {kwargs.get('rate')}, pitch: {kwargs.get('pitch')}")

    # Default to streaming unless --save flag is used
    stream = not save

    # Handle voice parameter (clone takes precedence)
    final_voice = clone if clone else voice

    # Show provider info if requested
    if "info" in kwargs and kwargs.pop("info").lower() in ("true", "1", "yes"):
        try:
            tts_engine = get_tts_engine()
            info = tts_engine.get_provider_info(model)
            if info:
                click.echo(f"Provider info for {model}:")
                for key, value in info.items():
                    click.echo(f"  {key}: {value}")
            else:
                click.echo(f"No info available for {model}")
        except Exception as e:
            click.echo(f"Error getting provider info: {e}", err=True)
        return

    try:
        # Use core TTS engine for synthesis
        tts_engine = get_tts_engine()

        # Display user feedback (only if not JSON output)
        if not json_output and not stream:
            click.echo(f"💾 Saving with {model}...")

        # Perform synthesis with timing
        start_time = time.time()
        result_path = tts_engine.synthesize_text(
            text=text,
            output_path=output if not stream else None,
            provider_name=model,
            voice=final_voice,
            stream=stream,
            output_format=output_format,
            **kwargs
        )
        duration = time.time() - start_time

        # Format and display results
        action = "save" if save else "stream"
        output_msg = format_output(
            success=True,
            provider=model,
            voice=final_voice,
            action=action,
            duration=duration,
            output_path=result_path if result_path else None,
            json_output=json_output,
            debug=debug
        )
        if output_msg:  # Only echo if there's something to display
            click.echo(output_msg)

    except KeyboardInterrupt:
        # Don't log errors for Ctrl+C
        raise
    except TTSError as e:
        logger.error(f"Synthesis failed with {model}: {e}")
        error_msg = format_output(
            success=False,
            error=str(e),
            error_code="TTS_ERROR",
            json_output=json_output
        )
        click.echo(error_msg, err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during synthesis with {model}: {e}")
        error_msg = format_output(
            success=False,
            error=str(e),
            error_code="UNEXPECTED_ERROR",
            json_output=json_output
        )
        click.echo(error_msg, err=True)
        sys.exit(1)


def handle_status_diagnostics() -> None:
    """Check system capabilities and provider availability"""
    click.echo("TTS System Health Check")
    click.echo("━━━━━━━━━━━━━━━━━━━━━━━━")

    # Suppress all logging during health checks
    original_level = logging.root.level
    logging.root.setLevel(logging.CRITICAL)

    # Check system requirements
    click.echo("\nSystem Requirements")

    # Check Python version
    python_version = sys.version.split()[0]
    if sys.version_info >= (3, 8):
        click.echo(f"├─ Python {python_version}                           ✅ Ready")
    else:
        click.echo(f"├─ Python {python_version}                           ❌ Requires >= 3.8")

    # Check ffmpeg/ffplay
    try:
        subprocess.run(['ffplay', '-version'], capture_output=True, check=True)
        click.echo("└─ FFmpeg/FFplay                           ✅ Ready")
    except (FileNotFoundError, subprocess.CalledProcessError):
        click.echo("└─ FFmpeg/FFplay                           ❌ Not found")

    # Check providers
    click.echo("\nTTS Providers")

    provider_status = {}
    provider_count = len(PROVIDERS)
    ready_count = 0

    for i, provider_name in enumerate(PROVIDERS.keys()):
        is_last = i == provider_count - 1
        prefix = "└─" if is_last else "├─"

        try:
            provider_class = load_provider(provider_name)
            provider = provider_class()
            info = provider.get_info()

            if provider_name == "edge_tts":
                voice_count = len(info.get('sample_voices', []))
                click.echo(f"{prefix} Edge TTS                                ✅ Ready ({voice_count} voices)")
                provider_status[provider_name] = "ready"
                ready_count += 1

            elif provider_name == "chatterbox":
                voice_count = len(info.get('sample_voices', []))
                has_pytorch = False
                try:
                    import importlib.util
                    if importlib.util.find_spec("torch") is not None:
                        has_pytorch = True
                except ImportError:
                    pass

                if voice_count > 0 and has_pytorch:
                    click.echo(f"{prefix} Chatterbox                              ✅ Ready ({voice_count} voices)")
                    provider_status[provider_name] = "ready"
                    ready_count += 1
                else:
                    click.echo(f"{prefix} Chatterbox                              ⚠️  Missing dependencies")
                    provider_status[provider_name] = "missing_deps"

                    # Show sub-items
                    if not is_last:
                        voice_status = "✅ Ready" if voice_count > 0 else "❌ No files in ./voices/"
                        pytorch_status = "✅ Ready" if has_pytorch else "❌ Not installed"
                        click.echo(f"│  ├─ Voice files                          {voice_status}")
                        click.echo(f"│  └─ PyTorch                              {pytorch_status}")
                    else:
                        voice_status = "✅ Ready" if voice_count > 0 else "❌ No files in ./voices/"
                        pytorch_status = "✅ Ready" if has_pytorch else "❌ Not installed"
                        click.echo(f"   ├─ Voice files                          {voice_status}")
                        click.echo(f"   └─ PyTorch                              {pytorch_status}")

            elif provider_name == "openai":
                click.echo(f"{prefix} OpenAI TTS                              ✅ Ready")
                provider_status[provider_name] = "ready"
                ready_count += 1

            elif provider_name == "google":
                click.echo(f"{prefix} Google Cloud TTS                        ✅ Ready")
                provider_status[provider_name] = "ready"
                ready_count += 1

            elif provider_name == "elevenlabs":
                # Check if API key is configured
                config = load_config()
                has_api_key = config.get('elevenlabs_api_key') is not None

                if has_api_key:
                    click.echo(f"{prefix} ElevenLabs                              ✅ Ready")
                    provider_status[provider_name] = "ready"
                    ready_count += 1
                else:
                    click.echo(f"{prefix} ElevenLabs                              ⚠️  API key not configured")
                    provider_status[provider_name] = "no_api_key"

        except (ProviderNotFoundError, ProviderLoadError, DependencyError):
            click.echo(f"{prefix} {provider_name.title()}                              ❌ Not available")
            provider_status[provider_name] = "error"
        except Exception:
            click.echo(f"{prefix} {provider_name.title()}                              ❌ Error")
            provider_status[provider_name] = "error"

    # Configuration
    click.echo("\nConfiguration")
    config = load_config()
    default_voice = config.get('voice', 'edge_tts:en-IE-EmilyNeural')
    provider, voice = parse_voice_setting(default_voice)
    output_dir = config.get('output_dir', '~/Downloads')
    config_path = "~/.config/tts/config.json"

    click.echo(f"├─ Default voice: {voice} ({provider.title()})")
    click.echo(f"├─ Output directory: {output_dir}")
    click.echo(f"└─ Config file: {config_path}")

    # Recommendations
    click.echo("\nRecommendations")
    recommendations = []

    if provider_status.get("chatterbox") == "missing_deps":
        recommendations.append("Install Chatterbox: tts install chatterbox gpu")

    if provider_status.get("elevenlabs") == "no_api_key":
        recommendations.append("Configure ElevenLabs: tts config elevenlabs_api_key YOUR_KEY")

    recommendations.append("Browse voices: tts voices")

    for i, rec in enumerate(recommendations):
        is_last = i == len(recommendations) - 1
        prefix = "└─" if is_last else "├─"
        click.echo(f"{prefix} {rec}")

    # Status summary
    click.echo(f"\nStatus: {ready_count} of {provider_count} providers ready")

    # Restore original logging level
    logging.root.setLevel(original_level)


def handle_install_command(args: tuple) -> None:
    """Install provider dependencies"""
    if len(args) == 0:
        click.echo("❌ Error: Specify a provider to install", err=True)
        click.echo("💡 Usage: tts install <provider> [gpu]")
        click.echo("Available providers: chatterbox")
        sys.exit(1)

    provider = args[0].lower()
    gpu_flag = "gpu" in args or "--gpu" in args

    if provider == "chatterbox":
        click.echo("🔧 Installing Chatterbox TTS dependencies...")

        # Check if already available
        try:
            provider_class = load_provider("chatterbox")
            provider_instance = provider_class()
            # Actually test if dependencies are available
            provider_instance._lazy_load()
            click.echo("✅ Chatterbox is already available!")

            # Check GPU status
            try:
                import torch
                if torch.cuda.is_available():
                    click.echo("🚀 GPU acceleration is ready")
                else:
                    if gpu_flag:
                        click.echo("⚠️  GPU requested but CUDA not available")
                        click.echo("💡 Make sure NVIDIA drivers and CUDA are installed")
                    else:
                        click.echo("💻 Using CPU (add --gpu for GPU acceleration)")
            except ImportError:
                if gpu_flag:
                    click.echo("📦 Installing PyTorch with CUDA support...")
                    click.echo("💡 This may take 5-10 minutes to download large packages...")
                    try:
                        subprocess.run([
                            'pipx', 'inject', '--index-url', 'https://download.pytorch.org/whl/cu121',
                            'goobits-tts', 'torch', 'torchvision', 'torchaudio'
                        ], check=True, timeout=600)  # 10 minute timeout
                        click.echo("✅ PyTorch with CUDA installed successfully!")
                    except subprocess.CalledProcessError as e:
                        click.echo(f"❌ Failed to install PyTorch with CUDA: {e}")
                        click.echo(
                            "💡 Try manually: pipx inject --index-url https://download.pytorch.org/whl/cu121 "
                            "goobits-tts torch torchvision torchaudio"
                        )
                        return
                else:
                    click.echo("📦 Installing PyTorch (CPU)...")
                    try:
                        subprocess.run([
                            'pipx', 'inject', 'goobits-tts', 'torch', 'torchvision', 'torchaudio'
                        ], check=True, capture_output=True)
                        click.echo("✅ PyTorch (CPU) installed successfully!")
                    except subprocess.CalledProcessError:
                        click.echo("❌ Failed to install PyTorch")
                        click.echo("💡 Try manually: pipx inject goobits-tts torch torchvision torchaudio")
                        return

            return

        except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
            click.echo(f"📦 Chatterbox not available: {e}")
            click.echo("📦 Installing dependencies...")

            # Install PyTorch with CUDA (required even for CPU usage with chatterbox-tts)
            click.echo("📦 Installing PyTorch with CUDA support...")
            click.echo("💡 Note: Chatterbox requires CUDA PyTorch even for CPU usage")
            if not gpu_flag:
                click.echo("💡 This may take 5-10 minutes to download large packages...")
            try:
                subprocess.run([
                    'pipx', 'inject', '--index-url',
                    'https://download.pytorch.org/whl/cu121',
                    'goobits-tts', 'torch', 'torchvision', 'torchaudio'
                ], check=True, timeout=600)  # 10 minute timeout
                click.echo("✅ PyTorch with CUDA installed!")
            except subprocess.CalledProcessError as e:
                click.echo(f"❌ Failed to install PyTorch with CUDA: {e}")
                click.echo(
                    "💡 Try manually: pipx inject --index-url https://download.pytorch.org/whl/cu121 "
                    "goobits-tts torch torchvision torchaudio"
                )
                return

            # Install chatterbox-tts
            click.echo("📦 Installing Chatterbox TTS...")
            try:
                subprocess.run(['pipx', 'inject', 'goobits-tts', 'chatterbox-tts'], check=True, capture_output=True)
                click.echo("✅ Chatterbox TTS installed successfully!")

                # Set chatterbox-compatible voice config
                set_setting('voice', 'chatterbox:')
                save_config()
                click.echo("🔧 Updated voice config to be compatible with Chatterbox")

                click.echo("🎉 Installation complete! You can now use Chatterbox with voice cloning.")
                click.echo("💡 Usage: tts @chatterbox \"Hello world\"")
                click.echo("💡 Voice cloning: tts @chatterbox --voice your_voice.wav \"Hello world\"")
            except subprocess.CalledProcessError as e:
                click.echo(f"❌ Failed to install Chatterbox TTS: {e}")
                click.echo("💡 Try manually: pipx inject goobits-tts chatterbox-tts")

    elif provider == "edge_tts":
        click.echo("✅ Edge TTS is already included and ready to use!")

    else:
        click.echo(f"❌ Error: Unknown provider '{provider}'", err=True)
        click.echo("Available providers: chatterbox, edge_tts")
        sys.exit(1)


def handle_load_command(args: tuple) -> None:
    """Load voice files into memory for fast access"""
    if len(args) == 0:
        click.echo("❌ Error: Specify voice files to load", err=True)
        click.echo("💡 Usage: tts load <voice_file> [voice_file2] ...")
        click.echo("💡 Example: tts load ~/my_voice.wav ~/narrator.wav")
        sys.exit(1)

    voice_manager = VoiceManager()

    for voice_path in args:
        voice_file = Path(voice_path).expanduser()
        if not voice_file.exists():
            click.echo(f"📁 Error: Voice file not found: {voice_file}", err=True)
            continue

        try:
            click.echo(f"🔄 Loading {voice_file.name}...")
            voice_manager.load_voice(str(voice_file))
            click.echo(f"✅ {voice_file.name} loaded successfully")
        except Exception as e:
            click.echo(f"❌ Failed to load {voice_file.name}: {e}", err=True)


def handle_info_command(args: tuple) -> None:
    """Show detailed provider information and available options"""
    if len(args) == 0:
        # Show all providers
        from .core import get_tts_engine
        tts_engine = get_tts_engine()
        providers = list(tts_engine.providers_registry.keys())

        click.echo("🎤 Available Providers:")
        for provider in providers:
            try:
                info = tts_engine.get_provider_info(provider)
                if info:
                    name = info.get('name', provider)
                    desc = info.get('description', 'No description')
                    click.echo(f"  • {provider}: {name} - {desc}")
                else:
                    click.echo(f"  • {provider}: Available")
            except Exception as e:
                click.echo(f"  • {provider}: Error loading ({str(e)[:50]}...)")

        click.echo()
        click.echo("Use 'tts info <provider>' to see detailed options for a specific provider")
        return

    # Show specific provider info
    provider_name = args[0]
    from .core import get_tts_engine
    tts_engine = get_tts_engine()

    if provider_name not in tts_engine.providers_registry:
        click.echo(f"❌ Error: Unknown provider '{provider_name}'", err=True)
        click.echo(f"Available providers: {', '.join(tts_engine.providers_registry.keys())}")
        return

    try:
        info = tts_engine.get_provider_info(provider_name)
        if not info:
            click.echo(f"❌ Error: No info available for {provider_name}", err=True)
            return

        # Display provider info in a nice format
        click.echo(f"🎤 {info.get('name', provider_name)}")
        click.echo(f"   {info.get('description', 'No description')}")
        click.echo()

        # Show available options
        options = info.get('options', {})
        if options:
            click.echo("📋 Available Options:")
            for option_name, option_desc in options.items():
                click.echo(f"   {option_name}={option_desc}")
            click.echo()

        # Show additional info
        if 'output_format' in info:
            click.echo(f"🔊 Output Format: {info['output_format']}")

        if 'features' in info:
            features = info['features']
            click.echo("✨ Features:")
            for feature, value in features.items():
                if isinstance(value, bool):
                    status = "✅" if value else "❌"
                    click.echo(f"   {status} {feature.replace('_', ' ').title()}")
                else:
                    click.echo(f"   • {feature.replace('_', ' ').title()}: {value}")
            click.echo()

        # Show sample voices
        sample_voices = info.get('sample_voices', [])
        if sample_voices:
            click.echo(f"🎭 Sample Voices ({len(sample_voices)} available):")
            # Show first 5 voices as examples
            for voice in sample_voices[:5]:
                click.echo(f"   • {voice}")
            if len(sample_voices) > 5:
                click.echo(f"   ... and {len(sample_voices) - 5} more")
            click.echo()

        # Show usage examples
        click.echo("💡 Usage Examples:")
        click.echo(f'   tts "Hello world" --model {provider_name}')
        if options:
            first_option = list(options.keys())[0]
            click.echo(f'   tts "Hello world" --model {provider_name} {first_option}=value')

    except Exception as e:
        click.echo(f"Error getting provider info: {e}", err=True)


def handle_status_command() -> None:
    """Show system status and loaded voices"""
    click.echo("🔍 TTS System Status")
    click.echo()

    # Check providers
    click.echo("Providers:")
    for provider_name in PROVIDERS.keys():
        try:
            provider_class = load_provider(provider_name)
            provider = provider_class()
            info = provider.get_info()

            if provider_name == "edge_tts":
                if info and 'sample_voices' in info:
                    voice_count = len(info['sample_voices'])
                    click.echo(f"  ✅ Edge TTS: Ready ({voice_count} voices available)")
                else:
                    click.echo("  ✅ Edge TTS: Ready")
            elif provider_name == "chatterbox":
                # Check GPU availability
                gpu_status = ""
                try:
                    import torch
                    if torch.cuda.is_available():
                        gpu_name = torch.cuda.get_device_name(0)
                        gpu_status = f" (GPU: {gpu_name})"
                    else:
                        gpu_status = " (CPU only)"
                except ImportError:
                    gpu_status = " (PyTorch not installed)"

                click.echo(f"  ✅ Chatterbox: Ready{gpu_status}")

        except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
            click.echo(f"  ❌ {provider_name.upper()}: {e}")
        except Exception as e:
            click.echo(f"  ❌ {provider_name.upper()}: Unexpected error: {e}")

    click.echo()

    # Check loaded voices
    voice_manager = VoiceManager()
    loaded_voices = voice_manager.get_loaded_voices()

    if loaded_voices:
        click.echo("Loaded Voices (Chatterbox):")
        memory_usage = 0
        for voice_info in loaded_voices:
            voice_name = Path(voice_info['path']).name
            load_time = voice_info.get('load_time', 'unknown')
            click.echo(f"  • {voice_name} (loaded {load_time})")
            memory_usage += voice_info.get('memory_mb', 0)

        click.echo()
        if memory_usage > 0:
            if memory_usage >= 1024:
                memory_str = f"{memory_usage/1024:.1f}GB"
            else:
                memory_str = f"{memory_usage}MB"
            click.echo(f"Memory: {len(loaded_voices)} voices using ~{memory_str}")
    else:
        click.echo("Loaded Voices (Chatterbox): None")

    click.echo()

    # Show configuration
    config = load_config()
    click.echo("Configuration:")
    click.echo(f"  • Default voice: {config.get('voice', 'en-IE-EmilyNeural')}")
    click.echo(f"  • Default action: {config.get('default_action', 'stream')}")
    if config.get('output_dir'):
        click.echo(f"  • Output directory: {config.get('output_dir')}")


def handle_document_processing(
    document_path: str,
    doc_format: str = "auto",
    ssml_platform: str = "generic",
    emotion_profile: str = "auto",
    debug: bool = False
) -> Optional[str]:
    """Process a document file and return text suitable for TTS synthesis.

    Args:
        document_path: Path to the document file
        doc_format: Document format (auto, html, json, markdown)
        ssml_platform: Target SSML platform (azure, google, amazon, generic)
        emotion_profile: Emotion profile to apply (technical, marketing, narrative, tutorial, auto)

    Returns:
        Processed text ready for TTS synthesis, or None on error
    """
    try:
        # Import document processing components
        import hashlib

        from .config import load_config
        from .document_processing.parser_factory import DocumentParserFactory
        from .document_processing.performance_cache import PerformanceOptimizer
        from .speech_synthesis.advanced_emotion_detector import AdvancedEmotionDetector
        from .speech_synthesis.speech_markdown import SpeechMarkdownConverter
        from .speech_synthesis.ssml_generator import SSMLGenerator, SSMLPlatform

        # Load configuration
        user_config = load_config()
        doc_config = user_config.get('document_parsing', {})
        speech_config = user_config.get('speech_synthesis', {})

        # Helper function to cache results
        def _cache_result(key: str, content: str) -> None:
            try:
                import pickle
                from pathlib import Path
                cache_dir = Path(".cache/documents")
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file = cache_dir / f"{key}.result"
                with open(cache_file, 'wb') as f:
                    pickle.dump(content, f)
            except Exception:
                # Ignore cache errors
                pass

        # Helper function to strip speech markdown syntax
        def _strip_speech_markdown(text: str) -> str:
            """Remove speech markdown syntax while preserving document structure."""
            import re
            # Remove emotion markers: (emotion)[text] -> text
            text = re.sub(r'\([^)]+\)\[([^\]]+)\]', r'\1', text)
            # Remove timing markers: [500ms] or [1s]
            text = re.sub(r'\[\d+(?:\.\d+)?(?:ms|s)\]', '', text)
            # Remove markdown bold: **text** -> text
            text = re.sub(r'\*\*([^\*]+?)\*\*', r'\1', text)
            # Remove markdown italic: *text* -> text (careful not to remove list markers)
            text = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'\1', text)
            # Remove inline code: `text` -> text
            text = re.sub(r'`([^`]+)`', r'\1', text)
            # Remove bullet markers at start of lines but keep the line structure
            text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
            # Clean up extra spaces on each line, but preserve newlines
            lines = text.split('\n')
            cleaned_lines = [line.strip() for line in lines]
            return '\n'.join(cleaned_lines)

        # Read the document
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Auto-detect format if needed
        if doc_format == "auto":
            doc_format = doc_config.get('default_format', 'auto')
            if doc_format == "auto":
                if document_path.endswith('.html'):
                    doc_format = "html"
                elif document_path.endswith('.json'):
                    doc_format = "json"
                elif document_path.endswith('.md'):
                    doc_format = "markdown"
                else:
                    # Try to detect from content
                    doc_format = "markdown"  # Default fallback

        if debug:
            click.echo(f"  Detected format: {doc_format}")

        # Generate cache key based on all processing parameters
        cache_key_data = f"{content}:{doc_format}:{ssml_platform}:{emotion_profile}"
        cache_key = hashlib.sha256(cache_key_data.encode()).hexdigest()

        # Try to use cached result if caching is enabled
        if doc_config.get('cache_enabled', True):
            optimizer = PerformanceOptimizer(enable_caching=True)

            # Check if we have a cached result for this exact configuration
            from pathlib import Path
            cache_dir = Path(".cache/documents")
            cache_file = cache_dir / f"{cache_key}.result"

            if cache_file.exists():
                import pickle
                import time

                # Check cache age
                file_age = time.time() - cache_file.stat().st_mtime
                cache_ttl = doc_config.get('cache_ttl', 3600)

                if file_age <= cache_ttl:
                    try:
                        with open(cache_file, 'rb') as f:
                            cached_result = pickle.load(f)
                        if debug:
                            click.echo(f"Using cached result for {document_path}")
                        return cached_result
                    except Exception:
                        # Cache corrupted, continue with normal processing
                        pass

        # Parse document to semantic elements
        if doc_config.get('cache_enabled', True):
            # Use performance optimizer for parsing
            optimizer = PerformanceOptimizer(enable_caching=True)
            elements = optimizer.process_document(content, doc_format)
        else:
            parser_factory = DocumentParserFactory()
            elements = parser_factory.parse_document(content, doc_format)

        if not elements:
            click.echo(f"⚠️  Warning: No content extracted from {document_path}", err=True)
            return None

        # Apply emotion detection if enabled
        if emotion_profile == "auto" and doc_config.get('emotion_detection', True):
            detector = AdvancedEmotionDetector()
            emotion_profile = detector.detect_document_type(elements)
            if debug:
                click.echo(f"  Detected emotion profile: {emotion_profile}")

        # Skip formatting - pass elements directly to emotion detector
        # The SemanticFormatter's format_for_speech method returns text, not elements

        # Convert to speech markdown
        speech_converter = SpeechMarkdownConverter()
        speech_markdown = speech_converter.convert_elements(elements)

        # Use configured SSML platform if not specified
        if ssml_platform == "generic":
            ssml_platform = speech_config.get('ssml_platform', 'generic')

        # Generate SSML if platform specified
        if ssml_platform != "generic":
            ssml_generator = SSMLGenerator()
            platform_map = {
                "azure": SSMLPlatform.AZURE,
                "google": SSMLPlatform.GOOGLE,
                "amazon": SSMLPlatform.AMAZON
            }
            ssml_generator = SSMLGenerator(platform=platform_map.get(ssml_platform, SSMLPlatform.AZURE))

            # Apply timing configuration
            if speech_config.get('paragraph_pause'):
                ssml_generator.paragraph_pause = speech_config['paragraph_pause']
            if speech_config.get('sentence_pause'):
                ssml_generator.sentence_pause = speech_config['sentence_pause']

            ssml_content = ssml_generator.convert_speech_markdown(speech_markdown)

            # Cache the final result
            if doc_config.get('cache_enabled', True):
                _cache_result(cache_key, ssml_content)

            return ssml_content

        # Return plain text for generic platform
        # Strip speech markdown syntax for plain text output
        plain_text = _strip_speech_markdown(speech_markdown)

        # Cache the final result
        if doc_config.get('cache_enabled', True):
            _cache_result(cache_key, plain_text)

        return plain_text

    except FileNotFoundError:
        click.echo(f"📁 Error: Document file not found: {document_path}", err=True)
        return None
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Document processing error: {e}")
        click.echo(f"❌ Error processing document: {e}", err=True)
        return None


def handle_unload_command(args: tuple) -> None:
    """Unload voice files from memory"""
    voice_manager = VoiceManager()

    # Handle --all flag
    if "--all" in args or (len(args) == 1 and args[0] == "all"):
        try:
            unloaded_count = voice_manager.unload_all_voices()
            if unloaded_count > 0:
                click.echo(f"✅ Unloaded {unloaded_count} voices")
            else:
                click.echo("No voices were loaded")
        except Exception as e:
            click.echo(f"❌ Failed to unload voices: {e}", err=True)
        return

    if len(args) == 0:
        click.echo("❌ Error: Specify voice files to unload or use --all", err=True)
        click.echo("💡 Usage: tts unload <voice_file> [voice_file2] ...")
        click.echo("       tts unload --all")
        click.echo("💡 Example: tts unload my_voice.wav")
        sys.exit(1)

    for voice_path in args:
        # Skip --all flag if mixed with specific files
        if voice_path == "--all":
            continue

        voice_file = Path(voice_path).expanduser()

        try:
            if voice_manager.unload_voice(str(voice_file)):
                click.echo(f"✅ Unloaded {voice_file.name}")
            else:
                click.echo(f"⚠️  {voice_file.name} was not loaded")
        except Exception as e:
            click.echo(f"❌ Failed to unload {voice_file.name}: {e}", err=True)


@click.group(cls=DefaultCommandGroup, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="TTS CLI")
@click.pass_context
def main(ctx: click.Context) -> None:
    """🔮 [bold cyan]TTS CLI v1.0-rc2[/bold cyan] - Multi-provider text-to-speech with voice cloning

    Transform text into natural speech using AI providers with auto-selection and real-time streaming.

     

    \b
    [bold yellow]💡 Quick Start:[/bold yellow]
      [green]tts "Hello world"[/green]                    [italic]# Speak instantly[/italic]
      [green]tts save "Hello" -o out.mp3[/green]          [italic]# Save as audio file[/italic]
      [green]tts @edge "Hello from Microsoft"[/green]     [italic]# Use Edge TTS (free)[/italic]
      [green]echo "Piped input" | tts @openai[/green]     [italic]# Pipeline with OpenAI[/italic]

    \b
    [bold yellow]🎯 Core Commands:[/bold yellow]
      [green]save[/green]     💾 Save text as audio file
      [green]voices[/green]   🔍 Browse and test voices interactively
      [green]config[/green]   🔧 Provider and application settings
      [green]status[/green]   🩺 Check system health and provider status

    \b
    [bold yellow]📊 Provider Management:[/bold yellow]
      [green]providers[/green] 📋 Available providers and status
      [green]install[/green]   📦 Install provider dependencies
      [green]info[/green]      👀 Provider details and capabilities

    \b
    [bold yellow]🎙️ Advanced Features:[/bold yellow]
      [green]voice[/green]    🎤 Load and cache voices for speed
      [green]document[/green] 📖 Convert documents to speech
      [green]version[/green]  📚 Show version information

    \b
    [bold yellow]🔑 First-time Setup:[/bold yellow]
      1. Check providers:  [green]tts providers[/green]
      2. Set API keys:     [green]tts config set openai_api_key YOUR_KEY[/green]
      3. Choose a voice:   [green]tts voices[/green]
      4. Start speaking:   [green]tts "Hello AI world"[/green]

    📚 For detailed help on a command, run: [green]tts [COMMAND] --help[/green]
    """
    # Check if this is a direct synthesis call (detected by DefaultCommandGroup)
    if ctx.meta.get('direct_synthesis', False):
        synthesis_args = ctx.meta.get('synthesis_args', [])
        handle_direct_synthesis(synthesis_args)
        return
    
    # If no subcommand is invoked, check for piped input
    if ctx.invoked_subcommand is None:
        # Check if there's piped input
        if not sys.stdin.isatty():
            handle_direct_synthesis([])  # Empty args, will read from stdin
            return
        else:
            # No subcommand and no stdin, show help
            click.echo(ctx.get_help())
            sys.exit(0)




@main.command()
@click.option("-o", "--output", help="💾 Output file path")
@click.option("-f", "--format", "output_format", type=click.Choice(['mp3', 'wav', 'ogg', 'flac']), help="🔧 Audio output format")
@click.option("-v", "--voice", help="🎤 Voice to use (e.g., en-GB-SoniaNeural for edge_tts)")
@click.option("--clone", help="🎭 Audio file to clone voice from (deprecated: use --voice instead)")
@click.option("--json", "json_output", is_flag=True, help="🔧 Output results as JSON")
@click.option("--debug", is_flag=True, help="🔍 Show debug information during processing")
@click.option("--rate", help="⚡ Speech rate adjustment (e.g., +20%, -50%, 150%)")
@click.option("--pitch", help="🎵 Pitch adjustment (e.g., +5Hz, -10Hz)")
@click.argument("text", required=False)
@click.argument("options", nargs=-1)
def save(
    output: str, output_format: str, voice: str, clone: str, json_output: bool,
    debug: bool, rate: str, pitch: str, text: str, options: tuple
) -> None:
    """💾 Save text as audio file
    
    \b
    Save synthesized speech to a file in various formats with provider shortcuts
    and advanced voice options.
    
    \b
    [bold]Examples:[/bold]
        tts save "Hello world"                   [italic]# Save with default settings[/italic]
        tts save @edge "Hello" -o output.mp3    [italic]# Edge TTS with custom output[/italic]
        tts save "Hello" voice=en-US-JennyNeural [italic]# Specific voice[/italic]
    """
    # Parse provider shortcut from text or options
    provider_from_shortcut = None
    final_text = text
    final_options = list(options)

    # Check if text starts with @provider shortcut
    if text and text.startswith('@'):
        provider_from_shortcut, remaining_args = parse_provider_shortcut([text])
        if remaining_args:
            final_text = remaining_args[0] if remaining_args else None
        else:
            final_text = None
    # Check if first option is @provider shortcut
    elif options and options[0].startswith('@'):
        provider_from_shortcut, remaining_args = parse_provider_shortcut(list(options))
        final_options = remaining_args

    if not final_text:
        click.echo("❌ Error: You must provide text to synthesize", err=True)
        sys.exit(1)

    # Show deprecation warning for --clone option
    if clone:
        click.echo("⚠️  Warning: --clone option is deprecated. Use --voice instead.", err=True)

    # Setup logging
    setup_logging()

    # Initialize core TTS engine
    initialize_tts_engine(PROVIDERS)

    # Call the save handler
    handle_save_command(
        text=final_text,
        provider=provider_from_shortcut,
        output=output,
        voice=voice,
        clone=clone,
        output_format=output_format,
        options=tuple(final_options),
        json_output=json_output,
        debug=debug,
        rate=rate,
        pitch=pitch
    )


@main.command()
@click.argument("document_path", type=click.Path(exists=True))
@click.option("--save", is_flag=True, help="💾 Save processed audio to file")
@click.option("-o", "--output", help="📁 Output file path")
@click.option("-f", "--format", "output_format", type=click.Choice(['mp3', 'wav', 'ogg', 'flac']), help="🔧 Audio output format")
@click.option("-v", "--voice", help="🎤 Voice to use")
@click.option("--clone", help="🎭 Audio file to clone voice from (deprecated: use --voice instead)")
@click.option("--json", "json_output", is_flag=True, help="🔧 Output results as JSON")
@click.option("--debug", is_flag=True, help="🔍 Show debug information during processing")
@click.option(
    "--doc-format", "doc_format", type=click.Choice(['auto', 'markdown', 'html', 'json']),
    default='auto', help="📄 Document format"
)
@click.option(
    "--ssml-platform", type=click.Choice(['azure', 'google', 'amazon', 'generic']),
    default='generic', help="🏗️ SSML platform"
)
@click.option(
    "--emotion-profile", type=click.Choice(['technical', 'marketing', 'narrative', 'tutorial', 'auto']),
    default='auto', help="🎭 Emotion profile"
)
@click.option("--rate", help="⚡ Speech rate adjustment")
@click.option("--pitch", help="🎵 Pitch adjustment")
@click.argument("options", nargs=-1)
def document(
    document_path: str, save: bool, output: str, output_format: str, voice: str, clone: str,
    json_output: bool, debug: bool, doc_format: str, ssml_platform: str, emotion_profile: str,
    rate: str, pitch: str, options: tuple
) -> None:
    """📖 Convert documents to speech
    
    Convert HTML, JSON, and Markdown documents to speech with emotion detection
    and platform-optimized SSML generation.
    
    \b
    Examples:
        tts document file.html                    [italic]# Process HTML document[/italic]
        tts document @edge file.md --save        [italic]# Markdown with Edge TTS[/italic]
        tts document file.json --emotion-profile technical [italic]# Technical content[/italic]
    """
    # Parse provider shortcut from options
    provider_from_shortcut = None
    final_options = list(options)

    # Check if first option is @provider shortcut
    if options and options[0].startswith('@'):
        provider_from_shortcut, remaining_args = parse_provider_shortcut(list(options))
        final_options = remaining_args

    # Show deprecation warning for --clone option
    if clone:
        click.echo("⚠️  Warning: --clone option is deprecated. Use --voice instead.", err=True)

    # Setup logging
    setup_logging()

    # Initialize core TTS engine
    initialize_tts_engine(PROVIDERS)

    # Call the document handler
    handle_document_command(
        document_path=document_path,
        provider=provider_from_shortcut,
        save=save,
        output=output,
        voice=voice,
        clone=clone,
        output_format=output_format,
        options=tuple(final_options),
        json_output=json_output,
        debug=debug,
        doc_format=doc_format,
        ssml_platform=ssml_platform,
        emotion_profile=emotion_profile,
        rate=rate,
        pitch=pitch
    )


@main.group()
def voice() -> None:
    """🎤 Voice loading and caching
    
    Load voice files into memory for fast synthesis and manage voice cache.
    
    \b
    Commands:
        load     📥 Load voice files into memory
        unload   📤 Remove voice files from memory
        status   📊 Show loaded voices and system status
    """
    pass


@voice.command()
@click.argument("voice_files", nargs=-1, required=True)
def load(voice_files: tuple) -> None:
    """📥 Load voice files into memory for fast access
    
    Preload voice files to improve synthesis speed with Chatterbox provider.
    
    \b
    Examples:
        tts voice load voice.wav                 [italic]# Load single voice[/italic]
        tts voice load ~/my_voice.wav ~/narrator.wav [italic]# Load multiple voices[/italic]
    """
    handle_load_command(voice_files)


@voice.command()
@click.argument("voice_files", nargs=-1)
@click.option("--all", is_flag=True, help="🧹 Unload all voices")
def unload(voice_files: tuple, all: bool) -> None:
    """📤 Unload voice files from memory
    
    Remove voice files from memory to free up resources.
    
    \b
    Examples:
        tts voice unload voice.wav               [italic]# Unload specific voice[/italic]
        tts voice unload --all                   [italic]# Unload all voices[/italic]
    """
    if all:
        handle_unload_command(("--all",))
    else:
        if not voice_files:
            click.echo("❌ Error: Specify voice files to unload or use --all", err=True)
            sys.exit(1)
        handle_unload_command(voice_files)


@voice.command()
def status() -> None:
    """📊 Show loaded voices and system status
    
    Display information about currently loaded voices, memory usage,
    and provider availability.
    """
    handle_status_command()


@main.command()
@click.argument("provider", required=False)
def info(provider: str) -> None:
    """👀 Provider information and capabilities
    
    Display detailed information about TTS providers including available
    options, features, and sample voices.
    
    \b
    Examples:
        tts info                             [italic]# Show all providers[/italic]
        tts info @edge                       [italic]# Show Edge TTS details[/italic]
        tts info edge_tts                    [italic]# Show Edge TTS details[/italic]
    """
    # Setup logging and initialize TTS engine
    setup_logging()
    initialize_tts_engine(PROVIDERS)

    if provider:
        # Handle @provider shortcuts
        if provider.startswith('@'):
            shortcut = provider[1:]
            if shortcut in PROVIDER_SHORTCUTS:
                provider = PROVIDER_SHORTCUTS[shortcut]
            else:
                click.echo(f"❌ Error: Unknown provider shortcut '@{shortcut}'", err=True)
                click.echo(f"💡 Available providers: {', '.join('@' + s for s in PROVIDER_SHORTCUTS.keys())}", err=True)
                sys.exit(1)
        handle_info_command((provider,))
    else:
        handle_info_command(())


@main.command()
@click.argument("provider_name", required=False)
def providers(provider_name: str) -> None:
    """📋 Available TTS providers and status
    
    List all TTS providers with their current status, configuration requirements,
    and setup instructions.
    
    \b
    Examples:
        tts providers                        [italic]# Show all providers[/italic]
        tts providers edge                   [italic]# Setup instructions for Edge TTS[/italic]
        tts providers @openai                [italic]# Setup instructions for OpenAI[/italic]
    """
    if provider_name:
        handle_provider_setup_instructions(provider_name)
    else:
        handle_providers_command()


@main.command()
def status() -> None:
    """🩺 System health and provider availability
    
    Perform comprehensive system diagnostics including Python version,
    dependencies, provider status, and configuration validation.
    """
    handle_status_diagnostics()


@main.command()
@click.argument("args", nargs=-1)
def install(args: tuple) -> None:
    """📦 Install provider dependencies
    
    Install and configure dependencies for TTS providers, including
    PyTorch for Chatterbox with optional GPU support.
    
    \b
    Examples:
        tts install chatterbox               [italic]# Install with CPU support[/italic]
        tts install chatterbox gpu           [italic]# Install with GPU support[/italic]
    """
    handle_install_command(args)


@main.command()
def version() -> None:
    """📚 Version and suite information
    
    Display current TTS CLI version and branding information.
    """
    click.echo(f"TTS {__version__} - Goobits Audio Suite")


@main.command()
@click.argument("args", nargs=-1)
def voices(args: tuple) -> None:
    """🔍 Browse available voices interactively
    
    Launch an interactive voice browser with three-panel layout,
    filtering capabilities, and real-time voice preview.
    
    \b
    Features:
        • Filter by provider, language, gender
        • Real-time voice preview
        • Mouse and keyboard navigation
        • Quality analysis and metadata
    """
    handle_voices_command(args, PROVIDERS, load_provider)


@main.command()
@click.argument("action", type=click.Choice(["show", "voice", "provider", "format", "get", "edit", "set"]), required=False)
@click.argument("key", required=False)
@click.argument("value", required=False)
def config(action: str, key: str, value: str) -> None:
    """🔧 TTS configuration
    
    \b
    Configure API keys, default voices, audio settings, and paths with
    interactive editing and validation.
    
    \b
    [bold]Examples:[/bold]
        tts config                           [italic]# Show current configuration[/italic]
        tts config voice en-US-JennyNeural   [italic]# Set default voice[/italic]
        tts config get voice                 [italic]# Get specific setting[/italic]
        tts config set rate +20%             [italic]# Set custom setting[/italic]
        tts config edit                      [italic]# Interactive editor[/italic]
    """
    if not action:
        action = "show"
    handle_config_commands(action, key, value)


def handle_interrupt(signum, frame):
    """Handle Ctrl+C gracefully without error spam."""
    click.echo("\nInterrupted.", err=True)
    sys.exit(130)  # Standard exit code for SIGINT


def cli():
    """Direct entry point that just calls main."""
    signal.signal(signal.SIGINT, handle_interrupt)
    main()


def cli_entry():
    """Smart entry point wrapper for better editable install support.

    This wrapper ensures that code changes work without reinstallation
    by providing a stable entry point that delegates to the main CLI.
    """
    # Set up signal handler for clean Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)

    # Simply delegate to main - the DefaultCommandGroup handles routing
    main()


if __name__ == "__main__":
    cli_entry()
