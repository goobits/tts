"""Google Cloud TTS provider implementation."""

from ..base import TTSProvider
from ..exceptions import DependencyError, ProviderError, NetworkError
from ..config import get_api_key, is_ssml, strip_ssml_tags
from typing import Optional, Dict, Any, List
import logging
import tempfile
import subprocess
import requests
import json
import base64


class GoogleTTSProvider(TTSProvider):
    """Google Cloud TTS provider with 380+ voices and full SSML support."""
    
    # Sample voices (a subset of available voices)
    SAMPLE_VOICES = {
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
        self._voices_cache = None
        self.base_url = "https://texttospeech.googleapis.com/v1"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request to Google Cloud TTS API."""
        api_key = get_api_key("google")
        if not api_key:
            raise ProviderError(
                "Google Cloud API key not found. Set with: tts config google_api_key YOUR_KEY"
            )
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = {"key": api_key}
        
        try:
            response = requests.request(method, url, params=params, **kwargs)
            return response
        except requests.RequestException as e:
            raise NetworkError(f"Google Cloud TTS API request failed: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information and capabilities."""
        api_key = get_api_key("google")
        api_status = "✅ Configured" if api_key else "❌ No API key"
        
        # Try to get voice count
        all_voices = self._get_all_voices()
        voice_count = len(all_voices) if all_voices else 0
        
        return {
            "name": "Google Cloud TTS",
            "description": f"Enterprise-grade TTS with {voice_count} voices and full SSML support",
            "api_status": api_status,
            "sample_voices": list(self.SAMPLE_VOICES.keys()),
            "all_voices": all_voices,
            "voice_descriptions": self.SAMPLE_VOICES,
            "options": {
                "voice": "Voice to use (e.g., en-US-Neural2-A)",
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
    
    def _get_all_voices(self) -> List[str]:
        """Fetch all available voices from Google Cloud TTS API."""
        if self._voices_cache is not None:
            return self._voices_cache
        
        try:
            response = self._make_request("GET", "/voices")
            
            if response.status_code == 200:
                data = response.json()
                voices = []
                for voice in data.get("voices", []):
                    voices.append(voice["name"])
                self._voices_cache = voices
                self.logger.info(f"Fetched {len(voices)} Google voices")
            else:
                self.logger.warning(f"Failed to fetch voices: HTTP {response.status_code}")
                self._voices_cache = []
        except Exception as e:
            self.logger.warning(f"Failed to fetch Google voices: {e}")
            self._voices_cache = []
        
        return self._voices_cache
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        """Synthesize speech using Google Cloud TTS REST API."""
        # Extract options
        voice = kwargs.get("voice", "en-US-Neural2-A")  # Default voice
        stream = kwargs.get("stream", "false").lower() in ("true", "1", "yes")
        output_format = kwargs.get("output_format", "wav")
        speaking_rate = float(kwargs.get("speaking_rate", "1.0"))
        pitch = float(kwargs.get("pitch", "0.0"))
        
        # Auto-detect SSML
        use_ssml = is_ssml(text)
        
        # Parse voice name
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
        
        # Prepare request payload
        payload = {
            "input": {
                "ssml" if use_ssml else "text": text
            },
            "voice": {
                "languageCode": language_code,
                "name": voice_name
            },
            "audioConfig": {
                "audioEncoding": "LINEAR16",  # WAV format
                "speakingRate": speaking_rate,
                "pitch": pitch
            }
        }
        
        self.logger.info(f"Generating speech with Google voice '{voice_name}'")
        if use_ssml:
            self.logger.info("Using SSML input")
        
        try:
            # Make synthesis request
            response = self._make_request(
                "POST", 
                "/text:synthesize",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                error_msg = f"Google Cloud TTS API error {response.status_code}"
                try:
                    error_detail = response.json()
                    if "error" in error_detail:
                        error_msg += f": {error_detail['error'].get('message', 'Unknown error')}"
                except:
                    error_msg += f": {response.text}"
                raise ProviderError(error_msg)
            
            # Get audio content from response
            response_data = response.json()
            audio_content = base64.b64decode(response_data["audioContent"])
            
            # Save audio content to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                tmp_file.write(audio_content)
            
            if stream:
                # Stream the audio
                self._stream_audio_file(tmp_path)
                # Clean up temp file
                import os
                os.unlink(tmp_path)
            else:
                # Convert and save to final output path
                if output_format.lower() != "wav":
                    self._convert_audio(tmp_path, output_path, output_format)
                    # Clean up temp file
                    import os
                    os.unlink(tmp_path)
                else:
                    # For WAV, just move the file
                    import shutil
                    shutil.move(tmp_path, output_path)
                    
        except requests.RequestException as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower() or "credentials" in str(e).lower():
                raise ProviderError(f"Google Cloud authentication failed: {e}")
            elif "quota" in str(e).lower() or "billing" in str(e).lower():
                raise ProviderError(f"Google Cloud quota/billing issue: {e}")
            else:
                raise NetworkError(f"Google Cloud TTS request failed: {e}")
        except Exception as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower() or "credentials" in str(e).lower():
                raise ProviderError(f"Google Cloud authentication failed: {e}")
            elif "quota" in str(e).lower() or "billing" in str(e).lower():
                raise ProviderError(f"Google Cloud quota/billing issue: {e}")
            else:
                raise ProviderError(f"Google TTS synthesis failed: {e}")
    
    def _stream_audio_file(self, audio_file: str) -> None:
        """Stream audio file to speakers using ffplay."""
        try:
            subprocess.run([
                'ffplay', '-nodisp', '-autoexit', audio_file
            ], check=True, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            self.logger.error("ffplay not found. Install ffmpeg to stream audio.")
            raise ProviderError("ffplay not found. Install ffmpeg to stream audio.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Audio playback failed: {e}")
            raise ProviderError(f"Audio playback failed: {e}")
    
    def _convert_audio(self, input_path: str, output_path: str, output_format: str) -> None:
        """Convert audio file to specified format using ffmpeg."""
        try:
            subprocess.run([
                'ffmpeg', '-i', input_path, '-y', output_path
            ], check=True, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            self.logger.error("ffmpeg not found. Install ffmpeg to convert audio formats.")
            raise ProviderError("ffmpeg not found. Install ffmpeg to convert audio formats.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Audio conversion failed: {e}")
            raise ProviderError(f"Audio conversion failed: {e}")