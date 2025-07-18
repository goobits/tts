# Shared Setup Framework

A generic, high-performance setup framework for Python projects that provides robust installation, dependency checking, and configuration management.

## Features

- **Multiple Installation Methods**: Support for pipx (recommended), pip, and development mode
- **System Requirements Validation**: Automatic checking of Python version, git, and other dependencies
- **Shell Integration**: Automatic setup of shell aliases and PATH configuration
- **Configuration-Driven**: YAML-based configuration for easy customization
- **Performance Optimized**: Caching and minimal external dependencies
- **Cross-Platform**: Works on Linux, macOS, and Windows (with WSL)

## Project Structure

```
your-project/
├── setup.sh              # Simple wrapper that calls the framework
├── setup-config.yaml     # Project-specific configuration
├── shared-setup/         # The generic framework (synced across projects)
│   ├── setup.sh         # Main framework script
│   └── README.md        # This file
└── sync-framework.sh    # Script to sync framework updates
```

## Configuration

The `setup-config.yaml` file defines project-specific settings:

```yaml
# Package information
package_name: your-package
display_name: "Your Package Display Name"
description: "Package description"

# Python requirements
python:
  minimum_version: "3.8"
  maximum_version: ""  # Empty means no maximum

# Dependencies
dependencies:
  required:
    - git
    - pipx
  optional:
    - curl

# Installation settings
installation:
  pypi_name: your-package  # Name on PyPI
  development_path: "."    # Relative to project root

# Shell integration
shell_integration:
  enabled: true
  alias: "yp"  # Short alias for the command

# Post-installation messages
messages:
  install_success: |
    Your package has been installed successfully!
  install_dev_success: |
    Development mode installed!
  upgrade_success: |
    Upgrade complete!
  uninstall_success: |
    Uninstalled successfully.

# Validation rules
validation:
  check_api_keys: false
  check_disk_space: true
  minimum_disk_space_mb: 100
```

## Usage

### Commands

```bash
# Show help
./setup.sh help

# Install from PyPI
./setup.sh install

# Install in development mode (editable)
./setup.sh install --dev

# Upgrade to latest version
./setup.sh upgrade

# Uninstall
./setup.sh uninstall

# Check installation status
./setup.sh status
```

### Framework Management

The `sync-framework.sh` script provides flexible framework distribution:

#### Basic Usage

```bash
# Sync to current project (default)
./sync-framework.sh

# Sync to specific projects
./sync-framework.sh /path/to/project1 /path/to/project2

# Sync to relative paths
./sync-framework.sh ../another-project ../../different-project
```

#### Advanced Usage

```bash
# Use custom framework source location
SETUP_FRAMEWORK_SOURCE=/path/to/central/framework ./sync-framework.sh

# Show help
./sync-framework.sh --help
```

#### Working Across Different Environments

The sync script automatically adapts to different environments:
- Uses relative paths from the script location
- Accepts both absolute and relative project paths
- Can be run from any directory
- Supports environment variable overrides

This ensures the framework works whether you're on `/workspace`, `/home/miko/projects`, or any other location.

## How It Works

1. **Project Setup Script**: The minimal `setup.sh` in your project root checks for the framework and configuration, then delegates to the framework script.

2. **Framework Script**: The generic `shared-setup/setup.sh` handles all the heavy lifting:
   - Parses the YAML configuration
   - Validates system requirements
   - Manages installations via pipx
   - Sets up shell integration
   - Provides user-friendly output

3. **Configuration Loading**: Uses a pure Bash YAML parser to avoid Python dependencies during setup.

4. **Caching**: System information is cached for 1 hour to improve performance on repeated runs.

## Adding to a New Project

1. Copy the `shared-setup` directory to your project
2. Create a `setup.sh` wrapper script (see example above)
3. Create a `setup-config.yaml` with your project settings
4. Add the project path to `sync-framework.sh` for future updates

## Benefits

- **Consistency**: Same setup experience across all projects
- **Maintainability**: Fix bugs or add features in one place
- **Performance**: Optimized for speed with caching and minimal dependencies
- **User-Friendly**: Clear error messages and helpful suggestions
- **Flexibility**: Easy to customize per project via configuration

## Requirements

- Bash 4.0+
- Python 3.8+ (for YAML parsing during setup)
- pipx (recommended) or pip
- git

## License

This framework is designed to be copied and used in your projects. No attribution required.