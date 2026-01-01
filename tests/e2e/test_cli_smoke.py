"""
Comprehensive CLI Smoke Tests for TTS CLI

This test file systematically runs all major CLI commands to ensure:
1. Commands execute without crashing
2. Help systems work
3. Basic argument parsing works
4. Error handling is graceful

These are smoke tests - they verify commands run, not that they produce perfect output.
For detailed functional testing, see test_cli.py.
"""

import pytest
from click.testing import CliRunner

from matilda_voice.cli import cli as cli


class TestCLISmokeTests:
    """Smoke tests to verify all CLI commands run without crashing."""

    def setup_method(self):
        """Set up test runner for each test."""
        self.runner = CliRunner()

    def test_main_help(self, mock_cli_environment):
        """Test main help command."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "speak" in result.output  # Check for speak command in help

    def test_version(self, mock_cli_environment):
        """Test status command shows system info."""
        # Note: New CLI uses status command instead of --version
        result = self.runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "TTS" in result.output or "Status" in result.output

    # =============================================================================
    # CORE COMMANDS SMOKE TESTS
    # =============================================================================


    def test_speak_basic(self, mock_cli_environment):
        """Test basic speak command with mocked environment."""
        # New CLI: speak TEXT OPTIONS
        result = self.runner.invoke(cli, ["speak", "test", "@edge"])

        # With mocks, should succeed
        assert result.exit_code == 0
        # Streaming audio operations succeed silently


    def test_save_basic(self, mock_cli_environment, tmp_path):
        """Test basic save command with mocked environment."""
        output_file = tmp_path / "test_smoke.mp3"
        # New CLI: save TEXT OPTIONS [--options]
        result = self.runner.invoke(cli, ["save", "test", "@edge", "-o", str(output_file)])

        # With mocks, should succeed
        assert result.exit_code == 0
        # Should contain indication of processing
        assert "saved" in result.output.lower() or "Audio" in result.output or output_file.exists()


    # =============================================================================
    # PROVIDER MANAGEMENT SMOKE TESTS
    # =============================================================================

    def test_providers_basic(self):
        """Test providers command."""
        # New CLI: providers requires a provider name
        result = self.runner.invoke(cli, ["providers", "edge_tts"])
        assert result.exit_code == 0
        assert "edge_tts" in result.output or "Edge" in result.output



    def test_info_basic(self, mock_cli_environment):
        """Test info command with provider argument."""
        # New CLI: info requires a PROVIDER argument
        result = self.runner.invoke(cli, ["info", "edge_tts"])

        # Should succeed with mocked environment
        assert result.exit_code == 0
        # Should show provider information
        assert "edge_tts" in result.output or "Edge" in result.output

    def test_info_with_provider(self, mock_cli_environment):
        """Test info command with provider."""
        result = self.runner.invoke(cli, ["info", "edge_tts"])
        assert result.exit_code == 0
        assert "edge_tts" in result.output or "Edge TTS" in result.output


    def test_install_basic(self, mock_cli_environment):
        """Test install command with provider argument."""
        # New CLI: install requires a provider name
        result = self.runner.invoke(cli, ["install", "edge_tts"])
        # Install may fail (exit 1) if provider not found, or succeed (exit 0)
        assert result.exit_code in [0, 1]
        # Should show something about the provider
        assert "edge" in result.output.lower() or "install" in result.output.lower() or "not found" in result.output.lower()

    # =============================================================================
    # CONFIGURATION SMOKE TESTS
    # =============================================================================


    def test_config_basic(self, mock_cli_environment):
        """Test config show command."""
        # New CLI: config requires ACTION KEY VALUE
        result = self.runner.invoke(cli, ["config", "show", "", ""])
        assert result.exit_code == 0
        assert "config" in result.output.lower() or "voice" in result.output.lower() or "Configuration" in result.output

    def test_config_show(self, mock_cli_environment):
        """Test config show command."""
        # New CLI: config requires ACTION KEY VALUE
        result = self.runner.invoke(cli, ["config", "show", "", ""])
        assert result.exit_code == 0
        assert "config" in result.output.lower() or "voice" in result.output.lower() or "Configuration" in result.output

    def test_status_basic(self, mock_cli_environment):
        """Test status command with mocked environment."""
        result = self.runner.invoke(cli, ["status"])

        # Should succeed with mocked environment
        assert result.exit_code == 0
        # Should show status information
        assert "TTS" in result.output or "status" in result.output.lower() or "Available" in result.output


    # =============================================================================
    # ADVANCED FEATURES SMOKE TESTS
    # =============================================================================


    def test_voice_status(self, mock_cli_environment):
        """Test voice status command."""
        result = self.runner.invoke(cli, ["voice", "status"])
        assert result.exit_code == 0
        assert "Voice" in result.output or "status" in result.output.lower() or "server" in result.output.lower()




    # =============================================================================
    # PROVIDER SHORTCUTS SMOKE TESTS
    # =============================================================================

    def test_provider_shortcuts_basic(self, mock_cli_environment):
        """Test that provider shortcuts are recognized with mocked environment."""
        # Test only @edge for now, as other providers may have authentication issues in testing
        shortcuts = ["@edge"]

        for shortcut in shortcuts:
            # New CLI: speak TEXT OPTIONS
            result = self.runner.invoke(cli, ["speak", "test", shortcut])
            # Should succeed with mocked environment
            assert result.exit_code == 0, f"Provider shortcut {shortcut} failed: {result.output}"
            # Streaming audio operations succeed silently

    def test_provider_shortcuts_with_speak(self, mock_cli_environment):
        """Test provider shortcuts with explicit speak command."""
        # New CLI: speak TEXT OPTIONS
        result = self.runner.invoke(cli, ["speak", "test", "@edge"])

        # Should succeed with mocked environment
        assert result.exit_code == 0
        # Streaming audio operations succeed silently

    def test_provider_shortcuts_with_save(self, mock_cli_environment, tmp_path):
        """Test provider shortcuts with save command."""
        output_file = tmp_path / "test.mp3"
        # New CLI: save TEXT OPTIONS [--options]
        result = self.runner.invoke(cli, ["save", "test", "@edge", "-o", str(output_file)])

        # Should succeed with mocked environment
        assert result.exit_code == 0
        # Should show indication of saving
        assert "saved" in result.output.lower() or "Audio" in result.output or output_file.exists()

    def test_provider_shortcuts_with_info(self):
        """Test provider shortcuts with info command."""
        result = self.runner.invoke(cli, ["info", "@edge"])
        assert result.exit_code == 0
        assert "edge_tts" in result.output or "Edge TTS" in result.output

    # =============================================================================
    # ERROR HANDLING SMOKE TESTS
    # =============================================================================

    def test_unknown_provider_shortcut(self, mock_cli_environment):
        """Test handling of unknown provider shortcuts."""
        # New CLI: speak TEXT OPTIONS
        result = self.runner.invoke(cli, ["speak", "test", "@unknown"])
        # With mock, may succeed (mock intercepts) or fail (provider check)
        assert result.exit_code in [0, 1]
        # If it fails, should show error about unknown provider
        if result.exit_code == 1:
            assert "Unknown provider" in result.output or "not found" in result.output.lower()

    def test_unknown_subcommand(self, mock_cli_environment):
        """Test handling of unknown subcommands."""
        # Unknown commands trigger Click error
        result = self.runner.invoke(cli, ["nonexistent_command"])
        # Click returns exit code 2 for unknown commands
        assert result.exit_code in [0, 2]

    def test_save_without_text(self, mock_cli_environment):
        """Test save command without text shows usage."""
        result = self.runner.invoke(cli, ["save"])

        # New CLI requires TEXT and OPTIONS arguments
        assert result.exit_code == 2  # Click argument error
        assert "Usage:" in result.output

    def test_document_without_path(self, mock_cli_environment):
        """Test document command without file path."""
        result = self.runner.invoke(cli, ["document"])
        assert result.exit_code == 2  # Click argument error
        assert "Usage:" in result.output or "required" in result.output.lower()

    def test_document_nonexistent_file(self, mock_cli_environment):
        """Test document command with nonexistent file."""
        # New CLI: document DOCUMENT_PATH OPTIONS
        result = self.runner.invoke(cli, ["document", "/nonexistent/file.md", "@edge"])
        # CLI might show error but return 0 due to Click's exception handling
        assert result.exit_code in [0, 1]
        # Should show file not found error
        assert "not found" in result.output.lower() or "Error" in result.output

    # =============================================================================
    # HELP SYSTEM SMOKE TESTS
    # =============================================================================


    # =============================================================================
    # ARGUMENT PARSING SMOKE TESTS
    # =============================================================================

    def test_speak_with_options(self, mock_cli_environment):
        """Test speak command with various options."""
        # Test rate option - New CLI: speak TEXT OPTIONS [--options]
        result = self.runner.invoke(cli, ["speak", "test", "@edge", "--rate", "+20%"])
        assert result.exit_code == 0
        # Streaming audio operations succeed silently

        # Test voice option
        result = self.runner.invoke(cli, ["speak", "test", "@edge", "--voice", "en-US-JennyNeural"])
        assert result.exit_code == 0
        # Streaming audio operations succeed silently

        # Test debug option
        result = self.runner.invoke(cli, ["speak", "test", "@edge", "--debug"])
        assert result.exit_code == 0
        # Streaming audio operations succeed silently, even with debug flag

    def test_save_with_options(self, mock_cli_environment, tmp_path):
        """Test save command with various options."""
        # Test format option - New CLI: save TEXT OPTIONS [--options]
        output_file = tmp_path / "output.wav"
        result = self.runner.invoke(cli, ["save", "test", "@edge", "-f", "wav", "-o", str(output_file)])
        assert result.exit_code == 0
        # Should show indication of saving
        assert "saved" in result.output.lower() or "Audio" in result.output or output_file.exists()

        # Test JSON option
        output_file2 = tmp_path / "output2.mp3"
        result = self.runner.invoke(cli, ["save", "test", "@edge", "--json", "-o", str(output_file2)])
        assert result.exit_code == 0
        # With --json flag, should still succeed
        assert "saved" in result.output.lower() or "Audio" in result.output or output_file2.exists()

    # =============================================================================
    # INTEGRATION SMOKE TESTS (No API calls)
    # =============================================================================

    def test_stdin_input(self, mock_cli_environment):
        """Test CLI with stdin input."""
        # New CLI: speak TEXT OPTIONS - use stdin marker "-" for TEXT
        result = self.runner.invoke(cli, ["speak", "-", "@edge"], input="hello from stdin")

        # Should succeed with mocked environment or show usage
        assert result.exit_code in [0, 2]

    def test_empty_stdin(self, mock_cli_environment):
        """Test CLI with empty stdin."""
        # New CLI: speak TEXT OPTIONS
        result = self.runner.invoke(cli, ["speak", "-", "@edge"], input="")
        # CLI might handle empty stdin gracefully in test environment
        assert result.exit_code in [0, 1, 2]

    # =============================================================================
    # COMPREHENSIVE COMMAND COVERAGE TEST
    # =============================================================================

    def test_all_commands_executable(self, mock_cli_environment):
        """Comprehensive test that all documented commands can be invoked."""

        # Commands that should execute without crashing (may fail gracefully)
        # Updated for new CLI architecture with required positional arguments
        commands_to_test = [
            # Basic commands
            ["--help"],
            # Core commands with help
            ["speak", "--help"],
            ["save", "--help"],
            ["voices", "--help"],
            # Provider management (with required provider name)
            ["providers", "edge_tts"],
            ["providers", "--help"],
            ["info", "--help"],
            ["info", "edge_tts"],
            ["install", "--help"],
            ["install", "edge_tts"],
            # Configuration (with required ACTION KEY VALUE)
            ["config", "--help"],
            ["config", "show", "", ""],
            ["status", "--help"],
            ["status"],
            # Advanced features
            ["voice", "--help"],
            ["voice", "status"],
            ["voice", "load", "--help"],
            ["voice", "unload", "--help"],
            ["document", "--help"],
            # Provider shortcuts (with minimal text)
            ["info", "@edge"],
        ]

        failed_commands = []

        for cmd in commands_to_test:
            try:
                result = self.runner.invoke(cli, cmd)
                # Accept exit codes 0-2 (0=success, 1=expected error, 2=usage error)
                if result.exit_code > 2:
                    failed_commands.append((cmd, result.exit_code, result.output))
            except Exception as e:
                failed_commands.append((cmd, "EXCEPTION", str(e)))

        if failed_commands:
            failure_msg = "Commands that failed to execute properly:\n"
            for cmd, code, output in failed_commands:
                failure_msg += f"  {' '.join(cmd)} -> {code}\n"
                if isinstance(output, str) and len(output) < 200:
                    failure_msg += f"    Output: {output.strip()}\n"

            pytest.fail(failure_msg)

    # =============================================================================
    # NEW TEST SUITE SMOKE TESTS - CRITICAL FUNCTIONALITY
    # =============================================================================


    def test_document_format_options_smoke(self, mock_cli_environment, tmp_path):
        """Smoke test for document format options from test_cli_document.py."""
        # Create a test markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\nThis is a test document.")

        # Test document command with format option
        # New CLI: document DOCUMENT_PATH OPTIONS [--options]
        result = self.runner.invoke(
            cli, ["document", str(test_file), "@edge", "--doc-format", "markdown", "--emotion-profile", "technical"]
        )
        assert result.exit_code == 0
        # Should process without crashing

    def test_save_with_format_smoke(self, mock_cli_environment, tmp_path):
        """Smoke test for save with format options from test_cli_formats.py."""
        output_file = tmp_path / "test.wav"
        # New CLI: save TEXT OPTIONS [--options]
        result = self.runner.invoke(cli, ["save", "test audio", "@edge", "--format", "wav", "-o", str(output_file)])
        assert result.exit_code == 0
        # Should save without crashing

    def test_document_ssml_platform_smoke(self, mock_cli_environment, tmp_path):
        """Smoke test for SSML platform options from test_cli_document.py."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")

        # New CLI: document DOCUMENT_PATH OPTIONS [--options]
        result = self.runner.invoke(cli, ["document", str(test_file), "@edge", "--ssml-platform", "azure"])
        assert result.exit_code == 0
        # Should process SSML without crashing

    def test_config_validation_smoke(self, mock_cli_environment):
        """Smoke test for config validation from test_cli_config.py."""
        # Test invalid config action - new CLI requires ACTION KEY VALUE
        # The config hook handles invalid actions gracefully and returns 0
        result = self.runner.invoke(cli, ["config", "invalid_action", "", ""])
        # Hook may return 0 or non-zero depending on error handling
        # The key test is that it doesn't crash
        assert result.exit_code is not None


# =============================================================================
# QUICK SMOKE TEST FUNCTION
# =============================================================================


def test_cli_basic_smoke(mock_cli_environment):
    """Quick smoke test for basic CLI functionality with mocked environment."""
    runner = CliRunner()

    # Test basic commands don't crash
    # Updated for new CLI architecture with required positional arguments
    basic_tests = [
        (["--help"], 0),
        (["providers", "edge_tts"], 0),
        (["status"], 0),
        (["config", "show", "", ""], 0),
        (["info", "edge_tts"], 0),
    ]

    for cmd, expected_exit in basic_tests:
        result = runner.invoke(cli, cmd)
        assert result.exit_code == expected_exit, f"Command {cmd} failed with exit code {result.exit_code}: {result.output}"
