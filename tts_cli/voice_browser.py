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

import curses
import logging
import subprocess
import tempfile
import threading
import time
from typing import List, Tuple, Set, Dict, Any, Optional

import click

from .config import set_setting, get_config_value
from .exceptions import ProviderNotFoundError, ProviderLoadError, DependencyError


def analyze_voice(provider: str, voice: str) -> Tuple[int, str, str]:
    """Analyze a voice name to extract quality, region, and gender information."""
    voice_lower = voice.lower()
    
    # Quality heuristics
    quality = 2  # Default medium
    if 'neural' in voice_lower or 'premium' in voice_lower or 'standard' in voice_lower:
        quality = 3  # High quality
    elif 'basic' in voice_lower or 'low' in voice_lower:
        quality = 1  # Low quality
    
    # Region detection
    region = "General"
    if any(marker in voice for marker in ['en-IE', 'Irish']):
        region = "Irish"
    elif any(marker in voice for marker in ['en-GB', 'en-UK', 'British']):
        region = "British"
    elif any(marker in voice for marker in ['en-US', 'American']):
        region = "American"
    elif any(marker in voice for marker in ['en-AU', 'Australian']):
        region = "Australian"
    elif any(marker in voice for marker in ['en-CA', 'Canadian']):
        region = "Canadian"
    elif any(marker in voice for marker in ['en-IN', 'Indian']):
        region = "Indian"
    elif provider == 'chatterbox':
        region = "Chatterbox"
    
    # Gender detection
    gender = "U"  # Unknown
    female_indicators = ['emily', 'jenny', 'aria', 'davis', 'jane', 'sarah', 'amy', 'emma', 'female', 'woman']
    male_indicators = ['guy', 'tony', 'brandon', 'christopher', 'eric', 'male', 'man']
    
    if any(indicator in voice_lower for indicator in female_indicators):
        gender = "F"
    elif any(indicator in voice_lower for indicator in male_indicators):
        gender = "M"
    
    return quality, region, gender


