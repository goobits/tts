"""Tests for audio utilities and file management.

These tests cover file operations, cleanup utilities, and audio processing
helpers that don't require external audio systems or mocks. They test:
- File cleanup operations
- Path handling and validation
- Command argument construction
- Error handling for file operations
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tts_cli.audio_utils import cleanup_file


class TestCleanupFile:
    """Test file cleanup utility functions."""

    def test_cleanup_existing_file(self):
        """Test cleanup of an existing file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"test content")

        # Verify file exists
        assert os.path.exists(temp_path)

        # Clean up the file
        cleanup_file(temp_path)

        # Verify file is deleted
        assert not os.path.exists(temp_path)

    def test_cleanup_nonexistent_file(self):
        """Test cleanup of non-existent file (should not raise error)."""
        nonexistent_path = "/tmp/nonexistent_file_12345.wav"

        # Should not raise any exception
        cleanup_file(nonexistent_path)

    def test_cleanup_with_logger(self):
        """Test cleanup with logger parameter."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"test content")

        # Mock logger
        mock_logger = Mock()

        # Clean up with logger
        cleanup_file(temp_path, logger=mock_logger)

        # Verify file is deleted
        assert not os.path.exists(temp_path)

        # Verify logger was called for debug message
        mock_logger.debug.assert_called_once()
        debug_call_args = mock_logger.debug.call_args[0][0]
        assert "Cleaned up temporary file" in debug_call_args
        assert temp_path in debug_call_args

    @patch('os.path.exists')
    @patch('os.unlink')
    def test_cleanup_permission_error(self, mock_unlink, mock_exists):
        """Test cleanup behavior when file cannot be deleted due to permissions."""
        # Setup mocks
        mock_exists.return_value = True
        mock_unlink.side_effect = PermissionError("Permission denied")

        mock_logger = Mock()
        test_path = "/fake/test/file.mp3"

        # Cleanup should not raise exception, but should log the error
        cleanup_file(test_path, logger=mock_logger)

        # Verify the file existence was checked
        mock_exists.assert_called_once_with(test_path)

        # Verify unlink was attempted
        mock_unlink.assert_called_once_with(test_path)

        # Verify error was logged
        mock_logger.debug.assert_called_once()
        debug_call_args = mock_logger.debug.call_args[0][0]
        assert "Could not clean up temporary file" in debug_call_args
        assert test_path in debug_call_args
        assert "Permission denied" in debug_call_args

    def test_cleanup_with_pathlib(self):
        """Test cleanup with pathlib.Path objects."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = Path(tmp.name)
            tmp.write(b"test content")

        # Verify file exists
        assert temp_path.exists()

        # Clean up using Path object (converted to string internally)
        cleanup_file(str(temp_path))

        # Verify file is deleted
        assert not temp_path.exists()


    def test_cleanup_directory_path(self):
        """Test cleanup when path points to directory instead of file."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_logger = Mock()

            # Try to cleanup directory (should not crash)
            cleanup_file(temp_dir, logger=mock_logger)

            # Directory should still exist (we don't delete directories)
            assert os.path.exists(temp_dir)


class TestFileOperations:
    """Test file operation utilities."""

    def test_temporary_file_creation_and_cleanup(self):
        """Test creation and cleanup of temporary files in context."""
        # This tests the pattern used in our audio utilities
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            temp_file = tmp.name
            tmp.write(b"fake audio data")

        # File should exist after context
        assert os.path.exists(temp_file)

        # Cleanup using our utility
        cleanup_file(temp_file)

        # File should be gone
        assert not os.path.exists(temp_file)

    def test_multiple_file_cleanup(self):
        """Test cleanup of multiple files."""
        temp_files = []

        # Create multiple temporary files
        for i in range(5):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.wav') as tmp:
                temp_files.append(tmp.name)
                tmp.write(f"test content {i}".encode())

        # Verify all files exist
        for temp_file in temp_files:
            assert os.path.exists(temp_file)

        # Clean up all files
        for temp_file in temp_files:
            cleanup_file(temp_file)

        # Verify all files are deleted
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)

    def test_file_size_handling(self):
        """Test cleanup of files with different sizes."""
        file_sizes = [0, 1, 1024, 1024*1024]  # 0B, 1B, 1KB, 1MB

        for size in file_sizes:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                temp_path = tmp.name
                tmp.write(b"A" * size)

            # Verify file exists and has correct size
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) == size

            # Clean up
            cleanup_file(temp_path)

            # Verify deleted
            assert not os.path.exists(temp_path)


class TestAudioUtilityIntegration:
    """Test integration patterns used by audio utilities."""

    def test_temporary_file_workflow(self):
        """Test the complete temporary file workflow used by providers."""
        # This simulates the pattern used in our refactored providers

        # Step 1: Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            temp_file = tmp.name

        try:
            # Step 2: Simulate writing audio data
            with open(temp_file, 'wb') as f:
                f.write(b"fake mp3 data")

            # Step 3: Verify file exists and has content
            assert os.path.exists(temp_file)
            assert os.path.getsize(temp_file) > 0

            # Step 4: Simulate audio processing (would use ffplay here)
            # In real usage, this is where play_audio_with_ffplay would be called

            # For testing, just verify file is accessible
            with open(temp_file, 'rb') as f:
                content = f.read()
                assert content == b"fake mp3 data"

        finally:
            # Step 5: Clean up temporary file
            cleanup_file(temp_file)

        # Verify cleanup completed
        assert not os.path.exists(temp_file)

    def test_error_handling_with_cleanup(self):
        """Test that cleanup happens even when errors occur."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_file = tmp.name
            tmp.write(b"test data")

        try:
            # Simulate an error during processing
            assert os.path.exists(temp_file)

            # Simulate error
            raise ValueError("Simulated processing error")

        except ValueError:
            # Error occurred, but we should still clean up
            cleanup_file(temp_file)

        # Verify cleanup happened despite error
        assert not os.path.exists(temp_file)

    def test_concurrent_file_operations(self):
        """Test handling of multiple temporary files concurrently."""
        temp_files = []

        try:
            # Create multiple temp files (simulating concurrent synthesis)
            for i in range(3):
                suffix = f'_concurrent_{i}.wav'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    temp_files.append(tmp.name)
                    tmp.write(f"concurrent audio data {i}".encode())

            # Verify all files exist
            for temp_file in temp_files:
                assert os.path.exists(temp_file)

            # Simulate concurrent processing (all files exist simultaneously)
            for i, temp_file in enumerate(temp_files):
                with open(temp_file, 'rb') as f:
                    content = f.read()
                    assert f"concurrent audio data {i}".encode() in content

        finally:
            # Clean up all files
            for temp_file in temp_files:
                cleanup_file(temp_file)

        # Verify all files cleaned up
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)


