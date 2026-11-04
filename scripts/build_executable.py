# -*- coding: utf-8 -*-
"""
Build script to compile SynapseFlow into a standalone Windows .exe
Runs PyInstaller in backend/.venv with all required assets, templates, and hidden imports.
"""

import os
import sys
import subprocess

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(workspace_root, "backend")
frontend_dist = os.path.join(workspace_root, "frontend", "dist")
db_file = os.path.join(backend_dir, "arsps.db")
launcher_file = os.path.join(backend_dir, "desktop_launcher.py")

pyinstaller_exe = r"C:\Users\prasa\OneDrive\Desktop\FYP\project\backend\.venv\Scripts\pyinstaller.exe"
if not os.path.exists(pyinstaller_exe):
    pyinstaller_exe = os.path.join(backend_dir, ".venv", "Scripts", "pyinstaller.exe")

print(f"Workspace Root: {workspace_root}")
print(f"Backend Dir:    {backend_dir}")
print(f"Frontend Dist:  {frontend_dist} (exists: {os.path.exists(frontend_dist)})")
print(f"Database File:  {db_file} (exists: {os.path.exists(db_file)})")
print(f"Launcher:       {launcher_file} (exists: {os.path.exists(launcher_file)})")

# Data files to bundle: format: source;destination
add_data = [
    f"{frontend_dist};dist",
    f"{db_file};."
]

hidden_imports = [
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespans",
    "uvicorn.lifespans.on",
    "uvicorn.lifespans.off",
    "fastapi",
    "starlette",
    "pydantic",
    "pydantic_settings",
    "sqlalchemy",
    "sqlite3",
    "webview",
    "clr",
    "pythonnet",
    "networkx",
    "jose",
    "passlib",
    "bcrypt",
    "email_validator",
    "multipart"
]

excludes = [
    "torch",
    "torchvision",
    "torchaudio",
    "scipy",
    "pytest",
    "matplotlib",
    "pandas",
    "IPython",
    "jupyter",
    "PIL"
]

cmd = [
    pyinstaller_exe,
    "--name=SynapseFlow",
    "--onefile",
    "--noconsole",
    f"--distpath={os.path.join(workspace_root, 'dist_executable')}",
    f"--workpath={os.path.join(backend_dir, 'build')}",
    f"--specpath={backend_dir}",
    f"--paths={backend_dir}",
    "--clean"
]

for ex in excludes:
    cmd.extend(["--exclude-module", ex])

for d in add_data:
    cmd.extend(["--add-data", d])

for hi in hidden_imports:
    cmd.extend(["--hidden-import", hi])

cmd.append(launcher_file)

print("\nStarting PyInstaller build command...")
result = subprocess.run(cmd, cwd=backend_dir)
if result.returncode == 0:
    print("\nSUCCESS! SynapseFlow.exe built successfully in dist_executable/!")
else:
    print(f"\nPyInstaller failed with code {result.returncode}")
    sys.exit(result.returncode)
