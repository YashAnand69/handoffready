#!/usr/bin/env python3
"""Start the built local app, optionally with its already-installed local model.

This launcher never downloads or installs anything. Use prepare_model.py for
explicit model setup. Only processes started by this launcher are stopped.
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from handoffready.model import ready


def sha(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def port_available(port):
    with socket.socket() as connection:
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            connection.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def stop(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def model_command():
    manifest_file = ROOT / ".model/manifest.json"
    if not manifest_file.is_file():
        raise SystemExit("Model is not installed. Explicitly run scripts/prepare_model.py first, or start without --with-model.")
    manifest = json.loads(manifest_file.read_text())
    weights = ROOT / ".model" / manifest["artifact"]
    if not weights.is_file() or sha(weights) != manifest["model_sha256"]:
        raise SystemExit("Installed model bytes do not match their receipt. Repair model setup explicitly.")
    servers = [path for path in (ROOT / ".runtime").rglob("llama-server") if path.is_file() and os.access(path, os.X_OK)]
    servers = [path for path in servers if sha(path) == manifest["runtime_server_sha256"]]
    if len(servers) != 1:
        raise SystemExit("Exactly one verified llama-server must match the installation receipt.")
    key = ROOT / ".model/server.key"
    if not key.is_file() or not key.read_text().strip():
        raise SystemExit("Local model server key is missing. Repair explicit model setup.")
    key.chmod(0o600)
    return [str(servers[0]), "-m", str(weights), "--alias", manifest["alias"], "--host", "127.0.0.1", "--port", "18081",
            "-c", "8192", "-np", "1", "-ngl", "99", "--jinja", "--no-webui", "--reasoning", "off", "--api-key-file", str(key), "--cors-origins", "http://127.0.0.1:8877"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-model", action="store_true", help="Start the verified installed model if not already running")
    parser.add_argument("--data-dir", help="Private persistent app directory; default is the user application-data directory")
    args = parser.parse_args()
    if not (ROOT / "frontend/dist/index.html").is_file():
        raise SystemExit("Build the frontend before starting the production app.")
    if not port_available(8877):
        raise SystemExit("Port 8877 is occupied. Use the existing app or stop its owner before starting another instance.")
    model_process, app_process, log = None, None, None
    try:
        if args.with_model:
            if not ready().get("available"):
                if not port_available(18081):
                    raise SystemExit("Port 18081 is occupied by an unverified model service. It was not replaced.")
                command = model_command()
                log_dir = ROOT / ".runtime"
                log_dir.mkdir(exist_ok=True, mode=0o700)
                log = (log_dir / "launcher-model.log").open("wb")
                model_process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                until = time.monotonic() + 120
                while time.monotonic() < until:
                    if model_process.poll() is not None:
                        raise SystemExit("Model server exited. Review the local runtime log.")
                    if ready(deadline=until).get("available"):
                        break
                    time.sleep(.25)
                else:
                    raise SystemExit("Model did not become ready within 120 seconds.")
            print("Verified installed local model is ready.", flush=True)
        environment = dict(os.environ)
        if args.data_dir:
            environment["HANDOFFREADY_DATA"] = str(Path(args.data_dir).expanduser().resolve())
        app_process = subprocess.Popen([sys.executable, str(ROOT / "scripts/run.py")], cwd=ROOT, env=environment)
        print("HandoffReady: http://127.0.0.1:8877 — press Ctrl+C to stop processes owned by this launcher.", flush=True)
        app_process.wait()
        if app_process.returncode:
            raise SystemExit(app_process.returncode)
    except KeyboardInterrupt:
        print("Stopping owned local processes.")
    finally:
        stop(app_process)
        stop(model_process)
        if log:
            log.close()


if __name__ == "__main__":
    main()
