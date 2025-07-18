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

# Detect shell and set RC file
detect_shell() {
    local detected_shell=""
    if [[ -n "$ZSH_VERSION" ]]; then
        detected_shell="zsh"
        echo "Detected: zsh"
    elif [[ -n "$BASH_VERSION" ]]; then
        detected_shell="bash"
        echo "Detected: bash"
    elif [[ "$SHELL" == *"fish"* ]]; then
        detected_shell="fish"
        echo "Detected: fish"
    else
        echo -e "${YELLOW}Warning: Could not detect shell. Defaulting to bash${NC}"
        detected_shell="bash"
    fi
    export DETECTED_SHELL="$detected_shell"
}

# Refresh shell environment to make tts command available immediately
refresh_shell_environment() {
    print_info "Refreshing shell environment..."
    
    # Ensure pipx path is in current PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Try to reload shell configuration
    case "$DETECTED_SHELL" in
        "zsh")
            if [[ -f "$HOME/.zshrc" ]]; then
                source "$HOME/.zshrc" 2>/dev/null || true
            fi
            ;;
        "bash")
            if [[ -f "$HOME/.bashrc" ]]; then
                source "$HOME/.bashrc" 2>/dev/null || true
            fi
            ;;
        "fish")
            # Fish doesn't source config files the same way
            # Just ensure PATH is updated for current session
            if [[ -d "$HOME/.local/bin" ]]; then
                export PATH="$HOME/.local/bin:$PATH"
            fi
            ;;
    esac
    
    # Verify tts command is now available
    if command -v tts >/dev/null 2>&1; then
        print_success "TTS command is now available in current session"
        return 0
    else
        print_warning "TTS command not immediately available - may need shell restart"
        return 1
    fi
}

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

# Spinner for long operations
with_spinner() {
    local pid=$!
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local temp
    printf "${BLUE}%s${NC}" "$1"
    while ps -p $pid > /dev/null 2>&1; do
        temp=${spinstr#?}
        printf " [%c]" "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b"
    done
    printf "    \b\b\b\b"
    wait $pid
    return $?
}

check_pipx() {
    if ! command -v pipx &> /dev/null; then
        print_info "Installing pipx..."
        if command -v python3 &> /dev/null; then
            (python3 -m pip install --user pipx && python3 -m pipx ensurepath) &> /dev/null &
            with_spinner "Installing pipx"
            print_success "Pipx installed"
        else
            print_error "Python 3 is required but not installed"
            exit 1
        fi
    else
        print_success "Pipx is available"
    fi
}

# Check Python version meets minimum requirements
check_python_version() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    
    if [ "$python_version" != "unknown" ]; then
        print_info "Detected Python $python_version"
    fi
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_error "Python 3.8+ required for TTS features (found $python_version)"
        echo "Please upgrade your Python installation"
        exit 1
    fi
    
    print_success "Python version check passed"
}

# Check for TTS-specific dependency conflicts
check_tts_conflicts() {
    print_info "Checking for TTS dependency conflicts..."
    
    local conflicts_found=false
    local warning_packages=()
    
    # Check for conflicting TTS/audio packages
    local conflict_packages=(
        "gTTS==2.0.*"           # Very old gTTS versions
        "edge-tts==4.*"         # Older edge-tts versions  
        "pyttsx3==2.6*"         # Old pyttsx3 versions
        "espeak==1.4*"          # Old espeak bindings
        "torch==1.1*"           # Very old PyTorch for voice cloning
    )
    
    # Check for packages that might conflict with TTS dependencies
    for package in "${conflict_packages[@]}"; do
        local pkg_name="${package%%==*}"  # Extract package name before ==
        
        if python3 -m pip show "$pkg_name" >/dev/null 2>&1; then
            local installed_version
            installed_version=$(python3 -m pip show "$pkg_name" 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
            
            # Check if this version might conflict
            case "$package" in
                "gTTS==2.0.*")
                    if [[ "$installed_version" =~ ^2\.0\. ]]; then
                        warning_packages+=("$pkg_name ($installed_version) - recommend upgrading to 2.3+")
                        conflicts_found=true
                    fi
                    ;;
                "edge-tts==4.*")
                    if [[ "$installed_version" =~ ^4\. ]]; then
                        warning_packages+=("$pkg_name ($installed_version) - recommend upgrading to 6.0+")
                        conflicts_found=true
                    fi
                    ;;
                "pyttsx3==2.6*")
                    if [[ "$installed_version" =~ ^2\.6 ]]; then
                        warning_packages+=("$pkg_name ($installed_version) - may cause audio driver conflicts")
                        conflicts_found=true
                    fi
                    ;;
                "torch==1.1*")
                    if [[ "$installed_version" =~ ^1\.1 ]]; then
                        warning_packages+=("$pkg_name ($installed_version) - too old for voice cloning features")
                        conflicts_found=true
                    fi
                    ;;
            esac
        fi
    done
    
    # Check for audio system conflicts on Linux
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Check if pulseaudio and pipewire are both running (can cause conflicts)
        if pgrep -x pulseaudio >/dev/null && pgrep -x pipewire >/dev/null; then
            print_warning "Both PulseAudio and PipeWire detected - may cause audio conflicts"
            echo "Consider using only one audio system for optimal TTS performance"
        fi
    fi
    
    if [ "$conflicts_found" = true ]; then
        print_warning "Potential TTS dependency conflicts detected:"
        for warning in "${warning_packages[@]}"; do
            echo "  ⚠️  $warning"
        done
        echo
        echo "These packages may cause TTS compatibility issues. Consider upgrading them:"
        for warning in "${warning_packages[@]}"; do
            local pkg_name="${warning%% (*}"  # Extract package name before space
            echo "  pip install --upgrade $pkg_name"
        done
        echo
        echo -n "Continue with TTS installation anyway? [y/N]: "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Installation cancelled. Please resolve TTS conflicts first."
            exit 1
        fi
    else
        print_success "No TTS dependency conflicts detected"
    fi
}

