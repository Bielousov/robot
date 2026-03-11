"""
MindProxy - CORS Proxy for Ollama API

Provides a CORS-enabled proxy server to allow web UIs to communicate with Ollama.
Handles GET, POST, and OPTIONS requests to forward them to the Ollama server.
"""

import json
import threading
import time
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional


class OllamaCORSProxy(BaseHTTPRequestHandler):
    """CORS proxy for Ollama API - allows web UI to communicate with Ollama"""
    
    ollama_base_url = "http://localhost:11434"
    
    def do_POST(self):
        """Handle POST requests to Ollama API"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            # Forward request to Ollama
            request = urllib.request.Request(
                f"{self.ollama_base_url}{self.path}",
                data=body,
                headers={
                    'Content-Type': 'application/json',
                    'Content-Length': str(len(body))
                }
            )
            
            with urllib.request.urlopen(request, timeout=300) as response:
                response_data = response.read()
                
            # Send response with CORS headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(response_data)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = json.dumps({'error': str(e)}).encode()
            self.wfile.write(error_response)
    
    def do_GET(self):
        """Handle GET requests to Ollama API"""
        try:
            with urllib.request.urlopen(f"{self.ollama_base_url}{self.path}", timeout=10) as response:
                response_data = response.read()
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.end_headers()
            self.wfile.write(response_data)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = json.dumps({'error': str(e)}).encode()
            self.wfile.write(error_response)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', '0')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress verbose logging"""
        pass


class OllamaAPIServer:
    """Manages CORS proxy server for Ollama API"""
    
    def __init__(self, proxy_port: int = 11435, ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama API server proxy.
        
        Args:
            proxy_port: Port to listen on (default: 11435)
            ollama_base_url: Base URL of Ollama server (default: http://localhost:11434)
        """
        self.proxy_port = proxy_port
        self.ollama_base_url = ollama_base_url
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        
        # Set the base URL on the handler class
        OllamaCORSProxy.ollama_base_url = ollama_base_url
    
    def start(self) -> bool:
        """
        Start the CORS proxy server.
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # Verify Ollama is reachable
            urllib.request.urlopen(f"{self.ollama_base_url}/api/tags", timeout=2)
            
            def run_server():
                self.server = HTTPServer(
                    ("0.0.0.0", self.proxy_port),
                    OllamaCORSProxy
                )
                print(f"[Robot] Ollama API proxy listening on http://0.0.0.0:{self.proxy_port}")
                self.server.serve_forever()
            
            # Start server in background daemon thread
            self.thread = threading.Thread(target=run_server, daemon=True)
            self.thread.start()
            time.sleep(0.5)  # Give server time to bind
            return True
            
        except Exception as e:
            print(f"[Robot] Warning: Could not start Ollama API proxy: {e}")
            return False
    
    def stop(self):
        """Stop the CORS proxy server"""
        if self.server:
            try:
                self.server.shutdown()
            except Exception as e:
                print(f"[Robot] Error stopping API proxy: {e}")
            finally:
                self.server = None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
