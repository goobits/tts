#!/usr/bin/env python3
"""
Client script to send text to the persistent Chatterbox server.
Usage: python speak.py "your text here"
"""
import socket
import sys

def send_text_to_server(text, port=12345):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', port))
        
        # Send text
        client_socket.send(text.encode('utf-8'))
        
        # Get response
        response = client_socket.recv(1024).decode('utf-8')
        print(response)
        
        client_socket.close()
        
    except ConnectionRefusedError:
        print("❌ Server not running! Start it with:")
        print("   python chatterbox_server_daemon.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python speak.py 'text to speak'")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    send_text_to_server(text)