# Check audio system for TTS functionality
check_audio_system() {
    print_info "Checking audio system compatibility..."
    
    local audio_warnings=()
    local audio_working=false
    
    # Check if we're in a headless environment
    if [[ -z "$DISPLAY" ]] && [[ -z "$WAYLAND_DISPLAY" ]] && [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_warning "Headless environment detected - audio output may be limited"
        echo "TTS will work but audio playback may require configuration"
    fi
    
    # Check for audio output devices on Linux
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Check for ALSA
        if command -v aplay &> /dev/null; then
            if aplay -l 2>/dev/null | grep -q "card [0-9]"; then
                print_success "ALSA audio devices detected"
                audio_working=true
            else
                audio_warnings+=("No ALSA audio devices found")
            fi
        fi
        
        # Check for PulseAudio
        if command -v pactl &> /dev/null; then
            if pactl info &>/dev/null; then
                print_success "PulseAudio is running"
                audio_working=true
            else
                audio_warnings+=("PulseAudio not running")
            fi
        fi
        
        # Check for PipeWire
        if command -v pw-cli &> /dev/null; then
            if pgrep -x pipewire &>/dev/null; then
                print_success "PipeWire is running"
                audio_working=true
            fi
        fi
        
        # Check for audio groups (common requirement)
        if ! groups | grep -E "(audio|pulse|pipewire)" &>/dev/null; then
            audio_warnings+=("User not in audio groups - may need to add to 'audio' group")
        fi
    fi
    
    # Check for macOS audio
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v afplay &> /dev/null; then
            print_success "macOS audio system available"
            audio_working=true
        fi
    fi
    
    # Check for Windows audio (in WSL or similar)
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || grep -qi microsoft /proc/version 2>/dev/null; then
        print_info "Windows/WSL environment detected"
        echo "Audio may require additional configuration for TTS playback"
    fi
    
    # Report warnings if any
    if [ ${#audio_warnings[@]} -gt 0 ]; then
        print_warning "Audio system issues detected:"
        for warning in "${audio_warnings[@]}"; do
            echo "  ⚠️  $warning"
        done
        echo
        echo "TTS text processing will work, but audio playback may have issues"
        echo "You can still use TTS with --save flag to create audio files"
    fi
    
    if [ "$audio_working" = true ]; then
        print_success "Audio system check passed"
    else
        print_info "Audio system check completed with warnings"
    fi
}

# Check for voice cloning requirements (GPU detection)
check_voice_cloning_support() {
    print_info "Checking voice cloning support..."
    
    # Check for NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &>/dev/null; then
            print_success "NVIDIA GPU detected - voice cloning with GPU acceleration available"
            echo "Use: tts install chatterbox --gpu"
        else
            print_info "nvidia-smi found but GPU not accessible"
        fi
    fi
    
    # Check for AMD GPU on Linux
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v rocm-smi &> /dev/null; then
        if rocm-smi &>/dev/null; then
            print_success "AMD GPU with ROCm detected - voice cloning may be supported"
        fi
    fi
    
    # Check available memory for CPU-based voice cloning
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        local mem_gb
        mem_gb=$(free -g | awk '/^Mem:/{print $2}')
        if [ "$mem_gb" -ge 8 ]; then
            print_success "Sufficient RAM ($mem_gb GB) for CPU-based voice cloning"
        else
            print_warning "Limited RAM ($mem_gb GB) - voice cloning may be slow"
        fi
    fi
    
    # Check for PyTorch availability
    if python3 -c "import torch; print('PyTorch version:', torch.__version__)" 2>/dev/null; then
        print_success "PyTorch available for advanced TTS features"
    else
        print_info "PyTorch not found - install for voice cloning: pip install torch"
    fi
}

# Fallback installation using pip when pipx fails
install_fallback() {
    print_warning "pipx installation failed, trying pip fallback..."
    
    # Create ~/.local/bin if it doesn't exist
    local LOCAL_BIN="$HOME/.local/bin"
    mkdir -p "$LOCAL_BIN"
    
    # Install with pip --user
    print_info "Installing with pip --user..."
    if python3 -m pip install --user "$SCRIPT_DIR"; then
        print_success "Package installed with pip"
    else
        print_error "pip installation also failed"
        exit 1
    fi
    
    # Create wrapper script if tts command not found
    if ! command -v tts &> /dev/null; then
        print_info "Creating tts command wrapper..."
        local TTS_WRAPPER="$LOCAL_BIN/tts"
        cat > "$TTS_WRAPPER" << 'EOF'
#!/bin/bash
python3 -m tts_cli "$@"
EOF
        chmod +x "$TTS_WRAPPER"
        print_success "Created tts command wrapper"
    fi
    
    # Check PATH
    if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
        print_warning "~/.local/bin is not in your PATH"
        echo "Add this to your shell profile (.bashrc, .zshrc, etc.):"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
}

# Fallback development installation using pip when pipx fails
install_dev_fallback() {
    print_warning "pipx development installation failed, trying pip fallback..."
    
    # Create ~/.local/bin if it doesn't exist
    local LOCAL_BIN="$HOME/.local/bin"
    mkdir -p "$LOCAL_BIN"
    
    # Install in editable mode with pip --user
    print_info "Installing in editable mode with pip --user..."
    if python3 -m pip install --user -e "$SCRIPT_DIR"; then
        print_success "Development package installed with pip"
    else
        print_error "pip development installation also failed"
        exit 1
    fi
    
    # Create wrapper script if tts command not found
    if ! command -v tts &> /dev/null; then
        print_info "Creating tts command wrapper..."
        local TTS_WRAPPER="$LOCAL_BIN/tts"
        cat > "$TTS_WRAPPER" << 'EOF'
#!/bin/bash
python3 -m tts_cli "$@"
EOF
        chmod +x "$TTS_WRAPPER"
        print_success "Created tts command wrapper"
    fi
    
    # Check PATH
    if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
        print_warning "~/.local/bin is not in your PATH"
        echo "Add this to your shell profile (.bashrc, .zshrc, etc.):"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
}

install_tts() {
    print_banner
    print_info "Installing $PROJECT_NAME with pipx..."
    
    detect_shell
    check_python_version
    check_tts_conflicts
    check_audio_system
    check_voice_cloning_support
    check_pipx
    
    # Remove existing installation if it exists
    if pipx list | grep -q "tts-cli"; then
        print_info "Removing existing installation..."
        pipx uninstall tts-cli &> /dev/null || true
    fi
    
    # Install package using pipx
    pipx install "$SCRIPT_DIR" &> /dev/null &
    with_spinner "Installing TTS CLI package"
    if wait $!; then
        print_success "Package installed successfully"
    else
        install_fallback
    fi
    
    # Refresh shell environment to make tts available immediately
    refresh_shell_environment
    
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
    
    detect_shell
    check_python_version
    check_tts_conflicts
    check_audio_system
    check_voice_cloning_support
    check_pipx
    
    # Remove existing installation if it exists
    if pipx list | grep -q "tts-cli"; then
        print_info "Removing existing installation..."
        pipx uninstall tts-cli &> /dev/null || true
    fi
    
    # Install in editable mode
    pipx install -e "$SCRIPT_DIR" &> /dev/null &
    with_spinner "Installing in development mode"
    if wait $!; then
        print_success "Development installation complete"
    else
        install_dev_fallback
    fi
    
    # Refresh shell environment to make tts available immediately
    refresh_shell_environment
    
    print_info "Package installed in editable mode - changes will be reflected immediately"
}

upgrade_tts() {
    print_banner
    print_info "Upgrading $PROJECT_NAME to latest version..."
    
    detect_shell
    check_python_version
    check_tts_conflicts
    check_audio_system
    check_voice_cloning_support
    
    if command -v pipx &> /dev/null && pipx list | grep -q "tts-cli"; then
        pipx upgrade tts-cli &> /dev/null &
        with_spinner "Upgrading TTS CLI"
        if wait $!; then
            print_success "TTS CLI upgraded successfully!"
        else
            print_error "Upgrade failed"
            exit 1
        fi
    else
        print_warning "No pipx installation found to upgrade"
        echo "Upgrade is only supported for pipx installations"
        echo "For other installation methods, please uninstall and reinstall:"
        echo "  $0 uninstall"
        echo "  $0 install"
        exit 1
    fi
    
    # Refresh shell environment to make tts available immediately
    refresh_shell_environment
    
    # Test installation
    print_info "Testing upgraded installation..."
    if command -v tts &> /dev/null && tts --help &> /dev/null; then
        print_success "Upgrade test passed"
    else
        print_error "Upgrade test failed - tts command not available"
        exit 1
    fi
    
    echo
    print_success "Upgrade complete!"
    print_info "Usage: tts \"Hello, upgraded world!\""
    print_info "Check system: tts doctor"
    print_info "Help: tts --help"
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
    echo "  upgrade     Upgrade existing installation to latest version"
    echo "  uninstall   Uninstall TTS CLI"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 install      # Install with pipx (recommended)"
    echo "  $0 dev          # Development setup with editable install"
    echo "  $0 upgrade      # Upgrade to latest version"
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
        "upgrade")
            upgrade_tts
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