import pytest
from click.testing import CliRunner
from tts_cli.tts import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Text-to-speech CLI' in result.output


def test_cli_missing_model():
    runner = CliRunner()
    result = runner.invoke(cli, ['Hello world'])
    assert result.exit_code == 1
    assert 'Error: You must specify a model' in result.output


def test_cli_unknown_model():
    runner = CliRunner()
    result = runner.invoke(cli, ['Hello world', '-m', 'unknown_model'])
    assert result.exit_code == 1
    assert 'Unknown model: unknown_model' in result.output


def test_cli_list_models():
    runner = CliRunner()
    result = runner.invoke(cli, ['-l'])
    assert result.exit_code == 0
    assert 'edge_tts' in result.output
    assert 'chatterbox' in result.output
    assert 'orpheus' in result.output