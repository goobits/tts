#!/usr/bin/env python3
"""Auto-generated from goobits.yaml"""
import os
import sys
import importlib.util
from pathlib import Path
import rich_click as click
from rich_click import RichGroup, RichCommand

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
        app_hooks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_hooks)
    else:
        # Try to import from Python path
        import app_hooks
except (ImportError, FileNotFoundError):
    # No hooks module found, use default behavior
    pass

def load_plugins(cli_group):
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
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)
                
                # Call register_plugin if it exists
                if hasattr(plugin_module, "register_plugin"):
                    plugin_module.register_plugin(cli_group)
                    click.echo(f"Loaded plugin: {plugin_name}", err=True)
            except Exception as e:
                click.echo(f"Failed to load plugin {plugin_name}: {e}", err=True)







def get_version():
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


def show_help_json(ctx, param, value):
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
          "nargs": "*",
          "choices": null
        }
      ],
      "options": [
        {
          "name": "voice",
          "short": "v",
          "type": "str",
          "desc": "Voice ID or name",
          "default": null,
          "choices": null
        },
        {
          "name": "provider",
          "short": "p",
          "type": "str",
          "desc": "TTS provider to use",
          "default": null,
          "choices": null
        },
        {
          "name": "model",
          "short": "m",
          "type": "str",
          "desc": "Model to use (provider-specific)",
          "default": null,
          "choices": null
        },
        {
          "name": "speed",
          "short": "s",
          "type": "float",
          "desc": "Speech speed (0.5-2.0)",
          "default": 1.0,
          "choices": null
        },
        {
          "name": "pitch",
          "short": null,
          "type": "float",
          "desc": "Voice pitch adjustment",
          "default": null,
          "choices": null
        },
        {
          "name": "language",
          "short": "l",
          "type": "str",
          "desc": "Language code (e.g., en-US)",
          "default": null,
          "choices": null
        },
        {
          "name": "emotion",
          "short": null,
          "type": "str",
          "desc": "Emotional tone",
          "default": null,
          "choices": [
            "neutral",
            "happy",
            "sad",
            "angry",
            "excited"
          ]
        },
        {
          "name": "wait",
          "short": "w",
          "type": "bool",
          "desc": "Wait for speech to complete",
          "default": true,
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
          "nargs": "*",
          "choices": null
        }
      ],
      "options": [
        {
          "name": "output",
          "short": "o",
          "type": "str",
          "desc": "Output file path",
          "default": "output.mp3",
          "choices": null
        },
        {
          "name": "voice",
          "short": "v",
          "type": "str",
          "desc": "Voice ID or name",
          "default": null,
          "choices": null
        },
        {
          "name": "provider",
          "short": "p",
          "type": "str",
          "desc": "TTS provider to use",
          "default": null,
          "choices": null
        },
        {
          "name": "model",
          "short": "m",
          "type": "str",
          "desc": "Model to use (provider-specific)",
          "default": null,
          "choices": null
        },
        {
          "name": "format",
          "short": "f",
          "type": "str",
          "desc": "Audio format",
          "default": "mp3",
          "choices": [
            "mp3",
            "wav",
            "ogg",
            "flac"
          ]
        },
        {
          "name": "quality",
          "short": "q",
          "type": "str",
          "desc": "Audio quality",
          "default": "high",
          "choices": [
            "low",
            "medium",
            "high",
            "ultra"
          ]
        },
        {
          "name": "speed",
          "short": "s",
          "type": "float",
          "desc": "Speech speed (0.5-2.0)",
          "default": 1.0,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "voices": {
      "desc": "Browse and test voices interactively",
      "icon": "🎭",
      "is_default": false,
      "args": [],
      "options": [
        {
          "name": "provider",
          "short": "p",
          "type": "str",
          "desc": "Filter by provider",
          "default": null,
          "choices": null
        },
        {
          "name": "language",
          "short": "l",
          "type": "str",
          "desc": "Filter by language",
          "default": null,
          "choices": null
        },
        {
          "name": "gender",
          "short": "g",
          "type": "str",
          "desc": "Filter by gender",
          "default": null,
          "choices": [
            "male",
            "female",
            "neutral"
          ]
        },
        {
          "name": "search",
          "short": "s",
          "type": "str",
          "desc": "Search voices by name",
          "default": null,
          "choices": null
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output as JSON",
          "default": null,
          "choices": null
        }
      ],
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
          "nargs": "?",
          "choices": null
        }
      ],
      "options": [
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output as JSON",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "models": {
      "desc": "List available models",
      "icon": "🤖",
      "is_default": false,
      "args": [
        {
          "name": "provider",
          "desc": "Provider name (optional)",
          "nargs": "?",
          "choices": null
        }
      ],
      "options": [
        {
          "name": "verbose",
          "short": "v",
          "type": "bool",
          "desc": "Show detailed information",
          "default": false,
          "choices": null
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output as JSON",
          "default": null,
          "choices": null
        }
      ],
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
          "choices": null
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
          "nargs": "?",
          "choices": null
        }
      ],
      "options": [
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output provider info in JSON format",
          "default": null,
          "choices": null
        }
      ],
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
          "choices": null
        }
      ],
      "options": [
        {
          "name": "save",
          "short": null,
          "type": "flag",
          "desc": "Save processed audio to file",
          "default": null,
          "choices": null
        },
        {
          "name": "output",
          "short": "o",
          "type": "str",
          "desc": "Output file path",
          "default": null,
          "choices": null
        },
        {
          "name": "format",
          "short": "f",
          "type": "str",
          "desc": "Audio output format",
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
          "desc": "Voice to use",
          "default": null,
          "choices": null
        },
        {
          "name": "clone",
          "short": null,
          "type": "str",
          "desc": "Audio file to clone voice from (deprecated)",
          "default": null,
          "choices": null
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output results as JSON",
          "default": null,
          "choices": null
        },
        {
          "name": "debug",
          "short": null,
          "type": "flag",
          "desc": "Show debug information",
          "default": null,
          "choices": null
        },
        {
          "name": "doc-format",
          "short": null,
          "type": "str",
          "desc": "Document format",
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
          "desc": "SSML platform",
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
          "desc": "Emotion profile",
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
          "desc": "Speech rate adjustment",
          "default": null,
          "choices": null
        },
        {
          "name": "pitch",
          "short": null,
          "type": "str",
          "desc": "Pitch adjustment",
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
              "choices": null
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
              "choices": null
            }
          ],
          "options": [
            {
              "name": "all",
              "short": null,
              "type": "flag",
              "desc": "Unload all voices",
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
    "clone": {
      "desc": "Clone a voice from audio",
      "icon": "🎤",
      "is_default": false,
      "args": [
        {
          "name": "audio_file",
          "desc": "Path to audio file for cloning",
          "nargs": null,
          "choices": null
        }
      ],
      "options": [
        {
          "name": "name",
          "short": "n",
          "type": "str",
          "desc": "Name for cloned voice",
          "default": null,
          "choices": null
        },
        {
          "name": "provider",
          "short": "p",
          "type": "str",
          "desc": "Provider to use for cloning",
          "default": null,
          "choices": null
        },
        {
          "name": "description",
          "short": "d",
          "type": "str",
          "desc": "Voice description",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "stream": {
      "desc": "Stream audio in real-time",
      "icon": "📡",
      "is_default": false,
      "args": [
        {
          "name": "text",
          "desc": "Text to stream",
          "nargs": "*",
          "choices": null
        }
      ],
      "options": [
        {
          "name": "voice",
          "short": "v",
          "type": "str",
          "desc": "Voice ID or name",
          "default": null,
          "choices": null
        },
        {
          "name": "provider",
          "short": "p",
          "type": "str",
          "desc": "TTS provider to use",
          "default": null,
          "choices": null
        },
        {
          "name": "chunk-size",
          "short": null,
          "type": "int",
          "desc": "Streaming chunk size",
          "default": 1024,
          "choices": null
        },
        {
          "name": "websocket",
          "short": null,
          "type": "bool",
          "desc": "Use WebSocket streaming",
          "default": false,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "status": {
      "desc": "Check system and provider status",
      "icon": "✅",
      "is_default": false,
      "args": [],
      "options": [
        {
          "name": "provider",
          "short": "p",
          "type": "str",
          "desc": "Check specific provider",
          "default": null,
          "choices": null
        },
        {
          "name": "verbose",
          "short": "v",
          "type": "bool",
          "desc": "Show detailed status",
          "default": false,
          "choices": null
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output as JSON",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "config": {
      "desc": "Manage configuration",
      "icon": "⚙️",
      "is_default": false,
      "args": [],
      "options": [],
      "subcommands": {
        "get": {
          "desc": "Get a configuration value",
          "icon": null,
          "is_default": false,
          "args": [
            {
              "name": "key",
              "desc": "Configuration key",
              "nargs": null,
              "choices": null
            }
          ],
          "options": [],
          "subcommands": null
        },
        "set": {
          "desc": "Set a configuration value",
          "icon": null,
          "is_default": false,
          "args": [
            {
              "name": "key",
              "desc": "Configuration key",
              "nargs": null,
              "choices": null
            },
            {
              "name": "value",
              "desc": "Configuration value",
              "nargs": null,
              "choices": null
            }
          ],
          "options": [],
          "subcommands": null
        },
        "list": {
          "desc": "List all configuration",
          "icon": null,
          "is_default": false,
          "args": [],
          "options": [
            {
              "name": "show-secrets",
              "short": null,
              "type": "bool",
              "desc": "Include API keys",
              "default": false,
              "choices": null
            }
          ],
          "subcommands": null
        },
        "reset": {
          "desc": "Reset configuration to defaults",
          "icon": null,
          "is_default": false,
          "args": [],
          "options": [
            {
              "name": "confirm",
              "short": null,
              "type": "bool",
              "desc": "Skip confirmation prompt",
              "default": false,
              "choices": null
            }
          ],
          "subcommands": null
        }
      }
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
        "models",
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
        "document",
        "clone",
        "stream"
      ],
      "icon": null
    },
    {
      "name": "Data Management",
      "commands": [
        "export"
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
    
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_command = default
    
    def resolve_command(self, ctx, args):
        try:
            # Try normal command resolution first
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # If no command found and we have a default, use it
            if self.default_command and args and not any(arg in ['--help-all', '--help-json'] for arg in args):
                # Get the default command object
                cmd = self.commands.get(self.default_command)
                if cmd:
                    # Return command name, command object, and all args
                    return self.default_command, cmd, args
            raise



@click.group(cls=DefaultGroup, default='speak', context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120})

@click.version_option(version=get_version(), prog_name="TTS CLI")
@click.pass_context

@click.option('--help-json', is_flag=True, callback=show_help_json, is_eager=True, help='Output CLI structure as JSON.', hidden=True)


@click.option('--help-all', is_flag=True, is_eager=True, help='Show help for all commands.', hidden=True)

def main(ctx, help_json=False, help_all=False):
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
            "commands": ['providers', 'models', 'info', 'install'],
        },
        
        {
            "name": "Configuration",
            "commands": ['config', 'status'],
        },
        
        {
            "name": "Advanced Features",
            "commands": ['voice', 'document', 'clone', 'stream'],
        },
        
        {
            "name": "Data Management",
            "commands": ['export'],
        },
        
    ]
}




@main.command()

@click.argument(
    "TEXT",
    nargs=-1
)


@click.option("-v", "--voice",
    type=str,
    help="Voice ID or name"
)

@click.option("-p", "--provider",
    type=str,
    help="TTS provider to use"
)

@click.option("-m", "--model",
    type=str,
    help="Model to use (provider-specific)"
)

@click.option("-s", "--speed",
    type=float,
    default=1.0,
    help="Speech speed (0.5-2.0)"
)

@click.option("--pitch",
    type=float,
    help="Voice pitch adjustment"
)

@click.option("-l", "--language",
    type=str,
    help="Language code (e.g., en-US)"
)

@click.option("--emotion",
    type=click.Choice(['neutral', 'happy', 'sad', 'angry', 'excited']),
    help="Emotional tone"
)

@click.option("-w", "--wait",
    type=bool,
    default=True,
    help="Wait for speech to complete"
)

def speak(text, voice, provider, model, speed, pitch, language, emotion, wait):
    """🗣️  Speak text aloud"""
    # Check if hook function exists
    hook_name = f"on_speak"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(text, voice, provider, model, speed, pitch, language, emotion, wait)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing speak command...")
        
        
        click.echo(f"  text: {text}")
        
        
        
        
        click.echo(f"  voice: {voice}")
        
        click.echo(f"  provider: {provider}")
        
        click.echo(f"  model: {model}")
        
        click.echo(f"  speed: {speed}")
        
        click.echo(f"  pitch: {pitch}")
        
        click.echo(f"  language: {language}")
        
        click.echo(f"  emotion: {emotion}")
        
        click.echo(f"  wait: {wait}")
        
        




@main.command()

@click.argument(
    "TEXT",
    nargs=-1
)


@click.option("-o", "--output",
    type=str,
    default="output.mp3",
    help="Output file path"
)

@click.option("-v", "--voice",
    type=str,
    help="Voice ID or name"
)

@click.option("-p", "--provider",
    type=str,
    help="TTS provider to use"
)

@click.option("-m", "--model",
    type=str,
    help="Model to use (provider-specific)"
)

@click.option("-f", "--format",
    type=click.Choice(['mp3', 'wav', 'ogg', 'flac']),
    default="mp3",
    help="Audio format"
)

@click.option("-q", "--quality",
    type=click.Choice(['low', 'medium', 'high', 'ultra']),
    default="high",
    help="Audio quality"
)

@click.option("-s", "--speed",
    type=float,
    default=1.0,
    help="Speech speed (0.5-2.0)"
)

def save(text, output, voice, provider, model, format, quality, speed):
    """💾 Save text as an audio file"""
    # Check if hook function exists
    hook_name = f"on_save"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(text, output, voice, provider, model, format, quality, speed)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing save command...")
        
        
        click.echo(f"  text: {text}")
        
        
        
        
        click.echo(f"  output: {output}")
        
        click.echo(f"  voice: {voice}")
        
        click.echo(f"  provider: {provider}")
        
        click.echo(f"  model: {model}")
        
        click.echo(f"  format: {format}")
        
        click.echo(f"  quality: {quality}")
        
        click.echo(f"  speed: {speed}")
        
        




@main.command()


@click.option("-p", "--provider",
    type=str,
    help="Filter by provider"
)

@click.option("-l", "--language",
    type=str,
    help="Filter by language"
)

@click.option("-g", "--gender",
    type=click.Choice(['male', 'female', 'neutral']),
    help="Filter by gender"
)

@click.option("-s", "--search",
    type=str,
    help="Search voices by name"
)

@click.option("--json",
    is_flag=True,
    help="Output as JSON"
)

def voices(provider, language, gender, search, json):
    """🎭 Browse and test voices interactively"""
    # Check if hook function exists
    hook_name = f"on_voices"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(provider, language, gender, search, json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing voices command...")
        
        
        
        click.echo(f"  provider: {provider}")
        
        click.echo(f"  language: {language}")
        
        click.echo(f"  gender: {gender}")
        
        click.echo(f"  search: {search}")
        
        click.echo(f"  json: {json}")
        
        




@main.command()

@click.argument(
    "PROVIDER_NAME",
    nargs=1,
    required=False
)


@click.option("--json",
    is_flag=True,
    help="Output as JSON"
)

def providers(provider_name, json):
    """📋 Available TTS providers and status"""
    # Check if hook function exists
    hook_name = f"on_providers"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(provider_name, json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing providers command...")
        
        
        click.echo(f"  provider_name: {provider_name}")
        
        
        
        
        click.echo(f"  json: {json}")
        
        




@main.command()

@click.argument(
    "PROVIDER",
    nargs=1,
    required=False
)


@click.option("-v", "--verbose",
    type=bool,
    default=False,
    help="Show detailed information"
)

@click.option("--json",
    is_flag=True,
    help="Output as JSON"
)

def models(provider, verbose, json):
    """🤖 List available models"""
    # Check if hook function exists
    hook_name = f"on_models"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(provider, verbose, json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing models command...")
        
        
        click.echo(f"  provider: {provider}")
        
        
        
        
        click.echo(f"  verbose: {verbose}")
        
        click.echo(f"  json: {json}")
        
        




@main.command()

@click.argument(
    "ARGS",
    nargs=-1
)


def install(args):
    """📦 Install provider dependencies"""
    # Check if hook function exists
    hook_name = f"on_install"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(args)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing install command...")
        
        
        click.echo(f"  args: {args}")
        
        
        




@main.command()

@click.argument(
    "PROVIDER",
    nargs=1,
    required=False
)


@click.option("--json",
    is_flag=True,
    help="Output provider info in JSON format"
)

def info(provider, json):
    """👀 Provider information and capabilities"""
    # Check if hook function exists
    hook_name = f"on_info"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(provider, json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing info command...")
        
        
        click.echo(f"  provider: {provider}")
        
        
        
        
        click.echo(f"  json: {json}")
        
        




@main.command()

@click.argument(
    "DOCUMENT_PATH"
)


@click.option("--save",
    is_flag=True,
    help="Save processed audio to file"
)

@click.option("-o", "--output",
    type=str,
    help="Output file path"
)

@click.option("-f", "--format",
    type=click.Choice(['mp3', 'wav', 'ogg', 'flac']),
    help="Audio output format"
)

@click.option("-v", "--voice",
    type=str,
    help="Voice to use"
)

@click.option("--clone",
    type=str,
    help="Audio file to clone voice from (deprecated)"
)

@click.option("--json",
    is_flag=True,
    help="Output results as JSON"
)

@click.option("--debug",
    is_flag=True,
    help="Show debug information"
)

@click.option("--doc-format",
    type=click.Choice(['auto', 'markdown', 'html', 'json']),
    default="auto",
    help="Document format"
)

@click.option("--ssml-platform",
    type=click.Choice(['azure', 'google', 'amazon', 'generic']),
    default="generic",
    help="SSML platform"
)

@click.option("--emotion-profile",
    type=click.Choice(['technical', 'marketing', 'narrative', 'tutorial', 'auto']),
    default="auto",
    help="Emotion profile"
)

@click.option("--rate",
    type=str,
    help="Speech rate adjustment"
)

@click.option("--pitch",
    type=str,
    help="Pitch adjustment"
)

def document(document_path, save, output, format, voice, clone, json, debug, doc_format, ssml_platform, emotion_profile, rate, pitch):
    """📖 Convert documents to speech"""
    # Check if hook function exists
    hook_name = f"on_document"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(document_path, save, output, format, voice, clone, json, debug, doc_format, ssml_platform, emotion_profile, rate, pitch)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing document command...")
        
        
        click.echo(f"  document_path: {document_path}")
        
        
        
        
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
def voice():
    """🎤 Voice loading and caching"""
    pass


@voice.command()

@click.argument(
    "VOICE_FILES",
    nargs=-1
)


def load(voice_files):
    """Load voice files into memory for fast access"""
    # Check if hook function exists
    hook_name = f"on_voice_load"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(voice_files)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing load command...")
        
        
        click.echo(f"  voice_files: {voice_files}")
        
        
        

@voice.command()

@click.argument(
    "VOICE_FILES",
    nargs=-1
)


@click.option("--all",
    is_flag=True,
    help="Unload all voices"
)

def unload(voice_files, all):
    """Unload voice files from memory"""
    # Check if hook function exists
    hook_name = f"on_voice_unload"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(voice_files, all)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing unload command...")
        
        
        click.echo(f"  voice_files: {voice_files}")
        
        
        
        
        click.echo(f"  all: {all}")
        
        

@voice.command()


def status():
    """Show loaded voices and system status"""
    # Check if hook function exists
    hook_name = f"on_voice_status"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func()
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing status command...")
        
        





@main.command()

@click.argument(
    "AUDIO_FILE"
)


@click.option("-n", "--name",
    type=str,
    help="Name for cloned voice"
)

@click.option("-p", "--provider",
    type=str,
    help="Provider to use for cloning"
)

@click.option("-d", "--description",
    type=str,
    help="Voice description"
)

def clone(audio_file, name, provider, description):
    """🎤 Clone a voice from audio"""
    # Check if hook function exists
    hook_name = f"on_clone"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(audio_file, name, provider, description)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing clone command...")
        
        
        click.echo(f"  audio_file: {audio_file}")
        
        
        
        
        click.echo(f"  name: {name}")
        
        click.echo(f"  provider: {provider}")
        
        click.echo(f"  description: {description}")
        
        




@main.command()

@click.argument(
    "TEXT",
    nargs=-1
)


@click.option("-v", "--voice",
    type=str,
    help="Voice ID or name"
)

@click.option("-p", "--provider",
    type=str,
    help="TTS provider to use"
)

@click.option("--chunk-size",
    type=int,
    default=1024,
    help="Streaming chunk size"
)

@click.option("--websocket",
    type=bool,
    default=False,
    help="Use WebSocket streaming"
)

def stream(text, voice, provider, chunk_size, websocket):
    """📡 Stream audio in real-time"""
    # Check if hook function exists
    hook_name = f"on_stream"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(text, voice, provider, chunk_size, websocket)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing stream command...")
        
        
        click.echo(f"  text: {text}")
        
        
        
        
        click.echo(f"  voice: {voice}")
        
        click.echo(f"  provider: {provider}")
        
        click.echo(f"  chunk-size: {chunk_size}")
        
        click.echo(f"  websocket: {websocket}")
        
        




@main.command()


@click.option("-p", "--provider",
    type=str,
    help="Check specific provider"
)

@click.option("-v", "--verbose",
    type=bool,
    default=False,
    help="Show detailed status"
)

@click.option("--json",
    is_flag=True,
    help="Output as JSON"
)

def status(provider, verbose, json):
    """✅ Check system and provider status"""
    # Check if hook function exists
    hook_name = f"on_status"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(provider, verbose, json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing status command...")
        
        
        
        click.echo(f"  provider: {provider}")
        
        click.echo(f"  verbose: {verbose}")
        
        click.echo(f"  json: {json}")
        
        




@main.group()
def config():
    """⚙️  Manage configuration"""
    pass


@config.command()

@click.argument(
    "KEY"
)


def get(key):
    """Get a configuration value"""
    # Check if hook function exists
    hook_name = f"on_config_get"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(key)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing get command...")
        
        
        click.echo(f"  key: {key}")
        
        
        

@config.command()

@click.argument(
    "KEY"
)

@click.argument(
    "VALUE"
)


def set(key, value):
    """Set a configuration value"""
    # Check if hook function exists
    hook_name = f"on_config_set"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(key, value)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing set command...")
        
        
        click.echo(f"  key: {key}")
        
        click.echo(f"  value: {value}")
        
        
        

@config.command()


@click.option("--show-secrets",
    type=bool,
    default=False,
    help="Include API keys"
)

def list(show_secrets):
    """List all configuration"""
    # Check if hook function exists
    hook_name = f"on_config_list"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(show_secrets)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing list command...")
        
        
        
        click.echo(f"  show-secrets: {show_secrets}")
        
        

@config.command()


@click.option("--confirm",
    type=bool,
    default=False,
    help="Skip confirmation prompt"
)

def reset(confirm):
    """Reset configuration to defaults"""
    # Check if hook function exists
    hook_name = f"on_config_reset"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(confirm)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing reset command...")
        
        
        
        click.echo(f"  confirm: {confirm}")
        
        





def cli_entry():
    """Entry point for the CLI when installed via pipx."""
    # Load plugins before running the CLI
    load_plugins(main)
    main()

if __name__ == "__main__":
    cli_entry()
