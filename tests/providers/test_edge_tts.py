import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from matilda_voice.exceptions import DependencyError
from matilda_voice.providers.edge_tts import EdgeTTSProvider


def test_edge_tts_synthesize():
    """Test EdgeTTSProvider synthesis with real provider logic."""
    provider = EdgeTTSProvider()

    # Mock only the edge_tts module import, not the provider itself
    mock_edge_tts = Mock()
    mock_communicate = AsyncMock()

    # Create a more realistic mock that simulates actual edge_tts behavior
    async def mock_save_impl(path):
        """Simulate edge_tts creating an actual audio file."""
        with open(path, "wb") as f:
            f.write(b"Mock MP3 audio data from edge_tts")

    mock_communicate.save.side_effect = mock_save_impl
    mock_edge_tts.Communicate.return_value = mock_communicate

    # Inject the mock into the provider
    provider.edge_tts = mock_edge_tts

    # Test synthesis with various parameters
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        output_path = tmp.name

    try:
        # Test basic synthesis
        provider.synthesize("Hello world", output_path, voice="en-US-JennyNeural")

        # Verify edge_tts.Communicate was called with correct parameters
        mock_edge_tts.Communicate.assert_called_once_with("Hello world", "en-US-JennyNeural", rate="+0%", pitch="+0Hz")

        # Verify save was called on the communicate object
        mock_communicate.save.assert_called_once_with(output_path)

        # Verify the output file was actually created
        assert os.path.exists(output_path), "Output file should exist"
        assert os.path.getsize(output_path) > 0, "Output file should not be empty"

        # Test with custom rate and pitch
        mock_edge_tts.Communicate.reset_mock()
        mock_communicate.save.reset_mock()

        provider.synthesize("Test with options", output_path, voice="en-GB-SoniaNeural", rate="+20%", pitch="-5Hz")

        # Verify custom parameters were passed
        mock_edge_tts.Communicate.assert_called_once_with(
            "Test with options", "en-GB-SoniaNeural", rate="+20%", pitch="-5Hz"
        )

    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_edge_tts_lazy_load_import_error():
    provider = EdgeTTSProvider()

    with patch("builtins.__import__", side_effect=ImportError):
        with pytest.raises(DependencyError, match="edge-tts not installed"):
            provider._lazy_load()
