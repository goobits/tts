#!/usr/bin/env python3
"""Auto-generated from goobits.yaml"""
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

import rich_click as click
from rich_click import RichGroup

# Set up rich-click configuration globally
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = False  # Disable markdown to avoid conflicts
click.rich_click.MARKUP_MODE = "rich"

# Environment variables for additional control
os.environ["RICH_CLICK_USE_RICH_MARKUP"] = "1"
os.environ["RICH_CLICK_FORCE_TERMINAL"] = "1"
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "#ff5555"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = "To find out more, visit https://github.com/anthropics/claude-code"
click.rich_click.MAX_WIDTH = 120  # Set reasonable width
click.rich_click.WIDTH = 120  # Set consistent width
click.rich_click.COLOR_SYSTEM = "auto"
click.rich_click.SHOW_SUBCOMMAND_ALIASES = True
click.rich_click.ALIGN_OPTIONS_SWITCHES = True
click.rich_click.STYLE_OPTION = "#ff79c6"      # Dracula Pink - for option flags
click.rich_click.STYLE_SWITCH = "#50fa7b"      # Dracula Green - for switches
click.rich_click.STYLE_METAVAR = "#8BE9FD not bold"   # Light cyan - for argument types (OPTIONS, COMMAND)
click.rich_click.STYLE_METAVAR_SEPARATOR = "#6272a4"  # Dracula Comment
click.rich_click.STYLE_HEADER_TEXT = "bold yellow"    # Bold yellow - for section headers
click.rich_click.STYLE_EPILOGUE_TEXT = "#6272a4"      # Dracula Comment
click.rich_click.STYLE_FOOTER_TEXT = "#6272a4"        # Dracula Comment
click.rich_click.STYLE_USAGE = "#BD93F9"              # Purple - for "Usage:" line
click.rich_click.STYLE_USAGE_COMMAND = "bold"         # Bold for main command name
click.rich_click.STYLE_DEPRECATED = "#ff5555"         # Dracula Red
click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "#f8f8f2" # Dracula Foreground
click.rich_click.STYLE_HELPTEXT = "#B3B8C0"           # Light gray - for help descriptions
click.rich_click.STYLE_OPTION_DEFAULT = "#ffb86c"     # Dracula Orange
click.rich_click.STYLE_REQUIRED_SHORT = "#ff5555"     # Dracula Red
click.rich_click.STYLE_REQUIRED_LONG = "#ff5555"      # Dracula Red
click.rich_click.STYLE_OPTIONS_PANEL_BORDER = "dim"   # Dim for subtle borders
click.rich_click.STYLE_COMMANDS_PANEL_BORDER = "dim"  # Dim for subtle borders
click.rich_click.STYLE_COMMAND = "#50fa7b"            # Dracula Green - for command names in list
click.rich_click.STYLE_COMMANDS_TABLE_COLUMN_WIDTH_RATIO = (1, 3)  # Command:Description ratio (1/4 : 3/4)


# Command groups will be set after main function is defined


# Hooks system - try to import app_hooks module
app_hooks = None
try:
    # Try to import from the same directory as this script
    script_dir = Path(__file__).parent
    hooks_path = script_dir / "app_hooks.py"

    if hooks_path.exists():
        spec = importlib.util.spec_from_file_location("app_hooks", hooks_path)
        if spec is not None and spec.loader is not None:
            app_hooks = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_hooks)
    else:
        # Try to import from Python path
        import app_hooks  # type: ignore
except (ImportError, FileNotFoundError):
    # No hooks module found, use default behavior
    pass

def load_plugins(cli_group: Any) -> None:
    """Load plugins from the conventional plugin directory."""
    # Define plugin directories to search
    plugin_dirs = [
        # User-specific plugin directory
        Path.home() / ".config" / "goobits" / "TTS CLI" / "plugins",
        # Local plugin directory (same as script)
        Path(__file__).parent / "plugins",
    ]

    for plugin_dir in plugin_dirs:
        if not plugin_dir.exists():
            continue

        # Add plugin directory to Python path
        sys.path.insert(0, str(plugin_dir))

        # Scan for plugin files
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            plugin_name = plugin_file.stem

            try:
                # Import the plugin module
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
                if spec is not None and spec.loader is not None:
                    plugin_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(plugin_module)

                    # Call register_plugin if it exists
                    if hasattr(plugin_module, "register_plugin"):
                        plugin_module.register_plugin(cli_group)
                        click.echo(f"Loaded plugin: {plugin_name}", err=True)
            except Exception as e:
                click.echo(f"Failed to load plugin {plugin_name}: {e}", err=True)







