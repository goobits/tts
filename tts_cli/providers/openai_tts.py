"""OpenAI TTS provider implementation."""

from ..base import TTSProvider
from ..exceptions import DependencyError, ProviderError, NetworkError
from ..config import get_api_key, is_ssml, strip_ssml_tags
from typing import Optional, Dict, Any
import logging
import tempfile
import subprocess


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS API provider with 6 high-quality voices."""
    
    # Available OpenAI TTS voices
    VOICES = {
        "alloy": "Balanced and versatile voice",
        "echo": "Clear and articulate voice", 
        "fable": "Warm and expressive voice",
        "nova": "Crisp and professional voice",
        "onyx": "Deep and authoritative voice",
        "shimmer": "Bright and energetic voice"
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._client = None
    
    def _get_client(self):
        """Get OpenAI client, initializing if needed."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise DependencyError(
                    "OpenAI library not installed. Install with: pip install openai"
                )
            
            api_key = get_api_key("openai")
            if not api_key:
                raise ProviderError(
                    "OpenAI API key not found. Set with: tts config openai_api_key YOUR_KEY"
                )
            
            self._client = OpenAI(api_key=api_key)
        
        return self._client
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        """Synthesize speech using OpenAI TTS API."""
        # Extract options
        voice = kwargs.get("voice", "nova")  # Default to nova voice
        stream = kwargs.get("stream", "false").lower() in ("true", "1", "yes")
        output_format = kwargs.get("output_format", "wav")
        
        # Handle SSML (OpenAI doesn't support SSML, so strip tags)
        if is_ssml(text):
            self.logger.warning("OpenAI TTS doesn't support SSML. Converting to plain text.")
            text = strip_ssml_tags(text)
        
        # Validate voice
        if voice not in self.VOICES:
            self.logger.warning(f"Unknown OpenAI voice '{voice}', using 'nova'")
            voice = "nova"
        
        try:
            client = self._get_client()
            
            # Generate speech
            self.logger.info(f"Generating speech with OpenAI voice '{voice}'")
            
            # OpenAI TTS API call
            response = client.audio.speech.create(
                model="tts-1",  # or "tts-1-hd" for higher quality
                voice=voice,
                input=text,
                response_format="mp3"  # OpenAI outputs MP3
            )
            
            # Save to temporary MP3 file first
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                response.stream_to_file(tmp_path)
            
            if stream:
                # Stream the audio
                self._stream_audio_file(tmp_path)
                # Clean up temp file
                import os
                os.unlink(tmp_path)
            else:
                # Convert to desired format if needed
                if output_format == "mp3":
                    # Direct save
                    import shutil
                    shutil.move(tmp_path, output_path)
                else:
                    # Convert using ffmpeg
                    self._convert_audio(tmp_path, output_path, output_format)
                    # Clean up temp file
                    import os
                    os.unlink(tmp_path)
                    
        except ImportError:
            raise DependencyError("OpenAI library not installed. Install with: pip install tts-cli[openai]")
        except Exception as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                raise ProviderError(f"OpenAI API authentication failed: {e}")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise NetworkError(f"OpenAI API network error: {e}")
            else:
                raise ProviderError(f"OpenAI TTS synthesis failed: {e}")
    
    def _stream_audio_file(self, audio_path: str) -> None:
        """Stream audio file to speakers using ffplay."""
        try:
            subprocess.run([
                'ffplay', '-nodisp', '-autoexit', audio_path
            ], stderr=subprocess.DEVNULL, check=True)
        except FileNotFoundError:
            raise DependencyError("ffplay not found. Please install ffmpeg for audio playback.")
        except subprocess.CalledProcessError as e:
            raise ProviderError(f"Audio playback failed: {e}")
    
    def _convert_audio(self, input_path: str, output_path: str, output_format: str) -> None:
        """Convert audio file to different format using ffmpeg."""
        try:
            subprocess.run([
                'ffmpeg', '-i', input_path, '-y', output_path
            ], stderr=subprocess.DEVNULL, check=True)
        except FileNotFoundError:
            raise DependencyError("ffmpeg not found. Please install ffmpeg for format conversion.")
        except subprocess.CalledProcessError as e:
            raise ProviderError(f"Audio conversion failed: {e}")
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """Get provider information including available voices."""
        # Check if API key is configured
        api_key = get_api_key("openai")
        api_status = "✅ Configured" if api_key else "❌ API key not set"
        
        return {
            "name": "OpenAI TTS",
            "description": "High-quality neural text-to-speech with 6 voices",
            "api_status": api_status,
            "sample_voices": list(self.VOICES.keys()),
            "voice_descriptions": self.VOICES,
            "options": {
                "voice": f"Voice to use ({', '.join(self.VOICES.keys())})",
                "stream": "Stream directly to speakers instead of saving to file (true/false)"
            },
            "features": {
                "ssml_support": False,
                "voice_cloning": False,
                "languages": "Multiple (auto-detected)",
                "quality": "High (tts-1 model)"
            },
            "pricing": "$15 per 1M characters",
            "output_format": "MP3 (converted to other formats via ffmpeg)"
        }