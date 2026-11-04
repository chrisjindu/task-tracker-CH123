from http.server import BaseHTTPRequestHandler, HTTPServer
import json
 
VERSION = "1.0.0"
PORT = 8080
TASKS = ["Set a budget alert", "Launch an EC2 instance", "Deploy Task Tracker"]
 
 
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok", "version": VERSION}).encode()
            content_type = "application/json"
        else:
            items = "".join(f"<li>{task}</li>" for task in TASKS)
            page = f"<h1>Task Tracker</h1><p>Version {VERSION}</p><ul>{items}</ul>"
            body = page.encode()
            content_type = "text/html"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body)
 
 
print(f"Task Tracker {VERSION} listening on port {PORT}", flush=True)
HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

