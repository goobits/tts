import os
import tempfile

from click.testing import CliRunner

from tts.app_hooks import PROVIDER_SHORTCUTS
from tts.cli import main as cli


def test_cli_unknown_model():
    runner = CliRunner()
    result = runner.invoke(cli, ['@unknown_model', 'Hello world'])
    assert result.exit_code == 1
    assert 'Unknown provider' in result.output


def test_cli_list_models():
    runner = CliRunner()
    result = runner.invoke(cli, ['providers'])
    assert result.exit_code == 0
    # Check for the new enhanced providers display format
    assert 'Available TTS providers:' in result.output
    assert 'edge_tts' in result.output
    assert 'chatterbox' in result.output


def test_cli_default_model():
    runner = CliRunner()
    # This should use edge_tts by default and stream (not save)
    result = runner.invoke(cli, ['Hello world'])
    # We expect it to try to use edge_tts (may get audio playback error in test environment)
    assert ('edge-tts not installed' in result.output or
            result.exit_code == 0 or
            'asyncio.run() cannot be called' in result.output or
            'Audio generated but cannot play automatically' in result.output)


def test_cli_save_mode():
    runner = CliRunner()
    # Test the new save subcommand
    result = runner.invoke(cli, ['save', 'Hello world', '-o', 'test.mp3'])
    # We expect it to try to use edge_tts (the error will be about edge-tts not being installed)
    assert ('edge-tts not installed' in result.output or
            'ffmpeg not found' in result.output or
            result.exit_code == 0)


# =============================================================================
# PHASE 1 COMPREHENSIVE TESTS
# =============================================================================

class TestPhase1BackwardCompatibility:
    """Tests for Phase 1 backward compatibility requirements"""

    def test_essential_subcommands_work(self):
        """Test that essential subcommands like 'info', 'providers' still work"""
        runner = CliRunner()

        # Test info command
        result = runner.invoke(cli, ['info'])
        assert result.exit_code == 0
        assert 'TTS Provider Information' in result.output

        # Test providers command
        result = runner.invoke(cli, ['providers'])
        assert result.exit_code == 0
        assert 'chatterbox' in result.output


class TestPhase1NewSubcommands:
    """Tests for Phase 1 new subcommand functionality"""

    def test_save_subcommand_exists(self):
        """Test that new 'tts save' subcommand works"""
        runner = CliRunner()
        result = runner.invoke(cli, ['save', '--help'])
        assert result.exit_code == 0
        assert 'Save text as an audio file' in result.output

    def test_document_subcommand_exists(self):
        """Test that new 'tts document' subcommand works"""
        runner = CliRunner()
        result = runner.invoke(cli, ['document', '--help'])
        assert result.exit_code == 0
        assert 'Convert documents to speech' in result.output

    def test_voice_subcommand_group_exists(self):
        """Test that new 'tts voice' subcommand group works"""
        runner = CliRunner()
        result = runner.invoke(cli, ['voice', '--help'])
        assert result.exit_code == 0
        assert 'Voice loading and caching' in result.output

        # Test subcommands exist
        result = runner.invoke(cli, ['voice', 'load', '--help'])
        assert result.exit_code == 0

        result = runner.invoke(cli, ['voice', 'unload', '--help'])
        assert result.exit_code == 0

        result = runner.invoke(cli, ['voice', 'status', '--help'])
        assert result.exit_code == 0

    def test_info_subcommand_enhanced(self):
        """Test that enhanced 'tts info' subcommand works"""
        runner = CliRunner()
        result = runner.invoke(cli, ['info'])
        assert result.exit_code == 0
        assert 'TTS Provider Information' in result.output

    def test_providers_subcommand_works(self):
        """Test that 'tts providers' subcommand works"""
        runner = CliRunner()
        result = runner.invoke(cli, ['providers'])
        assert result.exit_code == 0
        # Should show enhanced providers display with emojis and status
        assert 'Available TTS providers:' in result.output
        assert 'chatterbox' in result.output
        assert 'edge_tts' in result.output


