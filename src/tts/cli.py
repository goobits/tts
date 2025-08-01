#!/usr/bin/env python3
"""Auto-generated from goobits.yaml"""
import os
import sys
import signal
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

# Using configured hooks path: src/tts/app_hooks.py
try:
    # First try as a module import (e.g., "ttt.app_hooks")
    module_path = "src/tts/app_hooks.py".replace(".py", "").replace("/", ".")
    if module_path.startswith("src."):
        module_path = module_path[4:]  # Remove 'src.' prefix
    
    try:
        app_hooks = importlib.import_module(module_path)
    except ImportError:
        # If module import fails, try relative import
        try:
            from . import app_hooks
        except ImportError:
            # If relative import fails, try file-based import as last resort
            script_dir = Path(__file__).parent.parent.parent
            hooks_file = script_dir / "src/tts/app_hooks.py"
            
            if hooks_file.exists():
                spec = importlib.util.spec_from_file_location("app_hooks", hooks_file)
                app_hooks = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(app_hooks)
except Exception:
    # No hooks module found, use default behavior
    pass


# Built-in commands

def builtin_upgrade_command(check_only=False, pre=False, version=None, dry_run=False):
    """Built-in upgrade function for TTS - Text to Speech - uses enhanced setup.sh script."""
    import subprocess
    import sys
    from pathlib import Path

    if check_only:
        print(f"Checking for updates to TTS - Text to Speech...")
        print("Update check not yet implemented. Run without --check to upgrade.")
        return

    if dry_run:
        print("Dry run - would execute: pipx upgrade goobits-tts")
        return

    # Find the setup.sh script - look in common locations
    setup_script = None
    search_paths = [
        Path(__file__).parent / "setup.sh",  # Package directory (installed packages)
        Path(__file__).parent.parent / "setup.sh",  # Development mode 
        Path.home() / ".local" / "share" / "goobits-tts" / "setup.sh",  # User data
        # Remove Path.cwd() to prevent cross-contamination
    ]
    
    for path in search_paths:
        if path.exists():
            setup_script = path
            break
    
    if setup_script is None:
        # Fallback to basic upgrade if setup.sh not found
        print(f"Enhanced setup script not found. Using basic upgrade for TTS - Text to Speech...")
        import shutil
        
        package_name = "goobits-tts"
        pypi_name = "goobits-tts"
        
        if shutil.which("pipx"):
            result = subprocess.run(["pipx", "list"], capture_output=True, text=True)
            if package_name in result.stdout or pypi_name in result.stdout:
                cmd = ["pipx", "upgrade", pypi_name]
            else:
                cmd = [sys.executable, "-m", "pip", "install", "--upgrade", pypi_name]
        else:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", pypi_name]
        
        result = subprocess.run(cmd)
        if result.returncode == 0:
            print(f"✅ TTS - Text to Speech upgraded successfully!")
            print(f"Run 'tts --version' to verify the new version.")
        else:
            print(f"❌ Upgrade failed with exit code {result.returncode}")
            sys.exit(1)
        return

    # Use the enhanced setup.sh script
    result = subprocess.run([str(setup_script), "upgrade"])
    sys.exit(result.returncode)


