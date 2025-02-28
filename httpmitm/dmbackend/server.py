from http.server import *
import http.client as cli
import requests
import device_management_pb2
import socket
import json
from urllib import parse

class MITMHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        request_data = self.rfile.read(content_length)

        dmr = device_management_pb2.DeviceManagementRequest()
        try:
            dmr.ParseFromString(request_data)
            parsed_protobuf = str(dmr)
        except Exception as e:
            parsed_protobuf = f"Failed to parse Protobuf: {e}"

        log_data = {
            "method": self.command,
            "path": self.path,
            "headers": dict(self.headers),
            "raw_body": request_data.hex(),
            "parsed_protobuf": parsed_protobuf
        }
        print("\n===== Incoming Request =====")
        print(json.dumps(log_data, indent=4))

        google_url = 'https://m.google.com/devicemanagement/data/api?' + parse.urlparse(self.path).query
        google_response = requests.post(google_url, data=request_data, headers=dict(self.headers))

        log_response = {
            "status_code": google_response.status_code,
            "headers": dict(google_response.headers),
            "raw_body": google_response.content.hex()
        }
        print("\n===== Google Response =====")
        print(json.dumps(log_response, indent=4))

        self.send_response(google_response.status_code)
        for key, value in google_response.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(google_response.content)

print("Starting HTTP MITM Proxy on port 3040...")
server = HTTPServer(("0.0.0.0", 3040), MITMHandler, bind_and_activate=False)
server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
server.server_bind()
server.server_activate()

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down server...")
    server.server_close()