def get_version() -> str:
    """Get version from pyproject.toml or __init__.py"""
    import re

    try:
        # Try to get version from pyproject.toml FIRST (most authoritative)
        toml_path = Path(__file__).parent.parent / "pyproject.toml"
        if toml_path.exists():
            content = toml_path.read_text()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except Exception:
        pass

    try:
        # Fallback to __init__.py
        init_path = Path(__file__).parent / "__init__.py"
        if init_path.exists():
            content = init_path.read_text()
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except Exception:
        pass

    # Final fallback
    return "1.1"


def show_help_json(ctx: Any, param: Any, value: Any) -> None:
    """Callback for --help-json option."""
    if not value or ctx.resilient_parsing:
        return
    # The triple quotes are important to correctly handle the multi-line JSON string
    click.echo('''{
  "name": "TTS CLI",
  "version": "1.1",
  "display_version": true,
  "tagline": "Multi-provider text-to-speech with voice cloning",
  "description": "Transform text into natural speech using AI providers with auto-selection and real-time streaming.",
  "icon": null,
  "header_sections": [
    {
      "title": "Quick Start",
      "icon": null,
      "items": [
        {
          "item": "tts \\"Hello world\\"",
          "desc": "Speak instantly (implicit 'speak')",
          "style": "example"
        },
        {
          "item": "tts save \\"Hello\\" -o out.mp3",
          "desc": "Save as audio file",
          "style": "example"
        }
      ]
    },
    {
      "title": "Core Commands",
      "icon": null,
      "items": [
        {
          "item": "speak",
          "desc": "🗣️  Speak text aloud (default command)",
          "style": "command"
        },
        {
          "item": "save",
          "desc": "💾 Save text as an audio file",
          "style": "command"
        },
        {
          "item": "voices",
          "desc": "🎭 Browse and test voices interactively",
          "style": "command"
        }
      ]
    },
    {
      "title": "First-time Setup",
      "icon": null,
      "items": [
        {
          "item": "1. Check providers",
          "desc": "tts providers",
          "style": "setup"
        },
        {
          "item": "2. Set API keys",
          "desc": "tts config set openai_api_key YOUR_KEY",
          "style": "setup"
        }
      ]
    }
  ],
  "footer_note": null,
  "commands": {
    "speak": {
      "desc": "Speak text aloud",
      "icon": "🗣️",
      "is_default": true,
      "args": [
        {
          "name": "text",
          "desc": "Text to speak",
          "nargs": null,
          "choices": null,
          "required": false
        },
        {
          "name": "options",
          "desc": "Additional options",
          "nargs": "*",
          "choices": null,
          "required": true
        }
      ],
      "options": [
        {
          "name": "voice",
          "short": "v",
          "type": "str",
          "desc": "🎤 Voice to use (e.g., en-GB-SoniaNeural for edge_tts)",
          "default": null,
          "choices": null
        },
        {
          "name": "rate",
          "short": null,
          "type": "str",
          "desc": "⚡ Speech rate adjustment (e.g., +20%, -50%, 150%)",
          "default": null,
          "choices": null
        },
        {
          "name": "pitch",
          "short": null,
          "type": "str",
          "desc": "🎵 Pitch adjustment (e.g., +5Hz, -10Hz)",
          "default": null,
          "choices": null
        },
        {
          "name": "debug",
          "short": null,
          "type": "flag",
          "desc": "🔍 Show debug information during processing",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "save": {
      "desc": "Save text as an audio file",
      "icon": "💾",
      "is_default": false,
      "args": [
        {
          "name": "text",
          "desc": "Text to save as audio",
          "nargs": null,
          "choices": null,
          "required": false
        },
        {
          "name": "options",
          "desc": "Additional options",
          "nargs": "*",
          "choices": null,
          "required": true
        }
      ],
      "options": [
        {
          "name": "output",
          "short": "o",
          "type": "str",
          "desc": "💾 Output file path",
          "default": null,
          "choices": null
        },
        {
          "name": "format",
          "short": "f",
          "type": "str",
          "desc": "🔧 Audio output format",
          "default": null,
          "choices": [
            "mp3",
            "wav",
            "ogg",
            "flac"
          ]
        },
        {
          "name": "voice",
          "short": "v",
          "type": "str",
          "desc": "🎤 Voice to use (e.g., en-GB-SoniaNeural for edge_tts)",
          "default": null,
          "choices": null
        },
        {
          "name": "clone",
          "short": null,
          "type": "str",
          "desc": "🎭 Audio file to clone voice from (deprecated: use --voice instead)",
          "default": null,
          "choices": null
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "🔧 Output results as JSON",
          "default": null,
          "choices": null
        },
        {
          "name": "debug",
          "short": null,
          "type": "flag",
          "desc": "🔍 Show debug information during processing",
          "default": null,
          "choices": null
        },
        {
          "name": "rate",
          "short": null,
          "type": "str",
          "desc": "⚡ Speech rate adjustment (e.g., +20%, -50%, 150%)",
          "default": null,
          "choices": null
        },
        {
          "name": "pitch",
          "short": null,
          "type": "str",
          "desc": "🎵 Pitch adjustment (e.g., +5Hz, -10Hz)",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "voices": {
      "desc": "Browse and test voices interactively",
      "icon": "🔍",
      "is_default": false,
      "args": [
        {
          "name": "args",
          "desc": "Additional arguments",
          "nargs": "*",
          "choices": null,
          "required": false
        }
      ],
      "options": [],
      "subcommands": null
    },
    "providers": {
      "desc": "Available TTS providers and status",
      "icon": "📋",
      "is_default": false,
      "args": [
        {
          "name": "provider_name",
          "desc": "Provider name for setup instructions (optional)",
          "nargs": null,
          "choices": null,
          "required": false
        }
      ],
      "options": [],
      "subcommands": null
    },
    "install": {
      "desc": "Install provider dependencies",
      "icon": "📦",
      "is_default": false,
      "args": [
        {
          "name": "args",
          "desc": "Provider and options (e.g., 'chatterbox gpu')",
          "nargs": "*",
          "choices": null,
          "required": false
        }
      ],
      "options": [],
      "subcommands": null
    },
    "info": {
      "desc": "Provider information and capabilities",
      "icon": "👀",
      "is_default": false,
      "args": [
        {
          "name": "provider",
          "desc": "Provider name (optional)",
          "nargs": null,
          "choices": null,
          "required": false
        }
      ],
      "options": [],
      "subcommands": null
    },
    "document": {
      "desc": "Convert documents to speech",
      "icon": "📖",
      "is_default": false,
      "args": [
        {
          "name": "document_path",
          "desc": "Path to document file",
          "nargs": null,
          "choices": null,
          "required": true
        },
        {
          "name": "options",
          "desc": "Additional options",
          "nargs": "*",
          "choices": null,
          "required": true
        }
      ],
      "options": [
        {
          "name": "save",
          "short": null,
          "type": "flag",
          "desc": "💾 Save processed audio to file",
          "default": null,
          "choices": null
        },
        {
          "name": "output",
          "short": "o",
          "type": "str",
          "desc": "📁 Output file path",
          "default": null,
          "choices": null
        },
        {
          "name": "format",
          "short": "f",
          "type": "str",
          "desc": "🔧 Audio output format",
          "default": null,
          "choices": [
            "mp3",
            "wav",
            "ogg",
            "flac"
          ]
        },
        {
          "name": "voice",
          "short": "v",
          "type": "str",
          "desc": "🎤 Voice to use",
          "default": null,
          "choices": null
        },
        {
          "name": "clone",
          "short": null,
          "type": "str",
          "desc": "🎭 Audio file to clone voice from (deprecated: use --voice instead)",
          "default": null,
          "choices": null
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "🔧 Output results as JSON",
          "default": null,
          "choices": null
        },
        {
          "name": "debug",
          "short": null,
          "type": "flag",
          "desc": "🔍 Show debug information during processing",
          "default": null,
          "choices": null
        },
        {
          "name": "doc-format",
          "short": null,
          "type": "str",
          "desc": "📄 Document format",
          "default": "auto",
          "choices": [
            "auto",
            "markdown",
            "html",
            "json"
          ]
        },
        {
          "name": "ssml-platform",
          "short": null,
          "type": "str",
          "desc": "🏧️ SSML platform",
          "default": "generic",
          "choices": [
            "azure",
            "google",
            "amazon",
            "generic"
          ]
        },
        {
          "name": "emotion-profile",
          "short": null,
          "type": "str",
          "desc": "🎭 Emotion profile",
          "default": "auto",
          "choices": [
            "technical",
            "marketing",
            "narrative",
            "tutorial",
            "auto"
          ]
        },
        {
          "name": "rate",
          "short": null,
          "type": "str",
          "desc": "⚡ Speech rate adjustment",
          "default": null,
          "choices": null
        },
        {
          "name": "pitch",
          "short": null,
          "type": "str",
          "desc": "🎵 Pitch adjustment",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "voice": {
      "desc": "Voice loading and caching",
      "icon": "🎤",
      "is_default": false,
      "args": [],
      "options": [],
      "subcommands": {
        "load": {
          "desc": "Load voice files into memory for fast access",
          "icon": null,
          "is_default": false,
          "args": [
            {
              "name": "voice_files",
              "desc": "Voice files to load",
              "nargs": "*",
              "choices": null,
              "required": true
            }
          ],
          "options": [],
          "subcommands": null
        },
        "unload": {
          "desc": "Unload voice files from memory",
          "icon": null,
          "is_default": false,
          "args": [
            {
              "name": "voice_files",
              "desc": "Voice files to unload",
              "nargs": "*",
              "choices": null,
              "required": false
            }
          ],
          "options": [
            {
              "name": "all",
              "short": null,
              "type": "flag",
              "desc": "🧹 Unload all voices",
              "default": null,
              "choices": null
            }
          ],
          "subcommands": null
        },
        "status": {
          "desc": "Show loaded voices and system status",
          "icon": null,
          "is_default": false,
          "args": [],
          "options": [],
          "subcommands": null
        }
      }
    },
    "status": {
      "desc": "Check system and provider status",
      "icon": "🩺",
      "is_default": false,
      "args": [],
      "options": [],
      "subcommands": null
    },
    "config": {
      "desc": "Manage configuration",
      "icon": "🔧",
      "is_default": false,
      "args": [
        {
          "name": "action",
          "desc": "Configuration action",
          "nargs": null,
          "choices": [
            "show",
            "voice",
            "provider",
            "format",
            "get",
            "edit",
            "set"
          ],
          "required": false
        },
        {
          "name": "key",
          "desc": "Configuration key",
          "nargs": null,
          "choices": null,
          "required": false
        },
        {
          "name": "value",
          "desc": "Configuration value",
          "nargs": null,
          "choices": null,
          "required": false
        }
      ],
      "options": [],
      "subcommands": null
    }
  },
  "command_groups": [
    {
      "name": "Core Commands",
      "commands": [
        "speak",
        "save",
        "voices"
      ],
      "icon": null
    },
    {
      "name": "Provider Management",
      "commands": [
        "providers",
        "info",
        "install"
      ],
      "icon": null
    },
    {
      "name": "Configuration",
      "commands": [
        "config",
        "status"
      ],
      "icon": null
    },
    {
      "name": "Advanced Features",
      "commands": [
        "voice",
        "document"
      ],
      "icon": null
    }
  ],
  "config": {
    "rich_help_panel": true,
    "show_metavars_column": false,
    "append_metavars_help": true,
    "style_errors_suggestion": true,
    "max_width": 120
  },
  "enable_recursive_help": true,
  "enable_help_json": true
}''')
    ctx.exit()





























