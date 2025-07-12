from ..base import TTSProvider
from typing import Optional, Dict, Any
import asyncio
import logging


class EdgeTTSProvider(TTSProvider):
    def __init__(self):
        self.edge_tts = None
        self.logger = logging.getLogger(__name__)
        
    def _lazy_load(self):
        if self.edge_tts is None:
            try:
                import edge_tts
                self.edge_tts = edge_tts
            except ImportError:
                raise ImportError("edge-tts not installed. Please install with: pip install edge-tts")
    
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
                import subprocess
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    mp3_path = tmp.name
                
                try:
                    self.logger.debug(f"Saving MP3 to temporary file: {mp3_path}")
                    await communicate.save(mp3_path)
                    
                    # Convert using ffmpeg
                    self.logger.debug(f"Converting {mp3_path} to {output_format} format")
                    result = subprocess.run([
                        'ffmpeg', '-i', mp3_path, '-y', output_path
                    ], check=True, capture_output=True, text=True)
                    self.logger.debug("Format conversion completed successfully")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"FFmpeg conversion failed: {e.stderr}")
                    raise RuntimeError(f"Audio format conversion failed. Is ffmpeg installed? Error: {e.stderr}")
                except FileNotFoundError:
                    self.logger.error("FFmpeg not found")
                    raise RuntimeError("ffmpeg not found. Please install ffmpeg to use non-MP3 formats.")
                finally:
                    import os
                    if os.path.exists(mp3_path):
                        os.remove(mp3_path)
        except Exception as e:
            if "internet" in str(e).lower() or "network" in str(e).lower() or "connection" in str(e).lower():
                self.logger.error(f"Network error during Edge TTS synthesis: {e}")
                raise RuntimeError("Network error: Edge TTS requires internet connection. Check your network and try again.")
            else:
                self.logger.error(f"Edge TTS synthesis failed: {e}")
                raise
    
    async def _stream_async(self, text: str, voice: str, rate: str, pitch: str):
        """Stream TTS audio directly to speakers without saving to file"""
        import subprocess
        
        try:
            self.logger.debug(f"Starting Edge TTS streaming with voice: {voice}")
            communicate = self.edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            
            # Start ffplay process to play audio from stdin
            try:
                ffplay_process = subprocess.Popen([
                    'ffplay', '-nodisp', '-autoexit', '-i', 'pipe:0'
                ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                self.logger.error("FFplay not found for audio streaming")
                raise RuntimeError("ffplay not found. Please install ffmpeg to use audio streaming.")
            
            try:
                # Stream audio data directly to ffplay
                self.logger.debug("Streaming audio chunks to ffplay")
                async for chunk in communicate.stream():
                    if chunk['type'] == 'audio':
                        ffplay_process.stdin.write(chunk['data'])
                
                # Close stdin and wait for ffplay to finish
                ffplay_process.stdin.close()
                ffplay_process.wait()
                self.logger.debug("Audio streaming completed")
            except Exception as e:
                self.logger.error(f"Audio streaming failed: {e}")
                ffplay_process.terminate()
                if "internet" in str(e).lower() or "network" in str(e).lower():
                    raise RuntimeError("Network error during streaming. Check your internet connection.")
                raise e
        except Exception as e:
            if "internet" in str(e).lower() or "network" in str(e).lower() or "connection" in str(e).lower():
                self.logger.error(f"Network error during Edge TTS streaming: {e}")
                raise RuntimeError("Network error: Edge TTS requires internet connection. Check your network and try again.")
            else:
                self.logger.error(f"Edge TTS streaming failed: {e}")
                raise
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        self._lazy_load()
        
        # Extract provider-specific options
        voice = kwargs.get("voice", "en-US-JennyNeural")
        rate = kwargs.get("rate", "+0%")
        pitch = kwargs.get("pitch", "+0Hz")
        stream = kwargs.get("stream", "false").lower() in ("true", "1", "yes")
        output_format = kwargs.get("output_format", "mp3")
        
        # Format rate and pitch
        if not rate.endswith("%"):
            rate = f"+{rate}%" if not rate.startswith(("+", "-")) else f"{rate}%"
        if not pitch.endswith("Hz"):
            pitch = f"+{pitch}Hz" if not pitch.startswith(("+", "-")) else f"{pitch}Hz"
        
        # Stream or save based on option
        if stream:
            asyncio.run(self._stream_async(text, voice, rate, pitch))
        else:
            asyncio.run(self._synthesize_async(text, output_path, voice, rate, pitch, output_format))
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        self._lazy_load()
        
        # Get available voices
        voices = []
        try:
            import asyncio
            async def get_voices():
                return await self.edge_tts.list_voices()
            
            voice_list = asyncio.run(get_voices())
            voices = [v["ShortName"] for v in voice_list]
        except:
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