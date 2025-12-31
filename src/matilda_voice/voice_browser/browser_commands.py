"""Command handlers for the voice browser.

This module provides the main entry point functions for launching
and managing the voice browser interface.
"""

import logging
import sys
from typing import Any, Callable, Dict

import click

from ..exceptions import AuthenticationError, DependencyError, ProviderLoadError, ProviderNotFoundError
from .browser_ui import VoiceBrowser
from .voice_analyzer import analyze_voice


def interactive_voice_browser(providers_registry: Dict[str, Any], load_provider_func: Callable) -> None:
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


def show_browser_snapshot(providers_registry: Dict[str, str], load_provider_func: Callable) -> None:
    """Show a snapshot of what the browser would display."""
    click.echo("=== TTS VOICE BROWSER SNAPSHOT ===\n")

    # Load all voices exactly like the browser does
    all_voices = []
    voice_cache = {}

    click.echo("Loading voices from providers...")
    for provider_name in providers_registry.keys():
        try:
            provider_class = load_provider_func(provider_name)
            provider = provider_class()
            info = provider.get_info()
            if info:
                voices = info.get("all_voices") or info.get("sample_voices", [])
                click.echo(f"  {provider_name}: {len(voices)} voices")
                for voice in voices:
                    quality, region, gender = analyze_voice(provider_name, voice)
                    all_voices.append((provider_name, voice, quality, region, gender))
                    voice_cache[f"{provider_name}:{voice}"] = (quality, region, gender)
        except (ProviderNotFoundError, ProviderLoadError, DependencyError, AuthenticationError) as e:
            click.echo(f"  {provider_name}: SKIPPED ({e})")
            continue
        except (ImportError, AttributeError, RuntimeError) as e:
            click.echo(f"  {provider_name}: ERROR ({e})")
            continue

    click.echo(f"\nTotal voices loaded: {len(all_voices)}")

    # Default filters from browser
    filters: Dict[str, Dict[Any, bool]] = {
        "providers": {"edge_tts": True, "google": True, "openai": True, "elevenlabs": True, "chatterbox": True},
        "quality": {3: True, 2: True, 1: False},
        "regions": {
            "Irish": True,
            "British": True,
            "American": True,
            "Australian": True,
            "Canadian": True,
            "Indian": False,
            "S.African": False,
            "N.Zealand": False,
            "Singapore": False,
            "Hong Kong": False,
            "Philippine": False,
            "Nigerian": False,
            "Kenyan": False,
            "Tanzanian": False,
            "General": True,
            "Chatterbox": True,
        },
    }

    # Apply filters
    filtered_voices = []
    for provider, voice, quality, region, gender in all_voices:
        if not filters["providers"].get(provider, False):
            continue
        if not filters["quality"].get(quality, False):
            continue
        if not filters["regions"].get(region, False):
            continue
        filtered_voices.append((provider, voice, quality, region, gender))

    click.echo(f"After default filters: {len(filtered_voices)} voices\n")

    # Show active filters
    click.echo("ACTIVE FILTERS:")
    enabled_providers = [p for p, enabled in filters["providers"].items() if enabled]
    click.echo("  Providers: " + ", ".join(enabled_providers))
    quality_stars = [
        f"{'*' * q}" for q, enabled in filters["quality"].items() if enabled
    ]
    click.echo("  Quality: " + ", ".join(quality_stars))
    enabled_regions = [r for r, enabled in filters["regions"].items() if enabled]
    click.echo("  Regions: " + ", ".join(enabled_regions))
    click.echo()

    # Group by provider
    by_provider: Dict[str, list] = {}
    for provider, voice, quality, region, gender in filtered_voices:
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append((voice, quality, region, gender))

    # Display voices by provider
    click.echo("VOICES THAT WOULD BE VISIBLE IN BROWSER:")
    for provider_name in providers_registry.keys():
        if provider_name in by_provider:
            voices = by_provider[provider_name]
            click.echo(f"\n  {provider_name.upper()} ({len(voices)} voices):")
            for voice, quality, region, gender in voices:
                stars = "*" * quality + "-" * (3 - quality)
                gender_str = {"F": "Female", "M": "Male", "U": "Unknown"}[gender]
                click.echo(f"  {voice}")
                click.echo(f"    {stars} {gender_str} {region}")
        else:
            click.echo(f"\n  {provider_name.upper()}: No voices (filtered out)")

    click.echo(f"\nTOTAL VISIBLE: {len(filtered_voices)} voices")
    install_msg = "If you don't see these in the browser, try: "
    install_msg += "pipx uninstall tts-cli && pipx install -e ."
    click.echo(install_msg)


