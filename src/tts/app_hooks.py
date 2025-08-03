#!/usr/bin/env python3
"""
App hooks for TTS CLI - provides implementation for all TTS commands
This file connects the generated CLI to the actual TTS functionality
"""

import sys
from typing import Any, Dict, Optional

from tts.config import load_config, save_config

# Import TTS functionality
from tts.core import get_tts_engine

# Provider registry - this should match what was in the original CLI
PROVIDERS_REGISTRY = {
    "edge_tts": "tts.providers.edge_tts",
    "openai_tts": "tts.providers.openai_tts",
    "elevenlabs": "tts.providers.elevenlabs",
    "google_tts": "tts.providers.google_tts",
    "chatterbox": "tts.providers.chatterbox",
}

# Provider shortcuts mapping for @provider syntax
PROVIDER_SHORTCUTS = {
    "edge": "edge_tts",
    "openai": "openai_tts",
    "elevenlabs": "elevenlabs",
    "google": "google_tts",
    "chatterbox": "chatterbox",
}


def parse_provider_shortcuts(args: list) -> tuple[Optional[str], list]:
    """Parse @provider shortcuts from arguments"""
    if not args:
        return None, args

    # Check if first argument is a provider shortcut
    first_arg = args[0]
    if first_arg.startswith("@"):
        shortcut = first_arg[1:]  # Remove @
        if shortcut in PROVIDER_SHORTCUTS:
            provider_name = PROVIDER_SHORTCUTS[shortcut]
            remaining_args = args[1:]  # Rest of the arguments
            return provider_name, remaining_args
        else:
            # Invalid shortcut - let calling function handle the error
            return first_arg, args[1:]

    return None, args


def handle_provider_shortcuts(provider_arg: Optional[str]) -> Optional[str]:
    """Handle @provider syntax in commands"""
    if not provider_arg:
        return None

    if provider_arg.startswith("@"):
        shortcut = provider_arg[1:]  # Remove @
        if shortcut in PROVIDER_SHORTCUTS:
            return PROVIDER_SHORTCUTS[shortcut]
        else:
            # Return the original for error handling
            return provider_arg

    return provider_arg


def get_engine() -> Any:
    """Get or create TTS engine instance"""
    try:
        return get_tts_engine()
    except (ImportError, AttributeError, RuntimeError):
        from tts.core import initialize_tts_engine

        return initialize_tts_engine(PROVIDERS_REGISTRY)


def on_speak(
    text: Optional[str], options: tuple, voice: Optional[str], rate: Optional[str], pitch: Optional[str], debug: bool, **kwargs
) -> int:
    """Handle the speak command"""
    try:
        # Parse provider shortcuts from text and options
        provider_name = None
        all_args = []

        # Collect all arguments
        if text:
            all_args.append(text)
        if options:
            all_args.extend(options)

        # Check if first argument is a provider shortcut
        if all_args and all_args[0].startswith("@"):
            provider_name, remaining_args = parse_provider_shortcuts(all_args)
            # Handle invalid shortcuts
            if provider_name and provider_name.startswith("@"):
                shortcut = provider_name[1:]
                print(f"Error: Unknown provider shortcut '@{shortcut}'", file=sys.stderr)
                print(f"Available providers: {', '.join('@' + k for k in PROVIDER_SHORTCUTS.keys())}", file=sys.stderr)
                sys.exit(1)
            all_args = remaining_args

        # Parse any additional text from remaining arguments
        all_text = all_args

        if not all_text:
            # If no text provided, try to read from stdin
            if not sys.stdin.isatty():
                try:
                    text_input = sys.stdin.read().strip()
                    if text_input:
                        all_text.append(text_input)
                except (BrokenPipeError, IOError):
                    # Stdin was closed (e.g., in a pipeline that was interrupted)
                    # Exit gracefully without error message
                    sys.exit(0)

        if not all_text:
            print("Error: No text provided to speak")
            return 1

        final_text = " ".join(all_text)

        # Get TTS engine and synthesize
        engine = get_engine()

        # Create output parameters
        output_params: Dict[str, Any] = {
            "stream": True,  # For speaking, we want to stream to speakers
            "debug": debug,
        }

        if rate:
            output_params["rate"] = rate
        if pitch:
            output_params["pitch"] = pitch

        # Synthesize the text
        result = engine.synthesize_text(
            text=final_text,
            voice=voice,
            provider_name=provider_name,
            output_path=None,  # None means stream to speakers
            **output_params,
        )

        return 0 if result else 1

    except KeyboardInterrupt:
        # Clean shutdown on Ctrl+C
        return 0
    except BrokenPipeError:
        # Exit gracefully when output pipe is broken
        return 0
    except IOError as e:
        # Check if it's a broken pipe error
        import errno

        if e.errno == errno.EPIPE:
            return 0
        # Re-raise other IO errors
        raise
    except Exception:
        # Re-raise to let CLI handle it with user-friendly messages
        raise


