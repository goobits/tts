"""ElevenLabs TTS provider implementation with voice cloning support."""

from ..base import TTSProvider
from ..exceptions import DependencyError, ProviderError, NetworkError, AudioPlaybackError
from ..config import get_api_key, is_ssml, strip_ssml_tags
from typing import Optional, Dict, Any, List
import logging
import tempfile
import subprocess
import requests
import json
import time


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs TTS provider with premium voice cloning and custom voices."""
    
    # Default ElevenLabs voices (these are always available)
    DEFAULT_VOICES = {
        "rachel": "Calm and soothing female voice",
        "domi": "Strong and confident female voice", 
        "bella": "Warm and engaging female voice",
        "antoni": "Well-rounded male voice",
        "elli": "Emotional and dynamic female voice",
        "josh": "Deep and authoritative male voice",
        "arnold": "Crisp and commanding male voice",
        "adam": "Professional and clear male voice",
        "sam": "Natural and conversational male voice"
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._voices_cache = None
        self.base_url = "https://api.elevenlabs.io/v1"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request to ElevenLabs API."""
        api_key = get_api_key("elevenlabs")
        if not api_key:
            raise ProviderError(
                "ElevenLabs API key not found. Set with: tts config elevenlabs_api_key YOUR_KEY"
            )
        
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            return response
        except requests.RequestException as e:
            raise NetworkError(f"ElevenLabs API request failed: {e}")
    
    def _get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of all available voices from ElevenLabs."""
        if self._voices_cache is None:
            try:
                response = self._make_request("GET", "/voices")
                
                if response.status_code == 200:
                    data = response.json()
                    voices = []
                    
                    for voice in data.get("voices", []):
                        voice_info = {
                            "voice_id": voice["voice_id"],
                            "name": voice["name"],
                            "category": voice.get("category", "generated"),
                            "description": voice.get("description", "Custom voice"),
                            "gender": voice.get("labels", {}).get("gender", "unknown"),
                            "age": voice.get("labels", {}).get("age", "unknown")
                        }
                        voices.append(voice_info)
                    
                    self._voices_cache = voices
                else:
                    self.logger.warning(f"Failed to fetch ElevenLabs voices: {response.status_code}")
                    self._voices_cache = []
                    
            except Exception as e:
                self.logger.warning(f"Failed to fetch ElevenLabs voices: {e}")
                self._voices_cache = []
        
        return self._voices_cache
    
    def _get_voice_id(self, voice_name: str) -> Optional[str]:
        """Get voice ID from voice name."""
        # Check if it's already a voice ID (32 char hex string)
        if len(voice_name) == 32 and all(c in '0123456789abcdef' for c in voice_name.lower()):
            return voice_name
        
        # Search in available voices
        voices = self._get_available_voices()
        for voice in voices:
            if voice["name"].lower() == voice_name.lower():
                return voice["voice_id"]
        
        # Fallback to default voices (these have well-known IDs)
        voice_id_map = {
            "rachel": "21m00Tcm4TlvDq8ikWAM",
            "domi": "AZnzlk1XvdvUeBnXmlld", 
            "bella": "EXAVITQu4vr4xnSDxMaL",
            "antoni": "ErXwobaYiN019PkySvjV",
            "elli": "MF3mGyEYCl7XYWbV9V6O",
            "josh": "TxGEqnHWrfWFMLpVQ3VQ",
            "arnold": "VR6AewLTigWG4xSOukaG",
            "adam": "pNInz6obpgDQGcFmaJgB",
            "sam": "yoZ06aMxZJJ28mfd3POQ"
        }
        
        return voice_id_map.get(voice_name.lower())
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        """Synthesize speech using ElevenLabs API."""
        # Extract options
        voice = kwargs.get("voice", "rachel")  # Default voice
        stream = kwargs.get("stream", "false").lower() in ("true", "1", "yes")
        output_format = kwargs.get("output_format", "wav")
        stability = float(kwargs.get("stability", "0.5"))
        similarity_boost = float(kwargs.get("similarity_boost", "0.5"))
        style = float(kwargs.get("style", "0.0"))
        
        # Handle SSML (ElevenLabs doesn't support SSML, so strip tags)
        if is_ssml(text):
            self.logger.warning("ElevenLabs doesn't support SSML. Converting to plain text.")
            text = strip_ssml_tags(text)
        
        # Parse voice name
        if ":" in voice:
            # Format like "elevenlabs:rachel"
            _, voice_name = voice.split(":", 1)
        else:
            voice_name = voice
        
        # Get voice ID
        voice_id = self._get_voice_id(voice_name)
        if not voice_id:
            raise ProviderError(f"Voice '{voice_name}' not found. Use tts voices elevenlabs to see available voices.")
        
        try:
            if stream:
                # Use streaming method for real-time playback
                self._stream_realtime(text, voice_id, voice_name, stability, similarity_boost, style)
            else:
                # Use regular synthesis for file output
                # Prepare request payload
                payload = {
                    "text": text,
                    "model_id": "eleven_monolingual_v1",  # or "eleven_multilingual_v2"
                    "voice_settings": {
                        "stability": stability,
                        "similarity_boost": similarity_boost,
                        "style": style
                    }
                }
                
                self.logger.info(f"Generating speech with ElevenLabs voice '{voice_name}' (ID: {voice_id})")
                
                # Make synthesis request
                response = self._make_request(
                    "POST", 
                    f"/text-to-speech/{voice_id}",
                    json=payload
                )
                
                if response.status_code != 200:
                    error_msg = f"ElevenLabs API error {response.status_code}"
                    try:
                        error_detail = response.json().get("detail", {})
                        if isinstance(error_detail, dict):
                            error_msg += f": {error_detail.get('message', 'Unknown error')}"
                        else:
                            error_msg += f": {error_detail}"
                    except:
                        error_msg += f": {response.text}"
                    raise ProviderError(error_msg)
                
                # Save audio content to temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                    tmp_file.write(response.content)
                
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
                    
        except requests.RequestException as e:
            if 'response' in locals() and response.status_code == 401:
                raise ProviderError("ElevenLabs API authentication failed. Check your API key.")
            elif 'response' in locals() and response.status_code == 429:
                raise ProviderError("ElevenLabs API rate limit exceeded. Try again later.")
            elif 'response' in locals() and response.status_code >= 500:
                raise NetworkError(f"ElevenLabs server error: {response.status_code}")
            else:
                raise ProviderError(f"ElevenLabs API error: {e}")
        except Exception as e:
            raise ProviderError(f"ElevenLabs TTS synthesis failed: {e}")
    
    def _stream_realtime(self, text: str, voice_id: str, voice_name: str, 
                        stability: float, similarity_boost: float, style: float) -> None:
        """Stream TTS audio in real-time with minimal latency."""
        import os
        
        try:
            start_time = time.time()
            self.logger.debug(f"Starting ElevenLabs TTS streaming with voice: {voice_name}")
            
            # Check for audio environment first
            audio_env = self._check_audio_environment()
            if not audio_env['available']:
                self.logger.warning(f"Audio streaming not available: {audio_env['reason']}")
                # Fallback to temporary file method
                return self._stream_via_tempfile(text, voice_id, voice_name, stability, similarity_boost, style)
            
            # Start ffplay process for streaming
            try:
                ffplay_cmd = [
                    'ffplay', 
                    '-nodisp',           # No video display
                    '-autoexit',         # Exit when done
                    '-loglevel', 'quiet', # Reduce ffplay output
                    '-f', 'mp3',         # Specify MP3 format
                    '-i', 'pipe:0'       # Read from stdin
                ]
                
                self.logger.debug(f"Starting ffplay with command: {' '.join(ffplay_cmd)}")
                ffplay_process = subprocess.Popen(
                    ffplay_cmd,
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    bufsize=0  # Unbuffered for real-time streaming
                )
            except FileNotFoundError:
                self.logger.error("FFplay not found for audio streaming")
                raise DependencyError("ffplay not found. Please install ffmpeg to use audio streaming.")
            
            try:
                # Prepare request for streaming
                api_key = get_api_key("elevenlabs")
                if not api_key:
                    raise ProviderError(
                        "ElevenLabs API key not found. Set with: tts config elevenlabs_api_key YOUR_KEY"
                    )
                
                headers = {
                    "xi-api-key": api_key,
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": stability,
                        "similarity_boost": similarity_boost,
                        "style": style
                    }
                }
                
                url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
                
                # Make streaming request
                self.logger.debug("Starting ElevenLabs streaming request")
                response = requests.post(url, headers=headers, json=payload, stream=True)
                
                if response.status_code != 200:
                    error_msg = f"ElevenLabs API error {response.status_code}"
                    try:
                        error_detail = response.json().get("detail", {})
                        if isinstance(error_detail, dict):
                            error_msg += f": {error_detail.get('message', 'Unknown error')}"
                        else:
                            error_msg += f": {error_detail}"
                    except:
                        error_msg += f": {response.text[:200]}"
                    raise ProviderError(error_msg)
                
                # Stream audio data chunks
                self.logger.debug("Starting chunk-by-chunk audio streaming")
                chunk_count = 0
                bytes_written = 0
                first_chunk_time = None
                
                # ElevenLabs streams in chunks
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        chunk_count += 1
                        
                        # Log when we get the first chunk (latency measurement)
                        if chunk_count == 1:
                            first_chunk_time = time.time()
                            self.logger.debug("First audio chunk received - starting immediate playback")
                        
                        try:
                            # Write chunk immediately to start playback ASAP
                            ffplay_process.stdin.write(chunk)
                            ffplay_process.stdin.flush()
                            bytes_written += len(chunk)
                            
                            # Log progress every 10 chunks
                            if chunk_count % 10 == 0:
                                self.logger.debug(f"Streamed {chunk_count} chunks, {bytes_written} bytes")
                                
                        except BrokenPipeError:
                            # Check if ffplay process ended early
                            if ffplay_process.poll() is not None:
                                stderr_output = ffplay_process.stderr.read().decode('utf-8', errors='ignore')
                                self.logger.warning(f"FFplay ended early (exit code: {ffplay_process.returncode}): {stderr_output}")
                                break
                            else:
                                raise
                
                # Close stdin and wait for ffplay to finish
                try:
                    ffplay_process.stdin.close()
                    exit_code = ffplay_process.wait(timeout=5)
                    
                    # Calculate and log timing metrics
                    total_time = time.time() - start_time
                    if first_chunk_time:
                        latency = first_chunk_time - start_time
                        self.logger.info(f"ElevenLabs streaming optimization: First audio in {latency:.1f}s, Total: {total_time:.1f}s")
                    
                    self.logger.debug(f"Audio streaming completed. Chunks: {chunk_count}, Bytes: {bytes_written}, Exit code: {exit_code}")
                except subprocess.TimeoutExpired:
                    self.logger.warning("FFplay process timeout, terminating")
                    ffplay_process.terminate()
                    
            except Exception as e:
                self.logger.error(f"Audio streaming failed: {e}")
                # Ensure ffplay is terminated
                if ffplay_process.poll() is None:
                    ffplay_process.terminate()
                    try:
                        ffplay_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        ffplay_process.kill()
                
                if isinstance(e, BrokenPipeError):
                    raise AudioPlaybackError("Audio streaming failed: Audio device may not be available or configured properly.")
                raise ProviderError(f"Audio streaming failed: {e}")
                
        except Exception as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                self.logger.error(f"Authentication error during ElevenLabs streaming: {e}")
                raise ProviderError(f"ElevenLabs API authentication failed: {e}")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                self.logger.error(f"Network error during ElevenLabs streaming: {e}")
                raise NetworkError("ElevenLabs TTS requires internet connection. Check your network and try again.")
            else:
                self.logger.error(f"ElevenLabs TTS streaming failed: {e}")
                raise ProviderError(f"ElevenLabs TTS streaming failed: {e}")
    
    def _check_audio_environment(self):
        """Check if audio streaming is available in current environment."""
        import os
        
        result = {
            'available': False,
            'reason': 'Unknown',
            'pulse_available': False,
            'alsa_available': False
        }
        
        # Check for PulseAudio
        if 'PULSE_SERVER' in os.environ:
            result['pulse_available'] = True
            result['available'] = True
            result['reason'] = 'PulseAudio available'
            return result
        
        # Check for ALSA devices
        try:
            if os.path.exists('/proc/asound/cards') and os.path.getsize('/proc/asound/cards') > 0:
                result['alsa_available'] = True
                result['available'] = True
                result['reason'] = 'ALSA devices available'
                return result
        except (ImportError, OSError, subprocess.SubprocessError) as e:
            self.logger.debug(f"ALSA check failed: {e}")
            
        # Check if we can reach audio system
        try:
            subprocess.run(['aplay', '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         timeout=2)
            result['available'] = True
            result['reason'] = 'Audio system responsive'
            return result
        except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            self.logger.debug(f"Audio system check failed: {e}")
            
        result['reason'] = 'No audio devices or audio system unavailable'
        return result
    
    def _stream_via_tempfile(self, text: str, voice_id: str, voice_name: str,
                            stability: float, similarity_boost: float, style: float):
        """Fallback streaming method using temporary file when direct streaming fails."""
        self.logger.info("Using temporary file fallback for audio streaming")
        
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style
            }
        }
        
        response = self._make_request(
            "POST", 
            f"/text-to-speech/{voice_id}",
            json=payload
        )
        
        if response.status_code != 200:
            error_msg = f"ElevenLabs API error {response.status_code}: {response.text[:200]}"
            raise ProviderError(error_msg)
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            temp_file = tmp_file.name
            tmp_file.write(response.content)
        
        try:
            # Play the temporary file
            subprocess.run([
                'ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', temp_file
            ], check=True, timeout=30)
            self.logger.debug("Temporary file streaming completed")
        except FileNotFoundError:
            self.logger.warning(f"FFplay not available, audio saved to: {temp_file}")
            raise DependencyError(f"Audio generated but cannot play automatically. File saved to: {temp_file}")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"FFplay failed to play temporary file: {e}")
            raise AudioPlaybackError(f"Audio generated but playback failed. File saved to: {temp_file}")
        finally:
            # Clean up temporary file
            try:
                import os
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except OSError as e:
                self.logger.debug(f"Could not clean up temporary file {temp_file}: {e}")
    
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
        api_key = get_api_key("elevenlabs")
        api_status = "✅ Configured" if api_key else "❌ API key not set"
        
        # Get voice information
        try:
            all_voices = self._get_available_voices()
            custom_voices = [v for v in all_voices if v.get("category") != "premade"]
            premade_voices = [v for v in all_voices if v.get("category") == "premade"]
            
            voice_list = [f"{v['name']} ({v.get('category', 'unknown')})" for v in all_voices[:15]]
            if len(all_voices) > 15:
                voice_list.append(f"... and {len(all_voices) - 15} more voices")
                
        except Exception:
            voice_list = [f"{name}: {desc}" for name, desc in self.DEFAULT_VOICES.items()]
            custom_voices = []
            premade_voices = []
        
        return {
            "name": "ElevenLabs",
            "description": f"Premium voice cloning with {len(all_voices) if 'all_voices' in locals() else '10+'} voices",
            "api_status": api_status,
            "sample_voices": list(self.DEFAULT_VOICES.keys()),
            "all_voices": voice_list,
            "voice_descriptions": self.DEFAULT_VOICES,
            "custom_voices": len(custom_voices) if custom_voices else "Unknown",
            "options": {
                "voice": f"Voice to use (e.g., {list(self.DEFAULT_VOICES.keys())[0]})",
                "stability": "Voice stability (0.0-1.0, default: 0.5)",
                "similarity_boost": "Voice similarity boost (0.0-1.0, default: 0.5)", 
                "style": "Style exaggeration (0.0-1.0, default: 0.0)",
                "stream": "Stream directly to speakers instead of saving to file (true/false)"
            },
            "features": {
                "ssml_support": False,
                "voice_cloning": True,
                "languages": "Multiple languages",
                "quality": "Premium (voice cloning available)"
            },
            "pricing": "Starting at $5/month (subscription required)",
            "output_format": "MP3 (converted to other formats via ffmpeg)"
        }