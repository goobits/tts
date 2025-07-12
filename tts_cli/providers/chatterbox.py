from ..base import TTSProvider
from typing import Optional, Dict, Any


class ChatterboxProvider(TTSProvider):
    def __init__(self):
        self.tts = None
        
    def _lazy_load(self):
        if self.tts is None:
            try:
                from chatterbox.tts import ChatterboxTTS
                print("Loading Chatterbox (Resemble AI) model...")
                # Use GPU if available for much faster generation
                device = "cuda" if self._has_cuda() else "cpu"
                print(f"Using device: {device}")
                self.tts = ChatterboxTTS.from_pretrained(device=device)
                print("Chatterbox model loaded successfully.")
                
            except ImportError:
                raise ImportError("chatterbox dependencies not installed. Please install with: pip install chatterbox-tts")
            except Exception as e:
                raise RuntimeError(f"Failed to load Chatterbox model: {e}")
    
    def _has_cuda(self):
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        self._lazy_load()
        
        # Extract options
        stream = kwargs.get("stream", "false").lower() in ("true", "1", "yes")
        audio_prompt_path = kwargs.get("voice")  # Optional voice cloning
        exaggeration = float(kwargs.get("exaggeration", "0.5"))
        cfg_weight = float(kwargs.get("cfg_weight", "0.5"))
        temperature = float(kwargs.get("temperature", "0.8"))
        min_p = float(kwargs.get("min_p", "0.05"))
        output_format = kwargs.get("output_format", "wav")
        
        # Generate speech with optimized settings for speed
        if audio_prompt_path:
            # Voice cloning mode
            wav = self.tts.generate(text, audio_prompt_path=audio_prompt_path,
                                  exaggeration=exaggeration, cfg_weight=cfg_weight,
                                  temperature=temperature, min_p=min_p)
        else:
            # Default voice with speed optimizations
            wav = self.tts.generate(text, exaggeration=exaggeration, cfg_weight=cfg_weight,
                                  temperature=temperature, min_p=min_p)
        
        if stream:
            # Stream to speakers
            self._stream_to_speakers(wav)
        else:
            # Save to file
            if output_format == "wav":
                import torchaudio as ta
                ta.save(output_path, wav, self.tts.sr)
            else:
                # Convert to other formats using ffmpeg
                import tempfile
                import subprocess
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    wav_path = tmp.name
                
                try:
                    import torchaudio as ta
                    ta.save(wav_path, wav, self.tts.sr)
                    # Convert using ffmpeg
                    subprocess.run([
                        'ffmpeg', '-i', wav_path, '-y', output_path
                    ], check=True, capture_output=True)
                finally:
                    import os
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
    
    def _stream_to_speakers(self, wav_tensor):
        """Stream audio tensor directly to speakers using ffplay"""
        import subprocess
        import io
        import wave
        import numpy as np
        
        # Convert tensor to numpy and ensure it's on CPU
        audio_data = wav_tensor.cpu().numpy().squeeze()
        
        # Create an in-memory WAV file
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.tts.sr)  # Use model's sample rate
            # Normalize and convert to 16-bit PCM
            audio_normalized = np.clip(audio_data, -1.0, 1.0)
            audio_16bit = (audio_normalized * 32767 * 0.95).astype(np.int16)
            wav_file.writeframes(audio_16bit.tobytes())
        
        # Stream to ffplay
        buffer.seek(0)
        ffplay_process = subprocess.Popen([
            'ffplay', '-nodisp', '-autoexit', '-i', 'pipe:0'
        ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        ffplay_process.stdin.write(buffer.getvalue())
        ffplay_process.stdin.close()
        ffplay_process.wait()
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        return {
            "name": "Chatterbox (Resemble AI)",
            "description": "State-of-the-art zero-shot TTS with voice cloning and emotion control",
            "options": {
                "voice": "Path to reference audio file for voice cloning (optional)",
                "exaggeration": "Emotion/intensity control (0.0-1.0, default: 0.5)",
                "cfg_weight": "Speech pacing control (0.1-1.0, default: 0.5)",
                "stream": "Stream directly to speakers instead of saving to file (true/false)"
            },
            "output_format": "WAV 22kHz",
            "model": "Resemble AI Chatterbox (0.5B parameters)"
        }