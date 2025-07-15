"""Tests for voice analysis and metadata extraction.

These tests cover the voice analysis logic that extracts quality,
region, and gender information from voice names across different
providers. Tests pure business logic without external dependencies.
"""

import pytest
from tts_cli.voice_browser import analyze_voice


class TestVoiceQualityAnalysis:
    """Test voice quality assessment based on name patterns."""
    
    def test_high_quality_indicators(self):
        """Test detection of high-quality voice indicators."""
        high_quality_voices = [
            ("edge_tts", "en-US-JennyNeural"),
            ("edge_tts", "en-GB-LibbyNeural"),
            ("google", "en-US-Neural2-A"),
            ("provider", "voice-premium"),
            ("provider", "StandardVoice"),
            ("provider", "NEURAL-voice"),
        ]
        
        for provider, voice in high_quality_voices:
            quality, _, _ = analyze_voice(provider, voice)
            assert quality == 3, f"Voice '{voice}' should be detected as high quality (3)"
    
    def test_medium_quality_default(self):
        """Test that unknown voices default to medium quality."""
        medium_quality_voices = [
            ("edge_tts", "en-US-Jenny"),
            ("openai", "nova"),
            ("elevenlabs", "Rachel"),
            ("provider", "random-voice"),
            ("provider", "VoiceName"),
        ]
        
        for provider, voice in medium_quality_voices:
            quality, _, _ = analyze_voice(provider, voice)
            assert quality == 2, f"Voice '{voice}' should default to medium quality (2)"
    
    def test_low_quality_indicators(self):
        """Test detection of low-quality voice indicators."""
        low_quality_voices = [
            ("provider", "basic-voice"),
            ("provider", "LowQuality"),
            ("provider", "voice-basic"),
            ("provider", "BASIC-VOICE"),
        ]
        
        for provider, voice in low_quality_voices:
            quality, _, _ = analyze_voice(provider, voice)
            assert quality == 1, f"Voice '{voice}' should be detected as low quality (1)"
    
    def test_case_insensitive_quality_detection(self):
        """Test that quality detection is case-insensitive."""
        test_cases = [
            ("NEURAL", 3),
            ("neural", 3),
            ("Neural", 3),
            ("PREMIUM", 3),
            ("premium", 3),
            ("Premium", 3),
            ("BASIC", 1),
            ("basic", 1),
            ("Basic", 1),
        ]
        
        for voice_part, expected_quality in test_cases:
            quality, _, _ = analyze_voice("provider", f"voice-{voice_part}")
            assert quality == expected_quality, f"Voice with '{voice_part}' should have quality {expected_quality}"


class TestVoiceRegionAnalysis:
    """Test voice region detection based on name patterns."""
    
    def test_irish_region_detection(self):
        """Test detection of Irish English voices."""
        irish_voices = [
            "en-IE-EmilyNeural",
            "en-IE-Connor",
            "voice-Irish",
            "IrishAccent",
        ]
        
        for voice in irish_voices:
            _, region, _ = analyze_voice("edge_tts", voice)
            assert region == "Irish", f"Voice '{voice}' should be detected as Irish"
    
    def test_british_region_detection(self):
        """Test detection of British English voices."""
        british_voices = [
            "en-GB-LibbyNeural",
            "en-GB-Ryan",
            "en-UK-Voice",
            "voice-British",
            "BritishAccent",
        ]
        
        for voice in british_voices:
            _, region, _ = analyze_voice("edge_tts", voice)
            assert region == "British", f"Voice '{voice}' should be detected as British"
    
    def test_american_region_detection(self):
        """Test detection of American English voices."""
        american_voices = [
            "en-US-JennyNeural",
            "en-US-Brandon",
            "voice-American",
            "AmericanAccent",
        ]
        
        for voice in american_voices:
            _, region, _ = analyze_voice("edge_tts", voice)
            assert region == "American", f"Voice '{voice}' should be detected as American"
    
    def test_australian_region_detection(self):
        """Test detection of Australian English voices."""
        australian_voices = [
            "en-AU-NatashaNeural",
            "en-AU-William",
            "voice-Australian",
            "AustralianAccent",
        ]
        
        for voice in australian_voices:
            _, region, _ = analyze_voice("edge_tts", voice)
            assert region == "Australian", f"Voice '{voice}' should be detected as Australian"
    
    def test_canadian_region_detection(self):
        """Test detection of Canadian English voices."""
        canadian_voices = [
            "en-CA-ClaraNeural",
            "en-CA-Liam",
            "voice-Canadian",
            "CanadianAccent",
        ]
        
        for voice in canadian_voices:
            _, region, _ = analyze_voice("edge_tts", voice)
            assert region == "Canadian", f"Voice '{voice}' should be detected as Canadian"
    
    def test_indian_region_detection(self):
        """Test detection of Indian English voices."""
        indian_voices = [
            "en-IN-NeerjaNeural",
            "en-IN-Prabhat",
            "voice-Indian",
            "IndianAccent",
        ]
        
        for voice in indian_voices:
            _, region, _ = analyze_voice("edge_tts", voice)
            assert region == "Indian", f"Voice '{voice}' should be detected as Indian"
    
    def test_chatterbox_region_detection(self):
        """Test that chatterbox provider voices are detected as Chatterbox region."""
        chatterbox_voices = [
            "my_voice.wav",
            "custom_voice.mp3",
            "speaker_model",
            "whatever_name",
        ]
        
        for voice in chatterbox_voices:
            _, region, _ = analyze_voice("chatterbox", voice)
            assert region == "Chatterbox", f"Chatterbox voice '{voice}' should be detected as Chatterbox region"
    
    def test_general_region_default(self):
        """Test that unknown regions default to General."""
        general_voices = [
            ("openai", "nova"),
            ("elevenlabs", "Rachel"),
            ("google", "voice-without-region"),
            ("edge_tts", "unknown-voice"),
        ]
        
        for provider, voice in general_voices:
            if provider != "chatterbox":  # Chatterbox has special handling
                _, region, _ = analyze_voice(provider, voice)
                assert region == "General", f"Voice '{voice}' should default to General region"
    
    def test_region_priority_order(self):
        """Test that region detection follows the correct priority order."""
        # Test that more specific patterns take precedence
        # Irish should be detected before British for en-IE
        _, region, _ = analyze_voice("edge_tts", "en-IE-British-Voice")
        assert region == "Irish", "en-IE should be detected as Irish even with British in name"
        
        # British should be detected before American for en-GB
        _, region, _ = analyze_voice("edge_tts", "en-GB-American-Style")
        assert region == "British", "en-GB should be detected as British even with American in name"


