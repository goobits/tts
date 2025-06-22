from ..base import TTSProvider
from typing import Optional, Dict, Any


class NaturalSpeechProvider(TTSProvider):
    def __init__(self):
        self.model = None
        self.processor = None
        
    def _lazy_load(self):
        if self.model is None:
            try:
                from naturalspeech import NaturalSpeechModel, NaturalSpeechProcessor
                
                self.model = NaturalSpeechModel.from_pretrained("microsoft/naturalspeech")
                self.processor = NaturalSpeechProcessor.from_pretrained("microsoft/naturalspeech")
                
            except ImportError:
                raise ImportError("naturalspeech dependencies not installed. Please install with: pip install naturalspeech torch")
            except Exception as e:
                raise RuntimeError(f"Failed to load NaturalSpeech model: {e}")
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        self._lazy_load()
        
        # Extract provider-specific options
        emotion = kwargs.get("emotion", "neutral")
        pitch_shift = float(kwargs.get("pitch", 0.0))
        energy = float(kwargs.get("energy", 1.0))
        
        # Process text
        inputs = self.processor(
            text, 
            emotion=emotion,
            pitch_shift=pitch_shift,
            energy=energy,
            return_tensors="pt"
        )
        
        # Generate speech
        import torch
        with torch.no_grad():
            audio = self.model.generate(**inputs)
        
        # Save audio
        import torchaudio
        torchaudio.save(output_path, audio.cpu(), sample_rate=self.model.config.sampling_rate)
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        return {
            "name": "NaturalSpeech",
            "description": "Microsoft's high-quality TTS with emotion control",
            "options": {
                "emotion": "Emotion style (neutral, happy, sad, angry, surprised)",
                "pitch": "Pitch shift in semitones (default: 0.0)",
                "energy": "Energy/intensity multiplier (default: 1.0)"
            },
            "output_format": "WAV 24kHz",
            "emotions": ["neutral", "happy", "sad", "angry", "surprised", "fear", "disgust"]
        }