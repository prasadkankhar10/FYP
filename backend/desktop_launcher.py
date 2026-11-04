# -*- coding: utf-8 -*-
"""
SynapseFlow Desktop Native Window Entrypoint.
Starts the FastAPI server locally in a background daemon thread
and launches a clean native desktop window powered by Microsoft Edge WebView2 (pywebview).
"""

import os
import sys
import time
import socket
import threading
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app

# Determine dist folder location (PyInstaller bundled or local dev)
if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', current_dir)
    dist_dir = os.path.join(base_dir, "dist")
    db_source = os.path.join(base_dir, "arsps.db")
    # In frozen mode, ensure db exists in user working dir
    local_db = os.path.join(os.getcwd(), "arsps.db")
    if not os.path.exists(local_db) and os.path.exists(db_source):
        import shutil
        shutil.copy2(db_source, local_db)
else:
    dist_dir = os.path.abspath(os.path.join(current_dir, "..", "frontend", "dist"))

# Mount frontend assets
assets_dir = os.path.join(dist_dir, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="static_assets")

@app.middleware("http")
async def spa_middleware(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404:
        path = request.url.path
        api_prefixes = ("/auth", "/subjects", "/concepts", "/reviews", "/schedule", "/analytics", "/ai", "/graph", "/docs", "/openapi.json", "/health", "/assets")
        if not any(path.startswith(prefix) for prefix in api_prefixes):
            index_path = os.path.join(dist_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
    return response

@app.get("/")
async def serve_index():
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "SynapseFlow API is active, but frontend/dist/index.html was not found."}


def run_server(port: int):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def main():
    import webview
    
    port = 8000
    # Check if 8000 is open, else pick free port
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", port))
        s.close()
    except OSError:
        # Pick another free port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

    # Start FastAPI server in background daemon thread
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    time.sleep(1.0)
    app_url = f"http://127.0.0.1:{port}"
    print(f"SynapseFlow local backend running at {app_url}")

    # Create Native Desktop Window
    window = webview.create_window(
        title="SynapseFlow — Adaptive Multi-Concept Knowledge Graph SRS",
        url=app_url,
        width=1320,
        height=860,
        min_size=(1024, 680),
        text_select=True,
        confirm_close=False
    )
    
    # Start the native window event loop (blocks until window is closed)
    webview.start()


if __name__ == "__main__":
    main()
