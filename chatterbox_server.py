#!/usr/bin/env python3
"""
Persistent Chatterbox TTS server to avoid reloading the model each time.
Keeps the model loaded in memory for fast generation.
"""
import subprocess
import io
import wave
import numpy as np
from chatterbox.tts import ChatterboxTTS

class ChatterboxServer:
    def __init__(self):
        print("Loading Chatterbox model (one-time setup)...")
        self.model = ChatterboxTTS.from_pretrained(device='cuda')
        print("✓ Model loaded and ready!")
    
    def generate_and_play(self, text, **kwargs):
        """Generate speech and play directly to speakers"""
        print(f"Generating: '{text}'")
        
        # Extract options
        audio_prompt_path = kwargs.get("voice")
        exaggeration = float(kwargs.get("exaggeration", "0.5"))
        cfg_weight = float(kwargs.get("cfg_weight", "0.5"))
        temperature = float(kwargs.get("temperature", "0.8"))
        min_p = float(kwargs.get("min_p", "0.05"))
        
        # Generate speech
        if audio_prompt_path:
            wav = self.model.generate(text, audio_prompt_path=audio_prompt_path,
                                    exaggeration=exaggeration, cfg_weight=cfg_weight,
                                    temperature=temperature, min_p=min_p)
        else:
            wav = self.model.generate(text, exaggeration=exaggeration, cfg_weight=cfg_weight,
                                    temperature=temperature, min_p=min_p)
        
        # Stream to speakers
        self._stream_to_speakers(wav)
        print("✓ Audio played!")
    
    def _stream_to_speakers(self, wav_tensor):
        """Stream audio tensor directly to speakers using ffplay"""
        # Convert tensor to numpy and ensure it's on CPU
        audio_data = wav_tensor.cpu().numpy().squeeze()
        
        # Create an in-memory WAV file
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.model.sr)  # Use model's sample rate
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

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python chatterbox_server.py 'text to speak'")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    server = ChatterboxServer()
    server.generate_and_play(text)