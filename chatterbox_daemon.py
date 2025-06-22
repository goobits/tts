#!/usr/bin/env python3
"""
Persistent Chatterbox TTS daemon that keeps the model loaded in GPU memory
and accepts requests via command line arguments or simple socket.
"""
import sys
import time
import subprocess
import io
import wave
import numpy as np
from chatterbox.tts import ChatterboxTTS

class ChatterboxDaemon:
    def __init__(self):
        print("🚀 Starting Chatterbox daemon...")
        print("📡 Loading model to GPU (this takes ~6 seconds)...")
        start_time = time.time()
        self.model = ChatterboxTTS.from_pretrained(device='cuda')
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.2f}s and ready on GPU!")
        
        # Test GPU memory usage
        import torch
        print(f"🎯 GPU Memory: {torch.cuda.memory_allocated(0) / 1e9:.2f}GB allocated")
    
    def interactive_mode(self):
        """Interactive mode - keeps model loaded and waits for text input"""
        print("\n🎤 Interactive TTS Mode - Model stays loaded!")
        print("💡 Type text to speak, or 'quit' to exit")
        print("-" * 50)
        
        while True:
            try:
                text = input("\n📝 Text to speak: ").strip()
                if text.lower() in ['quit', 'exit', 'q']:
                    break
                if not text:
                    continue
                    
                start_time = time.time()
                self.generate_and_play(text)
                gen_time = time.time() - start_time
                print(f"⚡ Generated in {gen_time:.2f}s")
                
            except KeyboardInterrupt:
                break
        
        print("\n👋 Goodbye!")
    
    def generate_and_play(self, text, **kwargs):
        """Generate speech and play directly to speakers"""
        # Extract options
        audio_prompt_path = kwargs.get("voice")
        exaggeration = float(kwargs.get("exaggeration", "0.5"))
        cfg_weight = float(kwargs.get("cfg_weight", "0.5"))
        temperature = float(kwargs.get("temperature", "0.8"))
        min_p = float(kwargs.get("min_p", "0.05"))
        
        # Generate speech with progress
        print(f"🎵 Generating: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        if audio_prompt_path:
            wav = self.model.generate(text, audio_prompt_path=audio_prompt_path,
                                    exaggeration=exaggeration, cfg_weight=cfg_weight,
                                    temperature=temperature, min_p=min_p)
        else:
            wav = self.model.generate(text, exaggeration=exaggeration, cfg_weight=cfg_weight,
                                    temperature=temperature, min_p=min_p)
        
        # Stream to speakers
        self._stream_to_speakers(wav)
    
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
    daemon = ChatterboxDaemon()
    
    if len(sys.argv) > 1:
        # Single generation mode
        text = " ".join(sys.argv[1:])
        daemon.generate_and_play(text)
    else:
        # Interactive mode
        daemon.interactive_mode()