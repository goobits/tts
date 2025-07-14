#!/bin/bash

# TTS CLI Setup Script - PipX Version
# Modern installation using pipx for proper isolation

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
    echo -e "${BLUE}    Modern PipX Installation${NC}"
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

check_pipx() {
    if ! command -v pipx &> /dev/null; then
        print_info "Installing pipx..."
        if command -v python3 &> /dev/null; then
            python3 -m pip install --user pipx
            python3 -m pipx ensurepath
            print_success "Pipx installed"
        else
            print_error "Python 3 is required but not installed"
            exit 1
        fi
    else
        print_success "Pipx is available"
    fi
}

install_tts() {
    print_banner
    print_info "Installing $PROJECT_NAME with pipx..."
    
    check_pipx
    
    # Remove existing installation if it exists
    if pipx list | grep -q "tts-cli"; then
        print_info "Removing existing installation..."
        pipx uninstall tts-cli &> /dev/null || true
    fi
    
    # Install package using pipx
    print_info "Installing package..."
    if pipx install "$SCRIPT_DIR"; then
        print_success "Package installed successfully"
    else
        print_error "Package installation failed"
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
    print_info "Check system: tts doctor"
    print_info "Install providers: tts install chatterbox --gpu"
    print_info "Help: tts --help"
}

dev_install() {
    print_banner
    print_info "Installing $PROJECT_NAME in development mode..."
    
    check_pipx
    
    # Remove existing installation if it exists
    if pipx list | grep -q "tts-cli"; then
        print_info "Removing existing installation..."
        pipx uninstall tts-cli &> /dev/null || true
    fi
    
    # Install in editable mode
    print_info "Installing in editable mode..."
    if pipx install -e "$SCRIPT_DIR"; then
        print_success "Development installation complete"
    else
        print_error "Development installation failed"
        exit 1
    fi
    
    print_info "Package installed in editable mode - changes will be reflected immediately"
}

uninstall_tts() {
    print_banner
    print_info "Uninstalling $PROJECT_NAME..."
    
    if command -v pipx &> /dev/null && pipx list | grep -q "tts-cli"; then
        print_info "Removing pipx installation..."
        pipx uninstall tts-cli
        print_success "TTS CLI uninstalled"
    else
        print_warning "No pipx installation found"
    fi
    
    echo
    print_success "Uninstallation complete!"
    print_info "The 'tts' command has been removed from your system."
}

show_help() {
    print_banner
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  install     Install TTS CLI using pipx"
    echo "  dev         Install in development mode (editable)"
    echo "  uninstall   Uninstall TTS CLI"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 install      # Install with pipx (recommended)"
    echo "  $0 dev          # Development setup with editable install"
    echo "  $0 uninstall    # Remove installation"
    echo
    echo "After installation:"
    echo "  tts doctor               # Check system capabilities"
    echo "  tts install chatterbox --gpu  # Add GPU voice cloning"
    echo "  tts \"Hello world\"        # Basic usage"
}

main() {
    case "${1:-}" in
        "install")
            install_tts
            ;;
        "dev")
            dev_install
            ;;
        "uninstall")
            uninstall_tts
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