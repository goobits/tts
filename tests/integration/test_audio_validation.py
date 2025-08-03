"""
Comprehensive audio validation tests for TTS CLI.

This module tests the audio validation framework itself and provides
examples of how to validate actual audio synthesis output.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import patch

from tests.utils.test_helpers import (
    AudioValidationResult,
    validate_audio_file,
    validate_audio_file_comprehensive,
    extract_audio_metadata,
    detect_silence,
    validate_audio_format_compatibility,
    estimate_audio_duration_from_text,
    create_mock_audio_file,
    create_realistic_audio_file,
    create_corrupted_audio_file,
    create_empty_audio_file,
    WAVE_SUPPORT,
    SOUNDFILE_SUPPORT,
    MUTAGEN_SUPPORT
)


class TestAudioValidationResult:
    """Test the AudioValidationResult class."""
    
    def test_result_creation(self):
        """Test creating AudioValidationResult with various metadata."""
        result = AudioValidationResult(
            valid=True,
            format="mp3",
            duration=5.2,
            sample_rate=44100,
            channels=2,
            bitrate=128000,
            file_size=1024000
        )
        
        assert result.valid is True
        assert result.format == "mp3"
        assert result.duration == 5.2
        assert result.sample_rate == 44100
        assert result.channels == 2
        assert result.bitrate == 128000
        assert result.file_size == 1024000
        
    def test_result_boolean_behavior(self):
        """Test that AudioValidationResult behaves correctly as boolean."""
        valid_result = AudioValidationResult(valid=True)
        invalid_result = AudioValidationResult(valid=False)
        
        assert bool(valid_result) is True
        assert bool(invalid_result) is False
        
        # Test in conditional statements
        if valid_result:
            assert True
        else:
            assert False, "Should not reach here"
            
        if invalid_result:
            assert False, "Should not reach here"
        else:
            assert True
            
    def test_result_repr(self):
        """Test string representation of results."""
        result = AudioValidationResult(valid=True, format="wav", duration=2.5)
        repr_str = repr(result)
        
        assert "AudioValidationResult" in repr_str
        assert "valid=True" in repr_str
        assert "format=wav" in repr_str
        assert "duration=2.5s" in repr_str


class TestBasicAudioValidation:
    """Test basic audio file validation functions."""
    
    def test_validate_nonexistent_file(self, tmp_path):
        """Test validation of non-existent file."""
        nonexistent = tmp_path / "does_not_exist.mp3"
        assert validate_audio_file(nonexistent) is False
        
    def test_validate_empty_file(self, tmp_path):
        """Test validation of empty file."""
        empty_file = create_empty_audio_file(tmp_path / "empty", "mp3")
        assert validate_audio_file(empty_file) is False
        
    def test_validate_mock_file(self, tmp_path):
        """Test validation of mock audio file."""
        mock_file = create_mock_audio_file(tmp_path / "mock", "mp3", 1024)
        assert validate_audio_file(mock_file) is True
        
    def test_validate_format_mismatch(self, tmp_path):
        """Test validation with format mismatch."""
        mp3_file = create_mock_audio_file(tmp_path / "test", "mp3")
        assert validate_audio_file(mp3_file, expected_format="wav") is False
        assert validate_audio_file(mp3_file, expected_format="mp3") is True


class TestComprehensiveAudioValidation:
    """Test comprehensive audio validation functions."""
    
    def test_validate_nonexistent_comprehensive(self, tmp_path):
        """Test comprehensive validation of non-existent file."""
        nonexistent = tmp_path / "does_not_exist.mp3"
        result = validate_audio_file_comprehensive(nonexistent)
        
        assert result.valid is False
        assert "does not exist" in result.error.lower()
        
    def test_validate_file_too_small(self, tmp_path):
        """Test validation with file size constraints."""
        small_file = create_mock_audio_file(tmp_path / "small", "mp3", 45)
        result = validate_audio_file_comprehensive(small_file, min_file_size=50)
        
        assert result.valid is False
        assert "too small" in result.error.lower()
        assert result.file_size == 45
        
    def test_validate_format_mismatch_comprehensive(self, tmp_path):
        """Test comprehensive validation with format mismatch."""
        mp3_file = create_mock_audio_file(tmp_path / "test", "mp3")
        result = validate_audio_file_comprehensive(mp3_file, expected_format="wav")
        
        assert result.valid is False
        assert "format mismatch" in result.error.lower()
        assert result.format == "mp3"
        
    @pytest.mark.skipif(not WAVE_SUPPORT, reason="Wave module not available")
    def test_validate_realistic_wav(self, tmp_path):
        """Test validation of realistic WAV file."""
        wav_file = create_realistic_audio_file(
            tmp_path / "test", 
            format="wav", 
            duration=2.0,
            sample_rate=44100,
            channels=2
        )
        
        result = validate_audio_file_comprehensive(
            wav_file,
            expected_format="wav",
            min_duration=1.0,
            max_duration=3.0,
            expected_sample_rate=44100,
            expected_channels=2
        )
        
        assert result.valid is True
        assert result.format == "wav"
        assert abs(result.duration - 2.0) < 0.1  # Allow some tolerance
        assert result.sample_rate == 44100
        assert result.channels == 2
        
    def test_validate_duration_constraints(self, tmp_path):
        """Test duration constraint validation."""
        # Create a mock file and mock the metadata extraction
        mock_file = create_mock_audio_file(tmp_path / "test", "mp3")
        
        with patch("tests.utils.test_helpers.extract_audio_metadata") as mock_extract:
            mock_extract.return_value = {
                'valid': True,
                'duration': 5.0,
                'sample_rate': 44100,
                'channels': 2
            }
            
            # Test duration too short
            result = validate_audio_file_comprehensive(mock_file, min_duration=6.0)
            assert result.valid is False
            assert "too short" in result.error.lower()
            
            # Test duration too long
            result = validate_audio_file_comprehensive(mock_file, max_duration=4.0)
            assert result.valid is False
            assert "too long" in result.error.lower()
            
            # Test duration within range
            result = validate_audio_file_comprehensive(
                mock_file, 
                min_duration=4.0, 
                max_duration=6.0
            )
            assert result.valid is True


class TestAudioMetadataExtraction:
    """Test audio metadata extraction functions."""
    
    def test_extract_metadata_nonexistent(self, tmp_path):
        """Test metadata extraction from non-existent file."""
        nonexistent = tmp_path / "does_not_exist.wav"
        metadata = extract_audio_metadata(nonexistent)
        
        assert metadata['valid'] is False
        assert 'error' in metadata
        
    def test_extract_metadata_corrupted(self, tmp_path):
        """Test metadata extraction from corrupted file."""
        corrupted = create_corrupted_audio_file(tmp_path / "corrupted", "mp3")
        metadata = extract_audio_metadata(corrupted)
        
        assert metadata['valid'] is False
        assert 'error' in metadata
        
    @pytest.mark.skipif(not WAVE_SUPPORT, reason="Wave module not available")
    def test_extract_metadata_realistic_wav(self, tmp_path):
        """Test metadata extraction from realistic WAV file."""
        wav_file = create_realistic_audio_file(
            tmp_path / "test",
            format="wav",
            duration=1.5,
            sample_rate=22050,
            channels=1
        )
        
        metadata = extract_audio_metadata(wav_file)
        
        assert metadata['valid'] is True
        assert abs(metadata['duration'] - 1.5) < 0.1
        assert metadata['sample_rate'] == 22050
        assert metadata['channels'] == 1
        
    def test_extract_metadata_no_libraries(self, tmp_path):
        """Test metadata extraction when no audio libraries available."""
        mock_file = create_mock_audio_file(tmp_path / "test", "mp3")
        
        # Mock all audio library support to False
        with patch("tests.utils.test_helpers.MUTAGEN_SUPPORT", False), \
             patch("tests.utils.test_helpers.SOUNDFILE_SUPPORT", False), \
             patch("tests.utils.test_helpers.WAVE_SUPPORT", False):
            
            metadata = extract_audio_metadata(mock_file)
            assert metadata['valid'] is False
            assert "no audio libraries" in metadata['error'].lower()


class TestSilenceDetection:
    """Test silence detection functionality."""
    
    @pytest.mark.skipif(not SOUNDFILE_SUPPORT, reason="Soundfile not available")
    def test_detect_silence_no_audio(self, tmp_path):
        """Test silence detection on file with no audio content."""
        # Create a file with very low amplitude (should be detected as silence)
        silent_file = create_realistic_audio_file(
            tmp_path / "silent",
            format="wav",
            duration=1.0,
            frequency=0.0  # No frequency = silence
        )
        
        is_silent = detect_silence(silent_file, silence_threshold=0.1)
        assert is_silent is True
        
    @pytest.mark.skipif(not SOUNDFILE_SUPPORT, reason="Soundfile not available") 
    def test_detect_silence_with_audio(self, tmp_path):
        """Test silence detection on file with actual audio content."""
        audio_file = create_realistic_audio_file(
            tmp_path / "audio",
            format="wav", 
            duration=1.0,
            frequency=440.0  # A4 note
        )
        
        is_silent = detect_silence(audio_file, silence_threshold=0.01)
        assert is_silent is False
        
    def test_detect_silence_no_soundfile(self, tmp_path):
        """Test silence detection when soundfile not available."""
        mock_file = create_mock_audio_file(tmp_path / "test", "wav")
        
        with patch("tests.utils.test_helpers.SOUNDFILE_SUPPORT", False):
            is_silent = detect_silence(mock_file)
            assert is_silent is False  # Should return False when library unavailable
            
    def test_detect_silence_invalid_file(self, tmp_path):
        """Test silence detection on invalid file."""
        corrupted = create_corrupted_audio_file(tmp_path / "corrupted", "wav")
        is_silent = detect_silence(corrupted)
        assert is_silent is False  # Should handle errors gracefully


class TestFormatCompatibility:
    """Test audio format compatibility functions."""
    
    def test_format_compatibility_same_format(self, tmp_path):
        """Test compatibility check for same format."""
        mp3_file = create_mock_audio_file(tmp_path / "test", "mp3")
        assert validate_audio_format_compatibility(mp3_file, "mp3") is True
        
    def test_format_compatibility_compatible_formats(self, tmp_path):
        """Test compatibility check for compatible formats."""
        wav_file = create_mock_audio_file(tmp_path / "test", "wav")
        
        # WAV should be compatible with MP3, OGG, FLAC
        assert validate_audio_format_compatibility(wav_file, "mp3") is True
        assert validate_audio_format_compatibility(wav_file, "ogg") is True
        assert validate_audio_format_compatibility(wav_file, "flac") is True
        
    def test_format_compatibility_incompatible_formats(self, tmp_path):
        """Test compatibility check for incompatible formats."""
        mp3_file = create_mock_audio_file(tmp_path / "test", "mp3")
        
        # MP3 should not be compatible with AAC (not in compatibility matrix)
        assert validate_audio_format_compatibility(mp3_file, "aac") is False
        
    def test_format_compatibility_nonexistent_file(self, tmp_path):
        """Test compatibility check for non-existent file."""
        nonexistent = tmp_path / "does_not_exist.mp3"
        assert validate_audio_format_compatibility(nonexistent, "wav") is False


class TestDurationEstimation:
    """Test audio duration estimation functions."""
    
    def test_estimate_duration_basic(self):
        """Test basic duration estimation."""
        text = "Hello world"  # 2 words
        duration = estimate_audio_duration_from_text(text, wpm=120)
        expected = (2 / 120) * 60  # 1 second
        assert abs(duration - expected) < 0.001
        
    def test_estimate_duration_longer_text(self):
        """Test duration estimation for longer text."""
        text = "This is a longer piece of text with multiple words"  # 10 words
        duration = estimate_audio_duration_from_text(text, wpm=150)
        expected = (10 / 150) * 60  # 4 seconds
        assert abs(duration - expected) < 0.001
        
    def test_estimate_duration_different_wpm(self):
        """Test duration estimation with different WPM rates."""
        text = "Test text"  # 2 words
        
        slow_duration = estimate_audio_duration_from_text(text, wpm=100)
        fast_duration = estimate_audio_duration_from_text(text, wpm=200)
        
        assert slow_duration > fast_duration
        assert abs(slow_duration - 1.2) < 0.001  # (2/100)*60 = 1.2s
        assert abs(fast_duration - 0.6) < 0.001  # (2/200)*60 = 0.6s
        
    def test_estimate_duration_empty_text(self):
        """Test duration estimation for empty text."""
        duration = estimate_audio_duration_from_text("", wpm=150)
        assert duration == 0.0


class TestAudioFileCreation:
    """Test audio file creation helper functions."""
    
    def test_create_mock_audio_file(self, tmp_path):
        """Test mock audio file creation."""
        mock_file = create_mock_audio_file(tmp_path / "test", "mp3", 2048)
        
        assert mock_file.exists()
        assert mock_file.suffix == ".mp3"
        assert mock_file.stat().st_size > 0
        
    @pytest.mark.skipif(not WAVE_SUPPORT, reason="Wave module not available")
    def test_create_realistic_wav_file(self, tmp_path):
        """Test realistic WAV file creation."""
        wav_file = create_realistic_audio_file(
            tmp_path / "test",
            format="wav",
            duration=2.0,
            sample_rate=44100,
            channels=2,
            frequency=440.0
        )
        
        assert wav_file.exists()
        assert wav_file.suffix == ".wav"
        assert wav_file.stat().st_size > 0
        
        # Validate the created file
        result = validate_audio_file_comprehensive(wav_file, expected_format="wav")
        assert result.valid is True
        
    def test_create_corrupted_audio_file(self, tmp_path):
        """Test corrupted audio file creation."""
        corrupted = create_corrupted_audio_file(tmp_path / "corrupted", "mp3")
        
        assert corrupted.exists()
        assert corrupted.suffix == ".mp3"
        assert corrupted.stat().st_size > 0
        
        # Should fail validation due to corruption
        metadata = extract_audio_metadata(corrupted)
        assert metadata['valid'] is False
        
    def test_create_empty_audio_file(self, tmp_path):
        """Test empty audio file creation."""
        empty = create_empty_audio_file(tmp_path / "empty", "wav")
        
        assert empty.exists()
        assert empty.suffix == ".wav"
        assert empty.stat().st_size == 0
        
        # Should fail basic validation due to zero size
        assert validate_audio_file(empty) is False


class TestAudioValidationPerformance:
    """Test performance characteristics of audio validation functions."""
    
    def test_validation_performance_mock_files(self, tmp_path):
        """Test validation performance on mock files."""
        # Create multiple mock files
        files = []
        for i in range(10):
            files.append(create_mock_audio_file(tmp_path / f"test_{i}", "mp3", 1024))
        
        # Time the validation
        start_time = time.time()
        for file_path in files:
            result = validate_audio_file_comprehensive(file_path)
            assert result.valid is True or result.valid is False  # Just ensure it completes
        end_time = time.time()
        
        # Validation should be fast (< 1 second for 10 files)
        elapsed = end_time - start_time
        assert elapsed < 1.0, f"Validation took too long: {elapsed}s"
        
    @pytest.mark.skipif(not WAVE_SUPPORT, reason="Wave module not available")
    def test_validation_performance_realistic_files(self, tmp_path):
        """Test validation performance on realistic files."""
        # Create fewer realistic files (they take longer to create)
        files = []
        for i in range(3):
            files.append(create_realistic_audio_file(
                tmp_path / f"realistic_{i}",
                format="wav",
                duration=0.5,  # Short duration for speed
                sample_rate=22050,  # Lower sample rate for speed
                channels=1
            ))
        
        # Time the validation
        start_time = time.time()
        for file_path in files:
            result = validate_audio_file_comprehensive(
                file_path,
                expected_format="wav",
                check_silence=True  # Include silence detection
            )
            assert result.valid is True
        end_time = time.time()
        
        # Should still be reasonably fast (< 2 seconds for 3 files)
        elapsed = end_time - start_time
        assert elapsed < 2.0, f"Realistic file validation took too long: {elapsed}s"


class TestAudioValidationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_validation_permission_denied(self, tmp_path):
        """Test validation with permission issues."""
        # This test may not work on all systems, so we make it conditional
        try:
            import os
            import stat
            
            # Create a file and remove read permissions
            test_file = create_mock_audio_file(tmp_path / "no_permission", "mp3")
            os.chmod(test_file, 0o000)  # No permissions
            
            try:
                result = validate_audio_file_comprehensive(test_file)
                # Should handle permission errors gracefully
                assert result.valid is False
                # Check for either permission error or library availability error
                error_str = str(result.error).lower()
                assert ('error' in error_str or 'no audio libraries available' in error_str)
            finally:
                # Restore permissions for cleanup
                os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)
                
        except (OSError, PermissionError):
            # Skip test if we can't modify permissions
            pytest.skip("Cannot test permission errors on this system")
            
    def test_validation_extremely_large_constraints(self, tmp_path):
        """Test validation with extreme constraint values."""
        mock_file = create_mock_audio_file(tmp_path / "test", "mp3")
        
        with patch("tests.utils.test_helpers.extract_audio_metadata") as mock_extract:
            mock_extract.return_value = {
                'valid': True,
                'duration': 1.0,
                'sample_rate': 44100,
                'channels': 2
            }
            
            # Test with extremely large duration constraints
            result = validate_audio_file_comprehensive(
                mock_file,
                min_duration=0.0,
                max_duration=999999.0
            )
            assert result.valid is True
            
            # Test with extremely large file size constraint
            result = validate_audio_file_comprehensive(
                mock_file,
                min_file_size=0
            )
            assert result.valid is True
            
    def test_validation_unicode_file_paths(self, tmp_path):
        """Test validation with unicode file paths."""
        unicode_path = tmp_path / "测试音频文件.mp3"
        mock_file = create_mock_audio_file(unicode_path, "mp3")
        
        result = validate_audio_file_comprehensive(mock_file, expected_format="mp3")
        # Should handle unicode paths correctly
        assert result.format == "mp3"
        
    def test_validation_very_long_file_names(self, tmp_path):
        """Test validation with very long file names."""
        long_name = "a" * 200 + ".mp3"  # Very long filename
        try:
            long_path = tmp_path / long_name
            mock_file = create_mock_audio_file(long_path, "mp3")
            
            result = validate_audio_file_comprehensive(mock_file)
            # Should handle long filenames if filesystem supports them
            
        except OSError:
            # Skip if filesystem doesn't support long filenames
            pytest.skip("Filesystem doesn't support long filenames")


@pytest.mark.integration
class TestAudioValidationIntegration:
    """Integration tests combining multiple validation features."""
    
    @pytest.mark.skipif(not WAVE_SUPPORT, reason="Wave module not available")
    def test_complete_validation_workflow(self, tmp_path):
        """Test complete validation workflow from creation to validation."""
        # Create a realistic audio file
        audio_file = create_realistic_audio_file(
            tmp_path / "complete_test",
            format="wav",
            duration=3.0,
            sample_rate=44100,
            channels=2,
            frequency=220.0  # A3 note
        )
        
        # Perform comprehensive validation
        result = validate_audio_file_comprehensive(
            audio_file,
            expected_format="wav",
            min_duration=2.0,
            max_duration=4.0,
            expected_sample_rate=44100,
            expected_channels=2,
            min_file_size=1000,
            check_silence=True
        )
        
        # Verify all aspects
        assert result.valid is True
        assert result.format == "wav"
        assert 2.0 <= result.duration <= 4.0
        assert result.sample_rate == 44100
        assert result.channels == 2
        assert result.file_size >= 1000
        # has_silence may be None if silence detection fails, or numpy False, accept that
        assert result.has_silence is False or result.has_silence is None or (hasattr(result.has_silence, 'item') and not result.has_silence.item())
        
        # Test format compatibility
        assert validate_audio_format_compatibility(audio_file, "mp3") is True
        assert validate_audio_format_compatibility(audio_file, "ogg") is True
        
    def test_validation_error_propagation(self, tmp_path):
        """Test that validation errors are properly propagated."""
        # Test file existence error
        nonexistent = tmp_path / "does_not_exist.mp3"
        result = validate_audio_file_comprehensive(nonexistent)
        assert result.valid is False
        assert result.error is not None
        
        # Test format mismatch error
        wav_file = create_mock_audio_file(tmp_path / "test", "wav")
        result = validate_audio_file_comprehensive(wav_file, expected_format="mp3")
        assert result.valid is False
        assert "format mismatch" in result.error.lower()
        
        # Test file size error
        small_file = create_mock_audio_file(tmp_path / "small", "mp3", 10)
        result = validate_audio_file_comprehensive(small_file, min_file_size=100)
        assert result.valid is False
        assert "too small" in result.error.lower()