class DefaultGroup(RichGroup):
    """Allow a default command to be invoked without being specified."""

    def __init__(self, *args: Any, default: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.default_command = default

    def resolve_command(self, ctx: Any, args: List[str]) -> Tuple[Optional[str], Optional[Any], List[str]]:
        import os
        import sys

        try:
            # Try normal command resolution first
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # If no command found and we have a default, use it
            # Check if stdin is coming from a pipe or redirection
            has_stdin = False
            try:
                # Check if stdin is a pipe or file (not a terminal)
                stdin_stat = os.fstat(sys.stdin.fileno())
                # Use S_ISFIFO to check if it's a pipe, or S_ISREG to check if it's a regular file
                import stat
                has_stdin = stat.S_ISFIFO(stdin_stat.st_mode) or stat.S_ISREG(stdin_stat.st_mode)
            except Exception:
                # Fallback to isatty check
                has_stdin = not sys.stdin.isatty()

            is_help_request = any(arg in ['--help-all', '--help-json'] for arg in args)

            if self.default_command and not is_help_request:
                # Trigger default command if:
                # 1. We have args (existing behavior)
                # 2. We have stdin input (new behavior for pipes)
                if args or has_stdin:
                    cmd = self.commands.get(self.default_command)
                    if cmd:
                        # Return command name, command object, and all args
                        return self.default_command, cmd, args
            raise



@click.group(
    cls=DefaultGroup, default='speak',
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120}
)