def handle_voices_command(args: tuple, providers_registry: Dict[str, str], load_provider_func: Callable) -> None:
    """Handle voices subcommand."""
    logger = logging.getLogger(__name__)

    # Check for snapshot option
    if len(args) > 0 and args[0] == "--snapshot":
        show_browser_snapshot(providers_registry, load_provider_func)
        return

    # Parse language filter argument
    language_filter = None
    if len(args) > 0:
        language_filter = args[0].lower()

    if len(args) == 0:
        # tts voices - launch interactive browser
        if sys.stdout.isatty():
            # Terminal environment - use interactive browser
            interactive_voice_browser(providers_registry, load_provider_func)
        else:
            # Non-terminal (pipe/script) - use simple list
            click.echo("Available voices from all providers:")
            click.echo()

            for provider_name in providers_registry.keys():
                try:
                    provider_class = load_provider_func(provider_name)
                    provider = provider_class()
                    info = provider.get_info()

                    # Use all_voices if available, fallback to sample_voices
                    voices = info.get("all_voices") or info.get("sample_voices", [])

                    if voices:
                        click.echo(f"  {provider_name.upper()}:")
                        for voice in voices:
                            click.echo(f"  - {voice}")

                except (ProviderNotFoundError, ProviderLoadError, DependencyError, AuthenticationError):
                    # Skip providers that can't be loaded (missing dependencies, etc.)
                    continue
                except (ImportError, AttributeError, RuntimeError) as e:
                    # Log unexpected errors but continue with other providers
                    logger.warning(f"Unexpected error loading provider {provider_name}: {e}")
                    continue
    else:
        # Language filtering mode: tts voices en, tts voices english, etc.
        click.echo(f"Voices for language: {language_filter}")
        click.echo("=" * 40)

        # English language patterns
        if language_filter in ["en", "english", "eng"]:
            # Show only English voices
            for provider_name in providers_registry.keys():
                try:
                    provider_class = load_provider_func(provider_name)
                    provider = provider_class()
                    info = provider.get_info()

                    voices = info.get("all_voices") or info.get("sample_voices", [])
                    english_voices = []

                    if provider_name == "openai" or provider_name == "elevenlabs":
                        # OpenAI and ElevenLabs voices are English by default
                        english_voices = voices
                    else:
                        # Filter for English voices (en-*)
                        english_voices = [v for v in voices if v.startswith("en-")]

                    if english_voices:
                        click.echo(f"\n  {provider_name.upper()} (English):")

                        # Group by region for better organization
                        regions: Dict[str, list] = {}
                        for voice in english_voices:
                            if provider_name in ["openai", "elevenlabs"]:
                                region = "General"
                            else:
                                # Extract region from voice name (e.g., en-US-*, en-GB-*)
                                parts = voice.split("-")
                                if len(parts) >= 2:
                                    region_code = f"{parts[0]}-{parts[1]}"
                                    region_map = {
                                        "en-US": "US English",
                                        "en-GB": "British English",
                                        "en-IE": "Irish English",
                                        "en-AU": "Australian English",
                                        "en-CA": "Canadian English",
                                        "en-IN": "Indian English",
                                        "en-ZA": "South African English",
                                        "en-NZ": "New Zealand English",
                                        "en-SG": "Singapore English",
                                        "en-HK": "Hong Kong English",
                                        "en-PH": "Philippine English",
                                        "en-KE": "Kenyan English",
                                        "en-NG": "Nigerian English",
                                        "en-TZ": "Tanzanian English",
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

                except (ProviderNotFoundError, ProviderLoadError, DependencyError, AuthenticationError):
                    # Skip providers that can't be loaded (missing dependencies, etc.)
                    continue
                except (ImportError, AttributeError, RuntimeError) as e:
                    # Log unexpected errors but continue with other providers
                    logger.warning(f"Unexpected error loading provider {provider_name}: {e}")
                    continue
        else:
            # Generic language filtering
            for provider_name in providers_registry.keys():
                try:
                    provider_class = load_provider_func(provider_name)
                    provider = provider_class()
                    info = provider.get_info()

                    voices = info.get("all_voices") or info.get("sample_voices", [])
                    filtered_voices = [v for v in voices if language_filter in v.lower()]

                    if filtered_voices:
                        click.echo(f"\n  {provider_name.upper()}:")
                        for voice in filtered_voices:
                            click.echo(f"  - {voice}")

                except (ProviderNotFoundError, ProviderLoadError, DependencyError, AuthenticationError):
                    # Skip providers that can't be loaded (missing dependencies, etc.)
                    continue
                except (ImportError, AttributeError, RuntimeError) as e:
                    # Log unexpected errors but continue with other providers
                    logger.warning(f"Unexpected error loading provider {provider_name}: {e}")
                    continue


__all__ = [
    "interactive_voice_browser",
    "show_browser_snapshot",
    "handle_voices_command",
]
