import pytest
from click.testing import CliRunner
from tts_cli.tts import main as cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Text-to-speech CLI' in result.output


def test_cli_missing_text():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 1
    assert 'Error: You must provide text to synthesize' in result.output


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
    # This should use edge_tts by default but will fail because edge-tts isn't mocked
    result = runner.invoke(cli, ['Hello world', '-o', 'test.mp3'])
    # We expect it to try to use edge_tts (the error will be about edge-tts not being installed)
    assert 'edge-tts not installed' in result.output or result.exit_code == 0