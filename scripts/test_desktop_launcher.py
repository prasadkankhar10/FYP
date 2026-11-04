import os
import sys

backend_dir = os.path.abspath('backend')
sys.path.insert(0, backend_dir)

import desktop_launcher
from starlette.testclient import TestClient

client = TestClient(desktop_launcher.app)

# Test root /
resp = client.get("/")
print("Root / status:", resp.status_code)
print("Root / content-type:", resp.headers.get("content-type"))
print("Root / starts with HTML:", resp.text.strip().startswith("<!doctype") or resp.text.strip().startswith("<!DOCTYPE"))

# Test SPA route /dashboard
resp2 = client.get("/dashboard")
print("/dashboard status:", resp2.status_code)
print("/dashboard starts with HTML:", resp2.text.strip().startswith("<!doctype") or resp2.text.strip().startswith("<!DOCTYPE"))

# Test API route /health
resp3 = client.get("/health")
print("/health status:", resp3.status_code, resp3.json())

# Test API route /api/status
resp4 = client.get("/api/status")
print("/api/status status:", resp4.status_code, resp4.json())
