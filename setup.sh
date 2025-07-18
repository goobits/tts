#!/bin/bash
# TTS Setup Script - Uses Shared Framework with TTS-Specific Validation
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_SCRIPT="$SCRIPT_DIR/ttt/shared-setup/setup.sh"

# Check if framework exists
if [[ ! -f "$FRAMEWORK_SCRIPT" ]]; then
    echo "❌ Setup framework not found in this project's 'ttt/shared-setup' directory."
    echo "Please run: cd ../ttt && ./sync-framework.sh ../tts"
    exit 1
fi

# Check if configuration exists
if [[ ! -f "$SCRIPT_DIR/setup-config.yaml" ]]; then
    echo "❌ Configuration file setup-config.yaml not found."
    exit 1
fi

# TTS-specific pre-installation checks
run_tts_checks() {
    echo "🎵 Running TTS-specific validation..."

    # Check for TTS dependency conflicts
    echo "  Checking TTS dependencies..."
    python3 -c "
import subprocess
import sys

# Check for known problematic packages
conflicts = []
try:
    result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                          capture_output=True, text=True, check=True)
    installed = result.stdout.lower()
    
    if 'gtts' in installed and '2.0.' in installed:
        conflicts.append('gTTS 2.0.x (recommend upgrading to 2.3+)')
    if 'edge-tts' in installed and '4.' in installed:
        conflicts.append('edge-tts 4.x (recommend upgrading to 6.0+)')
        
    if conflicts:
        print('⚠️  Potential TTS conflicts detected:')
        for conflict in conflicts:
            print(f'   - {conflict}')
        print('Consider upgrading these packages before installation.')
    else:
        print('✅ No TTS dependency conflicts detected')
        
except Exception:
    print('ℹ️  Could not check TTS dependencies (continuing anyway)')
" 2>/dev/null || echo "  ℹ️  TTS dependency check skipped"

    # Check audio system
    echo "  Checking audio system..."
    audio_found=false

    if command -v pactl &>/dev/null && pactl info &>/dev/null; then
        echo "  ✅ PulseAudio detected"
        audio_found=true
    fi

    if command -v aplay &>/dev/null && aplay -l 2>/dev/null | grep -q "card"; then
        echo "  ✅ ALSA audio devices detected"
        audio_found=true
    fi

    if [[ "$OSTYPE" == "darwin"* ]] && command -v afplay &>/dev/null; then
        echo "  ✅ macOS audio system available"
        audio_found=true
    fi

    if [[ "$audio_found" == "false" ]]; then
        echo "  ⚠️  No audio system detected - TTS will work but audio playback may be limited"
    fi

    # Check for GPU capabilities
    echo "  Checking voice cloning support..."
    if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
        echo "  ✅ NVIDIA GPU detected - voice cloning with GPU acceleration available"
    elif python3 -c "import torch; print('✅ PyTorch available for voice cloning')" 2>/dev/null; then
        echo "  ✅ PyTorch available for CPU-based voice cloning"
    else
        echo "  ℹ️  Install PyTorch for voice cloning: pip install torch"
    fi

    echo "✅ TTS validation complete"
}

# Run TTS checks for install/upgrade commands
if [[ "$1" == "install" ]] || [[ "$1" == "upgrade" ]]; then
    run_tts_checks
fi

# Execute the framework, passing along all arguments
exec "$FRAMEWORK_SCRIPT" "$@"