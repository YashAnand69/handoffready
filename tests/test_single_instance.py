"""Exercise the documented server entry point with isolated synthetic storage."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest

from handoffready.store import Store, StoreError, canonical, exclusive_directory


ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as handle:
        handle.bind(("127.0.0.1", 0))
        return handle.getsockname()[1]


def start_server(directory, port):
    return subprocess.Popen(
        [sys.executable, str(ROOT / "scripts/run.py")], cwd=ROOT,
        env={**os.environ, "HANDOFFREADY_DATA": str(directory), "HANDOFFREADY_PORT": str(port)},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )


def wait_ready(process, port):
    with httpx.Client(trust_env=False, timeout=1) as client:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail("Server stopped before readiness: " + process.communicate()[0])
            try:
                if client.get(f"http://127.0.0.1:{port}/api/v1/bootstrap").status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(.05)
    pytest.fail("Server did not become ready")


def stop_server(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if process.stdout is not None and not process.stdout.closed:
        process.communicate()


@pytest.mark.parametrize("abrupt", [False, True])
def test_second_server_cannot_recover_live_storage_and_restart_can(tmp_path, abrupt):
    port = free_port()
    first = start_server(tmp_path, port)
    second = None
    restarted = None
    try:
        wait_ready(first, port)
        # Simulate a pending inspection after the owning process has started.
        store = Store(tmp_path)
        project = store.create("Synthetic active upload", 10)
        project["jobs"] = [{"id": "synthetic-job", "state": "running"}]
        with store.connection() as db:
            db.execute("UPDATE projects SET body=? WHERE id=?", (canonical(project), project["id"]))
        staged = store.files / "synthetic-upload-in-progress"
        staged.write_bytes(b"Synthetic staged original, not registered until inspection completes")
        before = store.get(project["id"])

        second = start_server(tmp_path, free_port())
        output, _ = second.communicate(timeout=10)
        assert second.returncode != 0
        assert "data folder is already open" in output
        assert staged.read_bytes().startswith(b"Synthetic staged original")
        assert store.get(project["id"]) == before
        assert first.poll() is None

        if abrupt:
            first.kill()
        stop_server(first)
        restarted_port = free_port()
        restarted = start_server(tmp_path, restarted_port)
        wait_ready(restarted, restarted_port)
        # Actual restart recovery is still allowed after ownership is released.
        with store.connection() as db:
            recovered = json.loads(db.execute("SELECT body FROM projects WHERE id=?", (project["id"],)).fetchone()[0])
        assert recovered["jobs"][0]["state"] == "interrupted"
        assert not staged.exists()
    finally:
        stop_server(first)
        if second is not None:
            stop_server(second)
        if restarted is not None:
            stop_server(restarted)


def test_directory_ownership_is_per_folder_and_lock_file_is_private(tmp_path):
    primary, separate = tmp_path / "primary", tmp_path / "separate"
    with exclusive_directory(primary):
        with pytest.raises(StoreError, match="already open"):
            with exclusive_directory(primary):
                pytest.fail("Two owners entered the same directory")
        with exclusive_directory(separate):
            assert (primary / ".instance.lock").stat().st_mode & 0o777 == 0o600
    with exclusive_directory(primary):
        pass


def test_lock_file_cannot_follow_a_symlink(tmp_path):
    original = tmp_path / "untouched"
    original.write_bytes(b"untouched")
    (tmp_path / ".instance.lock").symlink_to(original)
    with pytest.raises(OSError):
        with exclusive_directory(tmp_path):
            pytest.fail("Lock must not follow an existing symlink")
    assert original.read_bytes() == b"untouched"
