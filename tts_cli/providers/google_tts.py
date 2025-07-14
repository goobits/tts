"""Google Cloud Text-to-Speech provider implementation."""

from ..base import TTSProvider
from ..exceptions import DependencyError, ProviderError, NetworkError
from ..config import get_api_key, is_ssml
from typing import Optional, Dict, Any, List
import logging
import tempfile
import subprocess
import base64


class GoogleTTSProvider(TTSProvider):
    """Google Cloud TTS provider with 380+ voices and full SSML support."""
    
    # Popular Google voices for quick reference
    POPULAR_VOICES = {
        "en-US-Neural2-A": "US English, Neural2, Female",
        "en-US-Neural2-C": "US English, Neural2, Female", 
        "en-US-Neural2-D": "US English, Neural2, Male",
        "en-US-Neural2-F": "US English, Neural2, Female",
        "en-US-Neural2-G": "US English, Neural2, Female",
        "en-US-Neural2-H": "US English, Neural2, Female",
        "en-US-Neural2-I": "US English, Neural2, Male",
        "en-US-Neural2-J": "US English, Neural2, Male",
        "en-GB-Neural2-A": "UK English, Neural2, Female",
        "en-GB-Neural2-B": "UK English, Neural2, Male",
        "en-GB-Neural2-C": "UK English, Neural2, Female",
        "en-AU-Neural2-A": "Australian English, Neural2, Female",
        "en-AU-Neural2-B": "Australian English, Neural2, Male",
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._client = None
        self._voices_cache = None
    
    def _get_client(self):
        """Get Google Cloud TTS client, initializing if needed."""
        if self._client is None:
            try:
                from google.cloud import texttospeech
            except ImportError:
                raise DependencyError(
                    "Google Cloud TTS library not installed. Install with: pip install google-cloud-texttospeech"
                )
            
            api_key = get_api_key("google")
            if not api_key:
                raise ProviderError(
                    "Google Cloud API key not found. Set with: tts config google_api_key YOUR_KEY"
                )
            
            # Handle different authentication methods
            if api_key.startswith("AIza"):
                # API key authentication
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""  # Clear any existing
                self._client = texttospeech.TextToSpeechClient.from_service_account_info({
                    "type": "service_account",
                    "client_id": "",
                    "client_email": "",
                    "private_key": "",
                    "api_key": api_key
                })
            elif api_key.startswith("{"):
                # Service account JSON string
                import json
                credentials_info = json.loads(api_key)
                self._client = texttospeech.TextToSpeechClient.from_service_account_info(credentials_info)
            else:
                # OAuth token or other
                self._client = texttospeech.TextToSpeechClient()
        
        return self._client
    
    def _get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of all available voices from Google Cloud."""
        if self._voices_cache is None:
            try:
                client = self._get_client()
                response = client.list_voices()
                
                voices = []
                for voice in response.voices:
                    for language_code in voice.language_codes:
                        voice_info = {
                            "name": voice.name,
                            "language": language_code,
                            "gender": voice.ssml_gender.name,
                            "type": "Neural2" if "Neural2" in voice.name else "WaveNet" if "Wavenet" in voice.name else "Standard"
                        }
                        voices.append(voice_info)
                
                self._voices_cache = voices
            except Exception as e:
                self.logger.warning(f"Failed to fetch Google voices: {e}")
                self._voices_cache = []
        
        return self._voices_cache
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        """Synthesize speech using Google Cloud TTS API."""
        # Extract options
        voice = kwargs.get("voice", "en-US-Neural2-A")  # Default voice
        stream = kwargs.get("stream", "false").lower() in ("true", "1", "yes")
        output_format = kwargs.get("output_format", "wav")
        speaking_rate = float(kwargs.get("speaking_rate", "1.0"))
        pitch = float(kwargs.get("pitch", "0.0"))
        
        # Auto-detect SSML
        use_ssml = is_ssml(text)
        
        try:
            from google.cloud import texttospeech
            
            client = self._get_client()
            
            # Prepare synthesis input
            if use_ssml:
                synthesis_input = texttospeech.SynthesisInput(ssml=text)
                self.logger.info("Using SSML input")
            else:
                synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Parse voice name and set up voice selection
            if ":" in voice:
                # Format like "google:en-US-Neural2-A"
                _, voice_name = voice.split(":", 1)
            else:
                voice_name = voice
            
            # Extract language code from voice name (e.g., "en-US-Neural2-A" -> "en-US")
            parts = voice_name.split("-")
            if len(parts) >= 2:
                language_code = f"{parts[0]}-{parts[1]}"
            else:
                language_code = "en-US"
                self.logger.warning(f"Could not parse language from voice '{voice_name}', using en-US")
            
            voice_selection = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            
            # Audio configuration
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # WAV format
                speaking_rate=speaking_rate,
                pitch=pitch
            )
            
            # Perform synthesis
            self.logger.info(f"Generating speech with Google voice '{voice_name}'")
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_selection, 
                audio_config=audio_config
            )
            
            # Save audio content to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                tmp_file.write(response.audio_content)
            
            if stream:
                # Stream the audio
                self._stream_audio_file(tmp_path)
                # Clean up temp file
                import os
                os.unlink(tmp_path)
            else:
                # Convert to desired format if needed
                if output_format == "wav":
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
            raise DependencyError("Google Cloud TTS library not installed. Install with: pip install tts-cli[google]")
        except Exception as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower() or "credentials" in str(e).lower():
                raise ProviderError(f"Google Cloud authentication failed: {e}")
            elif "quota" in str(e).lower() or "billing" in str(e).lower():
                raise ProviderError(f"Google Cloud quota/billing error: {e}")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise NetworkError(f"Google Cloud API network error: {e}")
            else:
                raise ProviderError(f"Google TTS synthesis failed: {e}")
    
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
        api_key = get_api_key("google")
        api_status = "✅ Configured" if api_key else "❌ API key not set"
        
        # Get voice count
        try:
            all_voices = self._get_available_voices()
            voice_count = len(all_voices)
            voice_list = [f"{v['name']} ({v['language']}, {v['type']}, {v['gender']})" 
                         for v in all_voices[:20]]  # Show first 20
            if voice_count > 20:
                voice_list.append(f"... and {voice_count - 20} more voices")
        except Exception:
            voice_count = "380+"
            voice_list = [f"{name}: {desc}" for name, desc in self.POPULAR_VOICES.items()]
        
        return {
            "name": "Google Cloud TTS",
            "description": f"Enterprise-grade TTS with {voice_count} voices and full SSML support",
            "api_status": api_status,
            "sample_voices": list(self.POPULAR_VOICES.keys()),
            "all_voices": voice_list,
            "voice_descriptions": self.POPULAR_VOICES,
            "options": {
                "voice": f"Voice to use (e.g., {list(self.POPULAR_VOICES.keys())[0]})",
                "speaking_rate": "Speaking rate (0.25-4.0, default: 1.0)",
                "pitch": "Pitch adjustment (-20.0 to 20.0, default: 0.0)",
                "stream": "Stream directly to speakers instead of saving to file (true/false)"
            },
            "features": {
                "ssml_support": True,
                "voice_cloning": False,
                "languages": "40+ languages",
                "quality": "Highest (Neural2, WaveNet, Standard voices)"
            },
            "pricing": "$4 per 1M characters (WaveNet/Neural2), $0.4/1M (Standard)",
            "output_format": "WAV 16kHz (converted to other formats via ffmpeg)"
        }