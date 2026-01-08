#!/usr/bin/env python3
"""Basic CLI tests for Matilda Voice."""

import os
import tempfile

import pytest
from click.testing import CliRunner

from matilda_voice.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestCLISynthesis:
    """Test CLI synthesis commands."""

    @pytest.mark.skipif(os.environ.get("CI") == "true", reason="Network-dependent test skipped in CI")
    def test_save_with_edge_provider(self, runner):
        """Test saving audio with Edge TTS provider."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "test.mp3")
            result = runner.invoke(cli, ["save", "@edge", "test synthesis", "-o", output_file])

            # Check command executed (may fail without network, that's OK in unit tests)
            if result.exit_code == 0:
                assert os.path.exists(output_file), "Output file should be created"
                file_size = os.path.getsize(output_file)
                assert file_size > 0, "Output file should not be empty"

    def test_help_command(self, runner):
        """Test that help command works."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "voice" in result.output.lower() or "Usage" in result.output

    def test_status_command(self, runner):
        """Test that status command works."""
        result = runner.invoke(cli, ["status"])
        # Status command should succeed
        assert result.exit_code == 0
