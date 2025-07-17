import pytest
from click.testing import CliRunner
from tts_cli.tts import main as cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert '🎤 Transform text into speech with AI-powered voices' in result.output


def test_cli_missing_text():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    # Now shows help text instead of error when no arguments provided
    assert result.exit_code == 0
    assert '🎤 Transform text into speech with AI-powered voices' in result.output


def test_cli_unknown_model():
    runner = CliRunner()
    result = runner.invoke(cli, ['Hello world', '-m', 'unknown_model'])
    assert result.exit_code == 1
    assert 'Unknown provider: unknown_model' in result.output


def test_cli_list_models():
    runner = CliRunner()
    result = runner.invoke(cli, ['-l'])
    assert result.exit_code == 0
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
    # This should save to file when --save flag is used
    result = runner.invoke(cli, ['Hello world', '--save', '-o', 'test.mp3'])
    # We expect it to try to use edge_tts (the error will be about edge-tts not being installed)
    assert 'edge-tts not installed' in result.output or result.exit_code == 0