@click.version_option(version=get_version(), prog_name="TTS CLI")
@click.pass_context

@click.option(
    '--help-json', is_flag=True, callback=show_help_json, is_eager=True,
    help='Output CLI structure as JSON.', hidden=True
)


@click.option('--help-all', is_flag=True, is_eager=True, help='Show help for all commands.', hidden=True)

def main(ctx: Any, help_json: bool = False, help_all: bool = False) -> None:
    """[bold color(6)]TTS CLI v1.1[/bold color(6)] - Multi-provider text-to-speech with voice cloning


    \b
    [#B3B8C0]Transform text into natural speech using AI providers with auto-selection and real-time streaming.[/#B3B8C0]



    \b
    [bold yellow]Quick Start:[/bold yellow]
    [green]tts "Hello world"            [/green] [italic][#B3B8C0]# Speak instantly (implicit 'speak')[/#B3B8C0][/italic]
    [green]tts save "Hello" -o out.mp3  [/green] [italic][#B3B8C0]# Save as audio file[/#B3B8C0][/italic]

    \b
    [bold yellow]Core Commands:[/bold yellow]
    [green]speak   [/green]  🗣️  Speak text aloud (default command)
    [green]save    [/green]  💾 Save text as an audio file
    [green]voices  [/green]  🎭 Browse and test voices interactively

    \b
    [bold yellow]First-time Setup:[/bold yellow]
    1. Check providers: [green]tts providers[/green]
    2. Set API keys:    [green]tts config set openai_api_key YOUR_KEY[/green]

    \b
    """


    if help_all:
        # Print main help
        click.echo(ctx.get_help())
        click.echo() # Add a blank line for spacing

        # Get a list of all command names
        commands_to_show = sorted(ctx.command.list_commands(ctx))

        for cmd_name in commands_to_show:
            command = ctx.command.get_command(ctx, cmd_name)

            # Create a new context for the subcommand
            sub_ctx = click.Context(command, info_name=cmd_name, parent=ctx)

            # Print a separator and the subcommand's help
            click.echo("="*20 + f" HELP FOR: {cmd_name} " + "="*20)
            click.echo(sub_ctx.get_help())
            click.echo() # Add a blank line for spacing

        # Exit after printing all help
        ctx.exit()


    pass