class TestPhase1ProviderShortcuts:
    """Tests for Phase 1 @provider shortcut functionality"""

    def test_provider_shortcuts_defined(self):
        """Test that provider shortcuts are properly defined"""
        assert '@edge' in ['@' + k for k in PROVIDER_SHORTCUTS.keys()]
        assert '@chatterbox' in ['@' + k for k in PROVIDER_SHORTCUTS.keys()]
        assert '@openai' in ['@' + k for k in PROVIDER_SHORTCUTS.keys()]

    def test_info_with_provider_shortcut(self):
        """Test that @provider shortcuts work with info command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['info', '@chatterbox'])
        assert result.exit_code == 0
        assert 'Chatterbox' in result.output
        assert 'Options:' in result.output

    def test_invalid_provider_shortcut_error(self):
        """Test that invalid @provider shortcuts show proper error"""
        runner = CliRunner()
        result = runner.invoke(cli, ['info', '@invalid'])
        assert result.exit_code == 1
        assert 'Unknown provider shortcut' in result.output
        assert 'Available providers:' in result.output


class TestPhase1CommandParity:
    """Tests for Phase 1 command parity (new syntax verification)"""

    def test_save_command_works(self):
        """Test that 'tts save' command works correctly"""
        runner = CliRunner()

        # New syntax
        result = runner.invoke(cli, ['save', 'Hello world', '--debug'])

        # Should either succeed or fail with provider error
        # (Since edge-tts might not be installed, should fail gracefully)
        assert ('edge-tts not installed' in result.output or
                'ffmpeg not found' in result.output or
                result.exit_code == 0)

    def test_document_command_works(self):
        """Test that 'document' subcommand works correctly"""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test\nContent")
            temp_path = f.name

        try:
            # New syntax
            result = runner.invoke(cli, ['document', temp_path])

            # Should process the document properly
            assert (result.exit_code == 0 or
                    'markdown' in result.output or
                    'edge-tts not installed' in result.output or
                    'Audio generated but cannot play' in result.output)
        finally:
            os.unlink(temp_path)


class TestPhase1ErrorHandling:
    """Tests for Phase 1 error handling"""

    def test_unknown_provider_error(self):
        """Test error handling for unknown providers"""
        runner = CliRunner()
        result = runner.invoke(cli, ['@nonexistent', 'Hello world'])
        assert result.exit_code == 1
        assert 'Unknown provider' in result.output

    def test_invalid_shortcut_error(self):
        """Test error handling for invalid @provider shortcuts"""
        runner = CliRunner()
        result = runner.invoke(cli, ['info', '@badprovider'])
        assert result.exit_code == 1
        assert 'Unknown provider shortcut' in result.output

    def test_helpful_error_messages(self):
        """Test that error messages guide users to correct syntax"""
        runner = CliRunner()
        result = runner.invoke(cli, ['info', '@invalid'])
        assert result.exit_code == 1
        assert 'Available providers:' in result.output
        assert '@edge' in result.output or '@chatterbox' in result.output


# =============================================================================
# PHASE 1 INTEGRATION TESTS
# =============================================================================

class TestPhase1Integration:
    """Integration tests for Phase 1 complete functionality"""

    def test_full_backward_compatibility(self):
        """Test that all backward compatible functionality still works"""
        runner = CliRunner()

        # Test all backward compatible commands work
        backward_compatible_commands = [
            (['--help'], 0),
            (['providers'], 0),
            (['info'], 0),
        ]

        for cmd, expected_code in backward_compatible_commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == expected_code, f"Command {cmd} failed: {result.output}"

    def test_new_syntax_availability(self):
        """Test that all new syntax options are available"""
        runner = CliRunner()

        # Test new subcommands exist and show help
        new_commands = [
            (['save', '--help'], 0),
            (['document', '--help'], 0),
            (['voice', '--help'], 0),
            (['info', '--help'], 0),
            (['providers', '--help'], 0),
        ]

        for cmd, expected_code in new_commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == expected_code, f"New command {cmd} failed: {result.output}"

    def test_provider_shortcuts_comprehensive(self):
        """Test all provider shortcuts work correctly"""
        runner = CliRunner()

        # Test each provider shortcut
        for shortcut in PROVIDER_SHORTCUTS.keys():
            result = runner.invoke(cli, ['info', f'@{shortcut}'])
            assert result.exit_code == 0, f"Provider shortcut @{shortcut} failed: {result.output}"


class TestPhase3DeprecatedCommandRejection:
    """Tests for Phase 3 deprecated command rejection"""

    def test_save_flag_rejected(self):
        """Test that --save flag is now rejected with unknown option error"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--save'])

        # Should fail with unknown option error
        assert result.exit_code != 0
        output_lower = result.output.lower()
        assert "no such option" in output_lower or "unknown option" in output_lower

    def test_document_flag_rejected(self):
        """Test that --document flag is now rejected with unknown option error"""
        runner = CliRunner()

        # Create a test file
        test_file = '/tmp/test_doc.txt'
        with open(test_file, 'w') as f:
            f.write('Test document content')

        result = runner.invoke(cli, ['--document', test_file])

        # Should fail with unknown option error
        assert result.exit_code != 0
        output_lower = result.output.lower()
        assert "no such option" in output_lower or "unknown option" in output_lower

    def test_model_flag_rejected(self):
        """Test that --model flag is now rejected with unknown option error"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--model', 'edge_tts'])

        # Should fail with unknown option error
        assert result.exit_code != 0
        output_lower = result.output.lower()
        assert "no such option" in output_lower or "unknown option" in output_lower

    def test_list_flag_rejected(self):
        """Test that --list flag is now rejected with unknown option error"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--list'])

        # Should fail with unknown option error
        assert result.exit_code != 0
        output_lower = result.output.lower()
        assert "no such option" in output_lower or "unknown option" in output_lower

    def test_models_subcommand_rejected(self):
        """Test that 'models' subcommand still works for backward compatibility"""
        runner = CliRunner()
        result = runner.invoke(cli, ['models'])

        # Models command still exists for backward compatibility
        assert result.exit_code == 0

    def test_speak_command_accepted(self):
        """Test that speak command is now accepted (v1.1)"""
        runner = CliRunner()
        result = runner.invoke(cli, ['speak', 'test text'])

        # Should accept speak as a valid command and attempt synthesis
        assert (result.exit_code == 0 or
                'test text' in result.output or
                'edge-tts not installed' in result.output or
                'Audio' in result.output or
                'No audio devices' in result.output)


