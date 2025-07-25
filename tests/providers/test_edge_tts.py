import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tts_cli.exceptions import DependencyError
from tts_cli.providers.edge_tts import EdgeTTSProvider


def test_edge_tts_synthesize():
    provider = EdgeTTSProvider()

    # Mock edge_tts module and the async communicate object
    mock_edge_tts = Mock()
    mock_communicate = AsyncMock()
    mock_edge_tts.Communicate.return_value = mock_communicate
    provider.edge_tts = mock_edge_tts

    # Test synthesis
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        output_path = tmp.name

    try:
        provider.synthesize("Hello world", output_path, voice="en-US-JennyNeural")

        # Verify edge_tts.Communicate was called correctly
        mock_edge_tts.Communicate.assert_called_once_with(
            "Hello world",
            "en-US-JennyNeural",
            rate="+0%",
            pitch="+0Hz"
        )

        # Verify save was called on the communicate object
        mock_communicate.save.assert_called_once_with(output_path)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_edge_tts_lazy_load_import_error():
    provider = EdgeTTSProvider()

    with patch('builtins.__import__', side_effect=ImportError):
        with pytest.raises(DependencyError, match="edge-tts not installed"):
            provider._lazy_load()


