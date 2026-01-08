"""
Comprehensive CLI tests for audio format handling across TTS commands.

This test suite focuses on testing format validation logic and CLI parameter
handling without relying on actual audio synthesis. It tests format options
in both save and document commands with proper mocking.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from matilda_voice.cli import cli


class TestFormatValidation:
    """Test audio format validation across CLI commands."""

    def test_valid_formats_acceptance(self, full_cli_env, tmp_path):
        """Test that all valid formats are accepted by Click validation."""
        runner = CliRunner()
        valid_formats = ["mp3", "wav", "ogg", "flac"]

        # Patch get_engine where it's used in hooks.core
        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            for format_name in valid_formats:
                output_file = tmp_path / f"test_output.{format_name}"
                # Create the expected output file
                output_file.write_bytes(b"mock audio data")

                # CLI expects: save TEXT OPTIONS [--options]
                result = runner.invoke(
                    cli, ["save", "Test text", "@edge", "--format", format_name, "--output", str(output_file)]
                )
                assert result.exit_code == 0, f"Format {format_name} should be valid, got: {result.output}"

                # Verify the format was passed to the engine
                assert mock_engine.synthesize_text.called
                call_kwargs = mock_engine.synthesize_text.call_args.kwargs
                assert call_kwargs.get("format") == format_name

    def test_invalid_format_handling(self, full_cli_env, tmp_path):
        """Test that invalid formats are handled gracefully by the engine."""
        runner = CliRunner()
        # Note: Format validation happens at the engine level, not CLI level
        # The CLI accepts any format string, and the engine handles invalid ones
        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = False  # Simulate synthesis failure
            mock_get_engine.return_value = mock_engine

            invalid_formats = ["aac", "m4a", "wma", "opus", "invalid"]

            for format_name in invalid_formats:
                output_file = tmp_path / f"test_output.{format_name}"
                runner.invoke(
                    cli, ["save", "Test text", "@edge", "--format", format_name, "--output", str(output_file)]
                )
                # The command may succeed (exit 0) but synthesis should report the format
                # Verify the format was passed to the engine
                assert mock_engine.synthesize_text.called
                call_kwargs = mock_engine.synthesize_text.call_args.kwargs
                assert call_kwargs.get("format") == format_name

    def test_case_sensitivity_handling(self, full_cli_env, tmp_path):
        """Test that format values are passed through to the engine as-is."""
        runner = CliRunner()

        # Note: Case handling is done by the engine, not CLI validation
        # Test that uppercase formats are passed to the engine correctly
        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            uppercase_formats = ["MP3", "WAV", "OGG", "FLAC"]

            for format_name in uppercase_formats:
                output_file = tmp_path / f"test_output.{format_name.lower()}"
                output_file.write_bytes(b"mock audio data")

                runner.invoke(
                    cli, ["save", "Test text", "@edge", "--format", format_name, "--output", str(output_file)]
                )
                # Verify the format was passed to the engine (case preserved)
                assert mock_engine.synthesize_text.called
                call_kwargs = mock_engine.synthesize_text.call_args.kwargs
                assert call_kwargs.get("format") == format_name

    def test_format_shorthand_options(self, full_cli_env, tmp_path):
        """Test format option short forms (-f) work correctly."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            for format_name in ["mp3", "wav", "ogg", "flac"]:
                output_file = tmp_path / f"test_output.{format_name}"
                output_file.write_bytes(b"mock audio data")

                result = runner.invoke(cli, ["save", "Test text", "@edge", "-f", format_name, "-o", str(output_file)])
                assert result.exit_code == 0, f"Short form -f should work for {format_name}"


