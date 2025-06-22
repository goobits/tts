from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        pass
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        return None