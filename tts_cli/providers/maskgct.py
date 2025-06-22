from ..base import TTSProvider
from typing import Optional, Dict, Any


class MaskGCTProvider(TTSProvider):
    def __init__(self):
        self.model = None
        
    def _lazy_load(self):
        if self.model is None:
            try:
                from maskgct import MaskGCT
                
                self.model = MaskGCT.from_pretrained("maskgct-base")
                self.model.eval()
                
            except ImportError:
                raise ImportError("maskgct dependencies not installed. Please install with: pip install maskgct torch")
            except Exception as e:
                raise RuntimeError(f"Failed to load MaskGCT model: {e}")
    
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        self._lazy_load()
        
        # Extract provider-specific options
        steps = int(kwargs.get("steps", 50))
        guidance_scale = float(kwargs.get("guidance", 3.0))
        temperature = float(kwargs.get("temperature", 1.0))
        seed = kwargs.get("seed")
        
        # Set seed if provided
        if seed:
            import torch
            torch.manual_seed(int(seed))
        
        # Generate speech with masked generative codec transformer
        audio = self.model.synthesize(
            text,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            temperature=temperature
        )
        
        # Save audio
        import torchaudio
        torchaudio.save(output_path, audio, sample_rate=24000)
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        return {
            "name": "MaskGCT",
            "description": "Masked Generative Codec Transformer for high-quality TTS",
            "options": {
                "steps": "Number of denoising steps (default: 50)",
                "guidance": "Guidance scale for classifier-free guidance (default: 3.0)",
                "temperature": "Sampling temperature (default: 1.0)",
                "seed": "Random seed for reproducibility"
            },
            "output_format": "WAV 24kHz"
        }