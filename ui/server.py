"""
Simple HTTP server for the Agent Chat UI.
"""

import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"=" * 80)
        print(f"🌐 Agent Chat UI Server")
        print(f"=" * 80)
        print(f"\n✓ Server running at: http://localhost:{PORT}")
        print(f"✓ Open in your browser to interact with the agent")
        print(f"\nMake sure the API server is running on http://localhost:8123")
        print(f"\n" + "=" * 80 + "\n")
        httpd.serve_forever()