class TestVoiceGenderAnalysis:
    """Test voice gender detection based on name patterns."""
    
    def test_female_gender_detection(self):
        """Test detection of female voice indicators."""
        female_voices = [
            "en-US-JennyNeural",
            "en-IE-EmilyNeural",
            "en-GB-LibbyNeural",
            "voice-aria",
            "davis-voice",
            "jane-speaker",
            "sarah-model",
            "amy-voice",
            "emma-neural",
            "female-voice",
            "woman-speaker",
            "EMILY-VOICE",  # Test case insensitivity
        ]
        
        for voice in female_voices:
            _, _, gender = analyze_voice("edge_tts", voice)
            assert gender == "F", f"Voice '{voice}' should be detected as female"
    
    def test_male_gender_detection(self):
        """Test detection of male voice indicators."""
        male_voices = [
            "voice-guy",
            "tony-neural",
            "brandon-voice",
            "christopher-speaker",
            "eric-model",
            "male-voice",
            "man-speaker",
            "GUY-VOICE",  # Test case insensitivity
        ]
        
        for voice in male_voices:
            _, _, gender = analyze_voice("edge_tts", voice)
            assert gender == "M", f"Voice '{voice}' should be detected as male"
    
    def test_unknown_gender_default(self):
        """Test that voices without gender indicators default to unknown."""
        unknown_gender_voices = [
            "en-US-Voice1",
            "neural-voice",
            "premium-speaker",
            "random-name",
            "voice-123",
            "speaker-model",
        ]
        
        for voice in unknown_gender_voices:
            _, _, gender = analyze_voice("edge_tts", voice)
            assert gender == "U", f"Voice '{voice}' should default to unknown gender"
    
    def test_case_insensitive_gender_detection(self):
        """Test that gender detection is case-insensitive."""
        test_cases = [
            ("JENNY", "F"),
            ("jenny", "F"),
            ("Jenny", "F"),
            ("EMILY", "F"),
            ("emily", "F"),
            ("Emily", "F"),
            ("GUY", "M"),
            ("guy", "M"),
            ("Guy", "M"),
            ("TONY", "M"),
            ("tony", "M"),
            ("Tony", "M"),
        ]
        
        for name_part, expected_gender in test_cases:
            _, _, gender = analyze_voice("provider", f"voice-{name_part}")
            assert gender == expected_gender, f"Voice with '{name_part}' should be detected as {expected_gender}"
    
    def test_partial_name_matching(self):
        """Test that gender detection works with partial name matching."""
        # Gender indicators can appear anywhere in the voice name
        test_voices = [
            ("prefix-emily-suffix", "F"),
            ("jenny123neural", "F"),
            ("neural-guy-voice", "M"),
            ("tony-premium-model", "M"),
            ("complex-aria-neural-voice", "F"),
        ]
        
        for voice, expected_gender in test_voices:
            _, _, gender = analyze_voice("provider", voice)
            assert gender == expected_gender, f"Voice '{voice}' should be detected as {expected_gender}"


