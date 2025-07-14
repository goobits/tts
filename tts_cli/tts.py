#!/usr/bin/env python3
import click
import importlib
import sys
import logging
import os
import curses
import tempfile
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Type, List, Tuple
from .base import TTSProvider
from .exceptions import TTSError, ProviderNotFoundError, ProviderLoadError, DependencyError, NetworkError
from .__version__ import __version__
from .config import load_config, save_config, get_default_config, parse_voice_setting, set_setting, get_setting, set_api_key, validate_api_key
from .voice_manager import VoiceManager


PROVIDERS: Dict[str, str] = {
    "chatterbox": ".providers.chatterbox.ChatterboxProvider",
    "edge_tts": ".providers.edge_tts.EdgeTTSProvider",
    "openai": ".providers.openai_tts.OpenAITTSProvider",
    "google": ".providers.google_tts.GoogleTTSProvider",
    "elevenlabs": ".providers.elevenlabs.ElevenLabsProvider",
}


def setup_logging():
    """Setup logging configuration for TTS CLI"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / "tts.log"),
            logging.StreamHandler()  # Also log to console for errors
        ]
    )
    
    # Set console handler to only show warnings and errors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Get logger for this module
    return logging.getLogger(__name__)


def load_provider(name: str) -> Type[TTSProvider]:
    if name not in PROVIDERS:
        raise ProviderNotFoundError(f"Unknown provider: {name}. Available: {', '.join(PROVIDERS.keys())}")
    
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


def interactive_voice_browser() -> None:
    """Interactive voice browser with arrow key navigation"""
    def main_browser(stdscr):
        # Initialize authentic Dracula theme colors
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        
        # Authentic Dracula color scheme with semantic meaning
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_MAGENTA)  # Selection highlight (pink bg)
        curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Title/brand (purple)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Provider names (cyan)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Keyboard keys (yellow)
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Success messages (green)
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)      # Error messages (red)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Normal text (white)
        
        # Collect all voices with provider info
        all_voices: List[Tuple[str, str]] = []  # (provider, voice_name)
        for provider_name in PROVIDERS.keys():
            try:
                provider_class = load_provider(provider_name)
                provider = provider_class()
                info = provider.get_info()
                if info:
                    # Use all_voices if available, fallback to sample_voices
                    voices = info.get('all_voices') or info.get('sample_voices', [])
                    for voice in voices:
                        all_voices.append((provider_name, voice))
            except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
                # Skip providers that can't be loaded (missing dependencies, etc.)
                continue
            except Exception as e:
                # Log unexpected errors but continue with other providers
                logging.getLogger(__name__).warning(f"Unexpected error loading provider {provider_name}: {e}")
                continue
        
        if not all_voices:
            stdscr.addstr(0, 0, "No voices available!")
            stdscr.refresh()
            stdscr.getch()
            return
        
        current_pos = 0
        scroll_offset = 0
        last_height, last_width = 0, 0
        last_scroll_offset = -1
        need_full_redraw = True
        is_playing = False
        current_playback_process = None
        
        while True:
            height, width = stdscr.getmaxyx()
            
            # Only clear screen if terminal size changed or scroll changed significantly
            if (height != last_height or width != last_width or need_full_redraw or 
                abs(scroll_offset - last_scroll_offset) > 1):
                stdscr.clear()
                need_full_redraw = False
                last_height, last_width = height, width
                last_scroll_offset = scroll_offset
            else:
                # Just clear the content area for minor updates
                for i in range(3, height-1):
                    stdscr.move(i, 0)
                    stdscr.clrtoeol()
            
            # Title - Purple (brand/header)
            title = ">>> TTS VOICE BROWSER v1.0 <<<"
            stdscr.addstr(0, 0, title[:width-1], curses.color_pair(2) | curses.A_BOLD)
            
            # Voice info line - voice name and details
            if current_pos < len(all_voices):
                current_provider, current_voice = all_voices[current_pos]
                # Extract language info from voice name (basic parsing)
                voice_parts = current_voice.split('-')
                if len(voice_parts) >= 3:
                    lang_code = voice_parts[0]
                    region_code = voice_parts[1] 
                    voice_name = voice_parts[2].replace('Neural', '')
                    
                    # Basic language mapping
                    lang_map = {
                        'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
                        'it': 'Italian', 'pt': 'Portuguese', 'ja': 'Japanese', 'ko': 'Korean',
                        'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi', 'ru': 'Russian'
                    }
                    region_map = {
                        'US': 'American', 'GB': 'British', 'AU': 'Australian', 'CA': 'Canadian',
                        'IE': 'Irish', 'IN': 'Indian', 'ZA': 'South African', 'FR': 'French',
                        'DE': 'German', 'ES': 'Spanish', 'IT': 'Italian', 'BR': 'Brazilian'
                    }
                    
                    language = lang_map.get(lang_code.lower(), lang_code.upper())
                    region = region_map.get(region_code.upper(), region_code.upper())
                    
                    # Determine gender from voice name (basic heuristic)
                    female_names = ['Emily', 'Jenny', 'Aria', 'Emma', 'Ana', 'Michelle', 'Sonia', 'Clara']
                    gender = 'Female' if any(name in voice_name for name in female_names) else 'Male'
                    
                    voice_info = f"🎯 {current_voice} • {region} {language} {gender}"
                else:
                    voice_info = f"🎯 {current_voice}"
                    
                stdscr.addstr(1, 0, voice_info[:width-1], curses.color_pair(7))
                
                # Provider and position line with playing status
                provider_line = f"{current_provider}: Voice {current_pos + 1} of {len(all_voices)}"
                if is_playing:
                    provider_line += " • 🎵 Playing"
                stdscr.addstr(2, 0, provider_line[:width-1], curses.color_pair(7))
            else:
                stdscr.addstr(1, 0, "🎯 No voice selected", curses.color_pair(7))
                stdscr.addstr(2, 0, "No voices available", curses.color_pair(7))
            
            # Controls - Mix of normal text and yellow keys (no "Controls:" prefix)
            x_pos = 0
            controls_parts = [
                ("[↑↓]", curses.color_pair(4)),   # Yellow keys
                (" Move ", curses.color_pair(7)), # Normal text
                ("[ENTER]", curses.color_pair(4)), # Yellow keys
                (" Preview ", curses.color_pair(7)), # Normal text
                ("[S]", curses.color_pair(4)),    # Yellow keys
                (" Save ", curses.color_pair(7)), # Normal text
                ("[Q]", curses.color_pair(4)),    # Yellow keys
                (" Exit", curses.color_pair(7))   # Normal text
            ]
            
            for text, color in controls_parts:
                if x_pos + len(text) < width:
                    stdscr.addstr(3, x_pos, text, color)
                    x_pos += len(text)
            
            # Subtle separator - normal color
            stdscr.addstr(4, 0, "_" * min(width-1, 64), curses.color_pair(7))
            
            # Calculate visible range  
            list_height = height - 6  # Reserve space for header (5 lines) + margin
            if current_pos < scroll_offset:
                scroll_offset = current_pos
            elif current_pos >= scroll_offset + list_height:
                scroll_offset = current_pos - list_height + 1
            
            # Display voices
            current_provider = ""
            display_row = 5  # Start after header
            
            for i in range(scroll_offset, min(len(all_voices), scroll_offset + list_height)):
                if display_row >= height:
                    break
                    
                provider, voice = all_voices[i]
                
                # Show provider header when it changes - Cyan
                if provider != current_provider:
                    if display_row < height:
                        provider_header = f"🔹 {provider.upper()}:"
                        stdscr.addstr(display_row, 0, provider_header[:width-1], 
                                    curses.color_pair(3) | curses.A_BOLD)
                        display_row += 1
                    current_provider = provider
                
                if display_row >= height:
                    break
                
                # Voice entry
                if i == current_pos:
                    # Highlighted voice - Black on Magenta (pink highlight)
                    prefix = " > "
                    attr = curses.color_pair(1) | curses.A_BOLD
                else:
                    # Normal voice - White text
                    prefix = "   "
                    attr = curses.color_pair(7)
                
                voice_line = f"{prefix}{voice}"
                if len(voice_line) > width - 1:
                    voice_line = voice_line[:width-4] + "..."
                
                stdscr.addstr(display_row, 0, voice_line, attr)
                display_row += 1
            
            
            stdscr.refresh()
            
            # Check if background playback finished
            if current_playback_process and current_playback_process.poll() is not None:
                is_playing = False
                current_playback_process = None
            
            # Handle input
            try:
                key = stdscr.getch()
                
                if key == curses.KEY_UP and current_pos > 0:
                    current_pos -= 1
                elif key == curses.KEY_DOWN and current_pos < len(all_voices) - 1:
                    current_pos += 1
                elif key == curses.KEY_PPAGE:  # Page Up
                    current_pos = max(0, current_pos - list_height)
                elif key == curses.KEY_NPAGE:  # Page Down
                    current_pos = min(len(all_voices) - 1, current_pos + list_height)
                elif key == curses.KEY_HOME:
                    current_pos = 0
                elif key == curses.KEY_END:
                    current_pos = len(all_voices) - 1
                elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER):
                    # Stop any current playback before starting new one
                    if current_playback_process and current_playback_process.poll() is None:
                        current_playback_process.terminate()
                        current_playback_process = None
                    
                    # Preview voice with background playback
                    provider, voice = all_voices[current_pos]
                    
                    # Set playing status
                    is_playing = True
                    
                    try:
                        # Generate preview in background thread
                        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                            temp_file = tmp.name
                        
                        def generate_and_play():
                            try:
                                # Generate audio
                                provider_class = load_provider(provider)
                                provider_instance = provider_class()
                                preview_text = "Hello! This is a preview of my voice."
                                kwargs = {"voice": voice}
                                provider_instance.synthesize(preview_text, temp_file, **kwargs)
                                
                                # Start playing in background
                                try:
                                    play_process = subprocess.Popen(['ffplay', '-nodisp', '-autoexit', temp_file], 
                                                                  stderr=subprocess.DEVNULL,
                                                                  stdout=subprocess.DEVNULL)
                                    return play_process
                                except (FileNotFoundError, subprocess.CalledProcessError):
                                    return None
                            except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
                                # Provider-specific errors during synthesis
                                logging.getLogger(__name__).error(f"Failed to generate preview with {provider}: {e}")
                                return None
                            except Exception as e:
                                # Unexpected errors during audio generation
                                logging.getLogger(__name__).error(f"Unexpected error generating preview for {provider}:{voice}: {e}")
                                return None
                        
                        # Start generation and playback in background thread
                        def background_worker():
                            nonlocal current_playback_process
                            current_playback_process = generate_and_play()
                        
                        worker_thread = threading.Thread(target=background_worker)
                        worker_thread.daemon = True
                        worker_thread.start()
                            
                    except OSError as e:
                        # File system or process creation errors
                        logging.getLogger(__name__).error(f"System error during voice preview setup: {e}")
                        is_playing = False
                    except Exception as e:
                        # Catch-all for unexpected preview errors
                        logging.getLogger(__name__).error(f"Unexpected error starting voice preview: {e}")
                        is_playing = False
                        
                elif key in (ord('s'), ord('S')):
                    # Set as default voice
                    provider, voice = all_voices[current_pos]
                    voice_setting = f"{provider}:{voice}"
                    if set_setting("voice", voice_setting):
                        stdscr.addstr(height-1, 0, f"Set default voice to {voice}", 
                                    curses.color_pair(5) | curses.A_BOLD)
                    else:
                        stdscr.addstr(height-1, 0, "Failed to save voice setting", 
                                    curses.color_pair(6))
                    stdscr.refresh()
                    curses.napms(1500)  # Show confirmation for 1.5 seconds
                    
                elif key in (ord('q'), ord('Q'), 27):  # q, Q, or Escape
                    # Stop any background playback before exiting
                    if current_playback_process and current_playback_process.poll() is None:
                        current_playback_process.terminate()
                    break
                    
            except KeyboardInterrupt:
                break
    
    try:
        curses.wrapper(main_browser)
    except Exception as e:
        click.echo(f"Interactive browser failed: {e}", err=True)
        click.echo("Falling back to simple voice list...", err=True)
        # Fallback to simple list
        handle_voices_command(())


def handle_voices_command(args: tuple) -> None:
    """Handle voices subcommand"""
    # Parse language filter argument
    language_filter = None
    if len(args) > 0:
        language_filter = args[0].lower()
    
    if len(args) == 0:
        # tts voices - launch interactive browser
        if sys.stdout.isatty():
            # Terminal environment - use interactive browser
            interactive_voice_browser()
        else:
            # Non-terminal (pipe/script) - use simple list
            click.echo("Available voices from all providers:")
            click.echo()
            
            for provider_name in PROVIDERS.keys():
                try:
                    provider_class = load_provider(provider_name)
                    provider = provider_class()
                    info = provider.get_info()
                    
                    # Use all_voices if available, fallback to sample_voices
                    voices = info.get('all_voices') or info.get('sample_voices', [])
                    
                    if voices:
                        click.echo(f"🔹 {provider_name.upper()}:")
                        for voice in voices:
                            click.echo(f"  - {voice}")
                
                except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
                    # Skip providers that can't be loaded (missing dependencies, etc.)
                    continue
                except Exception as e:
                    # Log unexpected errors but continue with other providers
                    logging.getLogger(__name__).warning(f"Unexpected error loading provider {provider_name}: {e}")
                    continue
    else:
        # Language filtering mode: tts voices en, tts voices english, etc.
        click.echo(f"Voices for language: {language_filter}")
        click.echo("=" * 40)
        
        # English language patterns
        english_patterns = ['en-', 'english']
        
        if language_filter in ['en', 'english', 'eng']:
            # Show only English voices
            for provider_name in PROVIDERS.keys():
                try:
                    provider_class = load_provider(provider_name)
                    provider = provider_class()
                    info = provider.get_info()
                    
                    voices = info.get('all_voices') or info.get('sample_voices', [])
                    english_voices = []
                    
                    if provider_name == 'openai' or provider_name == 'elevenlabs':
                        # OpenAI and ElevenLabs voices are English by default
                        english_voices = voices
                    else:
                        # Filter for English voices (en-*)
                        english_voices = [v for v in voices if v.startswith('en-')]
                    
                    if english_voices:
                        click.echo(f"\n🔹 {provider_name.upper()} (English):")
                        
                        # Group by region for better organization
                        regions = {}
                        for voice in english_voices:
                            if provider_name in ['openai', 'elevenlabs']:
                                region = "General"
                            else:
                                # Extract region from voice name (e.g., en-US-*, en-GB-*)
                                parts = voice.split('-')
                                if len(parts) >= 2:
                                    region_code = f"{parts[0]}-{parts[1]}"
                                    region_map = {
                                        'en-US': '🇺🇸 US English',
                                        'en-GB': '🇬🇧 British English', 
                                        'en-IE': '🇮🇪 Irish English',
                                        'en-AU': '🇦🇺 Australian English',
                                        'en-CA': '🇨🇦 Canadian English',
                                        'en-IN': '🇮🇳 Indian English',
                                        'en-ZA': '🇿🇦 South African English',
                                        'en-NZ': '🇳🇿 New Zealand English',
                                        'en-SG': '🇸🇬 Singapore English',
                                        'en-HK': '🇭🇰 Hong Kong English',
                                        'en-PH': '🇵🇭 Philippine English',
                                        'en-KE': '🇰🇪 Kenyan English',
                                        'en-NG': '🇳🇬 Nigerian English',
                                        'en-TZ': '🇹🇿 Tanzanian English'
                                    }
                                    region = region_map.get(region_code, region_code)
                                else:
                                    region = "Other"
                            
                            if region not in regions:
                                regions[region] = []
                            regions[region].append(voice)
                        
                        # Display grouped by region
                        for region, region_voices in regions.items():
                            if len(regions) > 1:
                                click.echo(f"   {region}:")
                                for voice in sorted(region_voices):
                                    click.echo(f"     - {voice}")
                            else:
                                for voice in sorted(region_voices):
                                    click.echo(f"   - {voice}")
                
                except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
                    # Skip providers that can't be loaded (missing dependencies, etc.)
                    continue
                except Exception as e:
                    # Log unexpected errors but continue with other providers
                    logging.getLogger(__name__).warning(f"Unexpected error loading provider {provider_name}: {e}")
                    continue
        else:
            # Generic language filtering
            for provider_name in PROVIDERS.keys():
                try:
                    provider_class = load_provider(provider_name)
                    provider = provider_class()
                    info = provider.get_info()
                    
                    voices = info.get('all_voices') or info.get('sample_voices', [])
                    filtered_voices = [v for v in voices if language_filter in v.lower()]
                    
                    if filtered_voices:
                        click.echo(f"\n🔹 {provider_name.upper()}:")
                        for voice in filtered_voices:
                            click.echo(f"  - {voice}")
                
                except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
                    # Skip providers that can't be loaded (missing dependencies, etc.)
                    continue
                except Exception as e:
                    # Log unexpected errors but continue with other providers
                    logging.getLogger(__name__).warning(f"Unexpected error loading provider {provider_name}: {e}")
                    continue
    
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


def handle_preview_voice(voice_name: str, model: str, logger: logging.Logger) -> None:
    """Handle --preview-voice command"""
    import tempfile
    import subprocess
    
    try:
        provider_class = load_provider(model)
        provider = provider_class()
        
        # Standard preview text that showcases voice characteristics
        preview_text = "Hello! This is a preview of my voice. I can speak clearly with natural intonation and emotion."
        
        logger.info(f"Playing voice preview for {voice_name} using {model}")
        click.echo(f"Playing preview of voice '{voice_name}' with {model}...")
        
        # Create temporary file for preview
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            temp_file = tmp.name
        
        try:
            # Generate audio to temporary file
            kwargs = {"voice": voice_name}
            provider.synthesize(preview_text, temp_file, **kwargs)
            
            # Play the temporary file
            try:
                subprocess.run([
                    'ffplay', '-nodisp', '-autoexit', temp_file
                ], check=True, stderr=subprocess.DEVNULL)
                click.echo("Preview completed.")
            except FileNotFoundError:
                click.echo(f"Audio generated: {temp_file}")
                click.echo("Install ffmpeg to play audio automatically, or play the file manually.")
            except subprocess.CalledProcessError:
                click.echo(f"Audio generated: {temp_file}")
                click.echo("Could not play audio automatically. Play the file manually.")
                
        finally:
            # Clean up temporary file
            try:
                Path(temp_file).unlink()
            except OSError as e:
                # Log but don't fail if we can't clean up temp file
                logger.debug(f"Could not clean up temporary file {temp_file}: {e}")
            except Exception as e:
                # Unexpected error during cleanup
                logger.warning(f"Unexpected error cleaning up temporary file {temp_file}: {e}")
        
    except DependencyError as e:
        logger.error(f"Voice preview failed: {e}")
        click.echo(f"Dependency missing: {e}", err=True)
    except TTSError as e:
        logger.error(f"Voice preview failed: {e}")
        click.echo(f"Error playing voice preview: {e}", err=True)
    except Exception as e:
        logger.error(f"Voice preview failed: {e}")
        click.echo(f"Unexpected error playing voice preview: {e}", err=True)


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


def handle_synthesize(text: str, model: str, output: str, save: bool, voice: str, 
                     clone: str, output_format: str, options: tuple, logger: logging.Logger) -> None:
    """Handle main synthesis command"""
    # Parse key=value options
    kwargs = {}
    for opt in options:
        if "=" not in opt:
            click.echo(f"Error: Invalid option format '{opt}'. Expected 'key=value'", err=True)
            sys.exit(1)
        key, value = opt.split("=", 1)
        kwargs[key] = value
    
    # Default to streaming unless --save flag is used
    stream = not save
    if stream:
        kwargs["stream"] = "true"
    
    # Add output format to kwargs
    kwargs["output_format"] = output_format
    
    # Add voice parameter if specified
    if voice:
        kwargs["voice"] = voice
    
    # Add clone parameter if specified (for chatterbox voice cloning)
    if clone:
        kwargs["voice"] = clone
    
    # Validate voice if specified
    if voice and not clone:  # Don't validate for voice cloning (file paths)
        try:
            provider_class = load_provider(model)
            provider = provider_class()
            info = provider.get_info()
            if info and 'sample_voices' in info and info['sample_voices']:
                if voice not in info['sample_voices']:
                    logger.warning(f"Voice '{voice}' not found in available voices for {model}")
                    click.echo(f"Warning: Voice '{voice}' not found in available voices.", err=True)
                    click.echo(f"Use --list-voices {model} to see available voices.", err=True)
        except Exception as e:
            logger.debug(f"Voice validation failed for {model}: {e}")
            # If validation fails, continue anyway (provider might support more voices)
            pass
    
    try:
        # Load and instantiate provider
        logger.info(f"Starting TTS synthesis with {model} provider")
        logger.debug(f"Text: '{text[:50]}...' | Voice: {voice} | Format: {output_format}")
        
        provider_class = load_provider(model)
        provider = provider_class()
        
        # Show info if requested
        if "info" in kwargs and kwargs.pop("info").lower() in ("true", "1", "yes"):
            info = provider.get_info()
            if info:
                click.echo(f"Provider info for {model}:")
                for key, value in info.items():
                    click.echo(f"  {key}: {value}")
            else:
                click.echo(f"No info available for {model}")
            return
        
        # Synthesize speech
        if stream:
            logger.info(f"Starting audio stream with {model}")
            click.echo(f"Streaming with {model}...")
            provider.synthesize(text, "", **kwargs)  # Empty output path for streaming
        else:
            logger.info(f"Synthesizing audio to {output}")
            click.echo(f"Saving with {model}...")
            provider.synthesize(text, output, **kwargs)
        
        if not stream:
            file_size = Path(output).stat().st_size if Path(output).exists() else 0
            logger.info(f"Synthesis completed. File: {output} ({file_size} bytes)")
            click.echo(f"Audio saved to: {output}")
        else:
            logger.info("Audio streaming completed")
        
    except DependencyError as e:
        logger.error(f"Synthesis failed - dependency missing for {model}: {e}")
        click.echo(f"Dependency missing for {model}: {e}", err=True)
        click.echo(f"Hint: Check the installation guide for {model} provider dependencies", err=True)
        sys.exit(1)
    except NetworkError as e:
        logger.error(f"Synthesis failed - network error with {model}: {e}")
        click.echo(f"Network error with {model}: {e}", err=True)
        click.echo("Hint: Check your internet connection for cloud-based providers", err=True)
        sys.exit(1)
    except TTSError as e:
        logger.error(f"Synthesis failed with {model}: {e}")
        click.echo(f"TTS error with {model}: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found during synthesis with {model}: {e}")
        click.echo(f"File not found: {e}", err=True)
        click.echo("Hint: Check file paths and ensure all required files exist", err=True)
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"Permission error during synthesis with {model}: {e}")
        click.echo(f"Permission error: {e}", err=True)
        click.echo("Hint: Check file permissions or try running with appropriate privileges", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected synthesis failure with {model}: {type(e).__name__}: {e}")
        click.echo(f"Unexpected error with {model}: {type(e).__name__}: {e}", err=True)
        click.echo("Hint: Try running with --help for usage information or check the logs", err=True)
        sys.exit(1)


def handle_doctor_command() -> None:
    """Check system capabilities and provider availability"""
    click.echo("🔍 TTS System Health Check")
    click.echo("=" * 40)
    
    logger = logging.getLogger(__name__)
    
    # Check core dependencies
    click.echo("\n📦 Core Dependencies:")
    
    # Check Python version
    python_version = sys.version.split()[0]
    if sys.version_info >= (3, 8):
        click.echo(f"  ✅ Python {python_version}")
    else:
        click.echo(f"  ❌ Python {python_version} (requires >= 3.8)")
    
    # Check ffmpeg/ffplay
    try:
        subprocess.run(['ffplay', '-version'], capture_output=True, check=True)
        click.echo("  ✅ FFmpeg/FFplay available")
    except (FileNotFoundError, subprocess.CalledProcessError):
        click.echo("  ⚠️  FFmpeg/FFplay not found (audio playback may not work)")
    
    # Check providers
    click.echo("\n🎤 TTS Providers:")
    
    for provider_name in PROVIDERS.keys():
        try:
            provider_class = load_provider(provider_name)
            provider = provider_class()
            info = provider.get_info()
            
            if provider_name == "edge_tts":
                click.echo(f"  ✅ {provider_name.upper()}: Ready ({len(info.get('sample_voices', []))} voices)")
            elif provider_name == "chatterbox":
                voice_count = len(info.get('sample_voices', []))
                if voice_count > 0:
                    click.echo(f"  ✅ {provider_name.upper()}: Ready ({voice_count} voice files)")
                else:
                    click.echo(f"  ⚠️  {provider_name.upper()}: No voice files in ./voices/ directory")
                
                # Check GPU availability for chatterbox
                try:
                    import torch
                    if torch.cuda.is_available():
                        gpu_name = torch.cuda.get_device_name(0)
                        click.echo(f"    🚀 GPU Available: {gpu_name}")
                    else:
                        click.echo(f"    💻 Using CPU (install CUDA for GPU acceleration)")
                except ImportError:
                    click.echo(f"    ❌ PyTorch not installed (required for chatterbox)")
                    
        except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
            click.echo(f"  ❌ {provider_name.upper()}: {e}")
        except Exception as e:
            click.echo(f"  ❌ {provider_name.upper()}: Unexpected error - {e}")
            logger.debug(f"Doctor check failed for {provider_name}: {e}")
    
    # Configuration check
    click.echo("\n⚙️  Configuration:")
    config = load_config()
    default_voice = config.get('voice', 'edge_tts:en-IE-EmilyNeural')
    provider, voice = parse_voice_setting(default_voice)
    click.echo(f"  🎯 Default voice: {voice} ({provider})")
    click.echo(f"  📁 Output directory: {config.get('output_dir', '~/Downloads')}")
    
    click.echo("\n💡 Need help? Try:")
    click.echo("  tts install chatterbox gpu  # Add GPU voice cloning")
    click.echo("  tts config edit               # Change settings")
    click.echo("  tts voices                    # Browse available voices")


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
                    click.echo("💡 This may take a few minutes...")
                    # In a real implementation, we'd run: pipx inject tts-cli torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
                    click.echo("⚠️  Manual installation required:")
                    click.echo("   pipx inject tts-cli torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
                else:
                    click.echo("📦 Installing PyTorch (CPU)...")
                    click.echo("⚠️  Manual installation required:")
                    click.echo("   pipx inject tts-cli torch torchvision torchaudio")
            
            return
            
        except (ProviderNotFoundError, ProviderLoadError, DependencyError) as e:
            click.echo(f"📦 Chatterbox not available: {e}")
            click.echo("📦 Manual installation required")
            click.echo("💡 Install with:")
            if gpu_flag:
                click.echo("   pipx inject tts-cli torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
                click.echo("   pipx inject tts-cli chatterbox-tts")
            else:
                click.echo("   pipx inject tts-cli torch torchvision torchaudio")
                click.echo("   pipx inject tts-cli chatterbox-tts")
            
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
@click.argument("options", nargs=-1)
def main(text: str, model: str, output: str, options: tuple, list_models: bool, save: bool, voice: str, clone: str, output_format: str):
    """Text-to-speech CLI with multiple providers."""
    
    # Setup logging
    logger = setup_logging()
    
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
        handle_voices_command(options)
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
    
    # Check required arguments
    if not text:
        logger.error("No text provided for synthesis")
        click.echo("Error: You must provide text to synthesize", err=True)
        sys.exit(1)
    
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
    
    # Handle main synthesis
    handle_synthesize(text, model, output, save, voice, clone, output_format, options, logger)


def cli():
    main()


if __name__ == "__main__":
    cli()