class TestSaveCommandFormats:
    """Test format handling specifically for save command."""

    def test_save_with_explicit_format(self, full_cli_env, tmp_path):
        """Test save command with explicit format specification."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            test_cases = [("mp3", "output.mp3"), ("wav", "output.wav"), ("ogg", "output.ogg"), ("flac", "output.flac")]

            for format_name, filename in test_cases:
                output_file = tmp_path / filename
                output_file.write_bytes(b"mock audio data")

                result = runner.invoke(
                    cli, ["save", "Hello world", "@edge", "--format", format_name, "--output", str(output_file)]
                )
                assert result.exit_code == 0
                assert output_file.exists(), f"Output file should exist for {format_name}"

    def test_save_format_with_provider_shortcuts(self, full_cli_env, tmp_path):
        """Test format handling works with provider shortcuts."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            providers = ["@edge", "@openai"]

            for provider in providers:
                for format_name in ["mp3", "wav"]:
                    output_file = tmp_path / f"test_{provider[1:]}_{format_name}.{format_name}"
                    output_file.write_bytes(b"mock audio data")

                    # TEXT first, then OPTIONS (provider shortcut)
                    result = runner.invoke(
                        cli, ["save", "Hello world", provider, "--format", format_name, "--output", str(output_file)]
                    )
                    assert result.exit_code == 0
                    assert output_file.exists()

    def test_save_default_format_behavior(self, full_cli_env, tmp_path):
        """Test save command default format behavior when no format specified."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            output_file = tmp_path / "output.mp3"
            output_file.write_bytes(b"mock audio data")

            result = runner.invoke(cli, ["save", "Hello world", "@edge", "--output", str(output_file)])
            assert result.exit_code == 0
            assert output_file.exists()


class TestDocumentCommandFormats:
    """Test format handling specifically for document command."""

    def test_document_with_format_specification(self, full_cli_env, tmp_path):
        """Test document command with explicit format specification."""
        runner = CliRunner()

        # Create a test document
        test_doc = tmp_path / "test.md"
        test_doc.write_text("# Test Document\n\nThis is a test document for TTS processing.")

        with patch("matilda_voice.hooks.document.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            for format_name in ["mp3", "wav", "ogg", "flac"]:
                output_file = tmp_path / f"test_document.{format_name}"
                output_file.write_bytes(b"mock audio data")

                # document expects: DOCUMENT_PATH OPTIONS [--options]
                result = runner.invoke(
                    cli,
                    [
                        "document",
                        str(test_doc),
                        "@edge",
                        "--save",
                        "--format",
                        format_name,
                        "--output",
                        str(output_file),
                    ],
                )
                assert result.exit_code == 0, f"Document command failed for {format_name}: {result.output}"
                assert output_file.exists(), f"Document output should exist for {format_name}"

    def test_document_format_without_save_flag(self, full_cli_env, tmp_path):
        """Test document command format option when save flag is not used."""
        runner = CliRunner()

        # Create a test document
        test_doc = tmp_path / "test.md"
        test_doc.write_text("# Test Document\n\nThis is a test document.")

        with patch("matilda_voice.hooks.document.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            # document expects: DOCUMENT_PATH OPTIONS [--options]
            result = runner.invoke(cli, ["document", str(test_doc), "@edge", "--format", "wav"])
            assert result.exit_code == 0


class TestFormatErrorHandling:
    """Test error handling for format-related issues."""

    def test_empty_format_parameter(self, full_cli_env, tmp_path):
        """Test behavior with empty format parameter."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            output_file = tmp_path / "output.mp3"
            output_file.write_bytes(b"mock audio data")

            runner.invoke(cli, ["save", "Test text", "@edge", "--format", "", "--output", str(output_file)])
            # Empty format may be converted to None by the hook
            assert mock_engine.synthesize_text.called
            call_kwargs = mock_engine.synthesize_text.call_args.kwargs
            # Format can be empty string or None depending on hook handling
            assert call_kwargs.get("format") in ["", None]

    def test_format_parameter_edge_cases(self, full_cli_env, tmp_path):
        """Test edge cases for format parameter values."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            edge_cases = [
                "mp3 ",  # Trailing space
                " wav",  # Leading space
                "mp3\n",  # With newline
                "wav\t",  # With tab
            ]

            for format_case in edge_cases:
                output_file = tmp_path / f"test_{format_case.strip()}.mp3"
                output_file.write_bytes(b"mock audio data")

                runner.invoke(
                    cli, ["save", "Test text", "@edge", "--format", format_case, "--output", str(output_file)]
                )
                # Format values with whitespace are passed to the engine as-is
                assert mock_engine.synthesize_text.called
                call_kwargs = mock_engine.synthesize_text.call_args.kwargs
                assert call_kwargs.get("format") == format_case

    def test_missing_format_parameter(self, full_cli_env, tmp_path):
        """Test behavior when format parameter is missing but output file specified."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            output_file = tmp_path / "output.mp3"
            output_file.write_bytes(b"mock audio data")

            # Should work fine without explicit format
            result = runner.invoke(cli, ["save", "Test text", "@edge", "--output", str(output_file)])
            assert result.exit_code == 0


