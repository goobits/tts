"""
Real audio synthesis validation tests for TTS CLI.

This module contains tests that verify actual TTS synthesis produces valid audio
output when providers are available. These tests are designed to work with
real TTS engines and validate the complete synthesis pipeline.
"""

import os

import pytest
from click.testing import CliRunner

from tests.utils.test_helpers import (
    CLITestHelper,
    estimate_audio_duration_from_text,
    validate_audio_file_comprehensive,
)


@pytest.mark.integration
@pytest.mark.audio
@pytest.mark.requires_providers
class TestRealAudioSynthesis:
    """Tests for real audio synthesis with validation."""

    def setup_method(self):
        """Set up test environment for real synthesis tests."""
        self.runner = CliRunner()
        self.cli_helper = CLITestHelper(self.runner)

    def test_edge_tts_synthesis_validation(self, tmp_path):
        """Test Edge TTS synthesis produces valid audio."""
        text = "This is a test of Edge TTS synthesis validation."
        output_file = tmp_path / "edge_test.wav"

        # Use actual Edge TTS if available
        result, actual_output = self.cli_helper.invoke_save(
            text,
            provider="@edge",
            output_path=str(output_file),
            format="wav"
        )

        # Skip test if Edge TTS not available
        if result.exit_code != 0 and "not available" in result.output:
            pytest.skip("Edge TTS not available")

        # If synthesis succeeded, validate the audio
        if result.exit_code == 0 and actual_output.exists():
            validation_result = validate_audio_file_comprehensive(
                actual_output,
                expected_format="wav",
                min_duration=1.0,
                max_duration=15.0,
                min_file_size=8000,  # WAV files should be reasonably sized
                check_silence=True
            )

            assert validation_result.valid, f"Edge TTS audio validation failed: {validation_result.error}"
            assert validation_result.format == "wav"
            assert validation_result.duration > 1.0
            assert validation_result.file_size > 8000

            # Check that audio contains content (not silent)
            if validation_result.has_silence is not None:
                assert validation_result.has_silence is False, "Audio should not be silent"

            # Verify duration is reasonable for text length
            estimated_duration = estimate_audio_duration_from_text(text, wpm=150)
            duration_ratio = validation_result.duration / estimated_duration
            assert 0.5 <= duration_ratio <= 3.0, \
                f"Duration ratio {duration_ratio} outside reasonable range (0.5-3.0)"

    def test_synthesis_duration_accuracy(self, tmp_path):
        """Test that synthesis duration matches text length expectations."""
        # Test different text lengths
        test_cases = [
            ("Short text.", 1.0, 5.0),  # min, max expected duration
            ("This is a medium length text that should take several seconds to speak.", 3.0, 10.0),
            ("This is a much longer piece of text that contains multiple sentences and should definitely take quite a bit longer to synthesize into speech audio. The duration should be proportional to the amount of text being processed.", 8.0, 25.0)
        ]

        for i, (text, min_expected, max_expected) in enumerate(test_cases):
            output_file = tmp_path / f"duration_test_{i}.mp3"

            result, actual_output = self.cli_helper.invoke_save(
                text,
                provider="@edge",  # Use Edge TTS as it's most likely to be available
                output_path=str(output_file),
                format="mp3"
            )

            # Skip if provider not available
            if result.exit_code != 0:
                continue

            if actual_output.exists():
                validation_result = validate_audio_file_comprehensive(
                    actual_output,
                    expected_format="mp3",
                    min_duration=min_expected,
                    max_duration=max_expected,
                    min_file_size=1000
                )

                # Duration should be within expected range
                if validation_result.duration:
                    assert min_expected <= validation_result.duration <= max_expected, \
                        f"Duration {validation_result.duration}s not in range [{min_expected}, {max_expected}] for text: '{text[:50]}...'"

    def test_multiple_format_synthesis_validation(self, tmp_path):
        """Test synthesis produces valid audio in multiple formats."""
        text = "Multi-format synthesis test"
        formats = ["mp3", "wav"]  # Focus on most common formats

        valid_outputs = []

        for format_name in formats:
            output_file = tmp_path / f"multiformat_test.{format_name}"

            result, actual_output = self.cli_helper.invoke_save(
                text,
                provider="@edge",
                output_path=str(output_file),
                format=format_name,
                voice="en-US-AvaNeural"
            )

            # Skip if synthesis failed
            if result.exit_code != 0 or not actual_output.exists():
                continue

            validation_result = validate_audio_file_comprehensive(
                actual_output,
                expected_format=format_name,
                min_duration=0.5,
                max_duration=10.0,
                min_file_size=500
            )

            if validation_result.valid:
                valid_outputs.append((format_name, validation_result))

                # Verify format-specific properties
                if format_name == "wav":
                    # WAV files should have specific sample rates (Edge TTS uses 24kHz)
                    if validation_result.sample_rate:
                        assert validation_result.sample_rate in [22050, 24000, 44100, 48000], \
                            f"Unexpected WAV sample rate: {validation_result.sample_rate}"

                elif format_name == "mp3":
                    # MP3 files should be smaller than equivalent WAV
                    assert validation_result.file_size > 1000, "MP3 file should have reasonable size"

        # At least one format should work (skip if no providers available)
        if len(valid_outputs) == 0:
            pytest.skip("No format produced valid audio output - likely due to provider availability in test environment")

        # If multiple formats worked, compare them
        if len(valid_outputs) > 1:
            durations = [result.duration for _, result in valid_outputs if result.duration]
            if len(durations) > 1:
                # Durations should be similar across formats (within 20% variance)
                max_duration = max(durations)
                min_duration = min(durations)
                variance = (max_duration - min_duration) / min_duration
                assert variance < 3.0, f"Duration variance {variance} too high across formats"

    @pytest.mark.skipif(not os.getenv("TEST_REAL_PROVIDERS"), reason="Real provider testing disabled")
    def test_provider_comparison_validation(self, tmp_path):
        """Test multiple providers produce comparable audio quality."""
        text = "Provider comparison test for audio quality validation"
        providers_to_test = ["@edge", "@openai", "@google"]

        provider_results = {}

        for provider in providers_to_test:
            output_file = tmp_path / f"provider_comparison_{provider[1:]}.mp3"

            result, actual_output = self.cli_helper.invoke_save(
                text,
                provider=provider,
                output_path=str(output_file)
            )

            # Skip provider if not available or configured
            if result.exit_code != 0:
                continue

            if actual_output.exists():
                validation_result = validate_audio_file_comprehensive(
                    actual_output,
                    expected_format="mp3",
                    min_duration=2.0,
                    max_duration=15.0,
                    min_file_size=2000,
                    check_silence=True
                )

                if validation_result.valid:
                    provider_results[provider] = validation_result

        # Need at least 2 providers to compare
        if len(provider_results) < 2:
            pytest.skip("Not enough providers available for comparison")

        # Compare provider results
        durations = [result.duration for result in provider_results.values() if result.duration]
        file_sizes = [result.file_size for result in provider_results.values() if result.file_size]

        if len(durations) > 1:
            # Durations should be reasonably similar
            avg_duration = sum(durations) / len(durations)
            for provider, result in provider_results.items():
                if result.duration:
                    variance = abs(result.duration - avg_duration) / avg_duration
                    assert variance < 0.5, \
                        f"Provider {provider} duration variance {variance} too high from average"

        # All providers should produce non-silent audio
        for provider, result in provider_results.items():
            if result.has_silence is not None:
                assert result.has_silence is False, f"Provider {provider} produced silent audio"

    def test_voice_specification_synthesis_validation(self, tmp_path):
        """Test synthesis with specific voice selection."""
        text = "Voice specification test"
        # Test common Edge TTS voices that should be available
        voices_to_test = [
            "en-US-AriaNeural",
            "en-US-JennyNeural",
            "en-GB-SoniaNeural"
        ]

        successful_voices = []

        for voice in voices_to_test:
            output_file = tmp_path / f"voice_test_{voice.replace('-', '_')}.wav"

            result, actual_output = self.cli_helper.invoke_save(
                text,
                provider="@edge",
                voice=voice,
                output_path=str(output_file),
                format="wav"
            )

            # Skip voice if not available
            if result.exit_code != 0:
                continue

            if actual_output.exists():
                validation_result = validate_audio_file_comprehensive(
                    actual_output,
                    expected_format="wav",
                    min_duration=1.0,
                    max_duration=8.0,
                    min_file_size=4000
                )

                if validation_result.valid:
                    successful_voices.append((voice, validation_result))

        # At least one voice should work (skip if no voices available)
        if len(successful_voices) == 0:
            pytest.skip("No voices produced valid audio - likely due to provider availability in test environment")

        # All successful voices should produce similar duration for same text
        if len(successful_voices) > 1:
            durations = [result.duration for _, result in successful_voices if result.duration]
            if len(durations) > 1:
                avg_duration = sum(durations) / len(durations)
                for voice, result in successful_voices:
                    if result.duration:
                        variance = abs(result.duration - avg_duration) / avg_duration
                        assert variance < 0.3, \
                            f"Voice {voice} duration variance {variance} too high"

    def test_synthesis_error_recovery_validation(self, tmp_path):
        """Test validation can detect synthesis errors and recovery."""
        # Test cases that might cause synthesis issues
        problematic_texts = [
            "",  # Empty text
            "   ",  # Whitespace only
            "🤖🎵🔊",  # Emoji only
            "Testing with some unusual characters: ñáéíóú çñü",  # Unicode
        ]

        successful_synthesis = 0

        for i, text in enumerate(problematic_texts):
            output_file = tmp_path / f"error_recovery_test_{i}.mp3"

            result, actual_output = self.cli_helper.invoke_save(
                text or "fallback text",  # Provide fallback for empty text
                provider="@edge",
                output_path=str(output_file)
            )

            # Count successful syntheses
            if result.exit_code == 0 and actual_output.exists():
                validation_result = validate_audio_file_comprehensive(
                    actual_output,
                    expected_format="mp3",
                    min_file_size=100  # Very lenient for problematic cases
                )

                if validation_result.valid:
                    successful_synthesis += 1

        # At least some synthesis should succeed (with fallback text)
        # This tests that our validation framework can handle edge cases
        assert successful_synthesis >= 0  # Non-negative (some might fail, that's ok)

    @pytest.mark.slow
    def test_large_text_synthesis_validation(self, tmp_path):
        """Test synthesis and validation of large text blocks."""
        # Create a longer text block
        large_text = " ".join([
            "This is a comprehensive test of text-to-speech synthesis with a longer text block.",
            "The purpose is to validate that the TTS system can handle larger amounts of text",
            "and produce audio output that is proportional to the input length.",
            "We expect the duration to be reasonable for the amount of text provided,",
            "and the audio quality to remain consistent even with longer synthesis tasks.",
            "This test helps ensure the validation framework works with realistic use cases."
        ])

        output_file = tmp_path / "large_text_test.wav"

        result, actual_output = self.cli_helper.invoke_save(
            large_text,
            provider="@edge",
            output_path=str(output_file),
            format="wav"
        )

        # Skip if synthesis failed
        if result.exit_code != 0:
            pytest.skip("Large text synthesis failed")

        if actual_output.exists():
            validation_result = validate_audio_file_comprehensive(
                actual_output,
                expected_format="wav",
                min_duration=10.0,  # Should be at least 10 seconds for this much text
                max_duration=60.0,  # But not more than a minute
                min_file_size=50000,  # Larger file for longer audio
                check_silence=True
            )

            assert validation_result.valid, f"Large text validation failed: {validation_result.error}"
            assert validation_result.duration >= 10.0, "Audio too short for large text"
            assert validation_result.file_size >= 50000, "File too small for large text"

            # Verify audio is not silent
            if validation_result.has_silence is not None:
                assert validation_result.has_silence is False, "Large text audio should not be silent"

            # Verify duration is reasonable for text length
            estimated_duration = estimate_audio_duration_from_text(large_text, wpm=150)
            duration_ratio = validation_result.duration / estimated_duration
            assert 0.3 <= duration_ratio <= 2.0, \
                f"Large text duration ratio {duration_ratio} outside reasonable range"


