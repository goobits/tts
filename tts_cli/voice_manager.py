"""Voice management system for TTS CLI with server communication"""

import socket
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from .exceptions import TTSError


class VoiceManager:
    """Manages voice loading/unloading and server communication"""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 12345):
        self.server_host = server_host
        self.server_port = server_port
        self.logger = logging.getLogger(__name__)
        self._server_process = None
    
    def _ensure_server_running(self) -> bool:
        """Ensure chatterbox server is running, start if needed"""
        if self._is_server_running():
            return True
        
        # Start server
        try:
            script_path = Path(__file__).parent.parent / "chatterbox_server_daemon.py"
            if not script_path.exists():
                raise TTSError(f"Chatterbox server script not found: {script_path}")
            
            self.logger.info("Starting chatterbox server...")
            self._server_process = subprocess.Popen([
                "python", str(script_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for server to start
            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self._is_server_running():
                    self.logger.info("Chatterbox server started successfully")
                    return True
            
            raise TTSError("Server failed to start within timeout")
            
        except Exception as e:
            raise TTSError(f"Failed to start chatterbox server: {e}")
    
    def _is_server_running(self) -> bool:
        """Check if chatterbox server is running"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((self.server_host, self.server_port))
                return result == 0
        except Exception:
            return False
    
    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to server and get response"""
        if not self._ensure_server_running():
            raise TTSError("Cannot connect to chatterbox server")
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(30)  # 30 second timeout for voice loading
                sock.connect((self.server_host, self.server_port))
                
                # Send command
                command_str = json.dumps(command) + "\n"
                sock.sendall(command_str.encode('utf-8'))
                
                # Receive response
                response_data = b""
                while b"\n" not in response_data:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                
                response_str = response_data.decode('utf-8').strip()
                return json.loads(response_str)
                
        except socket.timeout:
            raise TTSError("Server communication timeout")
        except ConnectionRefusedError:
            raise TTSError("Cannot connect to chatterbox server")
        except json.JSONDecodeError as e:
            raise TTSError(f"Invalid server response: {e}")
        except Exception as e:
            raise TTSError(f"Server communication error: {e}")
    
    def load_voice(self, voice_path: str) -> bool:
        """Load a voice file into server memory"""
        voice_file = Path(voice_path).resolve()
        
        if not voice_file.exists():
            raise TTSError(f"Voice file not found: {voice_file}")
        
        if not voice_file.suffix.lower() in ['.wav', '.mp3', '.flac', '.ogg']:
            raise TTSError(f"Unsupported audio format: {voice_file.suffix}")
        
        command = {
            "action": "load_voice",
            "voice_path": str(voice_file)
        }
        
        response = self._send_command(command)
        
        if response.get("status") == "success":
            return True
        else:
            error_msg = response.get("error", "Unknown error")
            raise TTSError(f"Failed to load voice: {error_msg}")
    
    def unload_voice(self, voice_path: str) -> bool:
        """Unload a voice file from server memory"""
        voice_file = Path(voice_path).resolve()
        
        command = {
            "action": "unload_voice", 
            "voice_path": str(voice_file)
        }
        
        try:
            response = self._send_command(command)
            return response.get("status") == "success"
        except TTSError:
            # If server is not running, consider voice unloaded
            if not self._is_server_running():
                return False
            raise
    
    def unload_all_voices(self) -> int:
        """Unload all voices from server memory"""
        command = {"action": "unload_all"}
        
        try:
            response = self._send_command(command)
            if response.get("status") == "success":
                return response.get("unloaded_count", 0)
            else:
                error_msg = response.get("error", "Unknown error")
                raise TTSError(f"Failed to unload voices: {error_msg}")
        except TTSError:
            # If server is not running, no voices are loaded
            if not self._is_server_running():
                return 0
            raise
    
    def get_loaded_voices(self) -> List[Dict[str, Any]]:
        """Get list of currently loaded voices"""
        if not self._is_server_running():
            return []
        
        command = {"action": "list_voices"}
        
        try:
            response = self._send_command(command)
            if response.get("status") == "success":
                return response.get("voices", [])
            else:
                self.logger.warning(f"Failed to get voice list: {response.get('error')}")
                return []
        except TTSError:
            return []
    
    def is_voice_loaded(self, voice_path: str) -> bool:
        """Check if a specific voice is loaded"""
        voice_file = Path(voice_path).resolve()
        loaded_voices = self.get_loaded_voices()
        
        for voice_info in loaded_voices:
            if Path(voice_info['path']).resolve() == voice_file:
                return True
        return False
    
    def synthesize_with_loaded_voice(self, text: str, voice_path: str, **kwargs) -> bytes:
        """Use server to synthesize with a loaded voice"""
        voice_file = Path(voice_path).resolve()
        
        command = {
            "action": "synthesize",
            "text": text,
            "voice_path": str(voice_file),
            "options": kwargs
        }
        
        response = self._send_command(command)
        
        if response.get("status") == "success":
            # Get audio data (base64 encoded)
            import base64
            audio_data = base64.b64decode(response["audio_data"])
            return audio_data
        else:
            error_msg = response.get("error", "Unknown error")
            raise TTSError(f"Synthesis failed: {error_msg}")
    
    def shutdown_server(self) -> bool:
        """Shutdown the chatterbox server"""
        if not self._is_server_running():
            return True
        
        command = {"action": "shutdown"}
        
        try:
            response = self._send_command(command)
            return response.get("status") == "success"
        except TTSError:
            # Server might have shut down before responding
            return not self._is_server_running()