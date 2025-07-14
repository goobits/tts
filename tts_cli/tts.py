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


def analyze_voice(provider: str, voice_name: str) -> tuple:
    """Analyze voice to extract quality, region, and gender info"""
    # Quality analysis
    if 'Chirp3-HD' in voice_name or 'Studio' in voice_name:
        quality = 3  # ★★★
    elif 'Neural2' in voice_name or 'Wavenet' in voice_name or 'Chirp' in voice_name:
        quality = 3  # ★★★ 
    elif 'Neural' in voice_name or provider in ['openai', 'elevenlabs']:
        quality = 2  # ★★☆
    else:
        quality = 1  # ★☆☆
    
    # Region analysis
    region = "General"
    if voice_name.startswith('en-'):
        parts = voice_name.split('-')
        if len(parts) >= 2:
            region_code = f"{parts[0]}-{parts[1]}"
            region_map = {
                'en-US': 'American',
                'en-GB': 'British', 
                'en-IE': 'Irish',
                'en-AU': 'Australian',
                'en-CA': 'Canadian',
                'en-IN': 'Indian',
                'en-ZA': 'S.African',
                'en-NZ': 'N.Zealand',
                'en-SG': 'Singapore',
                'en-HK': 'Hong Kong'
            }
            region = region_map.get(region_code, region_code)
    
    # Gender analysis (basic heuristics)
    gender = "U"  # Unknown
    female_indicators = ['Emily', 'Jenny', 'Aria', 'Emma', 'Ana', 'Michelle', 'Sonia', 'Clara', 
                        'Libby', 'Maisie', 'rachel', 'bella', 'Nova', 'Female', 'F', 'A', 'C', 'E', 'G', 'I']
    male_indicators = ['Connor', 'Brian', 'Andrew', 'Christopher', 'Eric', 'Guy', 'Roger', 'Steffan',
                      'Ryan', 'Thomas', 'adam', 'antoni', 'arnold', 'josh', 'Male', 'M', 'B', 'D', 'F', 'H', 'J']
    
    voice_upper = voice_name.upper()
    if any(indicator.upper() in voice_upper for indicator in female_indicators):
        gender = "F"
    elif any(indicator.upper() in voice_upper for indicator in male_indicators):
        gender = "M"
    
    return quality, region, gender


