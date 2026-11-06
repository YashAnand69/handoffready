"""Exercise the narrow stdio tool boundary using disposable loopback HTTP."""

import importlib.util
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/delivery_tools.py"
SPEC = importlib.util.spec_from_file_location("delivery_tools", SCRIPT)
tools = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tools
SPEC.loader.exec_module(tools)
# Deliberately synthetic test value, never a usable account credential.
TEST_TOKEN = "synthetic-delivery-token-for-tests"


def environment(origin="http://127.0.0.1:8877"):
    return {"HANDOFFREADY_DELIVERY_ORIGIN": origin, "HANDOFFREADY_DELIVERY_BINDING": "binding-test", "HANDOFFREADY_DELIVERY_TOKEN": TEST_TOKEN}


def frame(method, identifier=1, params=None):
    return {"jsonrpc": "2.0", "id": identifier, "method": method, **({"params": params} if params is not None else {})}


def initialized_server(client):
    server = tools.Server(client)
    result = server.handle(frame("initialize", params={"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "synthetic", "version": "1"}}))
    assert result["protocolVersion"] == "2024-11-05"
    server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
    return server


@pytest.fixture
def backend():
    state = {"calls": [], "status": 200, "body": {"data": {"state": "needs_review", "source_revision": 3, "input_hash": "a" * 64}}, "content_type": "application/json"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            self.answer()

        def do_POST(self):
            self.answer()

        def answer(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            state["calls"].append({"path": self.path, "method": self.command, "headers": dict(self.headers), "body": json.loads(body) if body else None})
            self.send_response(state["status"])
            self.send_header("Content-Type", state["content_type"])
            if state["status"] == 302:
                self.send_header("Location", "/must-not-follow")
            self.end_headers()
            value = state["body"]
            self.wfile.write(value if isinstance(value, bytes) else json.dumps(value).encode())

    service = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=service.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{service.server_port}"
    try:
        yield tools.Config.from_env(environment(origin)), state
    finally:
        service.shutdown()
        service.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("origin", ["https://127.0.0.1:8877", "http://example.com:8877", "http://0.0.0.0:8877", "http://127.0.0.1", "http://127.0.0.1:80", "http://127.0.0.1:0", "http://127.0.0.1:99999", "http://user@127.0.0.1:8877", "http://127.0.0.1:8877/api", "http://127.0.0.1:8877?x=1", "http://127.0.0.1:8877#x", "http://127.0.0.1:8877\n"])
def test_refuses_nonlocal_or_ambiguous_origin(origin):
    with pytest.raises(tools.ConfigurationError):
        tools.Config.from_env(environment(origin))


def test_refuses_unsafe_binding_and_token_without_echoing_values():
    env = environment()
    env["HANDOFFREADY_DELIVERY_BINDING"] = "../another-project"
    with pytest.raises(tools.ConfigurationError):
        tools.Config.from_env(env)
    env = environment()
    env["HANDOFFREADY_DELIVERY_TOKEN"] = "sensitive\nheader"
    with pytest.raises(tools.ConfigurationError) as error:
        tools.Config.from_env(env)
    assert env["HANDOFFREADY_DELIVERY_TOKEN"] not in str(error.value)
    assert TEST_TOKEN not in repr(tools.Config.from_env(environment()))


def test_only_two_readonly_tools_and_no_calls_before_initialize(backend):
    config, state = backend
    client = tools.DeliveryClient(config)
    with pytest.raises(tools.RpcError):
        tools.Server(client).handle(frame("tools/list"))
    server = initialized_server(client)
    listed = server.handle(frame("tools/list"))["tools"]
    assert {tool["name"] for tool in listed} == {"delivery_status", "delivery_check_preview"}
    with pytest.raises(tools.RpcError) as error:
        server.handle(frame("tools/call", params={"name": "approve", "arguments": {"job_id": "job"}}))
    assert error.value.code == -32602
    assert not state["calls"]


def test_status_and_preview_use_fixed_binding_and_exact_currency(backend, monkeypatch):
    config, state = backend
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
    client = tools.DeliveryClient(config)
    assert client.call("delivery_status", {"job_id": "job-1"})["source_revision"] == 3
    selection = {"job_id": "job-1", "requirement_id": "r1", "file_ids": ["file-1"], "expected_revision": 3, "input_hash": "a" * 64}
    client.call("delivery_check_preview", selection)
    status, preview = state["calls"]
    assert status["path"] == "/api/v1/delivery/jobs/job-1/status"
    assert status["method"] == "GET"
    assert preview["method"] == "POST"
    assert preview["path"] == "/api/v1/delivery/jobs/job-1/preview"
    assert preview["body"] == {key: value for key, value in selection.items() if key != "job_id"}
    assert preview["headers"]["X-Delivery-Binding"] == config.binding
    assert preview["headers"]["X-Delivery-Token"] == TEST_TOKEN
    assert preview["headers"]["Origin"] == config.origin


@pytest.mark.parametrize("change", [{"job_id": "../other"}, {"job_id": "http://example.test"}, {"file_ids": ["x", "x"]}, {"file_ids": [["nested"]]}, {"expected_revision": True}, {"expected_revision": 0}, {"input_hash": "bad"}, {"url": "http://example.test"}, {"binding_id": "other"}, {"path": "/private"}])
def test_rejects_arbitrary_paths_and_invalid_selection_before_http(backend, change):
    config, state = backend
    arguments = {"job_id": "job", "requirement_id": "r", "file_ids": [], "expected_revision": 1, "input_hash": "a" * 64, **change}
    with pytest.raises(tools.RpcError):
        tools.DeliveryClient(config).call("delivery_check_preview", arguments)
    assert not state["calls"]


@pytest.mark.parametrize("status,code,advice", [(403, "access_refused", "operator_action"), (409, "revision_conflict", "refresh"), (422, "request_rejected", "correct_input"), (503, "backend_unavailable", "operator_action"), (302, "request_rejected", "correct_input")])
def test_http_error_never_echoes_body_or_follows_redirect(backend, status, code, advice):
    config, state = backend
    state.update(status=status, body={"private_note": "Do not expose", "token": TEST_TOKEN})
    result = tools.DeliveryClient(config).call("delivery_status", {"job_id": "job"})
    assert result["error"]["code"] == code
    assert result["retry_advice"] == advice
    assert "Do not expose" not in json.dumps(result)
    assert TEST_TOKEN not in json.dumps(result)
    assert len(state["calls"]) == 1


@pytest.mark.parametrize("body,content_type,code", [(b"not-json", "application/json", "backend_protocol"), ({"data": []}, "application/json", "backend_protocol"), ({"data": {"token": TEST_TOKEN}}, "application/json", "unsafe_response"), (b"x" * (tools.MAX_RESPONSE + 1), "application/json", "response_limit"), ({"data": {}}, "text/html", "backend_protocol")])
def test_upstream_shape_size_and_token_guards(backend, body, content_type, code):
    config, state = backend
    state.update(body=body, content_type=content_type)
    result = tools.DeliveryClient(config).call("delivery_status", {"job_id": "job"})
    assert result["error"]["code"] == code
    assert TEST_TOKEN not in json.dumps(result)


def test_stdio_protocol_framing_limits_and_recovery(backend):
    config, state = backend
    messages = [
        b"not JSON\n",
        b"x" * (tools.MAX_LINE + 200) + b"\n",
        b'{"jsonrpc":"2.0","id":9,"id":10,"method":"ping"}\n',
        json.dumps(frame("initialize", params={"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}})).encode() + b"\n",
        b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n',
        json.dumps(frame("tools/list", 2)).encode() + b"\n",
        json.dumps(frame("tools/call", 3, {"name": "delivery_status", "arguments": {"job_id": "job"}})).encode() + b"\n",
    ]
    output = io.BytesIO()
    tools.serve(config, io.BytesIO(b"".join(messages)), output)
    values = [json.loads(line) for line in output.getvalue().splitlines()]
    assert [value.get("error", {}).get("code") for value in values[:3]] == [-32700] * 3
    assert len(values) == 6  # Initialized notification produces no response.
    assert values[-1]["result"]["isError"] is False
    assert TEST_TOKEN.encode() not in output.getvalue()
    assert len(state["calls"]) == 1


def test_connection_failure_is_structured_and_never_requests_automatic_retry(monkeypatch):
    client = tools.DeliveryClient(tools.Config.from_env(environment()))

    def unavailable(*_, **__):
        raise tools.URLError("synthetic transport detail must remain private")

    monkeypatch.setattr(client.opener, "open", unavailable)
    result = client.call("delivery_status", {"job_id": "job"})
    assert result["error"]["code"] == "backend_unreachable"
    assert result["retry_advice"] == "operator_action"
    assert "synthetic transport detail" not in json.dumps(result)


def test_protocol_refuses_batches_boolean_ids_and_unknown_methods(backend):
    config, state = backend
    server = initialized_server(tools.DeliveryClient(config))
    for message in [[frame("ping")], frame("ping", True), frame("approve", 2)]:
        with pytest.raises(tools.RpcError):
            server.handle(message)
    assert server.handle({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "delivery_status", "arguments": {"job_id": "job"}}}) is None
    assert not state["calls"]


def test_real_subprocess_has_only_protocol_stdout_and_no_secret_stderr(backend):
    config, _ = backend
    messages = [frame("initialize", params={"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {}}), {"jsonrpc": "2.0", "method": "notifications/initialized"}, frame("tools/call", 2, {"name": "delivery_status", "arguments": {"job_id": "job"}})]
    result = subprocess.run([sys.executable, str(SCRIPT)], input="".join(json.dumps(message) + "\n" for message in messages), capture_output=True, text=True, env=environment(config.origin), timeout=5)
    assert result.returncode == 0
    values = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(values) == 2
    assert values[-1]["result"]["isError"] is False
    assert result.stderr == ""
    assert TEST_TOKEN not in result.stdout + result.stderr


def private_config(tmp_path, origin="http://127.0.0.1:8877", **changes):
    path = tmp_path / "private-tools.json"
    value = {"schema_version": 1, "origin": origin, "binding": "binding-test", "token": TEST_TOKEN, **changes}
    path.write_text(json.dumps(value))
    path.chmod(0o600)
    return path


def test_private_file_configuration_overrides_environment_and_hides_secret(backend, tmp_path):
    config, state = backend
    path = private_config(tmp_path, config.origin)
    assert tools.Config.from_private_file(str(path)) == config
    messages = [frame("initialize", params={"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {}}), {"jsonrpc": "2.0", "method": "notifications/initialized"}, frame("tools/call", 2, {"name": "delivery_status", "arguments": {"job_id": "job"}})]
    result = subprocess.run([sys.executable, str(SCRIPT), "--config-file", str(path)], input="".join(json.dumps(message) + "\n" for message in messages), capture_output=True, text=True, env=environment("http://127.0.0.1:1"), timeout=5)
    assert result.returncode == 0 and not result.stderr
    assert json.loads(result.stdout.splitlines()[-1])["result"]["isError"] is False
    assert len(state["calls"]) == 1
    assert TEST_TOKEN not in result.stdout


@pytest.mark.parametrize("change", [{"schema_version": 2}, {"schema_version": True}, {"origin": "https://untrusted.example:8877"}, {"origin": []}, {"binding": 13}, {"token": ["secret"]}, {"extra": "private"}])
def test_private_file_refuses_unsupported_and_invalid_values(tmp_path, change):
    path = private_config(tmp_path, **change)
    with pytest.raises(tools.ConfigurationError) as error:
        tools.Config.from_private_file(str(path))
    assert TEST_TOKEN not in str(error.value)
    assert "untrusted.example" not in str(error.value)


def test_private_file_requires_regular_owned_private_file(tmp_path):
    path = private_config(tmp_path)
    path.chmod(0o644)
    with pytest.raises(tools.ConfigurationError):
        tools.Config.from_private_file(str(path))
    path.chmod(0o600)
    link = tmp_path / "linked.json"
    link.symlink_to(path)
    with pytest.raises(tools.ConfigurationError):
        tools.Config.from_private_file(str(link))
    with pytest.raises(tools.ConfigurationError):
        tools.Config.from_private_file("relative.json")
    with pytest.raises(tools.ConfigurationError):
        tools.Config.from_private_file(str(tmp_path))


@pytest.mark.parametrize("raw", [b'{"token":"FIRST PRIVATE VALUE","token":"SECOND PRIVATE VALUE"}', b'x' * 16385, b'[]', b'not json', b'{"schema_version":NaN}'])
def test_bad_private_file_subprocess_has_redacted_error_and_no_stdout(tmp_path, raw):
    path = tmp_path / "broken.json"
    path.write_bytes(raw)
    path.chmod(0o600)
    result = subprocess.run([sys.executable, str(SCRIPT), "--config-file", str(path)], input="", text=True, capture_output=True, timeout=5)
    assert result.returncode == 2
    assert not result.stdout
    assert "PRIVATE VALUE" not in result.stderr
    assert "Traceback" not in result.stderr


def test_private_configuration_refuses_fifo_without_waiting(tmp_path):
    import os
    path = tmp_path / "not-a-file"
    os.mkfifo(path, 0o600)
    result = subprocess.run([sys.executable, str(SCRIPT), "--config-file", str(path)], input="", text=True, capture_output=True, timeout=3)
    assert result.returncode == 2 and not result.stdout


def run_command(path, name, raw, *options):
    return subprocess.run([sys.executable, str(SCRIPT), "--config-file", str(path), "--call-tool", name, *options], input=raw, capture_output=True, env=environment("http://127.0.0.1:1"), timeout=5)


@pytest.mark.parametrize("name,arguments,method,suffix", [
    ("delivery_status", {"job_id": "job-cli"}, "GET", "status"),
    ("delivery_check_preview", {"job_id": "job-cli", "requirement_id": "req-cli", "file_ids": ["file-cli"], "expected_revision": 3, "input_hash": "a" * 64}, "POST", "preview"),
])
def test_command_process_uses_private_config_and_scoped_client(backend, tmp_path, name, arguments, method, suffix):
    config, state = backend
    result = run_command(private_config(tmp_path, config.origin), name, json.dumps(arguments).encode())
    assert result.returncode == 0 and result.stderr == b""
    assert json.loads(result.stdout) == state["body"]["data"]
    assert len(state["calls"]) == 1
    request = state["calls"][0]
    assert request["method"] == method
    assert request["path"] == f"/api/v1/delivery/jobs/job-cli/{suffix}"
    assert request["headers"]["X-Delivery-Token"] == TEST_TOKEN
    assert request["headers"]["X-Delivery-Binding"] == config.binding
    if method == "POST":
        assert request["body"] == {key: value for key, value in arguments.items() if key != "job_id"}
    assert TEST_TOKEN.encode() not in result.stdout + result.stderr


@pytest.mark.parametrize("raw", [
    b"not-json private-input-marker", b"", b"[]", b'{"job_id":"a","job_id":"b"}',
    b'{"job_id":NaN}', b'{"job_id":"https://private.example/path"}',
    b'{"job_id":"job","url":"https://private.example/path"}',
    b'{"job_id":"job"} {"job_id":"another"}', b'\xff',
])
def test_command_process_invalid_json_and_arguments_never_reach_network(backend, tmp_path, raw):
    config, state = backend
    result = run_command(private_config(tmp_path, config.origin), "delivery_status", raw)
    assert result.returncode == 2 and result.stderr == b""
    assert json.loads(result.stdout)["error"]["code"] == "invalid_arguments"
    assert not state["calls"]
    assert b"private-input-marker" not in result.stdout
    assert b"private.example" not in result.stdout
    assert TEST_TOKEN.encode() not in result.stdout


def test_command_process_rejects_overbudget_before_network(backend, tmp_path):
    config, state = backend
    raw = b'{"job_id":"job"}' + b" " * tools.MAX_LINE
    result = run_command(private_config(tmp_path, config.origin), "delivery_status", raw)
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"]["code"] == "input_limit"
    assert not state["calls"]


@pytest.mark.parametrize("name,options", [("https://private.example/tool", ()), ("delivery_status", ("--url", "https://private.example/path")), ("delivery_status", ("--call", "private-input-marker"))])
def test_command_process_unknown_options_are_redacted_before_network(backend, tmp_path, name, options):
    config, state = backend
    result = run_command(private_config(tmp_path, config.origin), name, b'{"job_id":"job"}', *options)
    assert result.returncode == 2 and not result.stdout
    assert b"Invalid command options" in result.stderr
    assert b"private.example" not in result.stderr
    assert b"private-input-marker" not in result.stderr
    assert not state["calls"]


def test_command_process_configuration_failure_is_safe_and_nonzero(backend, tmp_path):
    _, state = backend
    path = private_config(tmp_path, "https://private.example:8877")
    result = run_command(path, "delivery_status", b'{"job_id":"job"}')
    assert result.returncode == 2 and result.stderr == b""
    assert json.loads(result.stdout)["error"]["code"] == "configuration_error"
    assert b"private.example" not in result.stdout
    assert TEST_TOKEN.encode() not in result.stdout
    assert not state["calls"]


def test_command_process_remote_error_is_redacted_and_nonzero(backend, tmp_path):
    config, state = backend
    state.update(status=503, body={"private": "private-input-marker", "token": TEST_TOKEN, "url": "https://private.example/path"})
    result = run_command(private_config(tmp_path, config.origin), "delivery_status", b'{"job_id":"job"}')
    assert result.returncode == 1 and result.stderr == b""
    assert json.loads(result.stdout)["error"]["code"] == "backend_unavailable"
    assert len(state["calls"]) == 1
    assert b"private-input-marker" not in result.stdout
    assert b"private.example" not in result.stdout
    assert TEST_TOKEN.encode() not in result.stdout


def test_command_process_transport_drop_is_structured_and_nonzero(tmp_path):
    with socket.socket() as service:
        service.bind(("127.0.0.1", 0))
        service.listen(1)
        service.settimeout(3)

        def disconnect():
            connection, _ = service.accept()
            with connection:
                connection.settimeout(3)
                connection.recv(4096)
                # Drop the actual request before sending an HTTP response.

        thread = threading.Thread(target=disconnect, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{service.getsockname()[1]}"
        result = run_command(private_config(tmp_path, origin), "delivery_status", b'{"job_id":"job"}')
        thread.join(timeout=3)
        assert not thread.is_alive()
    assert result.returncode == 1 and result.stderr == b""
    value = json.loads(result.stdout)
    assert value["error"]["code"] == "backend_unreachable"
    assert value["retry_advice"] == "operator_action"
    assert origin.encode() not in result.stdout
    assert TEST_TOKEN.encode() not in result.stdout


def test_command_input_reader_is_bounded(backend):
    config, state = backend

    class BoundedInput:
        def read(self, size):
            assert size == tools.MAX_LINE + 1
            return b"x" * size

    output = io.BytesIO()
    assert tools.call_once(config, "delivery_status", BoundedInput(), output) == 2
    assert json.loads(output.getvalue())["error"]["code"] == "input_limit"
    assert not state["calls"]
