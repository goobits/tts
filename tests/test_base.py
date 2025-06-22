import pytest
from tts_cli.base import TTSProvider


def test_tts_provider_is_abstract():
    with pytest.raises(TypeError):
        TTSProvider()


def test_tts_provider_abstract_methods():
    class MockProvider(TTSProvider):
        pass
    
    with pytest.raises(TypeError):
        MockProvider()


def test_tts_provider_concrete_implementation():
    class ConcreteProvider(TTSProvider):
        def synthesize(self, text: str, output_path: str, **kwargs) -> None:
            pass
    
    provider = ConcreteProvider()
    assert hasattr(provider, 'synthesize')
    assert hasattr(provider, 'get_info')
    assert provider.get_info() is None