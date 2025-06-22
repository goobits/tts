from ..base import TTSProvider
from typing import Optional, Dict, Any
import asyncio


class EdgeTTSProvider(TTSProvider):
    def __init__(self):
        self.edge_tts = None
        
    def _lazy_load(self):
        if self.edge_tts is None:
            try:
                import edge_tts
                self.edge_tts = edge_tts
            except ImportError:
                raise ImportError("edge-tts not installed. Please install with: pip install edge-tts")
    
    async def _synthesize_async(self, text: str, output_path: str, voice: str, rate: str, pitch: str):
        communicate = self.edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)
    
    async def _stream_async(self, text: str, voice: str, rate: str, pitch: str):
        """Stream TTS audio directly to speakers without saving to file"""
        import subprocess
        
        communicate = self.edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        
        # Start ffplay process to play audio from stdin
        ffplay_process = subprocess.Popen([
            'ffplay', '-nodisp', '-autoexit', '-i', 'pipe:0'
        ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        try:
            # Stream audio data directly to ffplay
            async for chunk in communicate.stream():
                if chunk['type'] == 'audio':
                    ffplay_process.stdin.write(chunk['data'])
            
            # Close stdin and wait for ffplay to finish
            ffplay_process.stdin.close()
            ffplay_process.wait()
        except Exception as e:
            ffplay_process.terminate()
            raise e
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        self._lazy_load()
        
        # Extract provider-specific options
        voice = kwargs.get("voice", "en-US-JennyNeural")
        rate = kwargs.get("rate", "+0%")
        pitch = kwargs.get("pitch", "+0Hz")
        stream = kwargs.get("stream", "false").lower() in ("true", "1", "yes")
        
        # Format rate and pitch
        if not rate.endswith("%"):
            rate = f"+{rate}%" if not rate.startswith(("+", "-")) else f"{rate}%"
        if not pitch.endswith("Hz"):
            pitch = f"+{pitch}Hz" if not pitch.startswith(("+", "-")) else f"{pitch}Hz"
        
        # Stream or save based on option
        if stream:
            asyncio.run(self._stream_async(text, voice, rate, pitch))
        else:
            asyncio.run(self._synthesize_async(text, output_path, voice, rate, pitch))
    
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
            "sample_voices": voices[:10] if voices else []
        }