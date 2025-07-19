#!/usr/bin/env python3
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
- `tts doctor` - System health diagnostics

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
import click
import importlib
import sys
import logging
import os
import json
import time
import subprocess  # Still needed for doctor command and other CLI operations
from pathlib import Path
from typing import Dict, Type, List, Tuple, Optional
from .base import TTSProvider
from .exceptions import TTSError, ProviderNotFoundError, ProviderLoadError, DependencyError, NetworkError
from .__version__ import __version__
from .config import load_config, save_config, get_default_config, parse_voice_setting, set_setting, get_setting, set_api_key, validate_api_key
from .voice_manager import VoiceManager
from .voice_browser import interactive_voice_browser, analyze_voice, show_browser_snapshot, handle_voices_command
from .core import initialize_tts_engine, get_tts_engine


PROVIDERS: Dict[str, str] = {
    "chatterbox": ".providers.chatterbox.ChatterboxProvider",
    "edge_tts": ".providers.edge_tts.EdgeTTSProvider",
    "openai": ".providers.openai_tts.OpenAITTSProvider",
    "google": ".providers.google_tts.GoogleTTSProvider",
    "elevenlabs": ".providers.elevenlabs.ElevenLabsProvider",
}


def setup_logging() -> logging.Logger:
    """Setup logging configuration for TTS CLI"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors on console
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    file_handler = logging.FileHandler(logs_dir / "tts.log")
    file_handler.setLevel(logging.INFO)  # Log everything to file
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
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


def format_output(success: bool, provider: str = None, voice: str = None, action: str = None, 
                 duration: float = None, output_path: str = None, error: str = None, 
                 error_code: str = None, json_output: bool = False, debug: bool = False) -> str:
    """Format output as JSON or human-readable text"""
    if json_output:
        if success:
            result = {"success": True}
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
            result = {"success": False}
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
        provider_class = getattr(module, class_name)
        
        if not issubclass(provider_class, TTSProvider):
            raise ProviderLoadError(f"{provider_class} is not a TTSProvider")
        
        return provider_class
    except ImportError as e:
        raise ProviderLoadError(f"Failed to load provider {name}: {e}")
    except AttributeError as e:
        raise ProviderLoadError(f"Provider class not found for {name}: {e}")



def handle_models_command(args: tuple) -> None:
    """Handle models subcommand"""
    if len(args) == 0:
        # tts models - list all available providers
        click.echo("Available models/providers:")
        for name in PROVIDERS.keys():
            click.echo(f"  - {name}")
    
    elif len(args) == 1:
        # tts models edge_tts - show info about specific provider
        provider_name = args[0]
        if provider_name not in PROVIDERS:
            click.echo(f"Error: Unknown provider '{provider_name}'", err=True)
            click.echo(f"Available providers: {', '.join(PROVIDERS.keys())}", err=True)
            sys.exit(1)
        
        try:
            provider_class = load_provider(provider_name)
            provider = provider_class()
            info = provider.get_info()
            
            click.echo(f"Provider info for {provider_name}:")
            if info:
                for key, value in info.items():
                    if key == 'sample_voices':
                        click.echo(f"  {key}: {len(value)} voices available")
                    else:
                        click.echo(f"  {key}: {value}")
            else:
                click.echo(f"  No detailed info available for {provider_name}")
        except TTSError as e:
            click.echo(f"Error loading provider {provider_name}: {e}", err=True)
        except Exception as e:
            click.echo(f"Unexpected error loading provider {provider_name}: {e}", err=True)
    
    else:
        click.echo("Error: Invalid models command", err=True)
        click.echo("Usage: tts models [provider]", err=True)
        sys.exit(1)



def handle_config_commands(action: str, key: str = None, value: str = None) -> None:
    """Handle --config subcommands"""
    if action == "show":
        config = load_config()
        click.echo("Current configuration:")
        for k, v in config.items():
            click.echo(f"  {k}: {v}")
    
    elif action == "set":
        if not key or not value:
            click.echo("Error: config set requires both key and value", err=True)
            click.echo("Usage: tts config voice en-IE-EmilyNeural", err=True)
            click.echo("       tts config openai_api_key sk-...", err=True)
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
                        click.echo("   OpenAI keys start with 'sk-' and are ~50 characters", err=True)
                    elif provider == "google":
                        click.echo("   Google keys start with 'AIza' (39 chars) or 'ya29.' (OAuth)", err=True)
                    elif provider == "elevenlabs":
                        click.echo("   ElevenLabs keys are 32-character hex strings", err=True)
                    sys.exit(1)
            else:
                click.echo(f"❌ Unknown provider '{provider}' for API key", err=True)
                click.echo("   Supported providers: openai, google, elevenlabs", err=True)
                sys.exit(1)
        else:
            # Regular config setting
            if set_setting(key, value):
                click.echo(f"✅ Set {key} = {value}")
            else:
                click.echo(f"❌ Failed to save configuration", err=True)
                sys.exit(1)
    
    elif action == "reset":
        if save_config(get_default_config()):
            click.echo("Configuration reset to defaults")
        else:
            click.echo("Failed to reset configuration", err=True)
            sys.exit(1)
    
    elif action == "edit":
        config = load_config()
        click.echo("Interactive configuration editor:")
        click.echo("Press Enter to keep current value, or type new value")
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
            click.echo("Configuration updated successfully")
        else:
            click.echo("Failed to save configuration", err=True)
            sys.exit(1)
    
    else:
        click.echo("Error: Unknown config action. Use: show, set, reset, or edit", err=True)
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
            click.echo(f"⚠️  Warning: ElevenLabs similarity_boost must be a number, got '{kwargs['similarity_boost']}'", err=True)
    
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


def handle_synthesize(text: str, model: str, output: str, save: bool, voice: str, 
                     clone: str, output_format: str, options: tuple, logger: logging.Logger, 
                     json_output: bool = False, debug: bool = False, rate: str = None, pitch: str = None) -> None:
    """Handle main synthesis command using the core TTS engine."""
    # Parse key=value options
    kwargs = {}
    for opt in options:
        if "=" not in opt:
            click.echo(f"Error: Invalid option format '{opt}'. Expected 'key=value'", err=True)
            sys.exit(1)
        key, value = opt.split("=", 1)
        kwargs[key] = value
    
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
            click.echo(f"Saving with {model}...")
        
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


def handle_doctor_command() -> None:
    """Check system capabilities and provider availability"""
    click.echo("TTS System Health Check")
    click.echo("━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Suppress all logging during health checks
    logger = logging.getLogger(__name__)
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
                    import torch
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
        click.echo("Error: Specify a provider to install", err=True)
        click.echo("Usage: tts install <provider> [gpu]")
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
                        click.echo("💡 Try manually: pipx inject --index-url https://download.pytorch.org/whl/cu121 goobits-tts torch torchvision torchaudio")
                        return
                else:
                    click.echo("📦 Installing PyTorch (CPU)...")
                    try:
                        subprocess.run([
                            'pipx', 'inject', 'goobits-tts', 'torch', 'torchvision', 'torchaudio'
                        ], check=True, capture_output=True)
                        click.echo("✅ PyTorch (CPU) installed successfully!")
                    except subprocess.CalledProcessError as e:
                        click.echo("❌ Failed to install PyTorch")
                        click.echo("💡 Try manually: pipx inject goobits-tts torch torchvision torchaudio")
                        return
            
            return
            
        except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
            click.echo(f"📦 Chatterbox not available: {e}")
            click.echo("📦 Installing dependencies...")
            
            # Install PyTorch first
            if gpu_flag:
                click.echo("📦 Installing PyTorch with CUDA support...")
                try:
                    subprocess.run([
                        'pipx', 'inject', '--index-url', 'https://download.pytorch.org/whl/cu121',
                        'goobits-tts', 'torch', 'torchvision', 'torchaudio'
                    ], check=True)
                    click.echo("✅ PyTorch with CUDA installed!")
                except subprocess.CalledProcessError as e:
                    click.echo(f"❌ Failed to install PyTorch with CUDA: {e}")
                    click.echo("💡 Try manually: pipx inject --index-url https://download.pytorch.org/whl/cu121 tts-cli torch torchvision torchaudio")
                    return
            else:
                click.echo("📦 Installing PyTorch (CPU)...")
                try:
                    subprocess.run([
                        'pipx', 'inject', 'tts-cli', 'torch', 'torchvision', 'torchaudio'
                    ], check=True, capture_output=True)
                    click.echo("✅ PyTorch (CPU) installed!")
                except subprocess.CalledProcessError as e:
                    click.echo(f"❌ Failed to install PyTorch: {e}")
                    click.echo("💡 Try manually: pipx inject goobits-tts torch torchvision torchaudio")
                    return
            
            # Install chatterbox-tts
            click.echo("📦 Installing Chatterbox TTS...")
            try:
                subprocess.run(['pipx', 'inject', 'goobits-tts', 'chatterbox-tts'], check=True, capture_output=True)
                click.echo("✅ Chatterbox TTS installed successfully!")
                click.echo("🎉 Installation complete! You can now use Chatterbox with voice cloning.")
            except subprocess.CalledProcessError as e:
                click.echo(f"❌ Failed to install Chatterbox TTS: {e}")
                click.echo("💡 Try manually: pipx inject goobits-tts chatterbox-tts")
            
    elif provider == "edge_tts":
        click.echo("✅ Edge TTS is already included and ready to use!")
        
    else:
        click.echo(f"Error: Unknown provider '{provider}'", err=True)
        click.echo("Available providers: chatterbox, edge_tts")
        sys.exit(1)


def handle_load_command(args: tuple) -> None:
    """Load voice files into memory for fast access"""
    if len(args) == 0:
        click.echo("Error: Specify voice files to load", err=True)
        click.echo("Usage: tts load <voice_file> [voice_file2] ...")
        click.echo("Example: tts load ~/my_voice.wav ~/narrator.wav")
        sys.exit(1)
    
    voice_manager = VoiceManager()
    
    for voice_path in args:
        voice_file = Path(voice_path).expanduser()
        if not voice_file.exists():
            click.echo(f"Error: Voice file not found: {voice_file}", err=True)
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
        click.echo(f"Error: Unknown provider '{provider_name}'", err=True)
        click.echo(f"Available providers: {', '.join(tts_engine.providers_registry.keys())}")
        return
    
    try:
        info = tts_engine.get_provider_info(provider_name)
        if not info:
            click.echo(f"Error: No info available for {provider_name}", err=True)
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
                    click.echo(f"  ✅ Edge TTS: Ready")
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
        from .document_processing.parser_factory import DocumentParserFactory
        from .document_processing.performance_cache import PerformanceOptimizer
        from .speech_synthesis.advanced_emotion_detector import AdvancedEmotionDetector
        from .speech_synthesis.ssml_generator import SSMLGenerator, SSMLPlatform
        from .speech_synthesis.speech_markdown import SpeechMarkdownConverter
        from .speech_synthesis.semantic_formatter import SemanticFormatter
        from .config import load_config
        import hashlib
        
        # Load configuration
        user_config = load_config()
        doc_config = user_config.get('document_parsing', {})
        speech_config = user_config.get('speech_synthesis', {})
        
        # Helper function to cache results
        def _cache_result(key: str, content: str) -> None:
            try:
                from pathlib import Path
                import pickle
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
                import time
                import pickle
                
                # Check cache age
                file_age = time.time() - cache_file.stat().st_mtime
                cache_ttl = doc_config.get('cache_ttl', 3600)
                
                if file_age <= cache_ttl:
                    try:
                        with open(cache_file, 'rb') as f:
                            cached_result = pickle.load(f)
                        if debug:
                            logger.info(f"Using cached result for {document_path}")
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
            click.echo(f"Warning: No content extracted from {document_path}", err=True)
            return None
        
        # Apply emotion detection if enabled
        if emotion_profile == "auto" and doc_config.get('emotion_detection', True):
            detector = AdvancedEmotionDetector()
            emotion_profile = detector.detect_document_type(elements)
            if debug:
                click.echo(f"  Detected emotion profile: {emotion_profile}")
        
        # Skip formatting - pass elements directly to emotion detector
        # The SemanticFormatter's format_for_speech method returns text, not elements
        formatted_elements = elements
        
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
        click.echo(f"Error: Document file not found: {document_path}", err=True)
        return None
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Document processing error: {e}")
        click.echo(f"Error processing document: {e}", err=True)
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
        click.echo("Error: Specify voice files to unload or use --all", err=True)
        click.echo("Usage: tts unload <voice_file> [voice_file2] ...")
        click.echo("       tts unload --all")
        click.echo("Example: tts unload my_voice.wav")
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


@click.command()
@click.version_option(version=__version__, prog_name="tts")
@click.option("-l", "--list", "list_models", is_flag=True, help="List available models")
@click.option("-s", "--save", is_flag=True, help="Save to file instead of streaming to speakers (default: stream)")
@click.argument("text", required=False)
@click.option("-m", "--model", help="TTS model to use")
@click.option("-o", "--output", help="Output file path")
@click.option("-f", "--format", "output_format", type=click.Choice(['mp3', 'wav', 'ogg', 'flac']), help="Audio output format")
@click.option("-v", "--voice", help="Voice to use (e.g., en-GB-SoniaNeural for edge_tts)")
@click.option("--clone", help="Audio file to clone voice from (deprecated: use --voice instead)")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
@click.option("--debug", is_flag=True, help="Show debug information during processing")
@click.option("--document", type=click.Path(exists=True), help="Convert document to speech (HTML, JSON, Markdown)")
@click.option("--doc-format", "doc_format", type=click.Choice(['auto', 'markdown', 'html', 'json']), default='auto', help="Document format (auto-detect by default)")
@click.option("--ssml-platform", type=click.Choice(['azure', 'google', 'amazon', 'generic']), default='generic', help="SSML platform for voice synthesis")
@click.option("--emotion-profile", type=click.Choice(['technical', 'marketing', 'narrative', 'tutorial', 'auto']), default='auto', help="Emotion profile for document type")
@click.option("--rate", help="Speech rate adjustment (e.g., +20%, -50%, 150%)")
@click.option("--pitch", help="Pitch adjustment (e.g., +5Hz, -10Hz)")
@click.argument("options", nargs=-1)
def main(text: str, model: str, output: str, options: tuple, list_models: bool, save: bool, voice: str, clone: str, output_format: str, json_output: bool, debug: bool, document: str, doc_format: str, ssml_platform: str, emotion_profile: str, rate: str, pitch: str) -> None:
    """🎤 Transform text into speech with AI-powered voices
    
    TTS CLI supports multiple providers with smart auto-selection and voice cloning.
    Stream directly to speakers or save high-quality audio files.
    
    \b
    📝 Basic Usage:
      tts "Hello world"                    # Stream with default voice
      tts "Hello" --save                   # Save to file
      tts "Hello" --voice edge_tts:en-US-JennyNeural
    
    \b
    📄 Document Processing:
      tts --document report.html           # Convert HTML to speech
      tts --document api.json --emotion-profile technical
      tts --document README.md --ssml-platform azure
    
    \b
    🎙️ Voice Management:
      tts voices                           # Interactive voice browser
      tts load voice.wav                   # Preload voice for fast access
      tts unload voice.wav                 # Remove voice from memory
    
    \b
    ⚙️ Configuration & System:
      tts config                           # Show current settings
      tts config voice edge_tts:en-IE-EmilyNeural
      tts doctor                           # Check system health
      tts status                           # Show loaded voices & providers
    
    \b
    📦 Provider Management:
      tts models                           # List all providers
      tts install chatterbox gpu           # Install dependencies
    
    \b
    🚀 Supported Providers:
      • Edge TTS (Microsoft): Free, 400+ neural voices
      • Chatterbox: Local voice cloning with GPU support  
      • OpenAI TTS: Premium voices (alloy, echo, fable, nova, onyx, shimmer)
      • Google Cloud TTS: Neural voices with 40+ languages
      • ElevenLabs: Advanced voice synthesis and cloning
    """
    
    
    # Check if no meaningful arguments provided (text is None and no flags set) and no stdin
    if not text and not list_models and not document and not any([model, output, voice, clone, save]) and sys.stdin.isatty():
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        sys.exit(0)
    
    # Setup logging
    logger = setup_logging()
    
    # Initialize core TTS engine
    tts_engine = initialize_tts_engine(PROVIDERS)
    
    # Load configuration first
    user_config = load_config()
    
    # Handle subcommands (first positional argument)
    if text and text.lower() == "config":
        if len(options) == 0:
            handle_config_commands("show")
        elif len(options) == 1:
            action = options[0]
            if action in ["show", "reset", "edit"]:
                handle_config_commands(action)
            else:
                click.echo("Error: Invalid config command", err=True)
                click.echo("Usage: tts config [show|reset|edit] or tts config <key> <value>", err=True)
                sys.exit(1)
        elif len(options) == 2:
            # New syntax: tts config key value
            key = options[0]
            value = options[1]
            handle_config_commands("set", key, value)
        elif len(options) >= 3 and options[0] == "set":
            # Legacy syntax: tts config set key value
            key = options[1]
            value = " ".join(options[2:])
            handle_config_commands("set", key, value)
        else:
            click.echo("Error: Invalid config command format", err=True)
            click.echo("Usage: tts config [show|reset|edit] or tts config <key> <value>", err=True)
            sys.exit(1)
        return
    
    # Handle voices subcommand
    if text and text.lower() == "voices":
        handle_voices_command(options, PROVIDERS, load_provider)
        return
    
    # Handle voices snapshot
    if text and text.lower() == "voices-snapshot":
        show_browser_snapshot(PROVIDERS, load_provider)
        return
    
    # Handle models subcommand
    if text and text.lower() == "models":
        handle_models_command(options)
        return
    
    # Handle doctor subcommand
    if text and text.lower() == "doctor":
        handle_doctor_command()
        return
    
    # Handle install subcommand
    if text and text.lower() == "install":
        handle_install_command(options)
        return
    
    # Handle load subcommand
    if text and text.lower() == "load":
        handle_load_command(options)
        return
    
    # Handle info subcommand
    if text and text.lower() == "info":
        handle_info_command(options)
        return
    
    # Handle status subcommand
    if text and text.lower() == "status":
        handle_status_command()
        return
    
    # Handle unload subcommand
    if text and text.lower() == "unload":
        handle_unload_command(options)
        return
    
    # Handle legacy list command (redirect to models subcommand)
    if list_models:
        handle_models_command(())
        return
    
    # Handle document processing
    if document:
        if debug:
            click.echo(f"📄 Processing document: {document}")
            click.echo(f"  Format: {doc_format}")
            click.echo(f"  SSML Platform: {ssml_platform}")
            click.echo(f"  Emotion Profile: {emotion_profile}")
        
        text = handle_document_processing(
            document_path=document,
            doc_format=doc_format,
            ssml_platform=ssml_platform,
            emotion_profile=emotion_profile,
            debug=debug
        )
        if not text:
            if not json_output:
                click.echo("Error: Failed to process document", err=True)
            else:
                click.echo(json.dumps({"success": False, "error": "Failed to process document"}))
            sys.exit(1)
    
    # Apply configuration defaults where CLI args weren't provided
    if not model:
        config_voice = user_config.get('voice', 'edge_tts:en-IE-EmilyNeural')
        provider, _ = parse_voice_setting(config_voice)
        model = provider or 'edge_tts'
    
    # Handle voice and provider detection
    if voice:
        # Voice specified on command line - parse for provider
        detected_provider, parsed_voice = parse_voice_setting(voice)
        if detected_provider:
            model = detected_provider  # Always use detected provider
        voice = parsed_voice
    elif not voice:
        config_voice = user_config.get('voice')
        if config_voice:
            _, voice = parse_voice_setting(config_voice)
    
    # Validate model/provider early
    if model not in PROVIDERS:
        click.echo(f"Error: Unknown provider: {model}", err=True)
        sys.exit(1)
    
    if not output:
        if user_config.get('default_action') == 'save':
            output_dir = Path(user_config.get('output_dir', '~/Downloads')).expanduser()
            output = str(output_dir / "output.wav")
        else:
            output = "output.wav"
    
    if not output_format:
        output_format = user_config.get('format', 'mp3')
    
    # Override save flag based on config default_action if not explicitly set
    if not save and user_config.get('default_action') == 'save':
        save = True
    
    # Check required arguments - try stdin if no text provided and no document
    if not text and not document:
        # Check if text is being piped in
        if not sys.stdin.isatty():
            # Read from stdin
            try:
                text = sys.stdin.read().strip()
                if not text:
                    # Show help when empty stdin is provided
                    ctx = click.get_current_context()
                    click.echo(ctx.get_help())
                    sys.exit(0)
                logger.debug(f"Read {len(text)} characters from stdin")
            except Exception as e:
                logger.error(f"Failed to read from stdin: {e}")
                click.echo("Error: Failed to read text from stdin", err=True)
                sys.exit(1)
        else:
            # Error when no text is provided
            click.echo("Error: You must provide text to synthesize", err=True)
            sys.exit(1)
    
    # Parse JSON input if provided and override parameters
    text, json_params = parse_input(text)
    if json_params:
        # Override CLI parameters with JSON values
        voice = json_params.get('voice', voice)
        save = json_params.get('action') == 'save' if 'action' in json_params else save
        output = json_params.get('output_path', output)
        output_format = json_params.get('format', output_format)
    
    # Check output file permissions only if saving to file
    if save:
        output_path = Path(output)
        try:
            # Check if output directory exists and is writable
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Test write permissions by creating a temporary file
            test_file = output_path.parent / ".tts_write_test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            logger.error(f"Cannot write to output path {output_path}: {e}")
            click.echo(f"Error: Cannot write to output path {output_path}: {e}", err=True)
            sys.exit(1)
    
    # In standard streaming mode, display the text being spoken
    if not save and not json_output and not debug:
        # Show exactly what's being sent to TTS
        click.echo(f"\n{text}\n")
    
    # Handle main synthesis
    handle_synthesize(text, model, output, save, voice, clone, output_format, options, logger, json_output, debug, rate, pitch)


def cli():
    main()


if __name__ == "__main__":
    cli()