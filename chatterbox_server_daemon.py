#!/usr/bin/env python3
"""
Enhanced Chatterbox TTS server with voice loading and management capabilities.
Supports multiple voice loading, unloading, and synthesis via JSON commands.
"""
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="perth")
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")

import socket
import threading
import time
import json
import base64
import subprocess
import io
import wave
import numpy as np
import torch
from pathlib import Path
from typing import Dict, Any, Optional
from chatterbox.tts import ChatterboxTTS


class EnhancedChatterboxServer:
    def __init__(self, port=12345):
        self.port = port
        self.model = None
        self.loaded_voices: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.idle_start_time = None
        self.shutdown_event = threading.Event()
        
        print("🚀 Starting Enhanced Chatterbox TTS Server...")
        self.load_model()
        
        # Start idle monitor thread
        self.idle_monitor_thread = threading.Thread(target=self._idle_monitor, daemon=True)
        self.idle_monitor_thread.start()
        
    def load_model(self):
        """Load the main TTS model"""
        print("📡 Loading Chatterbox model to GPU...")
        start_time = time.time()
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = ChatterboxTTS.from_pretrained(device=device)
        
        load_time = time.time() - start_time
        
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.memory_allocated(0) / 1e9
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ Model loaded in {load_time:.2f}s on {gpu_name}")
            print(f"🎯 GPU Memory: {gpu_memory:.2f}GB allocated")
        else:
            print(f"✅ Model loaded in {load_time:.2f}s on CPU")
        
        print(f"🎤 Server ready on port {self.port}")
    
    def _idle_monitor(self):
        """Monitor for idle timeout and auto-shutdown when no voices loaded"""
        while not self.shutdown_event.is_set():
            time.sleep(30)  # Check every 30 seconds
            
            with self.lock:
                if len(self.loaded_voices) == 0:
                    if self.idle_start_time is None:
                        self.idle_start_time = time.time()
                    elif time.time() - self.idle_start_time > 600:  # 10 minutes
                        print("🔄 Auto-shutdown: No voices loaded for 10 minutes")
                        self.shutdown_event.set()
                        break
                else:
                    self.idle_start_time = None
    
    def start_server(self):
        """Start the socket server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(1.0)  # Allow checking shutdown event
        
        try:
            server_socket.bind(('localhost', self.port))
            server_socket.listen(5)
            
            print(f"🌐 Server listening on localhost:{self.port}")
            print("💡 Send JSON commands via client")
            print("📝 Auto-shutdown after 10min idle (no voices loaded)")
            print("-" * 50)
            
            while not self.shutdown_event.is_set():
                try:
                    client_socket, address = server_socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                    thread.daemon = True
                    thread.start()
                except socket.timeout:
                    continue  # Check shutdown event
                except Exception as e:
                    if not self.shutdown_event.is_set():
                        print(f"❌ Server error: {e}")
                    
        except KeyboardInterrupt:
            print("\n👋 Shutting down server (Ctrl+C)...")
        except Exception as e:
            print(f"❌ Server startup error: {e}")
        finally:
            server_socket.close()
            print("🔒 Server socket closed")
    
    def handle_client(self, client_socket):
        """Handle client request with JSON commands"""
        try:
            # Receive JSON command
            data = b""
            while b"\n" not in data:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
            
            if not data:
                return
            
            command_str = data.decode('utf-8').strip()
            try:
                command = json.loads(command_str)
            except json.JSONDecodeError as e:
                response = {"status": "error", "error": f"Invalid JSON: {e}"}
                self._send_response(client_socket, response)
                return
            
            # Process command
            action = command.get("action")
            
            if action == "load_voice":
                response = self._handle_load_voice(command)
            elif action == "unload_voice":
                response = self._handle_unload_voice(command)
            elif action == "unload_all":
                response = self._handle_unload_all()
            elif action == "list_voices":
                response = self._handle_list_voices()
            elif action == "synthesize":
                response = self._handle_synthesize(command)
            elif action == "shutdown":
                response = {"status": "success", "message": "Shutting down"}
                self._send_response(client_socket, response)
                self.shutdown_event.set()
                return
            else:
                response = {"status": "error", "error": f"Unknown action: {action}"}
            
            self._send_response(client_socket, response)
            
        except Exception as e:
            print(f"❌ Client handling error: {e}")
            response = {"status": "error", "error": str(e)}
            self._send_response(client_socket, response)
        finally:
            client_socket.close()
    
    def _send_response(self, client_socket, response: dict):
        """Send JSON response to client"""
        try:
            response_str = json.dumps(response) + "\n"
            client_socket.send(response_str.encode('utf-8'))
        except Exception as e:
            print(f"❌ Failed to send response: {e}")
    
    def _handle_load_voice(self, command: dict) -> dict:
        """Load a voice file into memory"""
        voice_path = command.get("voice_path")
        if not voice_path:
            return {"status": "error", "error": "Missing voice_path"}
        
        voice_file = Path(voice_path).resolve()
        voice_key = str(voice_file)
        
        if not voice_file.exists():
            return {"status": "error", "error": f"Voice file not found: {voice_file}"}
        
        with self.lock:
            if voice_key in self.loaded_voices:
                return {"status": "success", "message": "Voice already loaded", "cached": True}
            
            try:
                # Load voice for chatterbox (just store the path, actual loading is per-synthesis)
                load_start = time.time()
                
                # Verify we can read the file
                if not voice_file.is_file():
                    return {"status": "error", "error": f"Not a valid file: {voice_file}"}
                
                # Store voice info
                self.loaded_voices[voice_key] = {
                    "path": voice_key,
                    "name": voice_file.name,
                    "load_time": time.strftime("%M:%S ago", time.localtime(load_start)),
                    "loaded_at": load_start,
                    "memory_mb": 50  # Estimate for voice embedding
                }
                
                load_time = time.time() - load_start
                print(f"🎵 Loaded voice: {voice_file.name} ({load_time:.2f}s)")
                
                return {
                    "status": "success", 
                    "message": f"Voice loaded: {voice_file.name}",
                    "load_time": f"{load_time:.2f}s"
                }
                
            except Exception as e:
                return {"status": "error", "error": f"Failed to load voice: {e}"}
    
    def _handle_unload_voice(self, command: dict) -> dict:
        """Unload a voice file from memory"""
        voice_path = command.get("voice_path")
        if not voice_path:
            return {"status": "error", "error": "Missing voice_path"}
        
        voice_file = Path(voice_path).resolve()
        voice_key = str(voice_file)
        
        with self.lock:
            if voice_key in self.loaded_voices:
                voice_name = self.loaded_voices[voice_key]["name"]
                del self.loaded_voices[voice_key]
                print(f"🗑️  Unloaded voice: {voice_name}")
                return {"status": "success", "message": f"Voice unloaded: {voice_name}"}
            else:
                return {"status": "error", "error": "Voice not loaded"}
    
    def _handle_unload_all(self) -> dict:
        """Unload all voices from memory"""
        with self.lock:
            count = len(self.loaded_voices)
            self.loaded_voices.clear()
            print(f"🗑️  Unloaded all voices ({count} total)")
            return {"status": "success", "unloaded_count": count}
    
    def _handle_list_voices(self) -> dict:
        """List all loaded voices"""
        with self.lock:
            voices = []
            current_time = time.time()
            
            for voice_info in self.loaded_voices.values():
                # Update relative time
                loaded_at = voice_info["loaded_at"]
                minutes_ago = int((current_time - loaded_at) / 60)
                if minutes_ago < 1:
                    time_str = "just now"
                elif minutes_ago == 1:
                    time_str = "1min ago"
                else:
                    time_str = f"{minutes_ago}min ago"
                
                voice_copy = voice_info.copy()
                voice_copy["load_time"] = time_str
                voices.append(voice_copy)
            
            return {"status": "success", "voices": voices}
    
    def _handle_synthesize(self, command: dict) -> dict:
        """Synthesize speech with a loaded voice"""
        text = command.get("text")
        voice_path = command.get("voice_path")
        options = command.get("options", {})
        
        if not text:
            return {"status": "error", "error": "Missing text"}
        
        if not voice_path:
            return {"status": "error", "error": "Missing voice_path"}
        
        voice_file = Path(voice_path).resolve()
        voice_key = str(voice_file)
        
        with self.lock:
            if voice_key not in self.loaded_voices:
                return {"status": "error", "error": "Voice not loaded"}
        
        try:
            print(f"🎵 Synthesizing with {voice_file.name}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Extract options
            exaggeration = float(options.get("exaggeration", 0.5))
            cfg_weight = float(options.get("cfg_weight", 0.5))
            temperature = float(options.get("temperature", 0.8))
            min_p = float(options.get("min_p", 0.05))
            
            # Generate with voice cloning
            gen_start = time.time()
            wav = self.model.generate(
                text, 
                audio_prompt_path=str(voice_file),
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                temperature=temperature,
                min_p=min_p
            )
            gen_time = time.time() - gen_start
            
            # Convert to audio data
            audio_data = self._wav_to_bytes(wav)
            
            # Encode as base64 for JSON transport
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            print(f"⚡ Generated in {gen_time:.2f}s")
            
            return {
                "status": "success",
                "audio_data": audio_b64,
                "generation_time": f"{gen_time:.2f}s",
                "sample_rate": self.model.sr
            }
            
        except Exception as e:
            print(f"❌ Synthesis error: {e}")
            return {"status": "error", "error": f"Synthesis failed: {e}"}
    
    def _wav_to_bytes(self, wav_tensor) -> bytes:
        """Convert WAV tensor to bytes"""
        audio_data = wav_tensor.cpu().numpy().squeeze()
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.model.sr)
            audio_normalized = np.clip(audio_data, -1.0, 1.0)
            audio_16bit = (audio_normalized * 32767 * 0.95).astype(np.int16)
            wav_file.writeframes(audio_16bit.tobytes())
        
        return buffer.getvalue()


if __name__ == "__main__":
    server = EnhancedChatterboxServer()
    server.start_server()