def interactive_voice_browser() -> None:
    """Enhanced interactive voice browser with search, filters, and preview"""
    def main_browser(stdscr):
        # Initialize curses and colors
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        
        # Color scheme
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_MAGENTA)  # Selection highlight
        curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Title/brand
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Provider/section headers
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Quality stars/keys
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Success/checked items
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)      # Error/unchecked
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Normal text
        curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Secondary text
        
        # Voice data structure: (provider, voice_name, quality, region, gender)
        all_voices = []
        voice_cache = {}
        
        # Load all voices with metadata
        for provider_name in PROVIDERS.keys():
            try:
                provider_class = load_provider(provider_name)
                provider = provider_class()
                info = provider.get_info()
                if info:
                    voices = info.get('all_voices') or info.get('sample_voices', [])
                    for voice in voices:
                        quality, region, gender = analyze_voice(provider_name, voice)
                        all_voices.append((provider_name, voice, quality, region, gender))
                        voice_cache[f"{provider_name}:{voice}"] = (quality, region, gender)
            except (ProviderNotFoundError, ProviderLoadError, DependencyError):
                continue
            except Exception as e:
                logging.getLogger(__name__).warning(f"Error loading provider {provider_name}: {e}")
                continue
        
        if not all_voices:
            stdscr.addstr(0, 0, "No voices available!")
            stdscr.refresh()
            stdscr.getch()
            return
        
        # Browser state
        current_pos = 0
        scroll_offset = 0
        search_text = ""
        search_active = False
        
        # Filter state
        filters = {
            'providers': {'edge_tts': True, 'google': True, 'openai': True, 'elevenlabs': True, 'chatterbox': True},
            'quality': {3: True, 2: True, 1: False},  # High, Medium, Low
            'regions': {'Irish': True, 'British': True, 'American': False, 'Australian': False, 'Canadian': False, 'General': True}
        }
        
        # Playback state
        is_playing = False
        current_playback_process = None
        playing_voice = None
        favorites = set()
        
        def filter_voices():
            """Apply current filters to voice list"""
            filtered = []
            for provider, voice, quality, region, gender in all_voices:
                # Provider filter
                if not filters['providers'].get(provider, False):
                    continue
                    
                # Quality filter  
                if not filters['quality'].get(quality, False):
                    continue
                    
                # Region filter
                if not filters['regions'].get(region, False):
                    continue
                    
                # Search filter
                if search_text:
                    search_lower = search_text.lower()
                    if not (search_lower in voice.lower() or 
                           search_lower in provider.lower() or
                           search_lower in region.lower() or
                           search_lower in gender.lower()):
                        continue
                
                filtered.append((provider, voice, quality, region, gender))
            
            return filtered
        
        def draw_interface():
            """Draw the three-panel interface"""
            height, width = stdscr.getmaxyx()
            stdscr.clear()
            
            # Calculate panel widths
            filter_width = 20
            preview_width = 18
            voice_width = width - filter_width - preview_width - 3  # 3 for borders
            
            # Header line
            title = f"TTS VOICE BROWSER v2.0"
            search_display = f"Search: [{search_text:<15}] 🔍"
            filtered_voices = filter_voices()
            status = f"Showing: {len(filtered_voices)}/{len(all_voices)}"
            playing_status = f"Playing: ♪ {playing_voice}" if is_playing and playing_voice else ""
            
            header = f"{title:<30} {search_display:<25} {status:<20} {playing_status}"
            stdscr.addstr(0, 0, header[:width-1], curses.color_pair(2) | curses.A_BOLD)
            
            # Draw borders
            stdscr.addstr(1, 0, "├" + "─" * (filter_width-1) + "┬" + "─" * (voice_width-1) + "┬" + "─" * (preview_width-1) + "┤")
            
            # Panel headers
            stdscr.addstr(1, 2, " FILTERS ", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(1, filter_width + 2, " VOICES ", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(1, filter_width + voice_width + 2, " PREVIEW ", curses.color_pair(3) | curses.A_BOLD)
            
            # Draw vertical borders for panels
            for row in range(2, height-1):
                if row < height-1:
                    stdscr.addstr(row, filter_width, "│")
                    stdscr.addstr(row, filter_width + voice_width, "│")
            
            # Bottom border
            stdscr.addstr(height-1, 0, "└" + "─" * (filter_width-1) + "┴" + "─" * (voice_width-1) + "┴" + "─" * (preview_width-1) + "┘")
            
            # Draw panels
            draw_filters_panel(2, 0, filter_width-1, height-3)
            draw_voices_panel(2, filter_width+1, voice_width-1, height-3, filtered_voices)
            draw_preview_panel(2, filter_width + voice_width + 1, preview_width-1, height-3, filtered_voices)
            
        def draw_filters_panel(start_row, start_col, width, height):
            """Draw the filters panel"""
            row = start_row
            
            # Provider filters
            stdscr.addstr(row, start_col + 1, "Providers:", curses.color_pair(7) | curses.A_BOLD)
            row += 1
            for provider in ['edge_tts', 'google', 'openai', 'elevenlabs']:
                if row >= start_row + height:
                    break
                check = "☑" if filters['providers'].get(provider, False) else "☐"
                color = curses.color_pair(5) if filters['providers'].get(provider, False) else curses.color_pair(6)
                display_name = provider.replace('_', ' ').title()
                stdscr.addstr(row, start_col + 1, f"{check} {display_name}"[:width-1], color)
                row += 1
            
            row += 1
            # Quality filters
            if row < start_row + height:
                stdscr.addstr(row, start_col + 1, "Quality:", curses.color_pair(7) | curses.A_BOLD)
                row += 1
                
                quality_labels = {3: "High (★★★)", 2: "Medium (★★☆)", 1: "Low (★☆☆)"}
                for quality, label in quality_labels.items():
                    if row >= start_row + height:
                        break
                    check = "☑" if filters['quality'].get(quality, False) else "☐"
                    color = curses.color_pair(5) if filters['quality'].get(quality, False) else curses.color_pair(6)
                    stdscr.addstr(row, start_col + 1, f"{check} {label}"[:width-1], color)
                    row += 1
            
            row += 1
            # Region filters
            if row < start_row + height:
                stdscr.addstr(row, start_col + 1, "Region:", curses.color_pair(7) | curses.A_BOLD)
                row += 1
                
                for region in ['Irish', 'British', 'American', 'Australian', 'General']:
                    if row >= start_row + height:
                        break
                    check = "☑" if filters['regions'].get(region, False) else "☐"
                    color = curses.color_pair(5) if filters['regions'].get(region, False) else curses.color_pair(6)
                    stdscr.addstr(row, start_col + 1, f"{check} {region}"[:width-1], color)
                    row += 1
        
        def draw_voices_panel(start_row, start_col, width, height, filtered_voices):
            """Draw the voices list panel"""
            nonlocal current_pos, scroll_offset
            
            # Adjust scroll if needed
            if current_pos < scroll_offset:
                scroll_offset = current_pos
            elif current_pos >= scroll_offset + height:
                scroll_offset = current_pos - height + 1
            
            # Draw voices
            for i in range(height):
                voice_idx = scroll_offset + i
                row = start_row + i
                
                if voice_idx >= len(filtered_voices):
                    break
                    
                provider, voice, quality, region, gender = filtered_voices[voice_idx]
                
                # Format voice entry
                quality_stars = "★" * quality + "☆" * (3 - quality)
                prefix = "▶ " if voice_idx == current_pos else "  "
                voice_display = f"{voice_idx == current_pos and '▶ ' or '  '}{voice}"[:25]
                
                # Truncate voice name if too long
                if len(voice_display) > width - 15:
                    voice_display = voice_display[:width - 18] + "..."
                
                info = f"{quality_stars} {gender} {region[:5]}"
                full_line = f"{voice_display:<{width-12}} {info}"[:width-1]
                
                # Color based on selection and quality
                if voice_idx == current_pos:
                    color = curses.color_pair(1) | curses.A_BOLD  # Selection highlight
                else:
                    color = curses.color_pair(4) if quality == 3 else curses.color_pair(7)
                
                stdscr.addstr(row, start_col + 1, full_line, color)
            
            # Navigation help at bottom
            if height > 5:
                nav_help = "↑↓ Navigate  Space Play  Enter Select"[:width-1]
                stdscr.addstr(start_row + height - 1, start_col + 1, nav_help, curses.color_pair(8))
        
        def draw_preview_panel(start_row, start_col, width, height, filtered_voices):
            """Draw the preview/details panel"""
            row = start_row
            
            stdscr.addstr(row, start_col + 1, "Voice Details:", curses.color_pair(7) | curses.A_BOLD)
            row += 1
            
            if current_pos < len(filtered_voices):
                provider, voice, quality, region, gender = filtered_voices[current_pos]
                
                # Voice details
                details = [
                    f"• {region} English" if region != "General" else f"• {provider.title()}",
                    f"• {gender == 'F' and 'Female' or gender == 'M' and 'Male' or 'Unknown'}",
                    f"• {'High' if quality == 3 else 'Medium' if quality == 2 else 'Low'} Quality",
                    f"• {provider.replace('_', ' ').title()}",
                ]
                
                for detail in details:
                    if row >= start_row + height - 2:
                        break
                    stdscr.addstr(row, start_col + 1, detail[:width-1], curses.color_pair(7))
                    row += 1
            
            row += 2
            # Controls
            if row < start_row + height:
                stdscr.addstr(row, start_col + 1, "Controls:", curses.color_pair(7) | curses.A_BOLD)
                row += 1
                
                controls = ["Space = Play", "Enter = Select", "F = Favorite", "/ = Search", "Q = Quit"]
                for control in controls:
                    if row >= start_row + height:
                        break
                    stdscr.addstr(row, start_col + 1, control[:width-1], curses.color_pair(8))
                    row += 1
            
            # Favorites count
            if row < start_row + height - 1:
                row = start_row + height - 2
                stdscr.addstr(row, start_col + 1, f"Favorites: {len(favorites)}", curses.color_pair(5))
        
        # Main browser loop
        while True:
            try:
                # Get current filtered voices
                filtered_voices = filter_voices()
                
                # Adjust current position if needed
                if current_pos >= len(filtered_voices) and len(filtered_voices) > 0:
                    current_pos = len(filtered_voices) - 1
                elif current_pos < 0:
                    current_pos = 0
                
                # Draw interface
                draw_interface()
                stdscr.refresh()
                
                # Check if background playback finished
                if current_playback_process and current_playback_process.poll() is not None:
                    is_playing = False
                    playing_voice = None
                    current_playback_process = None
                
                # Handle input
                key = stdscr.getch()
                
                if key == curses.KEY_UP and current_pos > 0:
                    current_pos -= 1
                elif key == curses.KEY_DOWN and current_pos < len(filtered_voices) - 1:
                    current_pos += 1
                elif key == curses.KEY_PPAGE:  # Page Up
                    current_pos = max(0, current_pos - 10)
                elif key == curses.KEY_NPAGE:  # Page Down
                    current_pos = min(len(filtered_voices) - 1, current_pos + 10)
                elif key == curses.KEY_HOME:
                    current_pos = 0
                elif key == curses.KEY_END:
                    current_pos = len(filtered_voices) - 1
                
                elif key == ord('/'):
                    # Toggle search mode
                    search_active = True
                    curses.curs_set(1)  # Show cursor
                    search_text = ""
                    
                elif search_active:
                    if key == ord('\n') or key == ord('\r') or key == 27:  # Enter or Escape
                        search_active = False
                        curses.curs_set(0)  # Hide cursor
                    elif key == curses.KEY_BACKSPACE or key == 127:
                        search_text = search_text[:-1]
                    elif 32 <= key <= 126:  # Printable characters
                        search_text += chr(key)
                
                elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER):
                    # Set as default voice
                    if filtered_voices and current_pos < len(filtered_voices):
                        provider, voice, quality, region, gender = filtered_voices[current_pos]
                        voice_setting = f"{provider}:{voice}"
                        if set_setting("voice", voice_setting):
                            # Show confirmation briefly
                            stdscr.addstr(0, 0, f"✅ Set default voice to {voice}"[:width-1], 
                                        curses.color_pair(5) | curses.A_BOLD)
                            stdscr.refresh()
                            curses.napms(1500)
                
                elif key == ord(' '):
                    # Play voice preview
                    if filtered_voices and current_pos < len(filtered_voices):
                        # Stop current playback
                        if current_playback_process and current_playback_process.poll() is None:
                            current_playback_process.terminate()
                            current_playback_process = None
                        
                        provider, voice, quality, region, gender = filtered_voices[current_pos]
                        playing_voice = voice
                        is_playing = True
                        
                        # Start preview in background thread
                        def background_preview():
                            nonlocal current_playback_process, is_playing, playing_voice
                            try:
                                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                                    temp_file = tmp.name
                                
                                provider_class = load_provider(provider)
                                provider_instance = provider_class()
                                preview_text = "Hello! This is a preview of my voice."
                                kwargs = {"voice": voice}
                                provider_instance.synthesize(preview_text, temp_file, **kwargs)
                                
                                # Play audio
                                play_process = subprocess.Popen(['ffplay', '-nodisp', '-autoexit', temp_file], 
                                                              stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                                current_playback_process = play_process
                                play_process.wait()
                                
                                # Cleanup
                                import os
                                try:
                                    os.unlink(temp_file)
                                except:
                                    pass
                                    
                                if current_playback_process == play_process:
                                    is_playing = False
                                    playing_voice = None
                                    current_playback_process = None
                                    
                            except Exception as e:
                                logging.getLogger(__name__).error(f"Preview failed: {e}")
                                is_playing = False
                                playing_voice = None
                                current_playback_process = None
                        
                        import threading
                        worker = threading.Thread(target=background_preview)
                        worker.daemon = True
                        worker.start()
                
                elif key in (ord('f'), ord('F')):
                    # Toggle favorite
                    if filtered_voices and current_pos < len(filtered_voices):
                        provider, voice, quality, region, gender = filtered_voices[current_pos]
                        voice_key = f"{provider}:{voice}"
                        if voice_key in favorites:
                            favorites.remove(voice_key)
                        else:
                            favorites.add(voice_key)
                
                elif key in (ord('q'), ord('Q'), 27):  # q, Q, or Escape
                    # Stop any background playback before exiting
                    if current_playback_process and current_playback_process.poll() is None:
                        current_playback_process.terminate()
                    break
                
                # Filter toggle keys (F1-F4 style functionality with numbers)
                elif key >= ord('1') and key <= ord('4'):
                    filter_num = key - ord('1')
                    if filter_num == 0:  # Toggle providers
                        # Cycle through provider combinations
                        pass  # Simplified for now
                    elif filter_num == 1:  # Toggle quality
                        # Cycle through quality filters
                        if all(filters['quality'].values()):
                            filters['quality'] = {3: True, 2: False, 1: False}  # High only
                        elif filters['quality'][3] and not filters['quality'][2]:
                            filters['quality'] = {3: True, 2: True, 1: False}  # High + Medium
                        else:
                            filters['quality'] = {3: True, 2: True, 1: True}  # All
                    elif filter_num == 2:  # Toggle regions
                        # Cycle through English regions
                        if filters['regions']['Irish'] and filters['regions']['British']:
                            filters['regions'] = {r: r in ['Irish'] for r in filters['regions']}
                        elif filters['regions']['Irish']:
                            filters['regions'] = {r: r in ['British'] for r in filters['regions']}
                        else:
                            filters['regions'] = {r: r in ['Irish', 'British', 'General'] for r in filters['regions']}
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.getLogger(__name__).error(f"Browser error: {e}")
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