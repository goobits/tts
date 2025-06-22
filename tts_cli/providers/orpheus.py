from ..base import TTSProvider
from typing import Optional, Dict, Any
import numpy as np


class OrpheusProvider(TTSProvider):
    def __init__(self):
        self.model = None
        self.processor = None
        self.vocoder = None
        self.embeddings_dataset = None
        self.device = None
        
    def _lazy_load(self):
        if self.model is None:
            try:
                import torch
                from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
                from datasets import load_dataset
                
                print("Loading Orpheus (SpeechT5) model...")
                
                # Set device
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                
                # Load model and processor
                self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
                self.model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
                self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
                
                # Move models to device
                self.model = self.model.to(self.device)
                self.vocoder = self.vocoder.to(self.device)
                
                # Load speaker embeddings dataset
                self.embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
                
                print("Orpheus model loaded successfully.")
                
            except ImportError:
                raise ImportError("orpheus dependencies not installed. Please install with: pip install transformers datasets torch soundfile")
            except Exception as e:
                raise RuntimeError(f"Failed to load Orpheus model: {e}")
    
    def _stream_to_speakers(self, audio_tensor):
        """Stream audio tensor directly to speakers using ffplay"""
        import subprocess
        import io
        import wave
        import numpy as np
        
        # Convert tensor to numpy array
        audio_data = audio_tensor.cpu().numpy()
        
        # Create an in-memory WAV file with better quality
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            # Normalize and convert to 16-bit PCM with better scaling
            audio_normalized = np.clip(audio_data, -1.0, 1.0)  # Clip to prevent clipping artifacts
            audio_16bit = (audio_normalized * 32767 * 0.95).astype(np.int16)  # Scale down slightly to prevent clipping
            wav_file.writeframes(audio_16bit.tobytes())
        
        # Stream to ffplay
        buffer.seek(0)
        ffplay_process = subprocess.Popen([
            'ffplay', '-nodisp', '-autoexit', '-i', 'pipe:0'
        ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        ffplay_process.stdin.write(buffer.getvalue())
        ffplay_process.stdin.close()
        ffplay_process.wait()

    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        self._lazy_load()
        
        import torch
        import soundfile as sf
        
        # Extract provider-specific options
        voice_id = int(kwargs.get("voice", "7306"))  # Default speaker embedding index
        stream = kwargs.get("stream", "false").lower() in ("true", "1", "yes")
        
        # Process text
        inputs = self.processor(text=text, return_tensors="pt").to(self.device)
        
        # Get speaker embeddings
        speaker_embeddings = torch.tensor(self.embeddings_dataset[voice_id]["xvector"]).unsqueeze(0).to(self.device)
        
        # Generate speech
        with torch.no_grad():
            speech = self.model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=self.vocoder)
        
        # Stream or save based on option
        if stream:
            self._stream_to_speakers(speech)
        else:
            # Save audio
            sf.write(output_path, speech.cpu().numpy(), samplerate=16000)
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        return {
            "name": "Orpheus (Microsoft SpeechT5)",
            "description": "High-quality neural text-to-speech using Microsoft's SpeechT5 model",
            "options": {
                "voice": "Voice ID (0-7930, default: 7306)",
                "stream": "Stream directly to speakers instead of saving to file (true/false)"
            },
            "output_format": "WAV 16kHz",
            "model": "microsoft/speecht5_tts"
        }