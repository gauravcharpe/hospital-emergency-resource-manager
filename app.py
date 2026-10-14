"""
Hospital Emergency Resource Manager (HERM)
Web Server and RESTful API Entry Point.
Runs a zero-dependency web server for the clinical command center dashboard.
"""

import http.server
import socketserver
import json
import os
import sys
import webbrowser
from typing import Dict, Any

# Ensure root directory is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from herm.core.simulator import HospitalSimulator, get_standard_test_workload, get_surge_workload
from herm.core.scheduler import SchedulingPolicy
from herm.core.models import Patient
from herm.core.benchmark import BenchmarkEngine

# Global singleton simulation instance
simulator = HospitalSimulator()

class HermAPIHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def send_json_response(self, data: Any, status_code: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index.html"):
            html_path = os.path.join(ROOT_DIR, "herm", "web", "index.html")
            with open(html_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        elif self.path == "/api/status":
            snapshot = simulator.get_state_snapshot()
            self.send_json_response(snapshot)
            return

        else:
            self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            req_data = json.loads(post_body) if post_body else {}
        except json.JSONDecodeError:
            req_data = {}

        if self.path == "/api/step":
            snapshot = simulator.step()
            self.send_json_response(snapshot)

        elif self.path == "/api/reset":
            policy_str = req_data.get("policy", "PREEMPTIVE_PRIORITY_AGING")
            banker = req_data.get("banker_enabled", True)
            try:
                policy = SchedulingPolicy[policy_str]
            except KeyError:
                policy = SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING
            
            simulator.reset(policy=policy, banker_enabled=banker)
            self.send_json_response(simulator.get_state_snapshot())

        elif self.path == "/api/trigger_deadlock":
            simulator.trigger_deadlock_scenario()
            self.send_json_response(simulator.get_state_snapshot())

        elif self.path == "/api/load_surge":
            simulator.load_workload(get_surge_workload())
            simulator.reset()
            self.send_json_response(simulator.get_state_snapshot())

        elif self.path == "/api/add_patient":
            new_p = Patient(
                pid=req_data.get("pid", f"P{len(simulator.all_patients)+1}"),
                name=req_data.get("name", "Emergency Patient"),
                arrival_time=simulator.current_time,
                base_priority=int(req_data.get("base_priority", 2)),
                burst_time=int(req_data.get("burst_time", 6)),
                max_resources=req_data.get("max_resources", {})
            )
            simulator.add_patient(new_p)
            self.send_json_response(simulator.get_state_snapshot())

        elif self.path == "/api/benchmark":
            results = BenchmarkEngine.run_comparative_study(get_surge_workload())
            self.send_json_response(results)

        else:
            self.send_error(404, "Endpoint Not Found")

def run_server(port: int = 5050, auto_open: bool = False):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), HermAPIHandler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\n" + "="*70)
        print(f"  HERM: Hospital Emergency Resource Manager (BCSE303L)")
        print(f"  Faculty: Dr. V. Ezhil Arasi | School of Computer Science, VIT")
        print(f"  Server active at: {url}")
        print(f"="*70 + "\n")
        if auto_open:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down HERM Server.")
            httpd.shutdown()

if __name__ == "__main__":
    port = 5050
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port, auto_open=False)