def on_save(
    text: Optional[str],
    options: tuple,
    output: Optional[str],
    format: Optional[str],
    voice: Optional[str],
    clone: Optional[str],
    json: bool,
    debug: bool,
    rate: Optional[str],
    pitch: Optional[str],
    **kwargs,
) -> int:
    """Handle the save command"""
    try:
        # Parse provider shortcuts from text and options
        provider_name = None
        all_args = []

        # Collect all arguments
        if text:
            all_args.append(text)
        if options:
            all_args.extend(options)

        # Check if first argument is a provider shortcut
        if all_args and all_args[0].startswith("@"):
            provider_name, remaining_args = parse_provider_shortcuts(all_args)
            # Handle invalid shortcuts
            if provider_name and provider_name.startswith("@"):
                shortcut = provider_name[1:]
                print(f"Error: Unknown provider shortcut '@{shortcut}'", file=sys.stderr)
                print(f"Available providers: {', '.join('@' + k for k in PROVIDER_SHORTCUTS.keys())}", file=sys.stderr)
                sys.exit(1)
            all_args = remaining_args

        # Parse any additional text from remaining arguments
        all_text = all_args

        if not all_text:
            print("Error: No text provided to save")
            return 1

        final_text = " ".join(all_text)

        # Default output filename if not provided
        if not output:
            output = "output.mp3"

        # Get TTS engine and synthesize
        engine = get_engine()

        # Create output parameters
        output_params: Dict[str, Any] = {
            "stream": False,  # For saving, we don't stream
            "debug": debug,
        }

        if rate:
            output_params["rate"] = rate
        if pitch:
            output_params["pitch"] = pitch
        if format:
            output_params["format"] = format

        # Synthesize the text
        result = engine.synthesize_text(
            text=final_text, voice=voice, provider_name=provider_name, output_path=output, **output_params
        )

        if result:
            print(f"Audio saved to: {output}")
            return 0
        else:
            return 1

    except Exception:
        # Re-raise to let CLI handle it with user-friendly messages
        raise


def on_voices(args: tuple, **kwargs) -> int:
    """Handle the voices command"""
    import os
    import sys

    try:
        from tts.voice_browser import VoiceBrowser

        engine = get_engine()

        # Create and launch voice browser
        browser = VoiceBrowser(PROVIDERS_REGISTRY, engine.load_provider)

        # Try to reset terminal state before launching curses
        try:
            # Reset terminal to a clean state
            os.system("stty sane")
        except OSError:
            pass

        # Run the browser with its built-in curses wrapper
        browser.run()
        return 0
    except Exception:
        # Re-raise to let CLI handle it with user-friendly messages
        raise
        print(f"  Interactive: {sys.stdout.isatty()}")
        print(f"  Terminal size: {os.get_terminal_size() if sys.stdout.isatty() else 'N/A'}")

        import traceback

        traceback.print_exc()

        print("\nTroubleshooting:")
        print("1. Try running: export TERM=xterm-256color")
        print("2. Or run: reset && tts voices")
        print("3. If in tmux/screen, try running outside of it")
        return 1


def on_providers(provider_name: Optional[str], **kwargs) -> int:
    """Handle the providers command"""
    try:
        engine = get_engine()
        available = engine.get_available_providers()

        if provider_name:
            if provider_name in available:
                info = engine.get_provider_info(provider_name)
                if info:
                    print(f"Provider: {provider_name}")
                    for key, value in info.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"No info available for {provider_name}")
            else:
                print(f"Provider {provider_name} not found")
                print(f"Available providers: {', '.join(available)}")
        else:
            print("Available TTS providers:")
            for provider in available:
                print(f"  • {provider}")

        return 0
    except (KeyError, AttributeError, ValueError) as e:
        print(f"Error in providers command: {e}")
        return 1


