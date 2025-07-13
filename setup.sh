#!/bin/bash

# TTS CLI Setup Script
# Global installation/uninstallation script using pipx

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project info
PROJECT_NAME="TTS CLI"
PACKAGE_NAME="tts-cli"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_banner() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}    TTS CLI Setup Script${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_requirements() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command -v pipx &> /dev/null; then
        print_error "pipx is required but not installed"
        print_info "Install with: python3 -m pip install --user pipx"
        print_info "Then run: python3 -m pipx ensurepath"
        print_info "Or on Ubuntu/Debian: sudo apt install pipx"
        exit 1
    fi
}

install_tts() {
    print_banner
    print_info "Installing $PROJECT_NAME globally with pipx..."
    
    check_requirements
    
    # Remove existing installation if it exists
    if pipx list | grep -q "tts-cli"; then
        print_info "Removing existing installation..."
        pipx uninstall tts-cli &> /dev/null || true
    fi
    
    # Install package globally using pipx
    print_info "Installing package in editable mode..."
    if pipx install -e "$SCRIPT_DIR"; then
        print_success "Package installed successfully"
    else
        print_error "Package installation failed"
        exit 1
    fi
    
    # Install required dependencies
    print_info "Installing edge-tts dependency..."
    if pipx inject tts-cli edge-tts; then
        print_success "Dependencies installed successfully"
    else
        print_error "Dependency installation failed"
        exit 1
    fi
    
    # Test installation
    print_info "Testing installation..."
    if command -v tts &> /dev/null && tts --help &> /dev/null; then
        print_success "Installation test passed"
    else
        print_error "Installation test failed - tts command not available"
        print_warning "You may need to restart your shell or run: pipx ensurepath"
        exit 1
    fi
    
    echo
    print_success "Installation complete!"
    print_info "Usage: tts \"Hello, world!\""
    print_info "Help:  tts --help"
    print_info ""
    print_info "The 'tts' command is now globally available and will stream by default."
    print_info "Use 'tts --save \"text\"' to save to a file instead."
}

uninstall_tts() {
    print_banner
    print_info "Uninstalling $PROJECT_NAME..."
    
    # Check if pipx is available
    if ! command -v pipx &> /dev/null; then
        print_warning "pipx not found, checking for manual cleanup..."
    else
        # Uninstall using pipx
        if pipx list | grep -q "tts-cli"; then
            print_info "Removing pipx installation..."
            pipx uninstall tts-cli
            print_success "Pipx installation removed"
        else
            print_warning "No pipx installation found"
        fi
    fi
    
    # Clean up logs
    if [ -d "$SCRIPT_DIR/logs" ]; then
        print_info "Cleaning up log files..."
        rm -rf "$SCRIPT_DIR/logs"
        print_success "Log files removed"
    fi
    
    # Clean up cache
    if [ -d "$SCRIPT_DIR/__pycache__" ]; then
        find "$SCRIPT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        print_success "Cache files removed"
    fi
    
    # Clean up local venv if it exists
    if [ -d "$SCRIPT_DIR/venv" ]; then
        print_info "Removing local virtual environment..."
        rm -rf "$SCRIPT_DIR/venv"
        print_success "Local virtual environment removed"
    fi
    
    # Clean up wrapper script if it exists
    if [ -f "$SCRIPT_DIR/tts" ]; then
        print_info "Removing wrapper script..."
        rm -f "$SCRIPT_DIR/tts"
        print_success "Wrapper script removed"
    fi
    
    echo
    print_success "Uninstallation complete!"
    print_info "The 'tts' command has been removed from your system."
}

dev_install() {
    print_banner
    print_info "Setting up $PROJECT_NAME for development..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! python3 -m venv --help &> /dev/null; then
        print_error "python3-venv is required but not installed"
        print_info "Install with: sudo apt-get install python3-venv"
        exit 1
    fi
    
    # Create virtual environment
    local venv_path="$SCRIPT_DIR/venv"
    if [ ! -d "$venv_path" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv "$venv_path"
        print_success "Virtual environment created"
    else
        print_info "Using existing virtual environment"
    fi
    
    # Install in development mode
    print_info "Installing in development mode..."
    "$venv_path/bin/pip" install --upgrade pip
    "$venv_path/bin/pip" install -e "$SCRIPT_DIR"
    "$venv_path/bin/pip" install edge-tts
    
    print_success "Development setup complete!"
    print_info "Activate with: source $venv_path/bin/activate"
    print_info "Then run: tts \"Hello, world!\""
}

show_help() {
    print_banner
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  install     Install TTS CLI globally using pipx"
    echo "  uninstall   Uninstall TTS CLI and clean up"
    echo "  dev         Set up local development environment"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 install      # Install globally (recommended)"
    echo "  $0 dev          # Development setup with local venv"
    echo "  $0 uninstall    # Remove installation"
    echo
    echo "The 'install' command creates a global 'tts' command that streams by default."
    echo "Use 'tts --save \"text\"' to save to file instead of streaming."
    echo
}

main() {
    case "${1:-}" in
        "install")
            install_tts
            ;;
        "uninstall")
            uninstall_tts
            ;;
        "dev")
            dev_install
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

main "$@"