class TestPathHandling:
    """Test path handling and validation utilities."""

    def test_path_normalization(self):
        """Test that paths are handled correctly across different formats."""
        # Create a temp file to work with
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"test")

        try:
            # Test different path representations
            path_variants = [
                temp_path,  # Original path
                os.path.abspath(temp_path),  # Absolute path
                str(Path(temp_path)),  # Path object converted to string
            ]

            for path_variant in path_variants:
                assert os.path.exists(path_variant)

                # All variants should refer to the same file
                assert os.path.samefile(path_variant, temp_path)

        finally:
            # Cleanup
            cleanup_file(temp_path)



class TestErrorScenarios:
    """Test error handling in audio utilities."""

    def test_cleanup_with_none_logger(self):
        """Test cleanup when logger is None."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"test")

        # Should work with None logger
        cleanup_file(temp_path, logger=None)
        assert not os.path.exists(temp_path)

    def test_cleanup_logging_levels(self):
        """Test that appropriate logging levels are used."""
        mock_logger = Mock()

        # Test successful cleanup logging
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"test")

        cleanup_file(temp_path, logger=mock_logger)

        # Should call debug for successful cleanup
        mock_logger.debug.assert_called_once()

        # Test non-existent file logging
        mock_logger.reset_mock()
        cleanup_file("/nonexistent/file.wav", logger=mock_logger)

        # Should call debug for non-existent file (not an error)
        mock_logger.debug.assert_called_once()

    def test_file_operations_edge_cases(self):
        """Test edge cases in file operations."""
        # Test with various invalid paths
        invalid_paths = [
            "",  # Empty string
            " ",  # Whitespace
            "\n",  # Newline
            "\t",  # Tab
            "\\",  # Just backslash (Windows)
            "/",   # Just forward slash (Unix)
        ]

        for invalid_path in invalid_paths:
            # Should not raise exceptions
            cleanup_file(invalid_path)

    def test_resource_cleanup_patterns(self):
        """Test resource cleanup patterns used in the codebase."""
        temp_files = []

        try:
            # Create resources
            for i in range(3):
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    temp_files.append(tmp.name)
                    tmp.write(f"resource {i}".encode())

            # Verify resources exist
            for temp_file in temp_files:
                assert os.path.exists(temp_file)

            # Simulate partial processing with error
            processed_files = []
            try:
                for temp_file in temp_files:
                    processed_files.append(temp_file)
                    if len(processed_files) >= 2:
                        raise RuntimeError("Simulated error during processing")

            except RuntimeError:
                # Clean up all files, even those not processed
                for temp_file in temp_files:
                    cleanup_file(temp_file)

                # Verify all cleaned up
                for temp_file in temp_files:
                    assert not os.path.exists(temp_file)

                temp_files = []  # Mark as cleaned up

        finally:
            # Final cleanup (should be no-op if already cleaned)
            for temp_file in temp_files:
                cleanup_file(temp_file)
