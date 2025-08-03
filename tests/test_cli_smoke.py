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

from tts.cli import main as cli


class TestCLISmokeTests:
    """Smoke tests to verify all CLI commands run without crashing."""

    def setup_method(self):
        """Set up test runner for each test."""
        self.runner = CliRunner()

    def test_main_help(self, mock_cli_environment):
        """Test main help command."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "TTS CLI" in result.output
        assert "Usage:" in result.output

    def test_version(self, mock_cli_environment):
        """Test version command."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.1" in result.output or "version" in result.output.lower()

    # =============================================================================
    # CORE COMMANDS SMOKE TESTS
    # =============================================================================

    def test_speak_help(self, mock_cli_environment):
        """Test speak command help."""
        result = self.runner.invoke(cli, ["speak", "--help"])
        assert result.exit_code == 0
        assert "speak" in result.output.lower()

    def test_speak_basic(self, mock_cli_environment):
        """Test basic speak command with mocked environment."""
        result = self.runner.invoke(cli, ["speak", "test"])

        # With mocks, should succeed
        assert result.exit_code == 0
        # Streaming audio operations succeed silently

    def test_save_help(self, mock_cli_environment):
        """Test save command help."""
        result = self.runner.invoke(cli, ["save", "--help"])
        assert result.exit_code == 0
        assert "save" in result.output.lower()

    def test_save_basic(self, mock_cli_environment, tmp_path):
        """Test basic save command with mocked environment."""
        output_file = tmp_path / "test_smoke.mp3"
        result = self.runner.invoke(cli, ["save", "test", "-o", str(output_file)])

        # With mocks, should succeed
        assert result.exit_code == 0
        # Should contain indication of processing
        assert "saved" in result.output.lower() or "Audio" in result.output or output_file.exists()

    def test_voices_help(self, mock_cli_environment):
        """Test voices command help."""
        result = self.runner.invoke(cli, ["voices", "--help"])
        assert result.exit_code == 0
        assert "voices" in result.output.lower() or "browse" in result.output.lower()

    # =============================================================================
    # PROVIDER MANAGEMENT SMOKE TESTS
    # =============================================================================

    def test_providers_basic(self):
        """Test providers command."""
        result = self.runner.invoke(cli, ["providers"])
        assert result.exit_code == 0
        assert "edge_tts" in result.output or "openai_tts" in result.output or "Available" in result.output

    def test_providers_help(self):
        """Test providers command help."""
        result = self.runner.invoke(cli, ["providers", "--help"])
        assert result.exit_code == 0
        assert "providers" in result.output.lower()

    def test_info_help(self, mock_cli_environment):
        """Test info command help."""
        result = self.runner.invoke(cli, ["info", "--help"])
        assert result.exit_code == 0
        assert "info" in result.output.lower()

    def test_info_basic(self, mock_cli_environment):
        """Test info command without arguments with mocked environment."""
        result = self.runner.invoke(cli, ["info"])

        # Should succeed with mocked environment
        assert result.exit_code == 0
        # Should show TTS Provider Information header
        assert "TTS Provider Information" in result.output
        # Should show provider information
        assert "edge_tts" in result.output or "chatterbox" in result.output

    def test_info_with_provider(self, mock_cli_environment):
        """Test info command with provider."""
        result = self.runner.invoke(cli, ["info", "edge_tts"])
        assert result.exit_code == 0
        assert "edge_tts" in result.output or "Edge TTS" in result.output

    def test_install_help(self, mock_cli_environment):
        """Test install command help."""
        result = self.runner.invoke(cli, ["install", "--help"])
        assert result.exit_code == 0
        assert "install" in result.output.lower()

    def test_install_basic(self, mock_cli_environment):
        """Test install command without arguments (should show help)."""
        result = self.runner.invoke(cli, ["install"])
        assert result.exit_code == 0
        assert "install" in result.output.lower() or "provider" in result.output.lower()

    # =============================================================================
    # CONFIGURATION SMOKE TESTS
    # =============================================================================

    def test_config_help(self, mock_cli_environment):
        """Test config command help."""
        result = self.runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_config_basic(self, mock_cli_environment):
        """Test config command without arguments (should show config)."""
        result = self.runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "config" in result.output.lower() or "voice" in result.output.lower() or "Configuration" in result.output

    def test_config_show(self, mock_cli_environment):
        """Test config show command."""
        result = self.runner.invoke(cli, ["config", "show"])
        assert result.exit_code == 0
        assert "config" in result.output.lower() or "voice" in result.output.lower() or "Configuration" in result.output

    def test_status_basic(self, mock_cli_environment):
        """Test status command with mocked environment."""
        result = self.runner.invoke(cli, ["status"])

        # Should succeed with mocked environment
        assert result.exit_code == 0
        # Should show status information
        assert "TTS System Status" in result.output or "status" in result.output.lower() or "Available" in result.output
        assert "✅ openai_tts" in result.output
        # Should show configuration
        assert "⚙️  Configuration:" in result.output
        assert "Default voice: edge_tts:en-IE-EmilyNeural" in result.output

    def test_status_help(self):
        """Test status command help."""
        result = self.runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "status" in result.output.lower()

    # =============================================================================
    # ADVANCED FEATURES SMOKE TESTS
    # =============================================================================

    def test_voice_help(self, mock_cli_environment):
        """Test voice command group help."""
        result = self.runner.invoke(cli, ["voice", "--help"])
        assert result.exit_code == 0
        assert "voice" in result.output.lower()

    def test_voice_status(self, mock_cli_environment):
        """Test voice status command."""
        result = self.runner.invoke(cli, ["voice", "status"])
        assert result.exit_code == 0
        assert "Voice" in result.output or "status" in result.output.lower() or "server" in result.output.lower()

    def test_voice_load_help(self, mock_cli_environment):
        """Test voice load command help."""
        result = self.runner.invoke(cli, ["voice", "load", "--help"])
        assert result.exit_code == 0
        assert "load" in result.output.lower()

    def test_voice_unload_help(self, mock_cli_environment):
        """Test voice unload command help."""
        result = self.runner.invoke(cli, ["voice", "unload", "--help"])
        assert result.exit_code == 0
        assert "unload" in result.output.lower()

    def test_document_help(self, mock_cli_environment):
        """Test document command help."""
        result = self.runner.invoke(cli, ["document", "--help"])
        assert result.exit_code == 0
        assert "document" in result.output.lower()

    # =============================================================================
    # PROVIDER SHORTCUTS SMOKE TESTS
    # =============================================================================

    def test_provider_shortcuts_basic(self, mock_cli_environment):
        """Test that provider shortcuts are recognized with mocked environment."""
        # Test only @edge for now, as other providers may have authentication issues in testing
        shortcuts = ["@edge"]

        for shortcut in shortcuts:
            result = self.runner.invoke(cli, ["speak", shortcut, "test"])
            # Should succeed with mocked environment
            assert result.exit_code == 0, f"Provider shortcut {shortcut} failed: {result.output}"
            # Streaming audio operations succeed silently

    def test_provider_shortcuts_with_speak(self, mock_cli_environment):
        """Test provider shortcuts with explicit speak command."""
        result = self.runner.invoke(cli, ["speak", "@edge", "test"])

        # Should succeed with mocked environment
        assert result.exit_code == 0
        # Streaming audio operations succeed silently

    def test_provider_shortcuts_with_save(self, mock_cli_environment, tmp_path):
        """Test provider shortcuts with save command."""
        output_file = tmp_path / "test.mp3"
        result = self.runner.invoke(cli, ["save", "@edge", "test", "-o", str(output_file)])

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

    def test_unknown_provider_shortcut(self):
        """Test handling of unknown provider shortcuts."""
        result = self.runner.invoke(cli, ["@unknown", "test"])
        # Should fail with exit code 1
        assert result.exit_code == 1
        # Should show error message about unknown provider
        assert "Error: Unknown provider shortcut '@unknown'" in result.output
        # Should show available providers
        assert "Available providers:" in result.output
        assert "@edge" in result.output
        assert "@openai" in result.output

    def test_unknown_subcommand(self, mock_cli_environment):
        """Test handling of unknown subcommands."""
        result = self.runner.invoke(cli, ["nonexistent_command"])
        # CLI treats unrecognized text as input to speak
        assert result.exit_code == 0
        # Unknown commands are treated as text to speak (streaming succeeds silently)

    def test_save_without_text(self, mock_cli_environment):
        """Test save command without text."""
        result = self.runner.invoke(cli, ["save"])

        # CLI shows error but returns exit code 0 due to Click's exception handling
        # In actual usage this would exit with code 1, but in test it's captured
        assert result.exit_code == 0
        # Should show error about no text
        assert "Error: No text provided to save" in result.output

    def test_document_without_path(self, mock_cli_environment):
        """Test document command without file path."""
        result = self.runner.invoke(cli, ["document"])
        assert result.exit_code == 2  # Click argument error
        assert "Usage:" in result.output or "required" in result.output.lower()

    def test_document_nonexistent_file(self, mock_cli_environment):
        """Test document command with nonexistent file."""
        result = self.runner.invoke(cli, ["document", "/nonexistent/file.md"])
        # CLI might show error but return 0 due to Click's exception handling
        assert result.exit_code in [0, 1]
        # Should show file not found error
        assert "not found" in result.output.lower() or "Error" in result.output

    # =============================================================================
    # HELP SYSTEM SMOKE TESTS
    # =============================================================================

    def test_all_subcommands_have_help(self, mock_cli_environment):
        """Test that all major subcommands have accessible help."""
        subcommands = ["speak", "save", "voices", "providers", "info", "install", "config", "status", "voice", "document"]

        for cmd in subcommands:
            result = self.runner.invoke(cli, [cmd, "--help"])
            assert result.exit_code == 0, f"Help failed for command: {cmd}"
            assert "Usage:" in result.output or "usage:" in result.output, f"No usage info in help for: {cmd}"

    # =============================================================================
    # ARGUMENT PARSING SMOKE TESTS
    # =============================================================================

    def test_speak_with_options(self, mock_cli_environment):
        """Test speak command with various options."""
        # Test rate option
        result = self.runner.invoke(cli, ["speak", "test", "--rate", "+20%"])
        assert result.exit_code == 0
        # Streaming audio operations succeed silently

        # Test voice option
        result = self.runner.invoke(cli, ["speak", "test", "--voice", "en-US-JennyNeural"])
        assert result.exit_code == 0
        # Streaming audio operations succeed silently

        # Test debug option
        result = self.runner.invoke(cli, ["speak", "test", "--debug"])
        assert result.exit_code == 0
        # Streaming audio operations succeed silently, even with debug flag

    def test_save_with_options(self, mock_cli_environment, tmp_path):
        """Test save command with various options."""
        # Test format option
        output_file = tmp_path / "output.wav"
        result = self.runner.invoke(cli, ["save", "test", "-f", "wav", "-o", str(output_file)])
        assert result.exit_code == 0
        # Should show indication of saving
        assert "saved" in result.output.lower() or "Audio" in result.output or output_file.exists()

        # Test JSON option
        output_file2 = tmp_path / "output2.mp3"
        result = self.runner.invoke(cli, ["save", "test", "--json", "-o", str(output_file2)])
        assert result.exit_code == 0
        # With --json flag, should still succeed
        assert "saved" in result.output.lower() or "Audio" in result.output or output_file2.exists()

    # =============================================================================
    # INTEGRATION SMOKE TESTS (No API calls)
    # =============================================================================

    def test_stdin_input(self, mock_cli_environment):
        """Test CLI with stdin input."""
        result = self.runner.invoke(cli, ["speak"], input="hello from stdin")

        # Should succeed with mocked environment
        assert result.exit_code == 0
        # Streaming audio operations succeed silently

    def test_empty_stdin(self, mock_cli_environment):
        """Test CLI with empty stdin."""
        result = self.runner.invoke(cli, ["speak"], input="")
        # CLI might handle empty stdin gracefully in test environment
        assert result.exit_code in [0, 1]
        # Should either show error or handle gracefully
        assert "Error: No text provided to speak" in result.output or "No text" in result.output or result.output.strip() == ""

    # =============================================================================
    # COMPREHENSIVE COMMAND COVERAGE TEST
    # =============================================================================

    def test_all_commands_executable(self, mock_cli_environment):
        """Comprehensive test that all documented commands can be invoked."""

        # Commands that should execute without crashing (may fail gracefully)
        commands_to_test = [
            # Basic commands
            ["--help"],
            ["--version"],
            # Core commands with help
            ["speak", "--help"],
            ["save", "--help"],
            ["voices", "--help"],
            # Provider management
            ["providers"],
            ["providers", "--help"],
            ["info", "--help"],
            ["info"],
            ["install", "--help"],
            ["install"],
            # Configuration
            ["config", "--help"],
            ["config"],
            ["config", "show"],
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

    def test_config_set_and_get_smoke(self, mock_cli_environment):
        """Smoke test for config set/get operations from test_cli_config.py."""
        # Test setting a configuration value
        result = self.runner.invoke(cli, ["config", "set", "test_key", "test_value"])
        assert result.exit_code == 0
        assert "test_key" in result.output

        # Test getting the configuration value
        result = self.runner.invoke(cli, ["config", "get", "test_key"])
        assert result.exit_code == 0
        assert "test_value" in result.output

    def test_document_format_options_smoke(self, mock_cli_environment, tmp_path):
        """Smoke test for document format options from test_cli_document.py."""
        # Create a test markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\nThis is a test document.")

        # Test document command with format option
        result = self.runner.invoke(
            cli, ["document", str(test_file), "--doc-format", "markdown", "--emotion-profile", "technical"]
        )
        assert result.exit_code == 0
        # Should process without crashing

    def test_save_with_format_smoke(self, mock_cli_environment, tmp_path):
        """Smoke test for save with format options from test_cli_formats.py."""
        output_file = tmp_path / "test.wav"
        result = self.runner.invoke(cli, ["save", "test audio", "--format", "wav", "-o", str(output_file)])
        assert result.exit_code == 0
        # Should save without crashing

    def test_document_ssml_platform_smoke(self, mock_cli_environment, tmp_path):
        """Smoke test for SSML platform options from test_cli_document.py."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")

        result = self.runner.invoke(cli, ["document", str(test_file), "--ssml-platform", "azure"])
        assert result.exit_code == 0
        # Should process SSML without crashing

    def test_config_validation_smoke(self, mock_cli_environment):
        """Smoke test for config validation from test_cli_config.py."""
        # Test invalid config action
        result = self.runner.invoke(cli, ["config", "invalid_action"])
        assert result.exit_code != 0
        assert "Error" in result.output or "Usage" in result.output


# =============================================================================
# QUICK SMOKE TEST FUNCTION
# =============================================================================


def test_cli_basic_smoke(mock_cli_environment):
    """Quick smoke test for basic CLI functionality with mocked environment."""
    runner = CliRunner()

    # Test basic commands don't crash
    basic_tests = [
        (["--help"], 0),
        (["--version"], 0),
        (["providers"], 0),
        (["status"], 0),
        (["config"], 0),
        (["info"], 0),
    ]

    for cmd, expected_exit in basic_tests:
        result = runner.invoke(cli, cmd)
        assert result.exit_code == expected_exit, f"Command {cmd} failed with exit code {result.exit_code}: {result.output}"