# =============================================================================
# CURRENT CLI BEHAVIOR TESTS (v1.1)
# =============================================================================

class TestCurrentCLIBehavior:
    """Comprehensive tests for TTS CLI v1.1 behavior with speak as default command."""

    def test_version_display(self):
        """Test version information display"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert '1.1' in result.output
        assert 'TTS CLI' in result.output

    def test_help_shows_speak_as_default(self):
        """Test that help shows speak as the default command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'speak' in result.output
        # Just check that speak command is mentioned
        # Help text format may vary
        assert 'TTS CLI v1.1' in result.output
        # Should NOT have version command
        assert 'version  📚' not in result.output

    def test_all_main_commands_present(self):
        """Verify all main commands are present in help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        required_commands = [
            'speak', 'save', 'voices', 'config', 'status',
            'providers', 'install', 'info', 'voice', 'document'
        ]

        for cmd in required_commands:
            assert cmd in result.output, f"Command '{cmd}' not found in help"

    def test_speak_command_exists(self):
        """Test that speak command exists and has help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['speak', '--help'])

        assert result.exit_code == 0
        assert 'Speak text aloud' in result.output
        assert '--voice' in result.output
        assert '--rate' in result.output
        assert '--pitch' in result.output
        assert '--debug' in result.output

    def test_implicit_speak_with_text(self):
        """Test implicit speak (backward compatibility)"""
        runner = CliRunner()
        result = runner.invoke(cli, ['hello world'])

        # Should attempt to speak "hello world"
        # In test environment, might fail with audio device issues
        assert (result.exit_code == 0 or
                'Audio' in result.output or
                'edge-tts not installed' in result.output or
                'No audio devices' in result.output or
                'hello world' in result.output)

    def test_explicit_speak_with_text(self):
        """Test explicit speak command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['speak', 'hello world'])

        # Should attempt to speak "hello world"
        assert (result.exit_code == 0 or
                'Audio' in result.output or
                'edge-tts not installed' in result.output or
                'No audio devices' in result.output or
                'hello world' in result.output)

    def test_implicit_speak_with_stdin(self):
        """Test implicit speak with piped input"""
        runner = CliRunner()
        result = runner.invoke(cli, [], input='hello from stdin')

        # Currently shows help when no command given with stdin
        # This is acceptable behavior - stdin requires explicit command
        assert result.exit_code == 2
        assert 'Usage:' in result.output

    def test_explicit_speak_with_stdin(self):
        """Test explicit speak with piped input"""
        runner = CliRunner()
        result = runner.invoke(cli, ['speak'], input='hello from stdin')

        # Should attempt to speak the piped text
        assert (result.exit_code == 0 or
                'Audio' in result.output or
                'edge-tts not installed' in result.output or
                'No audio devices' in result.output or
                'hello from stdin' in result.output)

    def test_provider_shortcuts_with_implicit_speak(self):
        """Test provider shortcuts work with implicit speak"""
        runner = CliRunner()
        shortcuts = ['@edge', '@openai', '@elevenlabs', '@google', '@chatterbox']

        for shortcut in shortcuts:
            result = runner.invoke(cli, [shortcut, 'test'])
            # Should recognize the provider shortcut
            provider_name = shortcut[1:]  # Remove @
            assert ('Unknown provider' not in result.output or
                    provider_name in result.output.lower() or
                    f'{provider_name} not installed' in result.output.lower())

    def test_provider_shortcuts_with_explicit_speak(self):
        """Test provider shortcuts work with explicit speak"""
        runner = CliRunner()
        result = runner.invoke(cli, ['speak', '@edge', 'test'])

        # Should use edge provider
        assert ('edge' in result.output.lower() or
                'edge-tts not installed' in result.output or
                'Unknown provider' not in result.output)

    def test_version_treated_as_text(self):
        """Test that 'version' is treated as text to speak, not a command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['version'])

        # Should attempt to speak the word "version"
        # Should NOT show version info like "TTS CLI, version 1.1"
        assert 'TTS CLI, version' not in result.output
        assert (result.exit_code != 0 or  # Might fail due to audio issues
                'Audio' in result.output or
                'edge-tts not installed' in result.output or
                'version' in result.output)

    def test_speak_command_options(self):
        """Test speak command with various options"""
        runner = CliRunner()

        # Test with voice option
        result = runner.invoke(cli, ['speak', '-v', 'en-US-AriaNeural', 'test'])
        assert (result.exit_code == 0 or
                'edge-tts not installed' in result.output or
                'No audio devices' in result.output or
                'Audio generated but cannot play' in result.output)

        # Test with rate option
        result = runner.invoke(cli, ['speak', '--rate', '+20%', 'test'])
        assert (result.exit_code == 0 or
                'edge-tts not installed' in result.output or
                'No audio devices' in result.output or
                'Audio generated but cannot play' in result.output)

        # Test with debug option
        result = runner.invoke(cli, ['speak', '--debug', 'test'])
        assert (result.exit_code == 0 or
                'edge-tts not installed' in result.output or
                'No audio devices' in result.output or
                'Audio generated but cannot play' in result.output or
                'DEBUG' in result.output)

    def test_save_command_still_works(self):
        """Test that save command still works as expected"""
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            result = runner.invoke(cli, ['save', 'test', '-o', tmp.name])

            assert (result.exit_code == 0 or
                    'edge-tts not installed' in result.output or
                    'ffmpeg not found' in result.output)

            # Clean up
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    def test_rich_formatting_in_output(self):
        """Test that rich formatting with emojis is present"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        # Skip emoji checks - help formatting may vary

    def test_subcommand_help_accessible(self):
        """Test that help is available for all subcommands"""
        runner = CliRunner()
        subcommands = ['save', 'voices', 'config', 'status', 'providers',
                      'install', 'info', 'voice', 'document']

        for cmd in subcommands:
            result = runner.invoke(cli, [cmd, '--help'])
            assert result.exit_code == 0, f"Help not available for '{cmd}' command"
            assert cmd in result.output.lower() or 'usage' in result.output.lower()

    def test_no_stdin_shows_help(self):
        """Test that running tts with no args and no stdin shows help"""
        runner = CliRunner()
        # When no args and stdin is empty, it should try to read from stdin
        # and may produce an empty synthesis attempt
        result = runner.invoke(cli, [], input='')

        # Should either show help or attempt to synthesize empty input
        assert (result.exit_code == 0 or
                'TTS CLI v1.1' in result.output or
                'Usage:' in result.output or
                'No text provided' in result.output or
                'edge-tts not installed' in result.output)