# Set command groups after main function is defined
click.rich_click.COMMAND_GROUPS = {
    "main": [

        {
            "name": "Core Commands",
            "commands": ['speak', 'save', 'voices'],
        },

        {
            "name": "Provider Management",
            "commands": ['providers', 'info', 'install'],
        },

        {
            "name": "Configuration",
            "commands": ['config', 'status'],
        },

        {
            "name": "Advanced Features",
            "commands": ['voice', 'document'],
        },

    ]
}




@main.command()

@click.argument(
    "TEXT",
    required=False
)

@click.argument(
    "OPTIONS",
    nargs=-1
)


@click.option("-v", "--voice",
    type=str,
    help="🎤 Voice to use (e.g., en-GB-SoniaNeural for edge_tts)"
)

@click.option("--rate",
    type=str,
    help="⚡ Speech rate adjustment (e.g., +20%, -50%, 150%)"
)

@click.option("--pitch",
    type=str,
    help="🎵 Pitch adjustment (e.g., +5Hz, -10Hz)"
)

@click.option("--debug",
    is_flag=True,
    help="🔍 Show debug information during processing"
)

def speak(text: Optional[str], options: Tuple[str, ...], voice: Optional[str], rate: Optional[str], pitch: Optional[str], debug: bool) -> Any:
    """🗣️  Speak text aloud"""
    # Check if hook function exists
    hook_name = "on_speak"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(text, options, voice, rate, pitch, debug)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing speak command...")


        click.echo(f"  text: {text}")

        click.echo(f"  options: {options}")




        click.echo(f"  voice: {voice}")

        click.echo(f"  rate: {rate}")

        click.echo(f"  pitch: {pitch}")

        click.echo(f"  debug: {debug}")






