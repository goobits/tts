#!/usr/bin/env python3
"""
Quick CLI Validation Script for TTS

This script runs a subset of the most critical CLI commands to verify
basic functionality is working. Use this for quick smoke testing
during development.

Usage:
    python tests/test_cli_quick.py
    # Or from virtual environment:
    source venv/bin/activate && python tests/test_cli_quick.py
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a CLI command and report results."""
    print(f"🔍 Testing: {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode <= 1:  # Accept 0 (success) or 1 (expected error)
            print(f"   ✅ PASS (exit code: {result.returncode})")
            return True
        else:
            print(f"   ❌ FAIL (exit code: {result.returncode})")
            if result.stderr:
                print(f"   📝 Error: {result.stderr.strip()[:100]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ TIMEOUT (command took too long)")
        return False
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        return False


def main():
    """Run quick CLI validation tests."""
    print("🚀 TTS CLI Quick Validation")
    print("=" * 50)
    
    # Check if tts command is available
    try:
        subprocess.run(['tts', '--version'], capture_output=True, timeout=5)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ ERROR: 'tts' command not found. Install with:")
        print("   source venv/bin/activate && pip install -e .")
        print("   or: ./setup.sh install --dev")
        return False
    
    # Test commands (command, description)
    test_commands = [
        (['tts', '--version'], 'Version display'),
        (['tts', '--help'], 'Main help menu'),
        (['tts', 'providers'], 'List providers'),
        (['tts', 'status'], 'System status'),
        (['tts', 'config', 'show'], 'Configuration display'),
        (['tts', 'info', 'edge_tts'], 'Provider info'),
        (['tts', 'info', '@edge'], 'Provider shortcut'),
        (['tts', 'install'], 'Install help'),
        (['tts', 'speak', '--help'], 'Speak command help'),
        (['tts', 'save', '--help'], 'Save command help'),
        (['tts', 'voice', 'status'], 'Voice status'),
        (['tts', 'document', '--help'], 'Document help'),
    ]
    
    passed = 0
    total = len(test_commands)
    
    print(f"\n📋 Running {total} quick validation tests...\n")
    
    for cmd, description in test_commands:
        if run_command(cmd, description):
            passed += 1
        print()  # Empty line for readability
    
    # Summary
    print("=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! CLI is working correctly.")
        return True
    else:
        failed = total - passed
        print(f"⚠️  {failed} tests failed. Check the output above.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)