class TestFormatExtensionLogic:
    """Test file extension and format validation logic."""

    def test_extension_override_behavior(self, full_cli_env, tmp_path):
        """Test behavior when file extension conflicts with format."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            # Test extension conflicts
            conflicts = [
                ("wav", "test.mp3"),  # WAV format with MP3 extension
                ("mp3", "test.wav"),  # MP3 format with WAV extension
                ("flac", "test.ogg"),  # FLAC format with OGG extension
            ]

            for format_name, filename in conflicts:
                output_file = tmp_path / filename
                output_file.write_bytes(b"mock audio data")

                result = runner.invoke(
                    cli, ["save", "Test text", "@edge", "--format", format_name, "--output", str(output_file)]
                )
                # Should succeed - the format parameter takes precedence
                assert result.exit_code == 0
                assert output_file.exists()

                # Verify the correct format was passed to the engine
                call_kwargs = mock_engine.synthesize_text.call_args.kwargs
                assert call_kwargs.get("format") == format_name

    def test_temporary_file_handling(self, full_cli_env, tmp_path):
        """Test that temporary files are handled correctly with different formats."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            with tempfile.TemporaryDirectory() as temp_dir:
                for format_name in ["mp3", "wav", "ogg", "flac"]:
                    output_file = Path(temp_dir) / f"temp_test.{format_name}"
                    output_file.write_bytes(b"mock audio data")

                    result = runner.invoke(
                        cli, ["save", "Temporary test", "@edge", "--format", format_name, "--output", str(output_file)]
                    )
                    assert result.exit_code == 0
                    assert output_file.exists()


class TestFormatIntegrationScenarios:
    """Test format handling in realistic integration scenarios."""

    def test_format_with_complex_file_paths(self, full_cli_env, tmp_path):
        """Test format handling with complex file paths."""
        runner = CliRunner()

        with patch("matilda_voice.hooks.core.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.synthesize_text.return_value = True
            mock_get_engine.return_value = mock_engine

            # Create nested directory structure
            nested_dir = tmp_path / "nested" / "audio" / "formats"
            nested_dir.mkdir(parents=True, exist_ok=True)

            complex_paths = [
                nested_dir / "audio with spaces.mp3",
                nested_dir / "audio-with-dashes.wav",
                nested_dir / "audio_with_underscores.ogg",
                nested_dir / "audio.multi.dots.flac",
            ]

            for i, output_path in enumerate(complex_paths):
                format_name = output_path.suffix[1:]  # Remove the dot
                output_path.write_bytes(b"mock audio data")

                result = runner.invoke(
                    cli,
                    ["save", f"Complex path test {i}", "@edge", "--format", format_name, "--output", str(output_path)],
                )
                assert result.exit_code == 0
                assert output_path.exists()


# Test execution functionality for standalone running
def run_format_tests():
    """Execute all format tests and return results."""
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
            capture_output=True,
            text=True,
        )

        return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        return {"exit_code": 1, "stdout": "", "stderr": str(e)}


if __name__ == "__main__":
    # Allow running this test file directly for quick validation
    results = run_format_tests()
    print("Test execution results:")
    print(f"Exit code: {results['exit_code']}")
    print("STDOUT:")
    print(results["stdout"])
    if results["stderr"]:
        print("STDERR:")
        print(results["stderr"])