class VoiceBrowser:
    """Interactive voice browser with filtering and preview capabilities."""
    
    def __init__(self, providers_registry: Dict[str, Any], load_provider_func):
        """Initialize the voice browser.
        
        Args:
            providers_registry: Dictionary of available providers
            load_provider_func: Function to load a provider by name
        """
        self.providers_registry = providers_registry
        self.load_provider = load_provider_func
        self.logger = logging.getLogger(__name__)
        
        # Browser state
        self.current_pos = 0
        self.scroll_offset = 0
        self.search_text = ""
        self.search_active = False
        
        # Filter state
        self.filters = {
            'providers': {'edge_tts': True, 'google': True, 'openai': True, 'elevenlabs': True, 'chatterbox': True},
            'quality': {3: True, 2: True, 1: False},  # High, Medium, Low
            'regions': {
                'Irish': True, 'British': True, 'American': True, 'Australian': True, 
                'Canadian': True, 'Indian': False, 'S.African': False, 'N.Zealand': False,
                'Singapore': False, 'Hong Kong': False, 'Philippine': False, 'Nigerian': False,
                'Kenyan': False, 'Tanzanian': False, 'General': True, 'Chatterbox': True
            }
        }
        
        # Playback state
        self.is_playing = False
        self.current_playback_process = None
        self.playing_voice = None
        self.favorites: Set[str] = set()
        
        # Double-click tracking
        self.last_click_time = 0
        self.last_click_pos = -1
        self.DOUBLE_CLICK_TIME = 0.8  # seconds
        
        # Voice data
        self.all_voices: List[Tuple[str, str, int, str, str]] = []
        self.voice_cache: Dict[str, Tuple[int, str, str]] = {}
    
    def load_voices(self) -> None:
        """Load all available voices from providers."""
        self.all_voices = []
        self.voice_cache = {}
        
        for provider_name in self.providers_registry.keys():
            try:
                provider_class = self.load_provider(provider_name)
                provider = provider_class()
                info = provider.get_info()
                if info:
                    voices = info.get('all_voices') or info.get('sample_voices', [])
                    for voice in voices:
                        quality, region, gender = analyze_voice(provider_name, voice)
                        self.all_voices.append((provider_name, voice, quality, region, gender))
                        self.voice_cache[f"{provider_name}:{voice}"] = (quality, region, gender)
            except (ProviderNotFoundError, ProviderLoadError, DependencyError):
                continue
            except Exception as e:
                self.logger.warning(f"Error loading provider {provider_name}: {e}")
                continue
    
    def filter_voices(self) -> List[Tuple[str, str, int, str, str]]:
        """Apply current filters to voice list."""
        filtered = []
        for provider, voice, quality, region, gender in self.all_voices:
            # Provider filter
            if not self.filters['providers'].get(provider, False):
                continue
                
            # Quality filter  
            if not self.filters['quality'].get(quality, False):
                continue
                
            # Region filter
            if not self.filters['regions'].get(region, False):
                continue
                
            # Search filter
            if self.search_text:
                search_lower = self.search_text.lower()
                if not (search_lower in voice.lower() or 
                       search_lower in provider.lower() or
                       search_lower in region.lower() or
                       search_lower in gender.lower()):
                    continue
            
            filtered.append((provider, voice, quality, region, gender))
        
        return filtered
    
    def draw_interface(self, stdscr) -> None:
        """Draw the three-panel interface."""
        height, width = stdscr.getmaxyx()
        stdscr.clear()
        
        # Calculate panel widths
        filter_width = 20
        preview_width = 18
        voice_width = width - filter_width - preview_width - 3  # 3 for borders
        
        # Header line
        title = "TTS VOICE BROWSER v2.5"
        search_display = f"Search: [{self.search_text:<15}] 🔍"
        filtered_voices = self.filter_voices()
        status = f"Showing: {len(filtered_voices)}/{len(self.all_voices)}"
        playing_status = f"Playing: ♪ {self.playing_voice}" if self.is_playing and self.playing_voice else ""
        
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
        self.draw_filters_panel(stdscr, 2, 0, filter_width-1, height-3)
        self.draw_voices_panel(stdscr, 2, filter_width+1, voice_width-1, height-3, filtered_voices)
        self.draw_preview_panel(stdscr, 2, filter_width + voice_width + 1, preview_width-1, height-3, filtered_voices)
    
    def draw_filters_panel(self, stdscr, start_row: int, start_col: int, width: int, height: int) -> None:
        """Draw the filters panel."""
        row = start_row
        
        # Provider filters
        stdscr.addstr(row, start_col + 1, "Providers:", curses.color_pair(7) | curses.A_BOLD)
        row += 1
        for provider in ['edge_tts', 'google', 'openai', 'elevenlabs', 'chatterbox']:
            if row >= start_row + height:
                break
            check = "☑" if self.filters['providers'].get(provider, False) else "☐"
            color = curses.color_pair(5) if self.filters['providers'].get(provider, False) else curses.color_pair(6)
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
                check = "☑" if self.filters['quality'].get(quality, False) else "☐"
                color = curses.color_pair(5) if self.filters['quality'].get(quality, False) else curses.color_pair(6)
                stdscr.addstr(row, start_col + 1, f"{check} {label}"[:width-1], color)
                row += 1
        
        row += 1
        # Region filters
        if row < start_row + height:
            stdscr.addstr(row, start_col + 1, "Region:", curses.color_pair(7) | curses.A_BOLD)
            row += 1
            
            # Show only most common regions to fit in panel
            common_regions = ['Irish', 'British', 'American', 'Australian', 'Canadian', 'Indian', 'General', 'Chatterbox']
            for region in common_regions:
                if row >= start_row + height:
                    break
                check = "☑" if self.filters['regions'].get(region, False) else "☐"
                color = curses.color_pair(5) if self.filters['regions'].get(region, False) else curses.color_pair(6)
                stdscr.addstr(row, start_col + 1, f"{check} {region}"[:width-1], color)
                row += 1
    
    def draw_voices_panel(self, stdscr, start_row: int, start_col: int, width: int, height: int, 
                         filtered_voices: List[Tuple[str, str, int, str, str]]) -> None:
        """Draw the voices list panel."""
        # Adjust scroll if needed
        if self.current_pos < self.scroll_offset:
            self.scroll_offset = self.current_pos
        elif self.current_pos >= self.scroll_offset + height:
            self.scroll_offset = self.current_pos - height + 1
        
        # Draw voices
        for i in range(height):
            voice_idx = self.scroll_offset + i
            row = start_row + i
            
            if voice_idx >= len(filtered_voices):
                break
                
            provider, voice, quality, region, gender = filtered_voices[voice_idx]
            
            # Format voice entry
            quality_stars = "★" * quality + "☆" * (3 - quality)
            voice_display = f"{voice_idx == self.current_pos and '▶ ' or '  '}{voice}"[:25]
            
            # Truncate voice name if too long
            if len(voice_display) > width - 15:
                voice_display = voice_display[:width - 18] + "..."
            
            info = f"{quality_stars} {gender} {region[:5]}"
            full_line = f"{voice_display:<{width-12}} {info}"[:width-1]
            
            # Color based on selection and quality
            if voice_idx == self.current_pos:
                color = curses.color_pair(1) | curses.A_BOLD  # Selection highlight
            else:
                color = curses.color_pair(4) if quality == 3 else curses.color_pair(7)
            
            stdscr.addstr(row, start_col + 1, full_line, color)
        
        # Navigation help at bottom
        if height > 5:
            nav_help = "↑↓ Navigate  Double-Click/Space Play  Enter Select"[:width-1]
            stdscr.addstr(start_row + height - 1, start_col + 1, nav_help, curses.color_pair(8))
    
    def draw_preview_panel(self, stdscr, start_row: int, start_col: int, width: int, height: int,
                          filtered_voices: List[Tuple[str, str, int, str, str]]) -> None:
        """Draw the preview/details panel."""
        row = start_row
        
        stdscr.addstr(row, start_col + 1, "Voice Details:", curses.color_pair(7) | curses.A_BOLD)
        row += 1
        
        if self.current_pos < len(filtered_voices):
            provider, voice, quality, region, gender = filtered_voices[self.current_pos]
            
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
            
            controls = ["Click = Select", "Dbl-Click = Play", "Space = Play", "Enter = Set", "/ = Search", "Q = Quit"]
            for control in controls:
                if row >= start_row + height:
                    break
                stdscr.addstr(row, start_col + 1, control[:width-1], curses.color_pair(8))
                row += 1
        
        # Favorites count
        if row < start_row + height - 1:
            row = start_row + height - 2
            stdscr.addstr(row, start_col + 1, f"Favorites: {len(self.favorites)}", curses.color_pair(5))
    
    def start_voice_preview(self, provider: str, voice: str) -> None:
        """Start playing a voice preview in background thread."""
        # Stop current playback
        if self.current_playback_process and self.current_playback_process.poll() is None:
            self.current_playback_process.terminate()
            self.current_playback_process = None
        
        self.playing_voice = voice
        self.is_playing = True
        
        def background_preview():
            try:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    temp_file = tmp.name
                
                provider_class = self.load_provider(provider)
                provider_instance = provider_class()
                preview_text = "Hello! This is a preview of my voice."
                kwargs = {"voice": voice}
                provider_instance.synthesize(preview_text, temp_file, **kwargs)
                
                # Play audio
                play_process = subprocess.Popen(['ffplay', '-nodisp', '-autoexit', temp_file], 
                                              stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                self.current_playback_process = play_process
                play_process.wait()
                
                # Cleanup
                import os
                try:
                    os.unlink(temp_file)
                except (OSError, FileNotFoundError):
                    # Ignore if file already deleted or doesn't exist
                    pass
                    
                if self.current_playback_process == play_process:
                    self.is_playing = False
                    self.playing_voice = None
                    self.current_playback_process = None
                    
            except Exception as e:
                self.logger.error(f"Preview failed: {e}")
                self.is_playing = False
                self.playing_voice = None
                self.current_playback_process = None
        
        worker = threading.Thread(target=background_preview)
        worker.daemon = True
        worker.start()
    
    def handle_mouse_click(self, stdscr, mx: int, my: int, is_double_click: bool) -> None:
        """Handle mouse click events."""
        height, width = stdscr.getmaxyx()
        filter_width = 20
        
        # Check if click is in filters panel
        if mx < filter_width and my >= 2:
            self.handle_filter_click(my)
        
        # Check if click is in voices panel
        elif filter_width <= mx < filter_width + (width - filter_width - 18) and my >= 2:
            self.handle_voice_click(stdscr, my, is_double_click)
    
    def handle_filter_click(self, my: int) -> None:
        """Handle clicks in the filters panel."""
        # Provider filters start at row 3 (after "Providers:" header)
        provider_start_row = 3
        providers = ['edge_tts', 'google', 'openai', 'elevenlabs', 'chatterbox']
        
        if provider_start_row <= my < provider_start_row + len(providers):
            # Clicked on a provider filter
            provider_idx = my - provider_start_row
            if provider_idx < len(providers):
                provider = providers[provider_idx]
                self.filters['providers'][provider] = not self.filters['providers'].get(provider, False)
        
        # Quality filters start after providers + 2 (spacing + header)
        quality_start_row = provider_start_row + len(providers) + 2
        quality_items = [3, 2, 1]  # High, Medium, Low
        
        if quality_start_row <= my < quality_start_row + len(quality_items):
            # Clicked on a quality filter
            quality_idx = my - quality_start_row
            if quality_idx < len(quality_items):
                quality = quality_items[quality_idx]
                self.filters['quality'][quality] = not self.filters['quality'].get(quality, False)
        
        # Region filters start after quality + 2 (spacing + header)
        region_start_row = quality_start_row + len(quality_items) + 2
        regions = ['Irish', 'British', 'American', 'Australian', 'Canadian', 'Indian', 'General', 'Chatterbox']
        
        if region_start_row <= my < region_start_row + len(regions):
            # Clicked on a region filter
            region_idx = my - region_start_row
            if region_idx < len(regions):
                region = regions[region_idx]
                self.filters['regions'][region] = not self.filters['regions'].get(region, False)
    
    def handle_voice_click(self, stdscr, my: int, is_double_click: bool) -> None:
        """Handle clicks in the voices panel."""
        voice_start_row = 2
        filtered_voices = self.filter_voices()
        height, width = stdscr.getmaxyx()
        
        if my >= voice_start_row and filtered_voices:
            # Calculate which voice was clicked
            voice_idx = my - voice_start_row + self.scroll_offset
            if 0 <= voice_idx < len(filtered_voices):
                if is_double_click:
                    # Double-click detected - trigger preview
                    stdscr.addstr(0, 0, f"DOUBLE-CLICK! Playing {filtered_voices[voice_idx][1][:20]}..."[:width-1],
                                curses.color_pair(5) | curses.A_BOLD)
                    stdscr.refresh()
                    curses.napms(1000)  # Show for 1 second
                    
                    provider, voice, quality, region, gender = filtered_voices[voice_idx]
                    self.start_voice_preview(provider, voice)
                    
                    # Reset double-click tracking
                    self.last_click_time = 0
                    self.last_click_pos = -1
                else:
                    # Single click - just select the voice
                    self.current_pos = voice_idx
                    self.last_click_time = time.time()
                    self.last_click_pos = voice_idx
                    
                    # Show click feedback
                    voice_name = filtered_voices[voice_idx][1]
                    stdscr.addstr(0, 0, f"CLICK! Selected {voice_name[:25]}... (double-click to play)"[:width-1],
                                curses.color_pair(7))
                    stdscr.refresh()
                    curses.napms(500)  # Show for 0.5 seconds
    
    def run(self) -> None:
        """Run the interactive voice browser."""
        def main_browser(stdscr):
            # Initialize curses and colors
            curses.curs_set(0)  # Hide cursor
            curses.start_color()
            
            # Enable mouse events
            curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_DOUBLE_CLICKED | 
                           curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED)
            
            # Color scheme
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_MAGENTA)  # Selection highlight
            curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Title/brand
            curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Provider/section headers
            curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Quality stars/keys
            curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Success/checked items
            curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)      # Error/unchecked
            curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Normal text
            curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Secondary text
            
            # Load voices
            self.load_voices()
            
            if not self.all_voices:
                stdscr.addstr(0, 0, "No voices available!")
                stdscr.refresh()
                stdscr.getch()
                return
            
            # Main browser loop
            while True:
                try:
                    # Get current filtered voices
                    filtered_voices = self.filter_voices()
                    
                    # Adjust current position if needed
                    if self.current_pos >= len(filtered_voices) and len(filtered_voices) > 0:
                        self.current_pos = len(filtered_voices) - 1
                    elif self.current_pos < 0:
                        self.current_pos = 0
                    
                    # Draw interface
                    self.draw_interface(stdscr)
                    stdscr.refresh()
                    
                    # Check if background playback finished
                    if self.current_playback_process and self.current_playback_process.poll() is not None:
                        self.is_playing = False
                        self.playing_voice = None
                        self.current_playback_process = None
                    
                    # Handle input
                    key = stdscr.getch()
                    
                    # Handle mouse events
                    if key == curses.KEY_MOUSE:
                        try:
                            _, mx, my, _, bstate = curses.getmouse()
                            
                            # Check for double-click
                            native_double_click = bool(bstate & curses.BUTTON1_DOUBLE_CLICKED)
                            current_time = time.time()
                            voice_idx = my - 2 + self.scroll_offset  # Voice start row is 2
                            manual_double_click = (voice_idx == self.last_click_pos and 
                                                  current_time - self.last_click_time < self.DOUBLE_CLICK_TIME)
                            
                            is_double_click = native_double_click or manual_double_click
                            self.handle_mouse_click(stdscr, mx, my, is_double_click)
                            
                        except curses.error:
                            # Mouse event parsing failed, ignore
                            pass
                    
                    # Handle keyboard input
                    elif key == curses.KEY_UP and self.current_pos > 0:
                        self.current_pos -= 1
                    elif key == curses.KEY_DOWN and self.current_pos < len(filtered_voices) - 1:
                        self.current_pos += 1
                    elif key == curses.KEY_PPAGE:  # Page Up
                        self.current_pos = max(0, self.current_pos - 10)
                    elif key == curses.KEY_NPAGE:  # Page Down
                        self.current_pos = min(len(filtered_voices) - 1, self.current_pos + 10)
                    elif key == curses.KEY_HOME:
                        self.current_pos = 0
                    elif key == curses.KEY_END:
                        self.current_pos = len(filtered_voices) - 1
                    
                    elif key == ord('/'):
                        # Toggle search mode
                        self.search_active = True
                        curses.curs_set(1)  # Show cursor
                        self.search_text = ""
                        
                    elif self.search_active:
                        if key == ord('\n') or key == ord('\r') or key == 27:  # Enter or Escape
                            self.search_active = False
                            curses.curs_set(0)  # Hide cursor
                        elif key == curses.KEY_BACKSPACE or key == 127:
                            self.search_text = self.search_text[:-1]
                        elif 32 <= key <= 126:  # Printable characters
                            self.search_text += chr(key)
                    
                    elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER):
                        # Set as default voice
                        if filtered_voices and self.current_pos < len(filtered_voices):
                            provider, voice, quality, region, gender = filtered_voices[self.current_pos]
                            voice_setting = f"{provider}:{voice}"
                            if set_setting("voice", voice_setting):
                                # Show confirmation briefly
                                height, width = stdscr.getmaxyx()
                                stdscr.addstr(0, 0, f"✅ Set default voice to {voice}"[:width-1], 
                                            curses.color_pair(5) | curses.A_BOLD)
                                stdscr.refresh()
                                curses.napms(1500)
                    
                    elif key == ord(' '):
                        # Play voice preview
                        if filtered_voices and self.current_pos < len(filtered_voices):
                            provider, voice, quality, region, gender = filtered_voices[self.current_pos]
                            self.start_voice_preview(provider, voice)
                    
                    elif key in (ord('f'), ord('F')):
                        # Toggle favorite
                        if filtered_voices and self.current_pos < len(filtered_voices):
                            provider, voice, quality, region, gender = filtered_voices[self.current_pos]
                            voice_key = f"{provider}:{voice}"
                            if voice_key in self.favorites:
                                self.favorites.remove(voice_key)
                            else:
                                self.favorites.add(voice_key)
                    
                    elif key in (ord('q'), ord('Q'), 27):  # q, Q, or Escape
                        # Stop any background playback before exiting
                        if self.current_playback_process and self.current_playback_process.poll() is None:
                            self.current_playback_process.terminate()
                        break
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.logger.error(f"Browser error: {e}")
                    break
        
        try:
            curses.wrapper(main_browser)
        except Exception as e:
            click.echo(f"Interactive browser failed: {e}", err=True)
            raise


def interactive_voice_browser(providers_registry: Dict[str, Any], load_provider_func) -> None:
    """Launch the interactive voice browser with curses-based UI.
    
    Creates and runs a VoiceBrowser instance that provides a comprehensive
    interface for exploring TTS voices across multiple providers. The browser
    features real-time filtering, voice previews, and interactive selection.
    
    Args:
        providers_registry: Dictionary mapping provider names to module paths
        load_provider_func: Function to dynamically load provider classes
        
    Returns:
        None - Function runs until user exits the browser
        
    Raises:
        Exception: If curses initialization fails or terminal is incompatible
    """
    browser = VoiceBrowser(providers_registry, load_provider_func)
    browser.run()