"""Reproduced backend audit cases; disposable data and explicit process/model doubles."""
import subprocess
import time
from types import SimpleNamespace

import pytest

import handoffready.api as backend
from test_api import FakeModel, create, fresh, mutate, wait_job
from test_delivery_context_api import local_client


@pytest.mark.parametrize("cleanup_error", [subprocess.TimeoutExpired("synthetic-parser", 2), OSError("synthetic reap failure")])
def test_unreaped_parser_returns_blocked_result_and_releases_queue(tmp_path, monkeypatch, cleanup_error):
    class UnreapedWorker:
        pid = 999999999

        def poll(self):
            return None

        def kill(self):
            pass

        def wait(self, timeout):
            raise cleanup_error

    monkeypatch.setattr(backend.subprocess, "Popen", lambda *args, **kwargs: UnreapedWorker())
    monkeypatch.setattr(backend.psutil, "Process", lambda pid: SimpleNamespace(
        memory_info=lambda: SimpleNamespace(rss=513 * 1024 * 1024)))
    result = backend.inspect_bounded(tmp_path / "unread.txt", "unread.txt", time.monotonic() + 5)
    assert result["inspection"] == "blocked"
    assert result["text"] == "" and result["metadata"] == {}
    assert "synthetic" not in result["error"]
    assert backend.PARSER_LOCK.acquire(blocking=False)
    backend.PARSER_LOCK.release()


def test_streamed_multipart_budget_returns_safe_413_without_mutation(tmp_path, monkeypatch):
    with local_client(backend.create_app(tmp_path)) as client:
        project = create(client)
        before = client.app.state.store.get(project["id"])
        payload = (b'--synthetic\r\nContent-Disposition: form-data; name="files[]"; filename="guide.txt"\r\n'
                   b'Content-Type: text/plain\r\n\r\n' + b'PRIVATE UPLOAD BYTES' * 100 + b'\r\n--synthetic--\r\n')
        monkeypatch.setitem(backend.LIMITS, "request_bytes", 200)
        result = client.post(f'/api/v1/projects/{project["id"]}/files',
                             content=iter([payload[:100], payload[100:]]),
                             headers={"If-Match": str(project["revision"]),
                                      "Content-Type": "multipart/form-data; boundary=synthetic"})
        assert result.status_code == 413
        assert result.json()["error"]["code"] == "request_limit"
        assert "PRIVATE" not in result.text and "Traceback" not in result.text
        assert client.app.state.store.get(project["id"]) == before
        assert list(client.app.state.store.files.iterdir()) == []


@pytest.mark.parametrize("omitted", [False, True])
def test_extraction_without_quote_is_rejected_as_source_evidence_failure(tmp_path, omitted):
    class MissingQuoteModel(FakeModel):
        def extract(self, brief, *, deadline=None):
            result = super().extract(brief)
            if omitted:
                result["requirements"][0].pop("quote")
            else:
                result["requirements"][0]["quote"] = None
            return result

    with local_client(backend.create_app(tmp_path, MissingQuoteModel())) as client:
        project = mutate(client, create(client), "put", "/brief", {"text": "Supply the actual delivery guide."})
        queued = mutate(client, project, "post", "/jobs/extract", {})
        job = wait_job(client, project, queued["job"]["id"])
        assert job["state"] == "failed"
        assert job["error_code"] == "invalid_source_quote"
        assert fresh(client, project)["baseline"]["requirements"] == []
