from ..base import TTSProvider
from ..audio_utils import convert_with_cleanup, check_audio_environment, stream_via_tempfile, create_ffplay_process, handle_ffplay_process_error
from ..config import get_config_value
from ..exceptions import DependencyError, NetworkError, AudioPlaybackError, ProviderError
from ..types import ProviderInfo
from typing import Optional, Dict, Any
import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor


class EdgeTTSProvider(TTSProvider):
    def __init__(self) -> None:
        self.edge_tts = None
        self.logger = logging.getLogger(__name__)
        self._executor = ThreadPoolExecutor(max_workers=get_config_value('thread_pool_max_workers'), thread_name_prefix="edge_tts")
        
    def _lazy_load(self) -> None:
        if self.edge_tts is None:
            try:
                import edge_tts
                self.edge_tts = edge_tts
            except ImportError:
                raise DependencyError("edge-tts not installed. Please install with: pip install edge-tts")
    
    def _run_async_safely(self, coro: Any) -> Any:
        """Safely run async coroutine, handling existing event loops."""
        try:
            # Try to get current event loop
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, run in thread pool
            return self._executor.submit(asyncio.run, coro).result()
        except RuntimeError:
            # No event loop running, safe to create new one
            return asyncio.run(coro)
    
    async def _synthesize_async(self, text: str, output_path: str, voice: str, rate: str, pitch: str, output_format: str = "mp3"):
        try:
            self.logger.debug(f"Creating Edge TTS communication with voice: {voice}")
            communicate = self.edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            
            if output_format == "mp3":
                self.logger.debug(f"Saving MP3 directly to {output_path}")
                await communicate.save(output_path)
            else:
                # For other formats, save as MP3 first then convert
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    mp3_path = tmp.name
                
                self.logger.debug(f"Saving MP3 to temporary file: {mp3_path}")
                await communicate.save(mp3_path)
                
                # Convert using utility function with cleanup
                convert_with_cleanup(mp3_path, output_path, output_format)
        except ConnectionError as e:
            self.logger.error(f"Network connection error during Edge TTS synthesis: {e}")
            raise NetworkError(f"Edge TTS connection failed: {e}. Check your internet connection and try again.")
        except OSError as e:
            self.logger.error(f"File system error during Edge TTS synthesis: {e}")
            raise ProviderError(f"Edge TTS file operation failed: {e}")
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["internet", "network", "connection", "dns", "timeout"]):
                self.logger.error(f"Network-related error during Edge TTS synthesis: {e}")
                raise NetworkError(f"Edge TTS network error: {e}. Check your internet connection and try again.")
            else:
                self.logger.error(f"Edge TTS synthesis failed with unexpected error: {type(e).__name__}: {e}")
                raise ProviderError(f"Edge TTS synthesis failed: {type(e).__name__}: {e}")
    
    async def _stream_async(self, text: str, voice: str, rate: str, pitch: str):
        """Stream TTS audio directly to speakers without saving to file"""
        import subprocess
        import os
        
        try:
            import time
            start_time = time.time()
            self.logger.debug(f"Starting Edge TTS streaming with voice: {voice}")
            communicate = self.edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            
            # Check for audio environment first
            audio_env = check_audio_environment()
            if not audio_env['available']:
                self.logger.warning(f"Audio streaming not available: {audio_env['reason']}")
                # Fallback to temporary file method
                return await self._stream_via_tempfile(text, voice, rate, pitch)
            
            # Start ffplay process with better error handling
            try:
                # Use more robust ffplay options
                ffplay_cmd = [
                    'ffplay', 
                    '-nodisp',           # No video display
                    '-autoexit',         # Exit when done
                    '-loglevel', 'quiet', # Reduce ffplay output
                    '-i', 'pipe:0'       # Read from stdin
                ]
                
                # Add audio device options if available
                if audio_env['pulse_available']:
                    ffplay_cmd.extend(['-f', 'pulse'])
                
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
                # Stream audio data with improved error handling
                self.logger.debug("Starting chunk-by-chunk audio streaming")
                chunk_count = 0
                bytes_written = 0
                
                # Optimized streaming: Start playback as soon as first chunks arrive
                first_chunk_time = None
                playback_started = False
                
                async for chunk in communicate.stream():
                    if chunk['type'] == 'audio':
                        chunk_count += 1
                        
                        # Log when we get the first chunk (latency measurement)
                        if chunk_count == 1:
                            import time
                            first_chunk_time = time.time()
                            self.logger.debug("First audio chunk received - starting immediate playback")
                        
                        try:
                            # Write chunk immediately to start playback ASAP
                            ffplay_process.stdin.write(chunk['data'])
                            ffplay_process.stdin.flush()  # Force immediate write for low latency
                            bytes_written += len(chunk['data'])
                            
                            # Mark playback as started after first few chunks
                            if chunk_count == get_config_value('streaming_playback_start_threshold') and not playback_started:
                                playback_started = True
                                self.logger.debug("Optimized streaming: Playback should have started")
                            
                            # Log progress every N chunks
                            if chunk_count % get_config_value('streaming_progress_interval') == 0:
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
                    exit_code = ffplay_process.wait()  # Let ffplay exit naturally with -autoexit
                    
                    # Calculate and log timing metrics
                    total_time = time.time() - start_time
                    if first_chunk_time:
                        latency = first_chunk_time - start_time
                        self.logger.info(f"Streaming optimization: First audio in {latency:.1f}s, Total: {total_time:.1f}s")
                    
                    self.logger.debug(f"Audio streaming completed. Chunks: {chunk_count}, Bytes: {bytes_written}, Exit code: {exit_code}")
                except Exception as e:
                    self.logger.error(f"FFplay process error: {e}")
                    ffplay_process.terminate()
                    
            except Exception as e:
                self.logger.error(f"Audio streaming failed: {e}")
                # Ensure ffplay is terminated
                if ffplay_process.poll() is None:
                    ffplay_process.terminate()
                    try:
                        ffplay_process.wait(timeout=get_config_value('ffplay_termination_timeout'))
                    except subprocess.TimeoutExpired:
                        ffplay_process.kill()
                
                if "internet" in str(e).lower() or "network" in str(e).lower():
                    raise NetworkError("Network error during streaming. Check your internet connection.")
                elif isinstance(e, BrokenPipeError):
                    raise AudioPlaybackError("Audio streaming failed: Audio device may not be available or configured properly.")
                raise ProviderError(f"Audio streaming failed: {e}")
                
        except Exception as e:
            if "internet" in str(e).lower() or "network" in str(e).lower() or "connection" in str(e).lower():
                self.logger.error(f"Network error during Edge TTS streaming: {e}")
                raise NetworkError("Edge TTS requires internet connection. Check your network and try again.")
            else:
                self.logger.error(f"Edge TTS streaming failed: {e}")
                raise ProviderError(f"Edge TTS streaming failed: {e}")
    
    
    async def _stream_via_tempfile(self, text: str, voice: str, rate: str, pitch: str) -> None:
        """Fallback streaming method using temporary file when direct streaming fails"""
        # Use the shared utility with async wrapper
        def sync_synthesize(text: str, output_path: str, **kwargs: Any) -> None:
            # Run async synthesis in sync context using proper event loop handling
            self._run_async_safely(self._synthesize_async(text, output_path, kwargs['voice'], 
                                                          kwargs['rate'], kwargs['pitch'], "mp3"))
        
        stream_via_tempfile(
            synthesize_func=sync_synthesize,
            text=text,
            logger=self.logger,
            file_suffix='.mp3',
            voice=voice,
            rate=rate,
            pitch=pitch
        )
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        self._lazy_load()
        
        # Extract provider-specific options
        voice = kwargs.get("voice", "en-US-JennyNeural")
        rate = kwargs.get("rate", "+0%")
        pitch = kwargs.get("pitch", "+0Hz")
        stream_param = kwargs.get("stream", False)
        if isinstance(stream_param, bool):
            stream = stream_param
        else:
            stream = str(stream_param).lower() in ("true", "1", "yes")
        output_format = kwargs.get("output_format", "mp3")
        
        # Format rate and pitch
        if not rate.endswith("%"):
            rate = f"+{rate}%" if not rate.startswith(("+", "-")) else f"{rate}%"
        if not pitch.endswith("Hz"):
            pitch = f"+{pitch}Hz" if not pitch.startswith(("+", "-")) else f"{pitch}Hz"
        
        # Stream or save based on option
        if stream:
            self._run_async_safely(self._stream_async(text, voice, rate, pitch))
        else:
            self._run_async_safely(self._synthesize_async(text, output_path, voice, rate, pitch, output_format))
    
    def get_info(self) -> Optional[ProviderInfo]:
        self._lazy_load()
        
        # Get available voices
        voices = []
        try:
            async def get_voices():
                return await self.edge_tts.list_voices()
            
            voice_list = self._run_async_safely(get_voices())
            voices = [v["ShortName"] for v in voice_list]
        except (ImportError, RuntimeError, OSError) as e:
            # Network issues, asyncio problems, or edge-tts import failures
            self.logger.warning(f"Could not fetch voice list from Edge TTS: {e}")
            voices = ["en-US-JennyNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"]
        except Exception as e:
            # Unexpected errors
            self.logger.error(f"Unexpected error fetching Edge TTS voices: {e}")
            voices = ["en-US-JennyNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"]
        
        return {
            "name": "Edge TTS",
            "description": "Free Microsoft Edge text-to-speech",
            "options": {
                "voice": f"Voice name (default: en-US-JennyNeural)",
                "rate": "Speech rate adjustment (e.g., +20%, -10%)",
                "pitch": "Pitch adjustment (e.g., +5Hz, -10Hz)",
                "stream": "Stream directly to speakers instead of saving to file (true/false)"
            },
            "output_format": "MP3",
            "sample_voices": voices if voices else []
        }