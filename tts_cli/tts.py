#!/usr/bin/env python3
import click
import importlib
import sys
import logging
import os
from pathlib import Path
from typing import Dict, Type
from .base import TTSProvider
from .exceptions import TTSError, ProviderNotFoundError, ProviderLoadError, DependencyError, NetworkError
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


def handle_list_voices(provider_name: str) -> None:
    """Handle --list-voices command"""
    try:
        provider_class = load_provider(provider_name)
        provider = provider_class()
        info = provider.get_info()
        if info and 'sample_voices' in info:
            click.echo(f"Available voices for {provider_name}:")
            for voice in info['sample_voices']:
                click.echo(f"  - {voice}")
        else:
            click.echo(f"No voice list available for {provider_name}")
    except TTSError as e:
        click.echo(f"Error listing voices for {provider_name}: {e}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error listing voices for {provider_name}: {e}", err=True)


def handle_find_voice(search_term: str, model: str) -> None:
    """Handle --find-voice command"""
    if not model:
        click.echo("Error: --find-voice requires -m/--model to specify provider", err=True)
        sys.exit(1)
    try:
        provider_class = load_provider(model)
        provider = provider_class()
        info = provider.get_info()
        if info and 'sample_voices' in info:
            search_terms = search_term.lower().split()
            matches = []
            for voice in info['sample_voices']:
                voice_lower = voice.lower()
                if all(term in voice_lower for term in search_terms):
                    matches.append(voice)
            
            if matches:
                click.echo(f"Matching voices for '{search_term}':")
                for voice in matches:
                    click.echo(f"  - {voice}")
            else:
                click.echo(f"No voices found matching '{search_term}'")
        else:
            click.echo(f"No voice search available for {model}")
    except TTSError as e:
        click.echo(f"Error searching voices: {e}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error searching voices: {e}", err=True)


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
            except:
                pass
        
    except DependencyError as e:
        logger.error(f"Voice preview failed: {e}")
        click.echo(f"Dependency missing: {e}", err=True)
    except TTSError as e:
        logger.error(f"Voice preview failed: {e}")
        click.echo(f"Error playing voice preview: {e}", err=True)
    except Exception as e:
        logger.error(f"Voice preview failed: {e}")
        click.echo(f"Unexpected error playing voice preview: {e}", err=True)


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
        logger.error(f"Synthesis failed - dependency missing: {e}")
        click.echo(f"Dependency missing: {e}", err=True)
        sys.exit(1)
    except NetworkError as e:
        logger.error(f"Synthesis failed - network error: {e}")
        click.echo(f"Network error: {e}", err=True)
        sys.exit(1)
    except TTSError as e:
        logger.error(f"Synthesis failed: {e}")
        click.echo(f"TTS error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.version_option(version=__version__, prog_name="tts-cli")
@click.option("-l", "--list", "list_models", is_flag=True, help="List available models")
@click.option("--list-voices", help="List available voices for a specific provider")
@click.option("--find-voice", help="Search voices by language/gender (e.g., 'british female')")
@click.option("--preview-voice", help="Play a sample of the specified voice")
@click.option("-s", "--save", is_flag=True, help="Save to file instead of streaming to speakers (default: stream)")
@click.argument("text", required=False)
@click.option("-m", "--model", default="edge_tts", help="TTS model to use (default: edge_tts)")
@click.option("-o", "--output", default="output.wav", help="Output file path")
@click.option("-f", "--format", "output_format", default="mp3", type=click.Choice(['mp3', 'wav', 'ogg', 'flac']), help="Audio output format")
@click.option("--voice", help="Voice to use (e.g., en-GB-SoniaNeural for edge_tts)")
@click.option("--clone", help="Audio file to clone voice from (for chatterbox)")
@click.argument("options", nargs=-1)
def main(text: str, model: str, output: str, options: tuple, list_models: bool, save: bool, voice: str, clone: str, list_voices: str, find_voice: str, preview_voice: str, output_format: str):
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
        handle_list_voices(list_voices)
        return
    
    # Handle find voice command
    if find_voice:
        handle_find_voice(find_voice, model)
        return
    
    # Handle preview voice command
    if preview_voice:
        handle_preview_voice(preview_voice, model, logger)
        return
    
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