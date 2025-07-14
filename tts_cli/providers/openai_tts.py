"""OpenAI TTS provider implementation."""

from ..base import TTSProvider
from ..exceptions import (
    DependencyError, ProviderError, NetworkError, AudioPlaybackError,
    AuthenticationError
)
from ..config import get_api_key, is_ssml, strip_ssml_tags, Config
from ..utils.audio import check_audio_environment, stream_audio_file, convert_audio
from typing import Optional, Dict, Any
import logging
import tempfile
import subprocess
import time


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
                raise AuthenticationError(
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
            if stream:
                # Use streaming method for real-time playback
                self._stream_realtime(text, voice)
            else:
                # Use regular synthesis for file output
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
                
                # Convert to desired format if needed
                if output_format == "mp3":
                    # Direct save
                    import shutil
                    shutil.move(tmp_path, output_path)
                else:
                    # Convert using ffmpeg
                    convert_audio(tmp_path, output_path, output_format)
                    # Clean up temp file
                    import os
                    os.unlink(tmp_path)
                    
        except ImportError:
            raise DependencyError("OpenAI library not installed. Install with: pip install tts-cli[openai]")
        except Exception as e:
            error_str = str(e).lower()
            if "authentication" in error_str or "api_key" in error_str:
                raise AuthenticationError(f"OpenAI API authentication failed: {e}")
            elif "network" in error_str or "connection" in error_str:
                raise NetworkError(f"OpenAI API network error: {e}")
            else:
                raise ProviderError(f"OpenAI TTS synthesis failed: {e}")
    
    def _stream_realtime(self, text: str, voice: str) -> None:
        """Stream TTS audio in real-time with minimal latency."""
        import os
        
        try:
            start_time = time.time()
            self.logger.debug(f"Starting OpenAI TTS streaming with voice: {voice}")
            
            client = self._get_client()
            
            # Check for audio environment first
            audio_env = check_audio_environment()
            if not audio_env['available']:
                self.logger.warning(f"Audio streaming not available: {audio_env['reason']}")
                # Fallback to temporary file method
                return self._stream_via_tempfile(text, voice)
            
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
                # Create streaming response
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    response_format="mp3"
                )
                
                # Stream audio data chunks
                self.logger.debug("Starting chunk-by-chunk audio streaming")
                chunk_count = 0
                bytes_written = 0
                first_chunk_time = None
                
                # OpenAI returns an iterator of bytes
                for chunk in response.iter_bytes(chunk_size=Config.HTTP_STREAMING_CHUNK_SIZE):
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
                        
                        # Log progress every N chunks
                        if chunk_count % Config.STREAMING_PROGRESS_INTERVAL == 0:
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
                    exit_code = ffplay_process.wait(timeout=Config.FFPLAY_TIMEOUT)
                    
                    # Calculate and log timing metrics
                    total_time = time.time() - start_time
                    if first_chunk_time:
                        latency = first_chunk_time - start_time
                        self.logger.info(f"OpenAI streaming optimization: First audio in {latency:.1f}s, Total: {total_time:.1f}s")
                    
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
                        ffplay_process.wait(timeout=Config.FFPLAY_TERMINATION_TIMEOUT)
                    except subprocess.TimeoutExpired:
                        ffplay_process.kill()
                
                if isinstance(e, BrokenPipeError):
                    raise AudioPlaybackError("Audio streaming failed: Audio device may not be available or configured properly.")
                raise ProviderError(f"Audio streaming failed: {e}")
                
        except Exception as e:
            error_str = str(e).lower()
            if "authentication" in error_str or "api_key" in error_str:
                self.logger.error(f"Authentication error during OpenAI streaming: {e}")
                raise AuthenticationError(f"OpenAI API authentication failed: {e}")
            elif "network" in error_str or "connection" in error_str:
                self.logger.error(f"Network error during OpenAI streaming: {e}")
                raise NetworkError("OpenAI TTS requires internet connection. Check your network and try again.")
            else:
                self.logger.error(f"OpenAI TTS streaming failed: {e}")
                raise ProviderError(f"OpenAI TTS streaming failed: {e}")
    
    
    def _stream_via_tempfile(self, text: str, voice: str):
        """Fallback streaming method using temporary file when direct streaming fails."""
        self.logger.info("Using temporary file fallback for audio streaming")
        
        client = self._get_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="mp3"
        )
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            temp_file = tmp_file.name
            response.stream_to_file(temp_file)
        
        try:
            # Play the temporary file
            stream_audio_file(temp_file)
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
            "all_voices": list(self.VOICES.keys()),  # Add all_voices for browser compatibility
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