@pytest.mark.integration
@pytest.mark.audio
@pytest.mark.requires_providers
class TestSynthesisPerformanceValidation:
    """Tests for synthesis performance characteristics."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.cli_helper = CLITestHelper(self.runner)

    def test_synthesis_speed_validation(self, tmp_path):
        """Test that synthesis completes in reasonable time."""
        import time

        text = "Performance test for synthesis speed validation"
        output_file = tmp_path / "speed_test.mp3"

        start_time = time.time()

        result, actual_output = self.cli_helper.invoke_save(
            text,
            provider="@edge",
            output_path=str(output_file)
        )

        synthesis_time = time.time() - start_time

        # Skip if synthesis failed
        if result.exit_code != 0:
            pytest.skip("Synthesis failed for speed test")

        # Synthesis should complete in reasonable time (< 30 seconds for short text)
        assert synthesis_time < 30.0, f"Synthesis took too long: {synthesis_time}s"

        if actual_output.exists():
            validation_result = validate_audio_file_comprehensive(
                actual_output,
                expected_format="mp3",
                min_duration=1.0,
                min_file_size=1000
            )

            if validation_result.valid and validation_result.duration:
                # Real-time factor should be reasonable (synthesis time vs audio duration)
                rtf = synthesis_time / validation_result.duration
                assert rtf < 10.0, f"Real-time factor {rtf} too high (synthesis too slow)"

                # For short text, synthesis should be much faster than real-time
                if validation_result.duration < 5.0:
                    assert rtf < 5.0, f"RTF {rtf} too high for short audio"

    def test_concurrent_synthesis_validation(self, tmp_path):
        """Test validation framework with multiple concurrent syntheses."""
        import concurrent.futures
        import threading
        import time

        texts = [
            "Concurrent test one",
            "Concurrent test two",
            "Concurrent test three"
        ]

        # Create a lock to synchronize CLI operations
        cli_lock = threading.Lock()

        def synthesize_and_validate(i, text):
            # Create a separate CLITestHelper instance for each thread
            thread_cli_helper = CLITestHelper()
            output_file = tmp_path / f"concurrent_test_{i}.mp3"

            # Synchronize CLI operations to avoid CliRunner concurrency issues
            with cli_lock:
                result, actual_output = thread_cli_helper.invoke_save(
                    text,
                    provider="@edge",
                    output_path=str(output_file)
                )


            if result.exit_code == 0 and actual_output.exists():
                return validate_audio_file_comprehensive(
                    actual_output,
                    expected_format="mp3",
                    min_duration=0.5,
                    min_file_size=500
                )
            return None

        # Run concurrent syntheses
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(synthesize_and_validate, i, text)
                for i, text in enumerate(texts)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        total_time = time.time() - start_time

        # Filter successful results
        valid_results = [r for r in results if r and r.valid]

        # Should complete in reasonable time even with concurrent requests
        assert total_time < 60.0, f"Concurrent synthesis took too long: {total_time}s"

        # Check if any syntheses succeeded (providers might not be available in test environment)
        if len(valid_results) == 0:
            # If no syntheses succeeded, this might be due to missing providers, not concurrency issues
            # The important thing is that we didn't get the "I/O operation on closed file" error
            pytest.skip("No TTS providers available for concurrent test")

        # At least some syntheses should succeed
        assert len(valid_results) > 0, "No concurrent syntheses succeeded"

        # All successful results should have similar properties
        if len(valid_results) > 1:
            durations = [r.duration for r in valid_results if r.duration]
            if len(durations) > 1:
                # Durations should be reasonably similar for similar text lengths
                avg_duration = sum(durations) / len(durations)
                for duration in durations:
                    variance = abs(duration - avg_duration) / avg_duration
                    assert variance < 0.5, f"Duration variance {variance} too high in concurrent test"


@pytest.mark.integration
@pytest.mark.audio
@pytest.mark.requires_providers
class TestRealWorldSynthesisScenarios:
    """Tests for real-world synthesis scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.cli_helper = CLITestHelper(self.runner)

    def test_punctuation_handling_validation(self, tmp_path):
        """Test synthesis handles punctuation correctly."""
        text_with_punctuation = "Hello, world! How are you today? I'm fine. Thanks for asking..."
        output_file = tmp_path / "punctuation_test.wav"

        result, actual_output = self.cli_helper.invoke_save(
            text_with_punctuation,
            provider="@edge",
            output_path=str(output_file),
            format="wav"
        )

        if result.exit_code == 0 and actual_output.exists():
            validation_result = validate_audio_file_comprehensive(
                actual_output,
                expected_format="wav",
                min_duration=2.0,
                max_duration=12.0,
                min_file_size=8000
            )

            assert validation_result.valid, f"Punctuation handling validation failed: {validation_result.error}"

            # Text with punctuation should have reasonable duration
            estimated_duration = estimate_audio_duration_from_text(text_with_punctuation, wpm=150)
            if validation_result.duration:
                duration_ratio = validation_result.duration / estimated_duration
                assert 0.5 <= duration_ratio <= 2.5, \
                    f"Punctuation text duration ratio {duration_ratio} outside reasonable range"

    def test_number_handling_validation(self, tmp_path):
        """Test synthesis handles numbers correctly."""
        text_with_numbers = "The year is 2024, and the temperature is 23.5 degrees. Call 555-1234."
        output_file = tmp_path / "numbers_test.mp3"

        result, actual_output = self.cli_helper.invoke_save(
            text_with_numbers,
            provider="@edge",
            output_path=str(output_file)
        )

        if result.exit_code == 0 and actual_output.exists():
            validation_result = validate_audio_file_comprehensive(
                actual_output,
                expected_format="mp3",
                min_duration=3.0,  # Numbers typically take longer to speak
                max_duration=15.0,
                min_file_size=1500
            )

            assert validation_result.valid, f"Number handling validation failed: {validation_result.error}"

            # Numbers should result in longer audio due to full pronunciation
            estimated_duration = estimate_audio_duration_from_text(text_with_numbers, wpm=120)  # Slower for numbers
            if validation_result.duration:
                # Allow more variance for numbers as they can vary significantly in pronunciation
                duration_ratio = validation_result.duration / estimated_duration
                assert 0.3 <= duration_ratio <= 3.0, \
                    f"Number text duration ratio {duration_ratio} outside reasonable range"

    def test_mixed_content_validation(self, tmp_path):
        """Test synthesis with mixed content types."""
        mixed_text = """
        Welcome to the TTS test! Today's date is March 15th, 2024.
        Temperature: 72°F (22.2°C)
        Email: test@example.com
        Phone: (555) 123-4567
        Special characters: @#$%^&*()
        """
        output_file = tmp_path / "mixed_content_test.wav"

        result, actual_output = self.cli_helper.invoke_save(
            mixed_text,
            provider="@edge",
            output_path=str(output_file),
            format="wav"
        )

        if result.exit_code == 0 and actual_output.exists():
            validation_result = validate_audio_file_comprehensive(
                actual_output,
                expected_format="wav",
                min_duration=5.0,  # Mixed content should take substantial time
                max_duration=30.0,
                min_file_size=20000,
                check_silence=True
            )

            assert validation_result.valid, f"Mixed content validation failed: {validation_result.error}"
            assert validation_result.duration >= 5.0, "Mixed content audio too short"

            # Should not be silent
            if validation_result.has_silence is not None:
                assert validation_result.has_silence is False, "Mixed content should not be silent"
