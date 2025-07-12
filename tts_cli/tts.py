#!/usr/bin/env python3
import click
import importlib
import sys
import logging
import os
from pathlib import Path
from typing import Dict, Type
from .base import TTSProvider
from .__version__ import __version__


PROVIDERS: Dict[str, str] = {
    "chatterbox": ".providers.chatterbox.ChatterboxProvider",
    "edge_tts": ".providers.edge_tts.EdgeTTSProvider",
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
        raise ValueError(f"Unknown provider: {name}. Available: {', '.join(PROVIDERS.keys())}")
    
    module_path, class_name = PROVIDERS[name].rsplit(".", 1)
    module = importlib.import_module(module_path, package=__package__)
    provider_class = getattr(module, class_name)
    
    if not issubclass(provider_class, TTSProvider):
        raise TypeError(f"{provider_class} is not a TTSProvider")
    
    return provider_class


@click.command()
@click.version_option(version=__version__, prog_name="tts-cli")
@click.option("-l", "--list", "list_models", is_flag=True, help="List available models")
@click.option("--list-voices", help="List available voices for a specific provider")
@click.option("--find-voice", help="Search voices by language/gender (e.g., 'british female')")
@click.option("-s", "--stream", is_flag=True, help="Stream directly to speakers (no file saved)")
@click.argument("text", required=False)
@click.option("-m", "--model", default="edge_tts", help="TTS model to use (default: edge_tts)")
@click.option("-o", "--output", default="output.wav", help="Output file path")
@click.option("-f", "--format", "output_format", default="mp3", type=click.Choice(['mp3', 'wav', 'ogg', 'flac']), help="Audio output format")
@click.option("--voice", help="Voice to use (e.g., en-GB-SoniaNeural for edge_tts)")
@click.option("--clone", help="Audio file to clone voice from (for chatterbox)")
@click.argument("options", nargs=-1)
def main(text: str, model: str, output: str, options: tuple, list_models: bool, stream: bool, voice: str, clone: str, list_voices: str, find_voice: str, output_format: str):
    """Text-to-speech CLI with multiple providers."""
    
    # Setup logging
    logger = setup_logging()
    
    # Handle list command
    if list_models:
        click.echo("Available models:")
        for name in PROVIDERS.keys():
            click.echo(f"  - {name}")
        return
    
    # Handle list voices command
    if list_voices:
        try:
            provider_class = load_provider(list_voices)
            provider = provider_class()
            info = provider.get_info()
            if info and 'sample_voices' in info:
                click.echo(f"Available voices for {list_voices}:")
                for voice in info['sample_voices']:
                    click.echo(f"  - {voice}")
            else:
                click.echo(f"No voice list available for {list_voices}")
        except Exception as e:
            click.echo(f"Error listing voices for {list_voices}: {e}", err=True)
        return
    
    # Handle find voice command
    if find_voice:
        if not model:
            click.echo("Error: --find-voice requires -m/--model to specify provider", err=True)
            sys.exit(1)
        try:
            provider_class = load_provider(model)
            provider = provider_class()
            info = provider.get_info()
            if info and 'sample_voices' in info:
                search_terms = find_voice.lower().split()
                matches = []
                for voice in info['sample_voices']:
                    voice_lower = voice.lower()
                    if all(term in voice_lower for term in search_terms):
                        matches.append(voice)
                
                if matches:
                    click.echo(f"Matching voices for '{find_voice}':")
                    for voice in matches:
                        click.echo(f"  - {voice}")
                else:
                    click.echo(f"No voices found matching '{find_voice}'")
            else:
                click.echo(f"No voice search available for {model}")
        except Exception as e:
            click.echo(f"Error searching voices: {e}", err=True)
        return
    
    # Check required arguments
    if not text:
        logger.error("No text provided for synthesis")
        click.echo("Error: You must provide text to synthesize", err=True)
        sys.exit(1)
    
    # Check output file permissions
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
    
    # Parse key=value options
    kwargs = {}
    for opt in options:
        if "=" not in opt:
            click.echo(f"Error: Invalid option format '{opt}'. Expected 'key=value'", err=True)
            sys.exit(1)
        key, value = opt.split("=", 1)
        kwargs[key] = value
    
    # Add stream flag to kwargs if set
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
        else:
            logger.info(f"Synthesizing audio to {output}")
            click.echo(f"Synthesizing with {model}...")
        
        provider.synthesize(text, output, **kwargs)
        
        if not stream:
            file_size = Path(output).stat().st_size if Path(output).exists() else 0
            logger.info(f"Synthesis completed. File: {output} ({file_size} bytes)")
            click.echo(f"Audio saved to: {output}")
        else:
            logger.info("Audio streaming completed")
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def cli():
    main()


if __name__ == "__main__":
    cli()