class TestVoiceAnalysisIntegration:
    """Test complete voice analysis with all three dimensions."""
    
    def test_typical_edge_tts_voices(self):
        """Test analysis of typical Edge TTS voice names."""
        test_cases = [
            ("en-US-JennyNeural", 3, "American", "F"),
            ("en-IE-EmilyNeural", 3, "Irish", "F"),
            ("en-GB-LibbyNeural", 3, "British", "F"),
            ("en-AU-NatashaNeural", 3, "Australian", "F"),
            ("en-CA-ClaraNeural", 3, "Canadian", "F"),
        ]
        
        for voice, expected_quality, expected_region, expected_gender in test_cases:
            quality, region, gender = analyze_voice("edge_tts", voice)
            assert quality == expected_quality, f"Quality mismatch for {voice}"
            assert region == expected_region, f"Region mismatch for {voice}"
            assert gender == expected_gender, f"Gender mismatch for {voice}"
    
    def test_openai_voices(self):
        """Test analysis of OpenAI voice names."""
        openai_voices = [
            ("alloy", 2, "General", "U"),
            ("echo", 2, "General", "U"),
            ("fable", 2, "General", "U"),
            ("onyx", 2, "General", "U"),
            ("nova", 2, "General", "U"),
            ("shimmer", 2, "General", "U"),
        ]
        
        for voice, expected_quality, expected_region, expected_gender in openai_voices:
            quality, region, gender = analyze_voice("openai", voice)
            assert quality == expected_quality, f"Quality mismatch for OpenAI voice {voice}"
            assert region == expected_region, f"Region mismatch for OpenAI voice {voice}"
            assert gender == expected_gender, f"Gender mismatch for OpenAI voice {voice}"
    
    def test_chatterbox_voices(self):
        """Test analysis of Chatterbox (custom) voice files."""
        chatterbox_voices = [
            ("my_voice.wav", 2, "Chatterbox", "U"),
            ("emily_clone.mp3", 2, "Chatterbox", "F"),
            ("guy_voice.wav", 2, "Chatterbox", "M"),
            ("premium_sarah.flac", 3, "Chatterbox", "F"),
        ]
        
        for voice, expected_quality, expected_region, expected_gender in chatterbox_voices:
            quality, region, gender = analyze_voice("chatterbox", voice)
            assert quality == expected_quality, f"Quality mismatch for Chatterbox voice {voice}"
            assert region == expected_region, f"Region mismatch for Chatterbox voice {voice}"
            assert gender == expected_gender, f"Gender mismatch for Chatterbox voice {voice}"
    
    def test_complex_voice_names(self):
        """Test analysis of complex voice names with multiple indicators."""
        complex_voices = [
            # Voice with multiple quality indicators (Neural should win)
            ("basic-neural-emily", "edge_tts", 3, "General", "F"),
            
            # Voice with multiple region indicators (first match should win)
            ("en-IE-american-style", "edge_tts", 2, "Irish", "U"),
            
            # Voice with multiple gender indicators (first match should win)
            ("emily-guy-voice", "provider", 2, "General", "F"),
            
            # Voice combining all dimensions
            ("en-US-premium-jenny-neural", "edge_tts", 3, "American", "F"),
        ]
        
        for voice, provider, expected_quality, expected_region, expected_gender in complex_voices:
            quality, region, gender = analyze_voice(provider, voice)
            assert quality == expected_quality, f"Quality mismatch for complex voice {voice}"
            assert region == expected_region, f"Region mismatch for complex voice {voice}"
            assert gender == expected_gender, f"Gender mismatch for complex voice {voice}"
    
    def test_empty_and_edge_cases(self):
        """Test analysis of empty strings and edge cases."""
        edge_cases = [
            ("", "provider", 2, "General", "U"),
            ("   ", "provider", 2, "General", "U"),
            ("123", "provider", 2, "General", "U"),
            ("!!!", "provider", 2, "General", "U"),
        ]
        
        for voice, provider, expected_quality, expected_region, expected_gender in edge_cases:
            quality, region, gender = analyze_voice(provider, voice)
            assert quality == expected_quality, f"Quality mismatch for edge case {voice}"
            assert region == expected_region, f"Region mismatch for edge case {voice}"
            assert gender == expected_gender, f"Gender mismatch for edge case {voice}"
    
    def test_analysis_return_types(self):
        """Test that analyze_voice returns correct types."""
        quality, region, gender = analyze_voice("provider", "test-voice")
        
        assert isinstance(quality, int), "Quality should be an integer"
        assert isinstance(region, str), "Region should be a string"
        assert isinstance(gender, str), "Gender should be a string"
        
        # Test value ranges
        assert 1 <= quality <= 3, "Quality should be between 1 and 3"
        assert gender in ["F", "M", "U"], "Gender should be F, M, or U"
        assert len(region) > 0, "Region should not be empty"
    
    def test_consistent_analysis(self):
        """Test that analyze_voice returns consistent results for same inputs."""
        test_voice = "en-US-JennyNeural"
        test_provider = "edge_tts"
        
        # Run analysis multiple times
        results = [analyze_voice(test_provider, test_voice) for _ in range(5)]
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "analyze_voice should return consistent results for same inputs"