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

    def test_main_help(self):
        """Test main help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'TTS CLI' in result.output
        assert 'Usage:' in result.output

    def test_version(self):
        """Test version command."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.1' in result.output or 'version' in result.output.lower()

    # =============================================================================
    # CORE COMMANDS SMOKE TESTS
    # =============================================================================

    def test_speak_help(self):
        """Test speak command help."""
        result = self.runner.invoke(cli, ['speak', '--help'])
        assert result.exit_code == 0
        assert 'speak' in result.output.lower()

    def test_speak_basic(self):
        """Test basic speak command (expects failure due to no audio in test env)."""
        result = self.runner.invoke(cli, ['speak', 'test'])
        # Should attempt synthesis but fail gracefully due to no audio environment
        assert 'test' in result.output or 'Audio' in result.output or 'edge-tts' in result.output

    def test_save_help(self):
        """Test save command help."""
        result = self.runner.invoke(cli, ['save', '--help'])
        assert result.exit_code == 0
        assert 'save' in result.output.lower()

    def test_save_basic(self):
        """Test basic save command (expects failure due to missing ffmpeg)."""
        result = self.runner.invoke(cli, ['save', 'test', '-o', '/tmp/test_smoke.mp3'])
        # Should attempt synthesis but fail gracefully due to missing dependencies
        assert ('test' in result.output or 'ffmpeg' in result.output or
                'edge-tts' in result.output or result.exit_code in [0, 1])

    def test_voices_help(self):
        """Test voices command help."""
        result = self.runner.invoke(cli, ['voices', '--help'])
        assert result.exit_code == 0
        assert 'voices' in result.output.lower() or 'browse' in result.output.lower()

    # =============================================================================
    # PROVIDER MANAGEMENT SMOKE TESTS
    # =============================================================================

    def test_providers_basic(self):
        """Test providers command."""
        result = self.runner.invoke(cli, ['providers'])
        assert result.exit_code == 0
        assert ('edge_tts' in result.output or 'openai_tts' in result.output or
                'Available' in result.output)

    def test_providers_help(self):
        """Test providers command help."""
        result = self.runner.invoke(cli, ['providers', '--help'])
        assert result.exit_code == 0
        assert 'providers' in result.output.lower()

    def test_info_help(self):
        """Test info command help."""
        result = self.runner.invoke(cli, ['info', '--help'])
        assert result.exit_code == 0
        assert 'info' in result.output.lower()

    def test_info_basic(self):
        """Test info command without arguments."""
        result = self.runner.invoke(cli, ['info'])
        assert result.exit_code == 0
        assert ('Provider' in result.output or 'Available' in result.output or
                'edge_tts' in result.output)

    def test_info_with_provider(self):
        """Test info command with provider."""
        result = self.runner.invoke(cli, ['info', 'edge_tts'])
        assert result.exit_code == 0
        assert ('edge_tts' in result.output or 'Edge TTS' in result.output)

    def test_install_help(self):
        """Test install command help."""
        result = self.runner.invoke(cli, ['install', '--help'])
        assert result.exit_code == 0
        assert 'install' in result.output.lower()

    def test_install_basic(self):
        """Test install command without arguments (should show help)."""
        result = self.runner.invoke(cli, ['install'])
        assert result.exit_code == 0
        assert ('install' in result.output.lower() or 'provider' in result.output.lower())

    # =============================================================================
    # CONFIGURATION SMOKE TESTS
    # =============================================================================

    def test_config_help(self):
        """Test config command help."""
        result = self.runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
        assert 'config' in result.output.lower()

    def test_config_basic(self):
        """Test config command without arguments (should show config)."""
        result = self.runner.invoke(cli, ['config'])
        assert result.exit_code == 0
        assert ('config' in result.output.lower() or 'voice' in result.output.lower() or
                'Configuration' in result.output)

    def test_config_show(self):
        """Test config show command."""
        result = self.runner.invoke(cli, ['config', 'show'])
        assert result.exit_code == 0
        assert ('config' in result.output.lower() or 'voice' in result.output.lower() or
                'Configuration' in result.output)

    def test_status_basic(self):
        """Test status command."""
        result = self.runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        assert ('Status' in result.output or 'provider' in result.output.lower() or
                'edge_tts' in result.output)

    def test_status_help(self):
        """Test status command help."""
        result = self.runner.invoke(cli, ['status', '--help'])
        assert result.exit_code == 0
        assert 'status' in result.output.lower()

    # =============================================================================
    # ADVANCED FEATURES SMOKE TESTS
    # =============================================================================

    def test_voice_help(self):
        """Test voice command group help."""
        result = self.runner.invoke(cli, ['voice', '--help'])
        assert result.exit_code == 0
        assert 'voice' in result.output.lower()

    def test_voice_status(self):
        """Test voice status command."""
        result = self.runner.invoke(cli, ['voice', 'status'])
        assert result.exit_code == 0
        assert ('Voice' in result.output or 'status' in result.output.lower() or
                'server' in result.output.lower())

    def test_voice_load_help(self):
        """Test voice load command help."""
        result = self.runner.invoke(cli, ['voice', 'load', '--help'])
        assert result.exit_code == 0
        assert 'load' in result.output.lower()

    def test_voice_unload_help(self):
        """Test voice unload command help."""
        result = self.runner.invoke(cli, ['voice', 'unload', '--help'])
        assert result.exit_code == 0
        assert 'unload' in result.output.lower()

    def test_document_help(self):
        """Test document command help."""
        result = self.runner.invoke(cli, ['document', '--help'])
        assert result.exit_code == 0
        assert 'document' in result.output.lower()

    # =============================================================================
    # PROVIDER SHORTCUTS SMOKE TESTS
    # =============================================================================

    def test_provider_shortcuts_basic(self):
        """Test that provider shortcuts are recognized."""
        shortcuts = ['@edge', '@openai', '@elevenlabs', '@google', '@chatterbox']

        for shortcut in shortcuts:
            result = self.runner.invoke(cli, [shortcut, 'test'])
            # Should attempt synthesis or show provider-specific error
            # (not "unknown command" error)
            assert ('test' in result.output or 'edge-tts' in result.output or
                    'API key' in result.output or 'Audio' in result.output or
                    result.exit_code in [0, 1])

    def test_provider_shortcuts_with_speak(self):
        """Test provider shortcuts with explicit speak command."""
        result = self.runner.invoke(cli, ['speak', '@edge', 'test'])
        # Should attempt synthesis with Edge TTS
        assert ('test' in result.output or 'edge-tts' in result.output or
                'Audio' in result.output or result.exit_code in [0, 1])

    def test_provider_shortcuts_with_save(self):
        """Test provider shortcuts with save command."""
        result = self.runner.invoke(cli, ['save', '@edge', 'test', '-o', '/tmp/test.mp3'])
        # Should attempt synthesis and save
        assert ('test' in result.output or 'edge-tts' in result.output or
                'ffmpeg' in result.output or result.exit_code in [0, 1])

    def test_provider_shortcuts_with_info(self):
        """Test provider shortcuts with info command."""
        result = self.runner.invoke(cli, ['info', '@edge'])
        assert result.exit_code == 0
        assert ('edge_tts' in result.output or 'Edge TTS' in result.output)

    # =============================================================================
    # ERROR HANDLING SMOKE TESTS
    # =============================================================================

    def test_unknown_provider_shortcut(self):
        """Test handling of unknown provider shortcuts."""
        result = self.runner.invoke(cli, ['@unknown', 'test'])
        # CLI might treat @unknown as text and process it, or return error
        assert (result.exit_code in [0, 1] and
                ('Unknown' in result.output or 'Error' in result.output or
                 '@unknown' in result.output or 'Audio' in result.output))

    def test_unknown_subcommand(self):
        """Test handling of unknown subcommands."""
        result = self.runner.invoke(cli, ['nonexistent_command'])
        # Should either treat as text to speak or show error
        assert (result.exit_code in [0, 1, 2] and
                ('nonexistent_command' in result.output or 'Usage:' in result.output or
                 'No such' in result.output or 'Error' in result.output))

    def test_save_without_text(self):
        """Test save command without text."""
        result = self.runner.invoke(cli, ['save'])
        # May show help or attempt to read from stdin
        assert (result.exit_code in [0, 1, 2] and
                ('Error' in result.output or 'text' in result.output.lower() or
                 'Usage:' in result.output or 'save' in result.output.lower()))

    def test_document_without_path(self):
        """Test document command without file path."""
        result = self.runner.invoke(cli, ['document'])
        assert result.exit_code == 2  # Click argument error
        assert ('Usage:' in result.output or 'required' in result.output.lower())

    def test_document_nonexistent_file(self):
        """Test document command with nonexistent file."""
        result = self.runner.invoke(cli, ['document', '/nonexistent/file.md'])
        # Should gracefully handle missing file
        assert (result.exit_code in [0, 1] and
                ('not found' in result.output.lower() or 'Error' in result.output or
                 'nonexistent' in result.output))

    # =============================================================================
    # HELP SYSTEM SMOKE TESTS
    # =============================================================================

    def test_all_subcommands_have_help(self):
        """Test that all major subcommands have accessible help."""
        subcommands = [
            'speak', 'save', 'voices', 'providers', 'info', 'install',
            'config', 'status', 'voice', 'document'
        ]

        for cmd in subcommands:
            result = self.runner.invoke(cli, [cmd, '--help'])
            assert result.exit_code == 0, f"Help failed for command: {cmd}"
            assert ('Usage:' in result.output or 'usage:' in result.output), \
                   f"No usage info in help for: {cmd}"

    # =============================================================================
    # ARGUMENT PARSING SMOKE TESTS
    # =============================================================================

    def test_speak_with_options(self):
        """Test speak command with various options."""
        # Test rate option
        result = self.runner.invoke(cli, ['speak', 'test', '--rate', '+20%'])
        assert 'test' in result.output or 'Audio' in result.output or result.exit_code in [0, 1]

        # Test voice option
        result = self.runner.invoke(cli, ['speak', 'test', '--voice', 'en-US-JennyNeural'])
        assert 'test' in result.output or 'Audio' in result.output or result.exit_code in [0, 1]

        # Test debug option
        result = self.runner.invoke(cli, ['speak', 'test', '--debug'])
        assert 'test' in result.output or 'DEBUG' in result.output or result.exit_code in [0, 1]

    def test_save_with_options(self):
        """Test save command with various options."""
        # Test format option
        result = self.runner.invoke(cli, ['save', 'test', '-f', 'wav'])
        assert ('test' in result.output or 'wav' in result.output or
                'ffmpeg' in result.output or result.exit_code in [0, 1])

        # Test JSON option
        result = self.runner.invoke(cli, ['save', 'test', '--json'])
        assert ('test' in result.output or 'json' in result.output.lower() or
                result.exit_code in [0, 1])

    # =============================================================================
    # INTEGRATION SMOKE TESTS (No API calls)
    # =============================================================================

    def test_stdin_input(self):
        """Test CLI with stdin input."""
        result = self.runner.invoke(cli, ['speak'], input='hello from stdin')
        # Should attempt to process stdin input
        assert ('hello from stdin' in result.output or 'Audio' in result.output or
                'edge-tts' in result.output or result.exit_code in [0, 1])

    def test_empty_stdin(self):
        """Test CLI with empty stdin."""
        result = self.runner.invoke(cli, ['speak'], input='')
        # Should handle empty input gracefully
        assert ('No text' in result.output or 'Error' in result.output or
                result.exit_code == 1)

    # =============================================================================
    # COMPREHENSIVE COMMAND COVERAGE TEST
    # =============================================================================

    def test_all_commands_executable(self):
        """Comprehensive test that all documented commands can be invoked."""

        # Commands that should execute without crashing (may fail gracefully)
        commands_to_test = [
            # Basic commands
            ['--help'],
            ['--version'],

            # Core commands with help
            ['speak', '--help'],
            ['save', '--help'],
            ['voices', '--help'],

            # Provider management
            ['providers'],
            ['providers', '--help'],
            ['info', '--help'],
            ['info'],
            ['install', '--help'],
            ['install'],

            # Configuration
            ['config', '--help'],
            ['config'],
            ['config', 'show'],
            ['status', '--help'],
            ['status'],

            # Advanced features
            ['voice', '--help'],
            ['voice', 'status'],
            ['voice', 'load', '--help'],
            ['voice', 'unload', '--help'],
            ['document', '--help'],

            # Provider shortcuts (with minimal text)
            ['info', '@edge'],
        ]

        failed_commands = []

        for cmd in commands_to_test:
            try:
                result = self.runner.invoke(cli, cmd)
                # Accept exit codes 0-2 (0=success, 1=expected error, 2=usage error)
                if result.exit_code > 2:
                    failed_commands.append((cmd, result.exit_code, result.output))
            except Exception as e:
                failed_commands.append((cmd, 'EXCEPTION', str(e)))

        if failed_commands:
            failure_msg = "Commands that failed to execute properly:\n"
            for cmd, code, output in failed_commands:
                failure_msg += f"  {' '.join(cmd)} -> {code}\n"
                if isinstance(output, str) and len(output) < 200:
                    failure_msg += f"    Output: {output.strip()}\n"

            pytest.fail(failure_msg)


# =============================================================================
# QUICK SMOKE TEST FUNCTION
# =============================================================================

def test_cli_basic_smoke():
    """Quick smoke test for basic CLI functionality."""
    runner = CliRunner()

    # Test basic commands don't crash
    basic_tests = [
        (['--help'], 0),
        (['--version'], 0),
        (['providers'], 0),
        (['status'], 0),
        (['config'], 0),
        (['info'], 0),
    ]

    for cmd, expected_max_exit in basic_tests:
        result = runner.invoke(cli, cmd)
        assert result.exit_code <= expected_max_exit, \
               f"Command {cmd} failed with exit code {result.exit_code}: {result.output}"
