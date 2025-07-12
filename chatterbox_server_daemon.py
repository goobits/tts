#!/usr/bin/env python3
"""
Persistent Chatterbox TTS server that stays running and accepts requests via socket.
Run once, then send text via client script.
"""
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="perth")
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")

import socket
import threading
import time
import subprocess
import io
import wave
import numpy as np
import torch
from chatterbox.tts import ChatterboxTTS

class ChatterboxServer:
    def __init__(self, port=12345):
        self.port = port
        self.model = None
        print("🚀 Starting Chatterbox TTS Server...")
        self.load_model()
        
    def load_model(self):
        print("📡 Loading model to GPU (one-time setup)...")
        start_time = time.time()
        self.model = ChatterboxTTS.from_pretrained(device='cuda')
        load_time = time.time() - start_time
        
        gpu_memory = torch.cuda.memory_allocated(0) / 1e9
        print(f"✅ Model loaded in {load_time:.2f}s!")
        print(f"🎯 GPU Memory: {gpu_memory:.2f}GB allocated")
        print(f"🎤 Server ready on port {self.port}")
    
    def start_server(self):
        """Start the socket server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', self.port))
        server_socket.listen(5)
        
        print(f"🌐 Server listening on localhost:{self.port}")
        print("💡 Send text via client script or telnet")
        print("📝 To stop server: Ctrl+C")
        print("-" * 50)
        
        try:
            while True:
                client_socket, address = server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                thread.start()
        except KeyboardInterrupt:
            print("\n👋 Shutting down server...")
        finally:
            server_socket.close()
    
    def handle_client(self, client_socket):
        """Handle client request"""
        try:
            # Receive text
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                return
                
            print(f"🎵 Generating: '{data[:50]}{'...' if len(data) > 50 else ''}'")
            
            # Time just the generation
            gen_start = time.time()
            wav = self.model.generate(data)
            gen_time = time.time() - gen_start
            
            # Play audio (separate from generation timing)
            play_start = time.time()
            self._stream_to_speakers(wav)
            play_time = time.time() - play_start
            
            print(f"⚡ Generated in {gen_time:.2f}s, played in {play_time:.2f}s")
            
            # Send response
            client_socket.send(f"✅ Generated in {gen_time:.2f}s".encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error: {e}")
            client_socket.send(f"❌ Error: {e}".encode('utf-8'))
        finally:
            client_socket.close()
    
    def _stream_to_speakers(self, wav_tensor):
        """Stream audio to speakers"""
        audio_data = wav_tensor.cpu().numpy().squeeze()
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.model.sr)
            audio_normalized = np.clip(audio_data, -1.0, 1.0)
            audio_16bit = (audio_normalized * 32767 * 0.95).astype(np.int16)
            wav_file.writeframes(audio_16bit.tobytes())
        
        buffer.seek(0)
        ffplay_process = subprocess.Popen([
            'ffplay', '-nodisp', '-autoexit', '-i', 'pipe:0'
        ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        ffplay_process.stdin.write(buffer.getvalue())
        ffplay_process.stdin.close()
        ffplay_process.wait()

if __name__ == "__main__":
    server = ChatterboxServer()
    server.start_server()