#!/usr/bin/env python3
import click
import importlib
import sys
from pathlib import Path
from typing import Dict, Type
from .base import TTSProvider
from .__version__ import __version__


PROVIDERS: Dict[str, str] = {
    "chatterbox": ".providers.chatterbox.ChatterboxProvider",
    "orpheus": ".providers.orpheus.OrpheusProvider",
    "naturalspeech": ".providers.naturalspeech.NaturalSpeechProvider",
    "maskgct": ".providers.maskgct.MaskGCTProvider",
    "edge_tts": ".providers.edge_tts.EdgeTTSProvider",
}


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
@click.option("-s", "--stream", is_flag=True, help="Stream directly to speakers (no file saved)")
@click.argument("text", required=False)
@click.option("-m", "--model", help="TTS model to use")
@click.option("-o", "--output", default="output.wav", help="Output file path")
@click.argument("options", nargs=-1)
def main(text: str, model: str, output: str, options: tuple, list_models: bool, stream: bool):
    """Text-to-speech CLI with multiple providers."""
    
    # Handle list command
    if list_models:
        click.echo("Available models:")
        for name in PROVIDERS.keys():
            click.echo(f"  - {name}")
        return
    
    # Check required arguments
    if not text or not model:
        click.echo("Error: You must specify a model with -m/--model", err=True)
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
    
    try:
        # Load and instantiate provider
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
            click.echo(f"Streaming with {model}...")
        else:
            click.echo(f"Synthesizing with {model}...")
        
        provider.synthesize(text, output, **kwargs)
        
        if not stream:
            click.echo(f"Audio saved to: {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def cli():
    main()


if __name__ == "__main__":
    cli()