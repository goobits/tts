import pytest
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from tts_cli.providers.edge_tts import EdgeTTSProvider


@patch('tts_cli.providers.edge_tts.asyncio.run')
def test_edge_tts_synthesize(mock_asyncio_run):
    provider = EdgeTTSProvider()
    
    # Mock edge_tts module
    mock_edge_tts = Mock()
    mock_communicate = Mock()
    mock_edge_tts.Communicate.return_value = mock_communicate
    provider.edge_tts = mock_edge_tts
    
    # Test synthesis
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        provider.synthesize("Hello world", output_path, voice="en-US-JennyNeural")
        
        # Verify edge_tts was called correctly
        mock_edge_tts.Communicate.assert_called_once_with(
            "Hello world", 
            "en-US-JennyNeural", 
            rate="+0%", 
            pitch="+0Hz"
        )
        mock_asyncio_run.assert_called_once()
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_edge_tts_lazy_load_import_error():
    provider = EdgeTTSProvider()
    
    with patch('builtins.__import__', side_effect=ImportError):
        with pytest.raises(ImportError, match="edge-tts not installed"):
            provider._lazy_load()


def test_edge_tts_get_info():
    provider = EdgeTTSProvider()
    
    # Mock edge_tts module
    mock_edge_tts = Mock()
    provider.edge_tts = mock_edge_tts
    
    info = provider.get_info()
    
    assert info['name'] == 'Edge TTS'
    assert 'voice' in info['options']
    assert info['output_format'] == 'MP3'