def load_plugins(cli_group):
    """Load plugins from the conventional plugin directory."""
    # Define plugin directories to search
    plugin_dirs = [
        # User-specific plugin directory
        Path.home() / ".config" / "goobits" / "GOOBITS TTS CLI" / "plugins",
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
                
            # Skip core system files that aren't plugins
            if plugin_file.name in ["loader.py", "__init__.py"]:
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
    return "1.1.2"


def show_help_json(ctx, param, value):
    """Callback for --help-json option."""
    if not value or ctx.resilient_parsing:
        return
    # The triple quotes are important to correctly handle the multi-line JSON string
    click.echo('''{
  "name": "GOOBITS TTS CLI",
  "version": "1.1.2",
  "display_version": true,
  "tagline": "Multi-provider text-to-speech with voice cloning",
  "description": "Convert text into natural speech with AI-powered auto-selection and real-time streaming.",
  "icon": "🔊",
  "header_sections": [
    {
      "title": "🚀 Quick Start",
      "icon": null,
      "items": [
        {
          "item": "tts \\"Hello world\\"",
          "desc": "Instantly speak text (default command)",
          "style": "example"
        },
        {
          "item": "tts save \\"Hello\\" -o out.mp3",
          "desc": "Save speech to audio file",
          "style": "example"
        }
      ]
    },
    {
      "title": "💡 Core Commands",
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
          "desc": "🔍 Explore and test available voices",
          "style": "command"
        }
      ]
    },
    {
      "title": "🔧 First-time Setup",
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
  "options": [],
  "commands": {
    "speak": {
      "desc": "Speak text aloud",
      "icon": "🗣️",
      "is_default": true,
      "lifecycle": "standard",
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
          "desc": "🎤 Voice selection (e.g., en-GB-SoniaNeural for edge_tts)",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "rate",
          "short": null,
          "type": "str",
          "desc": "⚡ Speech rate adjustment (e.g., +20%, -50%, 150%)",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "pitch",
          "short": null,
          "type": "str",
          "desc": "🎵 Pitch adjustment (e.g., +5Hz, -10Hz)",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "debug",
          "short": null,
          "type": "flag",
          "desc": "🐞 Display debug information during processing",
          "default": null,
          "choices": null,
          "multiple": false
        }
      ],
      "subcommands": null
    },
    "save": {
      "desc": "Save text as an audio file",
      "icon": "💾",
      "is_default": false,
      "lifecycle": "standard",
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
          "choices": null,
          "multiple": false
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
          ],
          "multiple": false
        },
        {
          "name": "voice",
          "short": "v",
          "type": "str",
          "desc": "🎤 Voice selection (e.g., en-GB-SoniaNeural for edge_tts)",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "clone",
          "short": null,
          "type": "str",
          "desc": "🎭 Audio file to clone voice from (deprecated: use --voice instead)",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "🔧 Output results as JSON",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "debug",
          "short": null,
          "type": "flag",
          "desc": "🐞 Display debug information during processing",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "rate",
          "short": null,
          "type": "str",
          "desc": "⚡ Speech rate adjustment (e.g., +20%, -50%, 150%)",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "pitch",
          "short": null,
          "type": "str",
          "desc": "🎵 Pitch adjustment (e.g., +5Hz, -10Hz)",
          "default": null,
          "choices": null,
          "multiple": false
        }
      ],
      "subcommands": null
    },
    "voices": {
      "desc": "Explore and test available voices",
      "icon": "🔍",
      "is_default": false,
      "lifecycle": "standard",
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
      "desc": "Show available providers and their status",
      "icon": "📋",
      "is_default": false,
      "lifecycle": "standard",
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
      "desc": "Install required provider dependencies",
      "icon": "📥",
      "is_default": false,
      "lifecycle": "standard",
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
      "desc": "Detailed provider information",
      "icon": "👀",
      "is_default": false,
      "lifecycle": "standard",
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
      "lifecycle": "standard",
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
          "desc": "💾 Save audio output to file",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "output",
          "short": "o",
          "type": "str",
          "desc": "📁 Output file path",
          "default": null,
          "choices": null,
          "multiple": false
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
          ],
          "multiple": false
        },
        {
          "name": "voice",
          "short": "v",
          "type": "str",
          "desc": "🎤 Voice to use",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "clone",
          "short": null,
          "type": "str",
          "desc": "🎭 Audio file to clone voice from (deprecated: use --voice instead)",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "🔧 Output results as JSON",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "debug",
          "short": null,
          "type": "flag",
          "desc": "🐞 Display debug information during processing",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "doc-format",
          "short": null,
          "type": "str",
          "desc": "📄 Input document format",
          "default": "auto",
          "choices": [
            "auto",
            "markdown",
            "html",
            "json"
          ],
          "multiple": false
        },
        {
          "name": "ssml-platform",
          "short": null,
          "type": "str",
          "desc": "🏧️ SSML format platform",
          "default": "generic",
          "choices": [
            "azure",
            "google",
            "amazon",
            "generic"
          ],
          "multiple": false
        },
        {
          "name": "emotion-profile",
          "short": null,
          "type": "str",
          "desc": "🎭 Speech emotion style",
          "default": "auto",
          "choices": [
            "technical",
            "marketing",
            "narrative",
            "tutorial",
            "auto"
          ],
          "multiple": false
        },
        {
          "name": "rate",
          "short": null,
          "type": "str",
          "desc": "⚡ Speech rate adjustment",
          "default": null,
          "choices": null,
          "multiple": false
        },
        {
          "name": "pitch",
          "short": null,
          "type": "str",
          "desc": "🎵 Pitch adjustment",
          "default": null,
          "choices": null,
          "multiple": false
        }
      ],
      "subcommands": null
    },
    "voice": {
      "desc": "Manage voice loading and caching",
      "icon": "🎤",
      "is_default": false,
      "lifecycle": "standard",
      "args": [],
      "options": [],
      "subcommands": {
        "load": {
          "desc": "Load voices into memory for faster access",
          "icon": null,
          "is_default": false,
          "lifecycle": "standard",
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
          "desc": "Remove voices from memory",
          "icon": null,
          "is_default": false,
          "lifecycle": "standard",
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
              "desc": "🧹 Remove all voices from memory",
              "default": null,
              "choices": null,
              "multiple": false
            }
          ],
          "subcommands": null
        },
        "status": {
          "desc": "Show currently loaded voices and system status",
          "icon": null,
          "is_default": false,
          "lifecycle": "standard",
          "args": [],
          "options": [],
          "subcommands": null
        }
      }
    },
    "status": {
      "desc": "Check system and provider health",
      "icon": "🩺",
      "is_default": false,
      "lifecycle": "standard",
      "args": [],
      "options": [],
      "subcommands": null
    },
    "config": {
      "desc": "Adjust CLI settings and API keys",
      "icon": "🔧",
      "is_default": false,
      "lifecycle": "standard",
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
    
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_command = default
    
    def main(self, *args, **kwargs):
        """Override main to handle stdin input when no command is provided."""
        import sys
        import os
        import stat
        
        # Check if we need to inject the default command due to stdin input
        if len(sys.argv) == 1 and self.default_command:  # Only script name provided
            # Check if stdin is coming from a pipe or redirection
            has_stdin = False
            try:
                # Check if stdin is a pipe or file (not a terminal)
                stdin_stat = os.fstat(sys.stdin.fileno())
                has_stdin = stat.S_ISFIFO(stdin_stat.st_mode) or stat.S_ISREG(stdin_stat.st_mode)
            except Exception:
                # Fallback to isatty check
                has_stdin = not sys.stdin.isatty()
            
            if has_stdin:
                # Inject the default command into sys.argv
                sys.argv.append(self.default_command)
        
        return super().main(*args, **kwargs)
    
    def resolve_command(self, ctx, args):
        import sys
        import os
        
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
            except Exception as e:
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



@click.group(cls=DefaultGroup, default='speak', context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120})

@click.version_option(version=get_version(), prog_name="GOOBITS TTS CLI")
@click.pass_context

@click.option('--help-json', is_flag=True, callback=show_help_json, is_eager=True, help='Output CLI structure as JSON.', hidden=True)


@click.option('--help-all', is_flag=True, is_eager=True, help='Show help for all commands.', hidden=True)


def main(ctx, help_json=False, help_all=False):
    """🔊 [bold color(6)]GOOBITS TTS CLI v1.1.2[/bold color(6)] - Multi-provider text-to-speech with voice cloning

    
    \b
    [#B3B8C0]Convert text into natural speech with AI-powered auto-selection and real-time streaming.[/#B3B8C0]
    

    
    
    [bold yellow]🚀 Quick Start[/bold yellow]
    
    
    [green]   tts "Hello world"            [/green] [italic][#B3B8C0]# Instantly speak text (default command)[/#B3B8C0][/italic]
    
    
    [green]   tts save "Hello" -o out.mp3  [/green] [italic][#B3B8C0]# Save speech to audio file[/#B3B8C0][/italic]
    
    [green] [/green]
    
    [bold yellow]💡 Core Commands[/bold yellow]
    
    
    [green]   speak   [/green]  🗣️  Speak text aloud (default command)
    
    
    [green]   save    [/green]  💾 Save text as an audio file
    
    
    [green]   voices  [/green]  🔍 Explore and test available voices
    
    [green] [/green]
    
    [bold yellow]🔧 First-time Setup[/bold yellow]
    
    
    [#B3B8C0]   1. Check providers: [/#B3B8C0][green]tts providers[/green]
    
    [#B3B8C0]   2. Set API keys:    [/#B3B8C0][green]tts config set openai_api_key YOUR_KEY[/green]
    [green] [/green]
    
    
    
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
    
    
    # Store global options in context for use by commands
    

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


# Built-in upgrade command (enabled by default)

@main.command()
@click.option('--check', is_flag=True, help='Check for updates without installing')
@click.option('--version', type=str, help='Install specific version')
@click.option('--pre', is_flag=True, help='Include pre-release versions')
@click.option('--dry-run', is_flag=True, help='Show what would be done without doing it')
def upgrade(check, version, pre, dry_run):
    """Upgrade TTS - Text to Speech to the latest version."""
    builtin_upgrade_command(check_only=check, version=version, pre=pre, dry_run=dry_run)




@main.command()
@click.pass_context

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
    help="🎤 Voice selection (e.g., en-GB-SoniaNeural for edge_tts)"
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
    help="🐞 Display debug information during processing"
)

def speak(ctx, text, options, voice, rate, pitch, debug):
    """🗣️  Speak text aloud"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_speak"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'speak'  # Pass command name for all commands
        
        
        kwargs['text'] = text
        
        kwargs['options'] = options
        
        
        
        
        
        
        
        kwargs['voice'] = voice
        
        
        
        
        kwargs['rate'] = rate
        
        
        
        
        kwargs['pitch'] = pitch
        
        
        
        
        kwargs['debug'] = debug
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing speak command...")
        
        
        click.echo(f"  text: {text}")
        
        click.echo(f"  options: {options}")
        
        
        
        
        click.echo(f"  voice: {voice}")
        
        click.echo(f"  rate: {rate}")
        
        click.echo(f"  pitch: {pitch}")
        
        click.echo(f"  debug: {debug}")
        
        
    
    




@main.command()
@click.pass_context

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
    help="🎤 Voice selection (e.g., en-GB-SoniaNeural for edge_tts)"
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
    help="🐞 Display debug information during processing"
)

@click.option("--rate",
    type=str,
    help="⚡ Speech rate adjustment (e.g., +20%, -50%, 150%)"
)

@click.option("--pitch",
    type=str,
    help="🎵 Pitch adjustment (e.g., +5Hz, -10Hz)"
)

def save(ctx, text, options, output, format, voice, clone, json, debug, rate, pitch):
    """💾 Save text as an audio file"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_save"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'save'  # Pass command name for all commands
        
        
        kwargs['text'] = text
        
        kwargs['options'] = options
        
        
        
        
        
        
        
        kwargs['output'] = output
        
        
        
        
        kwargs['format'] = format
        
        
        
        
        kwargs['voice'] = voice
        
        
        
        
        kwargs['clone'] = clone
        
        
        
        
        kwargs['json'] = json
        
        
        
        
        kwargs['debug'] = debug
        
        
        
        
        kwargs['rate'] = rate
        
        
        
        
        kwargs['pitch'] = pitch
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing save command...")
        
        
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
@click.pass_context

@click.argument(
    "ARGS",
    nargs=-1,
    required=False
)


def voices(ctx, args):
    """🔍 Explore and test available voices"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_voices"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'voices'  # Pass command name for all commands
        
        
        kwargs['args'] = args
        
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing voices command...")
        
        
        click.echo(f"  args: {args}")
        
        
        
    
    




@main.command()
@click.pass_context

@click.argument(
    "PROVIDER_NAME",
    required=False
)


def providers(ctx, provider_name):
    """📋 Show available providers and their status"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_providers"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'providers'  # Pass command name for all commands
        
        
        kwargs['provider_name'] = provider_name
        
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing providers command...")
        
        
        click.echo(f"  provider_name: {provider_name}")
        
        
        
    
    




@main.command()
@click.pass_context

@click.argument(
    "ARGS",
    nargs=-1,
    required=False
)


def install(ctx, args):
    """📥 Install required provider dependencies"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_install"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'install'  # Pass command name for all commands
        
        
        kwargs['args'] = args
        
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing install command...")
        
        
        click.echo(f"  args: {args}")
        
        
        
    
    




@main.command()
@click.pass_context

@click.argument(
    "PROVIDER",
    required=False
)


def info(ctx, provider):
    """👀 Detailed provider information"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_info"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'info'  # Pass command name for all commands
        
        
        kwargs['provider'] = provider
        
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing info command...")
        
        
        click.echo(f"  provider: {provider}")
        
        
        
    
    




@main.command()
@click.pass_context

@click.argument(
    "DOCUMENT_PATH"
)

@click.argument(
    "OPTIONS",
    nargs=-1
)


@click.option("--save",
    is_flag=True,
    help="💾 Save audio output to file"
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
    help="🐞 Display debug information during processing"
)

@click.option("--doc-format",
    type=click.Choice(['auto', 'markdown', 'html', 'json']),
    default="auto",
    help="📄 Input document format"
)

@click.option("--ssml-platform",
    type=click.Choice(['azure', 'google', 'amazon', 'generic']),
    default="generic",
    help="🏧️ SSML format platform"
)

@click.option("--emotion-profile",
    type=click.Choice(['technical', 'marketing', 'narrative', 'tutorial', 'auto']),
    default="auto",
    help="🎭 Speech emotion style"
)

@click.option("--rate",
    type=str,
    help="⚡ Speech rate adjustment"
)

@click.option("--pitch",
    type=str,
    help="🎵 Pitch adjustment"
)

def document(ctx, document_path, options, save, output, format, voice, clone, json, debug, doc_format, ssml_platform, emotion_profile, rate, pitch):
    """📖 Convert documents to speech"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_document"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'document'  # Pass command name for all commands
        
        
        kwargs['document_path'] = document_path
        
        kwargs['options'] = options
        
        
        
        
        
        
        
        kwargs['save'] = save
        
        
        
        
        kwargs['output'] = output
        
        
        
        
        kwargs['format'] = format
        
        
        
        
        kwargs['voice'] = voice
        
        
        
        
        kwargs['clone'] = clone
        
        
        
        
        kwargs['json'] = json
        
        
        
        
        kwargs['debug'] = debug
        
        
        
        
        kwargs['doc_format'] = doc_format
        
        
        
        
        kwargs['ssml_platform'] = ssml_platform
        
        
        
        
        kwargs['emotion_profile'] = emotion_profile
        
        
        
        
        kwargs['rate'] = rate
        
        
        
        
        kwargs['pitch'] = pitch
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing document command...")
        
        
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
def voice():
    """🎤 Manage voice loading and caching"""
    pass


@voice.command()
@click.pass_context

@click.argument(
    "VOICE_FILES",
    nargs=-1
)


def load(ctx, voice_files):
    """Load voices into memory for faster access"""
    # Check if hook function exists
    hook_name = f"on_voice_load"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'load'  # Pass command name for all commands
        
        
        kwargs['voice_files'] = voice_files
        
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing load command...")
        
        
        click.echo(f"  voice_files: {voice_files}")
        
        
        

@voice.command()
@click.pass_context

@click.argument(
    "VOICE_FILES",
    nargs=-1,
    required=False
)


@click.option("--all",
    is_flag=True,
    help="🧹 Remove all voices from memory"
)

def unload(ctx, voice_files, all):
    """Remove voices from memory"""
    # Check if hook function exists
    hook_name = f"on_voice_unload"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'unload'  # Pass command name for all commands
        
        
        kwargs['voice_files'] = voice_files
        
        
        
        
        kwargs['all'] = all
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing unload command...")
        
        
        click.echo(f"  voice_files: {voice_files}")
        
        
        
        
        click.echo(f"  all: {all}")
        
        

@voice.command()
@click.pass_context


def status(ctx):
    """Show currently loaded voices and system status"""
    # Check if hook function exists
    hook_name = f"on_voice_status"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'status'  # Pass command name for all commands
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing status command...")
        
        





@main.command()
@click.pass_context


def status(ctx):
    """🩺 Check system and provider health"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_status"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'status'  # Pass command name for all commands
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing status command...")
        
        
    
    




@main.command()
@click.pass_context

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


def config(ctx, action, key, value):
    """🔧 Adjust CLI settings and API keys"""
    
    # Check for built-in commands first
    
    # Standard command - use the existing hook pattern
    hook_name = f"on_config"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        # Prepare arguments including global options
        kwargs = {}
        kwargs['command_name'] = 'config'  # Pass command name for all commands
        
        
        kwargs['action'] = action
        
        kwargs['key'] = key
        
        kwargs['value'] = value
        
        
        
        
        # Add global options from context
        
        
        result = hook_func(**kwargs)
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing config command...")
        
        
        click.echo(f"  action: {action}")
        
        click.echo(f"  key: {key}")
        
        click.echo(f"  value: {value}")
        
        
        
    
    





























def cli_entry():
    """Entry point for the CLI when installed via pipx."""
    # Ignore SIGPIPE to prevent broken pipe errors from terminating the process
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        # SIGPIPE is not available on Windows
        pass
    
    # Load plugins before running the CLI
    load_plugins(main)
    
    try:
        main()
    except KeyboardInterrupt:
        # Exit gracefully on Ctrl+C
        sys.exit(0)
    except BrokenPipeError:
        # Exit gracefully when output pipe is broken
        sys.exit(0)

if __name__ == "__main__":
    cli_entry()