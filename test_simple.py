#!/usr/bin/env python3
"""Simple test runner for basic functionality testing without pytest."""

import sys
import traceback

def run_simple_tests():
    """Run basic tests without pytest to verify functionality."""
    
    print("🧪 Running Simple TTS CLI Tests")
    print("================================")
    
    test_count = 0
    pass_count = 0
    fail_count = 0
    
    def run_test(test_name, test_func):
        nonlocal test_count, pass_count, fail_count
        test_count += 1
        
        try:
            test_func()
            print(f"✅ {test_name}")
            pass_count += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            print(f"   {traceback.format_exc().split('Traceback')[1].strip()}")
            fail_count += 1
    
    # Test 1: Configuration parsing
    print("\n📋 Configuration Tests:")
    
    def test_parse_env_value_bool():
        from tts_cli.config import _parse_env_value
        assert _parse_env_value("true", bool) is True
        assert _parse_env_value("false", bool) is False
        assert _parse_env_value("1", bool) is True
        assert _parse_env_value("0", bool) is False
    
    def test_parse_voice_setting():
        from tts_cli.config import parse_voice_setting
        provider, voice = parse_voice_setting("edge_tts:en-US-JennyNeural")
        assert provider == "edge_tts"
        assert voice == "en-US-JennyNeural"
        
        provider, voice = parse_voice_setting("voice.wav")
        assert provider == "chatterbox"
        assert voice == "voice.wav"
    
    def test_validate_api_key():
        from tts_cli.config import validate_api_key
        assert validate_api_key("openai", "sk-1234567890abcdef1234567890abcdef12345678") is True
        assert validate_api_key("openai", "invalid") is False
    
    def test_ssml_processing():
        from tts_cli.config import is_ssml, strip_ssml_tags
        assert is_ssml("<speak>Hello</speak>") is True
        assert is_ssml("Hello world") is False
        assert strip_ssml_tags("<speak>Hello <break time='1s'/> world</speak>") == "Hello  world"
    
    run_test("Environment value parsing", test_parse_env_value_bool)
    run_test("Voice setting parsing", test_parse_voice_setting)
    run_test("API key validation", test_validate_api_key)
    run_test("SSML processing", test_ssml_processing)
    
    # Test 2: Exception handling
    print("\n🚨 Exception Tests:")
    
    def test_exception_hierarchy():
        from tts_cli.exceptions import TTSError, AuthenticationError, RateLimitError
        assert issubclass(AuthenticationError, TTSError)
        assert issubclass(RateLimitError, TTSError)
    
    def test_http_error_mapping():
        from tts_cli.exceptions import map_http_error, AuthenticationError, RateLimitError
        error = map_http_error(401)
        assert isinstance(error, AuthenticationError)
        
        error = map_http_error(429)
        assert isinstance(error, RateLimitError)
    
    run_test("Exception hierarchy", test_exception_hierarchy)
    run_test("HTTP error mapping", test_http_error_mapping)
    
    # Test 3: Voice analysis
    print("\n🎤 Voice Analysis Tests:")
    
    def test_voice_analysis():
        from tts_cli.voice_browser import analyze_voice
        quality, region, gender = analyze_voice("edge_tts", "en-US-JennyNeural")
        assert quality == 3  # Neural = high quality
        assert region == "American"
        assert gender == "F"
    
    run_test("Voice analysis", test_voice_analysis)
    
    # Test 4: Input parsing
    print("\n📝 Input Parsing Tests:")
    
    def test_input_parsing():
        from tts_cli.tts import parse_input
        text, params = parse_input('{"text": "Hello", "voice": "nova"}')
        assert text == "Hello"
        assert params["voice"] == "nova"
        
        text, params = parse_input("Plain text")
        assert text == "Plain text"
        assert params == {}
    
    run_test("Input parsing", test_input_parsing)
    
    # Test 5: Audio utilities (basic)
    print("\n🔊 Audio Utilities Tests:")
    
    def test_cleanup_file():
        import tempfile
        import os
        from tts_cli.audio_utils import cleanup_file
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"test")
        
        assert os.path.exists(temp_path)
        cleanup_file(temp_path)
        assert not os.path.exists(temp_path)
    
    run_test("File cleanup", test_cleanup_file)
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Total tests: {test_count}")
    print(f"   Passed: {pass_count} ✅")
    print(f"   Failed: {fail_count} ❌")
    
    if fail_count == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n💥 {fail_count} test(s) failed!")
        return 1

if __name__ == "__main__":
    sys.exit(run_simple_tests())