@main.command()

@click.argument(
    "TEXT",
    required=False
)

@click.argument(
    "OPTIONS",
    nargs=-1
)


@click.option("-o", "--output",
    type=str,
    help="💾 Output file path"
)

@click.option("-f", "--format",
    type=click.Choice(['mp3', 'wav', 'ogg', 'flac']),
    help="🔧 Audio output format"
)

@click.option("-v", "--voice",
    type=str,
    help="🎤 Voice to use (e.g., en-GB-SoniaNeural for edge_tts)"
)

@click.option("--clone",
    type=str,
    help="🎭 Audio file to clone voice from (deprecated: use --voice instead)"
)

@click.option("--json",
    is_flag=True,
    help="🔧 Output results as JSON"
)

@click.option("--debug",
    is_flag=True,
    help="🔍 Show debug information during processing"
)

@click.option("--rate",
    type=str,
    help="⚡ Speech rate adjustment (e.g., +20%, -50%, 150%)"
)

@click.option("--pitch",
    type=str,
    help="🎵 Pitch adjustment (e.g., +5Hz, -10Hz)"
)

def save(text: Optional[str], options: Tuple[str, ...], output: Optional[str], format: Optional[str], voice: Optional[str], clone: Optional[str], json: bool, debug: bool, rate: Optional[str], pitch: Optional[str]) -> Any:
    """💾 Save text as an audio file"""
    # Check if hook function exists
    hook_name = "on_save"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(text, options, output, format, voice, clone, json, debug, rate, pitch)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing save command...")


        click.echo(f"  text: {text}")

        click.echo(f"  options: {options}")




        click.echo(f"  output: {output}")

        click.echo(f"  format: {format}")

        click.echo(f"  voice: {voice}")

        click.echo(f"  clone: {clone}")

        click.echo(f"  json: {json}")

        click.echo(f"  debug: {debug}")

        click.echo(f"  rate: {rate}")

        click.echo(f"  pitch: {pitch}")






@main.command()

@click.argument(
    "ARGS",
    nargs=-1,
    required=False
)


def voices(args: Tuple[str, ...]) -> Any:
    """🔍 Browse and test voices interactively"""
    # Check if hook function exists
    hook_name = "on_voices"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(args)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing voices command...")


        click.echo(f"  args: {args}")







@main.command()

@click.argument(
    "PROVIDER_NAME",
    required=False
)


def providers(provider_name: Optional[str]) -> Any:
    """📋 Available TTS providers and status"""
    # Check if hook function exists
    hook_name = "on_providers"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(provider_name)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing providers command...")


        click.echo(f"  provider_name: {provider_name}")







@main.command()

@click.argument(
    "ARGS",
    nargs=-1,
    required=False
)


def install(args: Tuple[str, ...]) -> Any:
    """📦 Install provider dependencies"""
    # Check if hook function exists
    hook_name = "on_install"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(args)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing install command...")


        click.echo(f"  args: {args}")







@main.command()

@click.argument(
    "PROVIDER",
    required=False
)


def info(provider: Optional[str]) -> Any:
    """👀 Provider information and capabilities"""
    # Check if hook function exists
    hook_name = "on_info"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(provider)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing info command...")


        click.echo(f"  provider: {provider}")







@main.command()

@click.argument(
    "DOCUMENT_PATH"
)

@click.argument(
    "OPTIONS",
    nargs=-1
)


@click.option("--save",
    is_flag=True,
    help="💾 Save processed audio to file"
)

@click.option("-o", "--output",
    type=str,
    help="📁 Output file path"
)

@click.option("-f", "--format",
    type=click.Choice(['mp3', 'wav', 'ogg', 'flac']),
    help="🔧 Audio output format"
)

@click.option("-v", "--voice",
    type=str,
    help="🎤 Voice to use"
)

@click.option("--clone",
    type=str,
    help="🎭 Audio file to clone voice from (deprecated: use --voice instead)"
)

@click.option("--json",
    is_flag=True,
    help="🔧 Output results as JSON"
)