def on_install(args: tuple, **kwargs) -> int:
    """Handle the install command"""
    try:
        import subprocess

        if not args:
            print("🔧 TTS Provider Installation")
            print("===========================")
            print()
            print("Available providers to install:")
            print("  • edge-tts        - Microsoft Edge TTS (free)")
            print("  • openai          - OpenAI TTS API")
            print("  • elevenlabs      - ElevenLabs TTS API")
            print("  • google-tts      - Google Cloud TTS API")
            print("  • chatterbox      - Local voice cloning")
            print()
            print("Usage: tts install <provider>")
            print("Example: tts install edge-tts")
            return 0

        provider = args[0].lower()

        # Provider installation mappings
        install_commands = {
            "edge-tts": ["pip", "install", "edge-tts"],
            "edge_tts": ["pip", "install", "edge-tts"],
            "openai": ["pip", "install", "openai"],
            "elevenlabs": ["pip", "install", "elevenlabs"],
            "google-tts": ["pip", "install", "google-cloud-texttospeech"],
            "google_tts": ["pip", "install", "google-cloud-texttospeech"],
            "chatterbox": ["pip", "install", "torch", "torchaudio", "transformers", "librosa"],
        }

        if provider not in install_commands:
            print(f"❌ Unknown provider: {provider}", file=sys.stderr)
            print("Available providers: edge-tts, openai, elevenlabs, google-tts, chatterbox", file=sys.stderr)
            sys.exit(1)

        print(f"🔧 Installing {provider}...")
        print("=" * 40)

        try:
            # Special handling for chatterbox (multiple packages)
            if provider == "chatterbox":
                packages = ["torch", "torchaudio", "transformers", "librosa"]
                for package in packages:
                    print(f"📦 Installing {package}...")
                    result = subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True, text=True)

                    if result.returncode != 0:
                        print(f"❌ Failed to install {package}")
                        print(f"Error: {result.stderr}")
                        return 1
                    else:
                        print(f"✅ {package} installed successfully")
            else:
                # Single package installation
                cmd = install_commands[provider]
                print(f"📦 Running: {' '.join(cmd)}")

                result = subprocess.run(
                    [sys.executable, "-m"] + cmd[1:],  # Use current Python interpreter
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print("❌ Installation failed")
                    print(f"Error: {result.stderr}")
                    return 1

            print(f"✅ {provider} installed successfully!")

            # Provide next steps
            if provider in ["openai", "elevenlabs", "google-tts", "google_tts"]:
                print("\n💡 Next steps:")
                if provider == "openai":
                    print("   Set your API key: tts config set openai_api_key YOUR_KEY")
                elif provider == "elevenlabs":
                    print("   Set your API key: tts config set elevenlabs_api_key YOUR_KEY")
                elif provider in ["google-tts", "google_tts"]:
                    print("   Set up authentication:")
                    print("   • API key: tts config set google_api_key YOUR_KEY")
                    print("   • Or service account: tts config set google_credentials_path /path/to/credentials.json")

            # Test the installation
            print(f"\n🧪 Testing {provider}...")
            engine = get_engine()
            test_result = engine.test_provider(provider.replace("-", "_"))

            if test_result.get("available", False):
                print(f"✅ {provider} is working correctly!")
            else:
                error = test_result.get("error", "Unknown error")
                print(f"⚠️  {provider} installed but not fully configured: {error}")

            return 0

        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
            return 1
        except (ImportError, OSError, RuntimeError) as e:
            print(f"❌ Unexpected error during installation: {e}")
            return 1

    except (ImportError, ValueError, KeyError) as e:
        print(f"Error in install command: {e}")
        return 1


def on_info(provider: Optional[str], **kwargs) -> int:
    """Handle the info command"""
    try:
        engine = get_engine()

        if provider:
            # Handle provider shortcuts
            resolved_provider = handle_provider_shortcuts(provider)

            if resolved_provider and resolved_provider.startswith("@"):
                shortcut = resolved_provider[1:]
                print(f"Error: Unknown provider shortcut '@{shortcut}'", file=sys.stderr)
                print(f"Available providers: {', '.join('@' + k for k in PROVIDER_SHORTCUTS.keys())}", file=sys.stderr)
                sys.exit(1)

            provider_name = resolved_provider or provider

            # Use safe info method that handles authentication gracefully
            info = engine.get_provider_info_safe(provider_name)
            status = engine.get_provider_status(provider_name)

            # Determine status indicator
            if status["available"] and status["configured"]:
                status_icon = "✅"
                status_text = "Ready"
            elif status["available"] and not status["configured"]:
                status_icon = "🔑"
                status_text = "Needs API key"
            elif not status["installed"]:
                status_icon = "❌"
                status_text = "Not installed"
            elif status["error"]:
                status_icon = "⚠️"
                status_text = f"Warning: {status['error']}"
            else:
                status_icon = "❓"
                status_text = "Unknown status"

            print(f"📋 Provider: {provider_name} {status_icon}")
            print("=" * 40)
            print(f"🔄 Status: {status_text}")

            for key, value in info.items():
                if key == "name":
                    print(f"🏢 Name: {value}")
                elif key == "description":
                    print(f"📝 Description: {value}")
                elif key == "options":
                    print("⚙️  Options:")
                    for opt_key, opt_value in value.items():
                        print(f"   • {opt_key}: {opt_value}")
                elif key == "output_formats":
                    if isinstance(value, list):
                        print(f"🎵 Formats: {', '.join(value)}")
                    else:
                        print(f"🎵 Formats: {value}")
                elif key == "sample_voices":
                    if isinstance(value, list) and value:
                        print(f"🎤 Sample Voices ({len(value)}):")
                        for voice in value[:10]:  # Show first 10
                            print(f"   • {voice}")
                        if len(value) > 10:
                            print(f"   ... and {len(value) - 10} more")
                    else:
                        print("🎤 Sample Voices: None available")
                elif key == "capabilities":
                    if isinstance(value, list) and value:
                        print(f"⭐ Capabilities: {', '.join(value)}")
                elif key not in ["status", "error"]:  # Skip internal status fields
                    print(f"   {key}: {value}")

            # Show setup instructions for unconfigured providers
            if not status["configured"] and status["installed"]:
                print("\n💡 Setup Instructions:")
                api_key_name = engine._get_api_key_provider_name(provider_name)
                if provider_name == "openai_tts":
                    print(f"   Set API key: tts config set {api_key_name}_api_key YOUR_KEY")
                    print("   Get your key at: https://platform.openai.com/api-keys")
                elif provider_name == "elevenlabs":
                    print(f"   Set API key: tts config set {api_key_name}_api_key YOUR_KEY")
                    print("   Get your key at: https://elevenlabs.io/profile")
                elif provider_name == "google_tts":
                    print(f"   Option 1 - API key: tts config set {api_key_name}_api_key YOUR_KEY")
                    print(
                        f"   Option 2 - Service account: tts config set {api_key_name}_credentials_path /path/to/credentials.json"
                    )
                    print("   Get credentials at: https://console.cloud.google.com/")

        else:
            # Show general info about all providers
            print("📋 TTS Provider Information")
            print("==========================")
            available = engine.get_available_providers()

            for provider_name in available:
                info = engine.get_provider_info_safe(provider_name)
                status = engine.get_provider_status(provider_name)

                # Determine status indicator
                if status["available"] and status["configured"]:
                    status_icon = "✅"
                elif status["available"] and not status["configured"]:
                    status_icon = "🔑"
                elif not status["installed"]:
                    status_icon = "❌"
                else:
                    status_icon = "⚠️"

                name = info.get("name", provider_name)
                description = info.get("description", "No description")
                print(f"\n{status_icon} {name}")
                print(f"   {description}")

                # Find shortcut
                shortcut = None
                for k, v in PROVIDER_SHORTCUTS.items():
                    if v == provider_name:
                        shortcut = k
                        break
                if shortcut:
                    print(f"   💡 Use: @{shortcut} or {provider_name}")
                else:
                    print(f"   💡 Use: {provider_name}")

            print("\n💡 Get detailed info: tts info <provider>")
            print("Example: tts info @edge")

        return 0
    except (KeyError, AttributeError, ValueError) as e:
        print(f"Error in info command: {e}")
        return 1


def on_document(
    document_path: str,
    options: tuple,
    save: bool,
    output: Optional[str],
    format: Optional[str],
    voice: Optional[str],
    clone: Optional[str],
    json: bool,
    debug: bool,
    doc_format: str,
    ssml_platform: str,
    emotion_profile: str,
    rate: Optional[str],
    pitch: Optional[str],
    **kwargs,
) -> int:
    """Handle the document command"""
    try:
        from pathlib import Path

        from tts.document_processing.parser_factory import DocumentParserFactory

        # Check if document file exists
        doc_file = Path(document_path)
        if not doc_file.exists():
            print(f"Error: Document file not found: {document_path}")
            return 1

        # Read document content
        try:
            content = doc_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Error: Unable to read document as UTF-8: {document_path}")
            return 1

        # Parse document using factory
        factory = DocumentParserFactory()
        semantic_elements = factory.parse_document(content=content, filename=document_path, format_override=doc_format)

        if not semantic_elements:
            print("Warning: No content found in document")
            return 1

        # Extract text from semantic elements
        text_parts = []
        for element in semantic_elements:
            if hasattr(element, "content") and element.content:
                text_parts.append(element.content)

        if not text_parts:
            print("Warning: No text content extracted from document")
            return 1

        final_text = " ".join(text_parts)

        if debug:
            print(f"Extracted {len(semantic_elements)} elements")
            print(f"Text length: {len(final_text)} characters")

        # Get TTS engine and synthesize
        engine = get_engine()

        # Create output parameters
        output_params: Dict[str, Any] = {"debug": debug}

        if rate:
            output_params["rate"] = rate
        if pitch:
            output_params["pitch"] = pitch
        if format:
            output_params["format"] = format

        # Determine if we should save or stream
        if save or output:
            # Save mode
            if not output:
                # Generate output filename based on input
                output = doc_file.with_suffix(".mp3").name

            output_params["stream"] = False
            result = engine.synthesize_text(text=final_text, voice=voice, output_path=output, **output_params)

            if result:
                print(f"Document audio saved to: {output}")
                return 0
            else:
                return 1
        else:
            # Stream mode (default)
            output_params["stream"] = True
            result = engine.synthesize_text(text=final_text, voice=voice, output_path=None, **output_params)

            return 0 if result else 1

    except Exception:
        # Re-raise to let CLI handle it with user-friendly messages
        raise


def on_voice_load(voice_files: tuple, **kwargs) -> int:
    """Handle the voice load command"""
    try:
        from pathlib import Path

        from tts.voice_manager import VoiceManager

        if not voice_files:
            print("Error: No voice files specified")
            print("Usage: tts voice load <voice_file> [voice_file2] ...")
            return 1

        manager = VoiceManager()
        loaded_count = 0
        failed_count = 0

        for voice_file in voice_files:
            voice_path = Path(voice_file)

            # Check if file exists
            if not voice_path.exists():
                print(f"❌ Voice file not found: {voice_file}")
                failed_count += 1
                continue

            # Check if already loaded
            if manager.is_voice_loaded(str(voice_path)):
                print(f"ℹ️  Voice already loaded: {voice_path.name}")
                continue

            try:
                print(f"🔄 Loading voice: {voice_path.name}...")
                success = manager.load_voice(str(voice_path))

                if success:
                    print(f"✅ Successfully loaded: {voice_path.name}")
                    loaded_count += 1
                else:
                    print(f"❌ Failed to load: {voice_path.name}")
                    failed_count += 1

            except (IOError, OSError, ValueError) as e:
                print(f"❌ Error loading {voice_path.name}: {e}")
                failed_count += 1

        # Summary
        total = len(voice_files)
        print("\n📊 Voice Loading Summary:")
        print(f"   Total: {total}, Loaded: {loaded_count}, Failed: {failed_count}")

        # Show currently loaded voices
        loaded_voices = manager.get_loaded_voices()
        if loaded_voices:
            print(f"\n🎤 Currently Loaded Voices ({len(loaded_voices)}):")
            for voice_info in loaded_voices:
                voice_path = Path(voice_info["path"])
                print(f"   • {voice_path.name}")

        return 0 if failed_count == 0 else 1

    except (ImportError, IOError, OSError) as e:
        print(f"Error in voice load command: {e}")
        return 1


def on_voice_unload(voice_files: tuple, all: bool, **kwargs) -> int:
    """Handle the voice unload command"""
    try:
        from pathlib import Path

        from tts.voice_manager import VoiceManager

        manager = VoiceManager()

        # Handle unload all
        if all:
            try:
                print("🔄 Unloading all voices...")
                unloaded_count = manager.unload_all_voices()

                if unloaded_count > 0:
                    print(f"✅ Successfully unloaded {unloaded_count} voices")
                else:
                    print("ℹ️  No voices were loaded")

                return 0

            except (IOError, OSError, RuntimeError) as e:
                print(f"❌ Error unloading all voices: {e}")
                return 1

        # Handle specific voice files
        if not voice_files:
            print("Error: No voice files specified")
            print("Usage: tts voice unload <voice_file> [voice_file2] ...")
            print("       tts voice unload --all")
            return 1

        unloaded_count = 0
        failed_count = 0

        for voice_file in voice_files:
            voice_path = Path(voice_file)

            # Check if voice is loaded
            if not manager.is_voice_loaded(str(voice_path)):
                print(f"ℹ️  Voice not loaded: {voice_path.name}")
                continue

            try:
                print(f"🔄 Unloading voice: {voice_path.name}...")
                success = manager.unload_voice(str(voice_path))

                if success:
                    print(f"✅ Successfully unloaded: {voice_path.name}")
                    unloaded_count += 1
                else:
                    print(f"❌ Failed to unload: {voice_path.name}")
                    failed_count += 1

            except (IOError, OSError, ValueError) as e:
                print(f"❌ Error unloading {voice_path.name}: {e}")
                failed_count += 1

        # Summary
        total = len(voice_files)
        print("\n📊 Voice Unloading Summary:")
        print(f"   Total: {total}, Unloaded: {unloaded_count}, Failed: {failed_count}")

        # Show remaining loaded voices
        loaded_voices = manager.get_loaded_voices()
        if loaded_voices:
            print(f"\n🎤 Still Loaded Voices ({len(loaded_voices)}):")
            for voice_info in loaded_voices:
                voice_path = Path(voice_info["path"])
                print(f"   • {voice_path.name}")
        else:
            print("\n✨ No voices currently loaded")

        return 0 if failed_count == 0 else 1

    except (ImportError, IOError, OSError) as e:
        print(f"Error in voice unload command: {e}")
        return 1


def on_voice_status(**kwargs) -> int:
    """Handle the voice status command"""
    try:
        from pathlib import Path

        from tts.voice_manager import VoiceManager

        manager = VoiceManager()

        print("🎤 Voice Manager Status")
        print("======================")

        # Check if server is running
        if manager._is_server_running():
            print("✅ Chatterbox server: Running")
            print(f"🌐 Server address: {manager.server_host}:{manager.server_port}")
        else:
            print("❌ Chatterbox server: Not running")
            print("💡 Server will start automatically when loading voices")

        # Get loaded voices
        loaded_voices = manager.get_loaded_voices()

        if not loaded_voices:
            print("\n📭 No voices currently loaded")
            print("💡 Use 'tts voice load <voice_file>' to load voices for fast synthesis")
        else:
            print(f"\n🎤 Loaded Voices ({len(loaded_voices)}):")
            print("   " + "=" * 50)

            for i, voice_info in enumerate(loaded_voices, 1):
                voice_path = Path(voice_info["path"])
                print(f"   {i}. {voice_path.name}")
                print(f"      📁 Path: {voice_path}")

                # Show file size if available
                if voice_path.exists():
                    size_mb = voice_path.stat().st_size / (1024 * 1024)
                    print(f"      📏 Size: {size_mb:.1f} MB")
                else:
                    print("      ⚠️  File not found at original location")

                # Show additional info if available
                if "loaded_at" in voice_info:
                    print(f"      ⏰ Loaded: {voice_info['loaded_at']}")

                print()  # Empty line between voices

        # Show memory usage hint
        if loaded_voices:
            print("💡 Tips:")
            print("   • Use 'tts voice unload <voice_file>' to free memory")
            print("   • Use 'tts voice unload --all' to unload all voices")
            print("   • Loaded voices provide faster synthesis with Chatterbox")

        return 0

    except (ImportError, IOError, OSError, AttributeError) as e:
        print(f"Error in voice status command: {e}")
        return 1


def on_status(**kwargs) -> int:
    """Handle the status command"""
    try:
        engine = get_engine()
        config = load_config()

        print("🩺 TTS System Status")
        print("==================")

        print("\n📋 Provider Status:")
        available = engine.get_available_providers()

        ready_count = 0
        needs_setup_count = 0
        error_count = 0

        for provider in available:
            status = engine.get_provider_status(provider)

            # Determine status indicator and count
            if status["available"] and status["configured"]:
                status_icon = "✅"
                status_text = "Ready"
                ready_count += 1
            elif status["available"] and not status["configured"]:
                status_icon = "🔑"
                status_text = "Needs API key"
                needs_setup_count += 1
            elif not status["installed"]:
                status_icon = "❌"
                status_text = "Not installed"
                error_count += 1
            elif status["error"]:
                status_icon = "⚠️"
                status_text = f"Warning: {status['error']}"
                error_count += 1
            else:
                status_icon = "❓"
                status_text = "Unknown"
                error_count += 1

            print(f"  {status_icon} {provider:<15} {status_text}")

            # Show helpful setup hints for providers that need configuration
            if not status["configured"] and status["installed"]:
                api_key_name = engine._get_api_key_provider_name(provider)
                if provider == "openai_tts":
                    print(f"      💡 Run: tts config set {api_key_name}_api_key YOUR_KEY")
                elif provider == "elevenlabs":
                    print(f"      💡 Run: tts config set {api_key_name}_api_key YOUR_KEY")
                elif provider == "google_tts":
                    print(f"      💡 Run: tts config set {api_key_name}_api_key YOUR_KEY")
                    print(f"      💡 Or:  tts config set {api_key_name}_credentials_path /path/to/creds.json")

        # Summary
        total = len(available)
        print(f"\n📊 Summary: {ready_count}/{total} ready, {needs_setup_count} need setup, {error_count} errors")

        print("\n⚙️  Configuration:")
        print(f"  Default voice: {config.get('voice', 'Not set')}")
        print(f"  Config file: {config.get('config_path', 'Default location')}")

        # Show some important config values
        important_keys = ["openai_api_key", "elevenlabs_api_key", "google_api_key", "google_credentials_path"]
        configured_apis = []
        for key in important_keys:
            if config.get(key):
                api_name = key.replace("_api_key", "").replace("_credentials_path", "")
                configured_apis.append(api_name)

        if configured_apis:
            print(f"  Configured APIs: {', '.join(configured_apis)}")
        else:
            print("  Configured APIs: None")

        # Show helpful next steps
        if needs_setup_count > 0:
            print("\n💡 Setup Help:")
            print("  • Get OpenAI key: https://platform.openai.com/api-keys")
            print("  • Get ElevenLabs key: https://elevenlabs.io/profile")
            print("  • Get Google Cloud creds: https://console.cloud.google.com/")
            print("  • Run 'tts info <provider>' for detailed setup instructions")

        return 0
    except (ImportError, KeyError, AttributeError) as e:
        print(f"Error in status command: {e}")
        return 1


def on_config(action: Optional[str], key: Optional[str], value: Optional[str], **kwargs) -> int:
    """Handle the config command"""
    try:
        config = load_config()

        if action == "show" or not action:
            print("🔧 TTS Configuration")
            print("===================")
            for k, v in config.items():
                if k != "config_path":  # Skip internal keys
                    print(f"  {k}: {v}")
        elif action == "get" and key:
            print(config.get(key, "Not set"))
        elif action == "set" and key and value:
            config[key] = value
            save_config(config)
            print(f"Set {key} = {value}")
        else:
            print("Usage: config [show|get|set] [key] [value]")

        return 0
    except (IOError, OSError, ValueError, KeyError) as e:
        print(f"Error in config command: {e}")
        return 1