@click.option("--debug",
    is_flag=True,
    help="🔍 Show debug information during processing"
)

@click.option("--doc-format",
    type=click.Choice(['auto', 'markdown', 'html', 'json']),
    default="auto",
    help="📄 Document format"
)

@click.option("--ssml-platform",
    type=click.Choice(['azure', 'google', 'amazon', 'generic']),
    default="generic",
    help="🏧️ SSML platform"
)

@click.option("--emotion-profile",
    type=click.Choice(['technical', 'marketing', 'narrative', 'tutorial', 'auto']),
    default="auto",
    help="🎭 Emotion profile"
)

@click.option("--rate",
    type=str,
    help="⚡ Speech rate adjustment"
)

@click.option("--pitch",
    type=str,
    help="🎵 Pitch adjustment"
)

def document(document_path: str, options: Tuple[str, ...], save: bool, output: Optional[str], format: Optional[str], voice: Optional[str], clone: Optional[str], json: bool, debug: bool,
             doc_format: str, ssml_platform: str, emotion_profile: str, rate: Optional[str], pitch: Optional[str]) -> Any:
    """📖 Convert documents to speech"""
    # Check if hook function exists
    hook_name = "on_document"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(
            document_path, options, save, output, format, voice, clone, json, debug,
            doc_format, ssml_platform, emotion_profile, rate, pitch
        )

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing document command...")


        click.echo(f"  document_path: {document_path}")

        click.echo(f"  options: {options}")




        click.echo(f"  save: {save}")

        click.echo(f"  output: {output}")

        click.echo(f"  format: {format}")

        click.echo(f"  voice: {voice}")

        click.echo(f"  clone: {clone}")

        click.echo(f"  json: {json}")

        click.echo(f"  debug: {debug}")

        click.echo(f"  doc-format: {doc_format}")

        click.echo(f"  ssml-platform: {ssml_platform}")

        click.echo(f"  emotion-profile: {emotion_profile}")

        click.echo(f"  rate: {rate}")

        click.echo(f"  pitch: {pitch}")






@main.group()
def voice() -> None:
    """🎤 Voice loading and caching"""
    pass


@voice.command()

@click.argument(
    "VOICE_FILES",
    nargs=-1,
    required=True
)


def load(voice_files: Tuple[str, ...]) -> Any:
    """Load voice files into memory for fast access"""
    # Check if hook function exists
    hook_name = "on_voice_load"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(voice_files)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing load command...")


        click.echo(f"  voice_files: {voice_files}")




@voice.command()

@click.argument(
    "VOICE_FILES",
    nargs=-1,
    required=False
)


@click.option("--all",
    is_flag=True,
    help="🧹 Unload all voices"
)

def unload(voice_files: Tuple[str, ...], all: bool) -> Any:
    """Unload voice files from memory"""
    # Check if hook function exists
    hook_name = "on_voice_unload"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(voice_files, all)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing unload command...")


        click.echo(f"  voice_files: {voice_files}")




        click.echo(f"  all: {all}")



@voice.command()


def status() -> Any:
    """Show loaded voices and system status"""
    # Check if hook function exists
    hook_name = "on_voice_status"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func()

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing status command...")







@main.command("status")


def system_status() -> Any:
    """🩺 Check system and provider status"""
    # Check if hook function exists
    hook_name = "on_status"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func()

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing status command...")






@main.command()

@click.argument(
    "ACTION",
    required=False,
    type=click.Choice(['show', 'voice', 'provider', 'format', 'get', 'edit', 'set'])
)

@click.argument(
    "KEY",
    required=False
)

@click.argument(
    "VALUE",
    required=False
)


def config(action: Optional[str], key: Optional[str], value: Optional[str]) -> Any:
    """🔧 Manage configuration"""
    # Check if hook function exists
    hook_name = "on_config"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)

        result = hook_func(action, key, value)

        return result
    else:
        # Default placeholder behavior
        click.echo("Executing config command...")


        click.echo(f"  action: {action}")

        click.echo(f"  key: {key}")

        click.echo(f"  value: {value}")







def cli_entry() -> None:
    """Entry point for the CLI when installed via pipx."""
    # Load plugins before running the CLI
    load_plugins(main)
    main()

if __name__ == "__main__":
    cli_entry()
