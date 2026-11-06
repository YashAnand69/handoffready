#!/usr/bin/env python3
"""Narrow delivery MCP stdio adapter, protocol 2024-11-05 tools subset.

No SDK, HTTP MCP transport, sampling, resources, or approval tools. This is not
an isolation boundary against other processes running as the same OS user.
Configure origin/binding/token in the environment or an owner-private JSON
file. Command-line arguments may name the file, never contain the secrets.
With --call-tool, read one bounded JSON argument object and exit with 0 for
success, 1 for a service failure, or 2 for invalid input/configuration.
Protocol reference: https://modelcontextprotocol.io/specification/2024-11-05
"""

import argparse
import base64
import json
import hashlib
import os
import re
import selectors
import time
import stat
import sys
from dataclasses import dataclass, field
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

PROTOCOL = "2024-11-05"
MAX_LINE = 64 * 1024
MAX_RESPONSE = 128 * 1024
HTTP_TIMEOUT = 10
INPUT_TIMEOUT = 10
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
ID_SCHEMA = {"type": "string", "minLength": 1, "maxLength": 100, "pattern": "^[A-Za-z0-9_-]+$"}
TOOLS = [
    {
        "name": "delivery_status",
        "description": "Read the configured delivery job's safe status. This cannot approve, share, or change a review.",
        "inputSchema": {"type": "object", "properties": {"job_id": ID_SCHEMA}, "required": ["job_id"], "additionalProperties": False},
    },
    {
        "name": "delivery_check_preview",
        "description": "Preview narrow checks of a proposed file selection at an exact revision/hash. This saves no human assessment or approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": ID_SCHEMA,
                "requirement_id": ID_SCHEMA,
                "file_ids": {"type": "array", "items": ID_SCHEMA, "maxItems": 30, "uniqueItems": True},
                "expected_revision": {"type": "integer", "minimum": 1, "maximum": 2**53 - 1},
                "input_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            },
            "required": ["job_id", "requirement_id", "file_ids", "expected_revision", "input_hash"],
            "additionalProperties": False,
        },
    },
]


STAGE_TOOL = {
    "name": "delivery_stage_receipt",
    "description": "Receive one file from the configured attachment folder. This does not commit a packet, approve, assess or share anything. Source provenance is unverified until the local reviewer confirms it.",
    "inputSchema": {"type": "object", "properties": {"job_id": ID_SCHEMA,
        "operation_key": {"type": "string", "minLength": 1, "maxLength": 128},
        "source_id": {"type": "string", "minLength": 1, "maxLength": 256},
        "filename": {"type": "string", "minLength": 1, "maxLength": 200},
        "file_path": {"type": "string", "minLength": 1, "maxLength": 4096}},
        "required": ["job_id", "operation_key", "source_id", "filename", "file_path"], "additionalProperties": False},
}
CONTEXT_TOOLS = [
    {
        "name": "delivery_propose_question",
        "description": "Propose unverified contextual clarification with provisional backend checks at exact revision, input hash and context epoch. Saves no assessment, scope decision, approval or share authorization. Preserve the operation key and exact arguments when retrying an unknown outcome.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": ID_SCHEMA,
                "operation_key": {"type": "string", "minLength": 1, "maxLength": 128},
                "expected_revision": {"type": "integer", "minimum": 1, "maximum": 2**53 - 1},
                "input_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "expected_context_epoch": {"type": "integer", "minimum": 0, "maximum": 2**53 - 1},
                "requirement_id": ID_SCHEMA,
                "file_ids": {"type": "array", "items": ID_SCHEMA, "maxItems": 30, "uniqueItems": True},
                "question": {"type": "string", "minLength": 1, "maxLength": 1000},
                "source_ref": {"type": "string", "minLength": 1, "maxLength": 256},
            },
            "required": ["job_id", "operation_key", "expected_revision", "input_hash", "expected_context_epoch", "requirement_id", "file_ids", "question", "source_ref"],
            "additionalProperties": False,
        },
    },
    {
        "name": "delivery_record_reply",
        "description": "Record an explicitly unverified reply against a question's immutable original input hash. Historical replies cannot apply automatically. Saves no local resolution or approval. Preserve the operation key and exact arguments when retrying an unknown outcome.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": ID_SCHEMA,
                "question_id": ID_SCHEMA,
                "operation_key": {"type": "string", "minLength": 1, "maxLength": 128},
                "question_input_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "source_ref": {"type": "string", "minLength": 1, "maxLength": 256},
                "reported_speaker": {"type": "string", "minLength": 1, "maxLength": 120},
                "text": {"type": "string", "minLength": 1, "maxLength": 2000},
            },
            "required": ["job_id", "question_id", "operation_key", "question_input_hash", "source_ref", "reported_speaker", "text"],
            "additionalProperties": False,
        },
    },
]
SHARE_BYTES = 5 * 1024 * 1024
SHARE_TOOL = {
    "name": "delivery_take_share",
    "description": "Prepare an already locally authorized frozen Markdown record, then consume a one-use send permission. Send only when send_permitted is true, using the exact returned Switch arguments ONCE. Never retry an ambiguous external send; reconcile in the local desk. This cannot authorize, approve or verify delivery.",
    "inputSchema": {"type": "object", "properties": {"job_id": ID_SCHEMA,"intent_id": ID_SCHEMA,
        "operation_key": {"type":"string","minLength":1,"maxLength":128}},
        "required":["job_id","intent_id","operation_key"],"additionalProperties":False},
}
FILE_BYTES = 10 * 1024 * 1024


def open_attachment_root(root):
    """Walk an absolute folder without following any path-component symlink."""
    path = Path(root)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError()
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor); descriptor = child
        if os.fstat(descriptor).st_uid != os.getuid():
            raise ValueError()
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


class ConfigurationError(ValueError):
    pass


class RpcError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


@dataclass(frozen=True)
class Config:
    origin: str
    binding: str
    token: str = field(repr=False)
    attachment_root: str | None = None
    schema_version: int = 1
    outgoing_root: str | None = None

    @classmethod
    def from_private_file(cls, filename):
        try:
            path = Path(filename).expanduser()
            if not path.is_absolute():
                raise ValueError()
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, "rb") as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or not 1 <= info.st_size <= 16384:
                    raise ValueError()
                raw = source.read(16385)
            if len(raw) > 16384:
                raise ValueError()
            value = strict_json(raw)
            if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value["schema_version"] not in {1, 2, 3, 4}:
                raise ValueError()
            expected = {"schema_version", "origin", "binding", "token"} | ({"attachment_root"} if value["schema_version"] in {2, 3, 4} else set())
            if value["schema_version"] == 4:expected.add("outgoing_root")
            if set(value) != expected:
                raise ValueError()
            root = value.get("attachment_root")
            if value["schema_version"] in {2, 3, 4}:
                if not isinstance(root, str) or not 1 <= len(root) <= 4096:
                    raise ValueError()
                descriptor = open_attachment_root(root)
                os.close(descriptor)
            if any(not isinstance(value[key], str) for key in ("origin", "binding", "token")):
                raise ValueError()
            config = cls.from_env({"HANDOFFREADY_DELIVERY_ORIGIN": value["origin"], "HANDOFFREADY_DELIVERY_BINDING": value["binding"], "HANDOFFREADY_DELIVERY_TOKEN": value["token"]})
            outgoing = value.get("outgoing_root")
            if value["schema_version"] == 4:
                if not isinstance(outgoing,str) or not 1 <= len(outgoing) <= 4096:raise ValueError()
                descriptor=open_attachment_root(outgoing)
                try:
                    if os.fstat(descriptor).st_mode & 0o077:raise ValueError()
                finally:os.close(descriptor)
            return cls(config.origin, config.binding, config.token, root, value["schema_version"], outgoing)
        except (OSError, ValueError, TypeError, RecursionError):
            raise ConfigurationError("Use a valid owner-private tool configuration file at an absolute path (permissions 600).") from None

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        origin = env.get("HANDOFFREADY_DELIVERY_ORIGIN", "")
        try:
            parts = urlsplit(origin)
            valid = (
                parts.scheme == "http"
                and parts.hostname in {"127.0.0.1", "localhost", "::1"}
                and parts.port is not None and 1024 <= parts.port <= 65535
                and parts.username is None and parts.password is None
                and parts.path in {"", "/"} and not parts.query and not parts.fragment
                and not any(character.isspace() for character in origin)
                and "\\" not in origin
            )
        except ValueError:
            valid = False
        binding = env.get("HANDOFFREADY_DELIVERY_BINDING", "")
        token = env.get("HANDOFFREADY_DELIVERY_TOKEN", "")
        if not valid or not IDENTIFIER.fullmatch(binding):
            raise ConfigurationError("Configure a loopback HTTP origin with an explicit unprivileged port and a valid delivery binding.")
        if not isinstance(token, str) or not 16 <= len(token) <= 4096 or any(not 33 <= ord(character) <= 126 for character in token):
            raise ConfigurationError("Configure a valid delivery-scoped token in the environment.")
        return cls(origin.rstrip("/"), binding, token)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def failure(code, message, retry_advice="none", **extra):
    return {"error": {"code": code, "message": message}, "retry_advice": retry_advice, **extra}


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("Duplicate JSON key")
            value[key] = item
        return value

    def constant(_):
        raise ValueError("Non-finite JSON value")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


class DeliveryClient:
    def __init__(self, config):
        self.config = config
        # Local requests must not use environment proxies or follow redirects.
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, job_id, preview=None, *, suffix=None, response_limit=MAX_RESPONSE):
        suffix = suffix or ("status" if preview is None else "preview")
        body = None if preview is None else json.dumps(preview, allow_nan=False).encode()
        request = Request(
            f"{self.config.origin}/api/v1/delivery/jobs/{job_id}/{suffix}",
            data=body,
            headers={
                "X-Delivery-Token": self.config.token,
                "X-Delivery-Binding": self.config.binding,
                "Origin": self.config.origin,
                "Accept": "application/json",
                **({"Content-Type": "application/json"} if body is not None else {}),
            },
            method="GET" if body is None else "POST",
        )
        try:
            with self.opener.open(request, timeout=HTTP_TIMEOUT) as response:
                raw = response.read(response_limit + 1)
                if len(raw) > response_limit:
                    return failure("response_limit", "The local response exceeded the tool budget.", "operator_action")
                if response.headers.get_content_type() != "application/json":
                    return failure("backend_protocol", "The local service returned an unexpected response type.", "operator_action")
                value = strict_json(raw)
                if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
                    return failure("backend_protocol", "The local service returned an invalid result envelope.", "operator_action")
                encoded = json.dumps(value["data"], allow_nan=False)
                if self.config.token in encoded:
                    return failure("unsafe_response", "The local result could not be safely returned.", "operator_action")
                return value["data"]
        except HTTPError as error:
            # Never echo an arbitrary upstream body, URL, headers, or credentials.
            retry = "refresh" if error.code in {409, 412, 428} else "operator_action" if error.code in {401, 403, 500, 502, 503, 504} else "correct_input"
            code = "revision_conflict" if retry == "refresh" else "access_refused" if error.code in {401, 403} else "backend_unavailable" if error.code >= 500 else "request_rejected"
            error.close()
            return failure(code, "The local delivery service refused this operation. Follow the retry advice; preserve the operation key and exact arguments for an unknown outcome.", retry, http_status=error.code)
        except (URLError, TimeoutError, OSError, HTTPException):
            return failure("backend_unreachable", "The local delivery service could not be reached. Check its running status; preserve the operation key and exact arguments before retrying an unknown outcome.", "operator_action")
        except (ValueError, UnicodeError, RecursionError):
            return failure("backend_protocol", "The local service returned invalid JSON.", "operator_action")

    def call(self, name, arguments):
        if name == "delivery_take_share":return self.take_share(arguments)
        if name in {tool["name"] for tool in CONTEXT_TOOLS}:
            return self.context_call(name, arguments)
        if name == "delivery_stage_receipt":
            return self.stage(arguments)
        if name not in {tool["name"] for tool in TOOLS}:
            raise RpcError(-32602, "Unknown tool")
        expected = {"job_id"} if name == "delivery_status" else {"job_id", "requirement_id", "file_ids", "expected_revision", "input_hash"}
        if not isinstance(arguments, dict) or set(arguments) != expected:
            raise RpcError(-32602, "Invalid tool arguments")
        if not isinstance(arguments["job_id"], str) or not IDENTIFIER.fullmatch(arguments["job_id"]):
            raise RpcError(-32602, "Invalid job ID")
        if name == "delivery_status":
            return self.safe_status(self.request(arguments["job_id"]))
        requirement, files = arguments["requirement_id"], arguments["file_ids"]
        revision, fingerprint = arguments["expected_revision"], arguments["input_hash"]
        if (
            not isinstance(requirement, str) or not IDENTIFIER.fullmatch(requirement)
            or not isinstance(files, list) or len(files) > 30
            or any(not isinstance(item, str) or not IDENTIFIER.fullmatch(item) for item in files)
            or len(set(files)) != len(files)
            or type(revision) is not int or not 1 <= revision <= 2**53 - 1
            or not isinstance(fingerprint, str) or not HASH.fullmatch(fingerprint)
        ):
            raise RpcError(-32602, "Invalid preview selection or currency")
        return self.request(arguments["job_id"], {key: arguments[key] for key in expected - {"job_id"}})


    @property
    def tools(self):
        return TOOLS + ([STAGE_TOOL] if self.config.attachment_root is not None else []) + (CONTEXT_TOOLS if self.config.schema_version in {3,4} else []) + ([SHARE_TOOL] if self.config.schema_version == 4 else [])

    @staticmethod
    def safe_status(result):
        # Context text is local-only even if a backend accidentally expands its
        # projection. Preserve the foundation status and compact question IDs.
        result = dict(result)
        for key in ("replies", "resolutions", "latest_resolution", "delivery_context_basis", "active_context"):
            result.pop(key, None)
        if "questions" in result:
            if not isinstance(result["questions"], list) or any(not isinstance(q, dict) for q in result["questions"]):
                return failure("backend_protocol", "The local service returned invalid context status.", "operator_action")
            allowed = {"question_id", "requirement_id", "state", "input_hash", "source_revision"}
            result["questions"] = [{k: q[k] for k in allowed if k in q} for q in result["questions"]]
        return result

    def context_call(self, name, arguments):
        if self.config.schema_version not in {3,4}:
            raise RpcError(-32602, "Context tools require an explicit version-3 private configuration")
        tool = next(tool for tool in CONTEXT_TOOLS if tool["name"] == name)
        expected = set(tool["inputSchema"]["required"])
        if not isinstance(arguments, dict) or set(arguments) != expected:
            raise RpcError(-32602, "Invalid context arguments")
        for key in ("job_id", "question_id", "requirement_id"):
            if key in arguments and (not isinstance(arguments[key], str) or not IDENTIFIER.fullmatch(arguments[key])):
                raise RpcError(-32602, "Invalid context identity")
        bounds = {"operation_key": 128, "question": 1000, "source_ref": 256, "reported_speaker": 120, "text": 2000}
        for key, maximum in bounds.items():
            if key not in arguments:
                continue
            value = arguments[key]
            if (not isinstance(value, str) or not value.strip() or len(value) > maximum
                    or any(not char.isprintable() and not (key == "text" and char in "\n\t") for char in value)):
                raise RpcError(-32602, "Invalid bounded context text")
        hash_key = "input_hash" if name == "delivery_propose_question" else "question_input_hash"
        if not isinstance(arguments[hash_key], str) or not HASH.fullmatch(arguments[hash_key]):
            raise RpcError(-32602, "Invalid context input hash")
        if name == "delivery_propose_question":
            revision, epoch, files = arguments["expected_revision"], arguments["expected_context_epoch"], arguments["file_ids"]
            if (type(revision) is not int or not 1 <= revision <= 2**53 - 1
                    or type(epoch) is not int or not 0 <= epoch <= 2**53 - 1
                    or not isinstance(files, list) or len(files) > 30
                    or any(not isinstance(item, str) or not IDENTIFIER.fullmatch(item) for item in files)
                    or len(set(files)) != len(files)):
                raise RpcError(-32602, "Invalid context selection or currency")
            suffix = "questions"
        else:
            suffix = f"questions/{arguments['question_id']}/replies"
        # The caller owns this immutable key and payload. Never generate a new
        # operation key, silently alter currency, or automatically retry writes.
        body = {key: value for key, value in arguments.items() if key not in {"job_id", "question_id"}}
        return self.request(arguments["job_id"], body, suffix=suffix)

    def take_share(self, arguments):
        if self.config.schema_version != 4 or self.config.outgoing_root is None:
            raise RpcError(-32602,"Record return requires an explicit version-4 configuration")
        if not isinstance(arguments,dict) or set(arguments)!={"job_id","intent_id","operation_key"}:
            raise RpcError(-32602,"Invalid return arguments")
        if any(not isinstance(arguments[k],str) or IDENTIFIER.fullmatch(arguments[k]) is None for k in ("job_id","intent_id")):
            raise RpcError(-32602,"Invalid return identity")
        key=arguments["operation_key"]
        if not isinstance(key,str) or not key.strip() or len(key)>128 or any(not c.isprintable() for c in key):raise RpcError(-32602,"Invalid operation key")
        job,intent=arguments["job_id"],arguments["intent_id"]
        material=self.request(job,suffix=f"shares/{intent}/material",response_limit=4*((SHARE_BYTES+2)//3)+8192)
        if "error" in material:return {**material,"send_permitted":False}
        try:
            if set(material)!={"intent_id","filename","artifact_sha256","artifact_size","content_base64"} or material["intent_id"]!=intent:raise ValueError()
            filename=material["filename"];sha=material["artifact_sha256"]
            if not isinstance(filename,str) or re.fullmatch(r"handoff-[a-f0-9]{32}\.md",filename) is None:raise ValueError()
            if not isinstance(sha,str) or HASH.fullmatch(sha) is None or type(material["artifact_size"])is not int or not 1<=material["artifact_size"]<=SHARE_BYTES:raise ValueError()
            raw=base64.b64decode(material["content_base64"],validate=True)
            if len(raw)!=material["artifact_size"] or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError()
        except (ValueError,TypeError,KeyError):return failure("share_artifact_refused","The authorized record identity could not be verified.","operator_action",send_permitted=False)
        rootfd=None;created=False
        try:
            rootfd=open_attachment_root(self.config.outgoing_root)
            if os.fstat(rootfd).st_mode & 0o077:raise ValueError()
            try:fd=os.open(filename,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=rootfd);created=True
            except FileExistsError:
                fd=os.open(filename,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=rootfd)
                with os.fdopen(fd,"rb") as existing:
                    info=os.fstat(existing.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode & 0o077 or info.st_size!=len(raw) or existing.read(SHARE_BYTES+1)!=raw:raise ValueError()
            else:
                with os.fdopen(fd,"wb") as target:target.write(raw);target.flush();os.fsync(target.fileno())
        except (OSError,ValueError):
            if created and rootfd is not None:os.unlink(filename,dir_fd=rootfd)
            return failure("share_output_refused","Prepare a safe owner-private outgoing folder before issuing a return.","operator_action",send_permitted=False)
        finally:
            if rootfd is not None:os.close(rootfd)
        # Material preparation alone authorizes no external effect. A lost issue
        # reply is unverified; this command never calls Switch or retries it.
        result=self.request(job,{"operation_key":key,"artifact_sha256":sha},suffix=f"shares/{intent}/issue")
        if "error" in result:return {**result,"send_permitted":False}
        outcome=result.get("result",{})
        if outcome.get("send_permitted") is not True:return result
        send=outcome.get("switch_send_arguments")
        if (outcome.get("intent_id")!=intent or outcome.get("artifact_sha256")!=sha or not isinstance(send,dict)
                or set(send)!={"room_id","caption"} or not isinstance(send["room_id"],str) or not send["room_id"]
                or not isinstance(send["caption"],str) or len(send["caption"])>1000 or "@" in send["caption"]):
            return failure("share_issue_unknown","The issue result could not be safely interpreted. Do not send; reconcile locally.","reconcile",send_permitted=False)
        return {**result,"result":{**outcome,"switch_send_arguments":{**send,"path":str(Path(self.config.outgoing_root)/filename)}}}

    def stage(self, arguments):
        if self.config.attachment_root is None:
            raise RpcError(-32602, "Attachment intake is not configured")
        expected = {"job_id", "operation_key", "source_id", "filename", "file_path"}
        if not isinstance(arguments, dict) or set(arguments) != expected:
            raise RpcError(-32602, "Invalid staging arguments")
        bounds = {"job_id": 100, "operation_key": 128, "source_id": 256, "filename": 200, "file_path": 4096}
        if any(not isinstance(arguments[key], str) or not arguments[key].strip() or len(arguments[key]) > maximum
               or any(ord(char) < 32 for char in arguments[key]) for key, maximum in bounds.items()):
            raise RpcError(-32602, "Invalid staging arguments")
        name = arguments["filename"]
        if not IDENTIFIER.fullmatch(arguments["job_id"]) or name in {".", ".."} or "/" in name or "\\" in name:
            raise RpcError(-32602, "Invalid staging arguments")
        descriptor = None
        try:
            root = Path(self.config.attachment_root)
            path = Path(arguments["file_path"])
            if not path.is_absolute() or ".." in path.parts:
                raise ValueError()
            relative = path.relative_to(root)
            if not relative.parts:
                raise ValueError()
            descriptor = open_attachment_root(root)
            for part in relative.parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
                os.close(descriptor); descriptor = child
            file = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
            with os.fdopen(file, "rb") as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or not 1 <= info.st_size <= FILE_BYTES:
                    raise ValueError()
                content = source.read(FILE_BYTES + 1)
                after = os.fstat(source.fileno())
                if len(content) != info.st_size or len(content) > FILE_BYTES or (after.st_size, after.st_mtime_ns) != (info.st_size, info.st_mtime_ns):
                    raise ValueError()
        except (OSError, ValueError):
            return failure("attachment_refused", "Choose an unchanged, bounded regular file inside the configured attachment folder, without links.", "operator_action")
        finally:
            if descriptor is not None:
                os.close(descriptor)
        body = {key: arguments[key] for key in ("operation_key", "source_id", "filename")}
        body["content_base64"] = base64.b64encode(content).decode("ascii")
        return self.request(arguments["job_id"], body, suffix="receipts")


class Server:
    def __init__(self, client):
        self.client = client
        self.initialized = False
        self.ready = False

    def handle(self, message):
        if not isinstance(message, dict):
            raise RpcError(-32600, "Invalid request")
        identifier = message.get("id")
        has_id = "id" in message
        if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            raise RpcError(-32600, "Invalid request")
        if has_id and (type(identifier) not in {str, int} or (isinstance(identifier, str) and len(identifier) > 200)):
            raise RpcError(-32600, "Invalid request ID")
        method, params = message["method"], message.get("params", {})
        if not isinstance(params, dict):
            raise RpcError(-32602, "Invalid parameters")
        if not has_id:
            if method == "notifications/initialized" and self.initialized:
                self.ready = True
            return None
        if method == "ping":
            return {}
        if method == "initialize":
            if self.initialized:
                raise RpcError(-32600, "Already initialized")
            if not isinstance(params.get("protocolVersion"), str) or not isinstance(params.get("capabilities"), dict) or not isinstance(params.get("clientInfo"), dict):
                raise RpcError(-32602, "Invalid initialization")
            self.initialized = True
            return {"protocolVersion": PROTOCOL, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "handoffready-delivery-readonly", "version": "0.1.0"}}
        if not self.ready:
            raise RpcError(-32002, "Initialize the tool server first")
        if method == "tools/list":
            if set(params) - {"_meta", "cursor"}:
                raise RpcError(-32602, "Unsupported list parameters")
            if params.get("cursor") not in (None, ""):
                raise RpcError(-32602, "Unknown pagination cursor")
            return {"tools": self.client.tools}
        if method == "tools/call":
            if set(params) - {"name", "arguments", "_meta"} or not isinstance(params.get("name"), str):
                raise RpcError(-32602, "Invalid tool call")
            result = self.client.call(params["name"], params.get("arguments", {}))
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, allow_nan=False)}], "isError": "error" in result}
        raise RpcError(-32601, "Method not found")


def serve(config, source, output):
    server = Server(DeliveryClient(config))
    while raw := source.readline(MAX_LINE + 1):
        identifier, notification = None, False
        try:
            if len(raw) > MAX_LINE:
                while raw and not raw.endswith(b"\n"):
                    raw = source.readline(MAX_LINE + 1)
                raise RpcError(-32700, "Message exceeds the input budget")
            try:
                message = strict_json(raw)
            except (ValueError, UnicodeError, RecursionError):
                raise RpcError(-32700, "Invalid JSON") from None
            if isinstance(message, dict):
                candidate = message.get("id")
                identifier = candidate if type(candidate) is int or (isinstance(candidate, str) and len(candidate) <= 200) else None
                notification = "id" not in message and isinstance(message.get("method"), str) and message.get("jsonrpc") == "2.0"
            result = server.handle(message)
            if notification:
                continue
            response = {"jsonrpc": "2.0", "id": identifier, "result": result}
        except RpcError as error:
            if notification:
                continue
            response = {"jsonrpc": "2.0", "id": identifier, "error": {"code": error.code, "message": error.message}}
        output.write(json.dumps(response, ensure_ascii=True, allow_nan=False).encode() + b"\n")
        output.flush()


def read_command_input(source):
    """Bound both bytes and waiting time on actual CLI pipes."""
    try:
        descriptor = source.fileno()
    except (AttributeError, OSError):
        return source.read(MAX_LINE + 1)
    # Regular-file stdin does not need select (kqueue may reject it).
    if stat.S_ISREG(os.fstat(descriptor).st_mode):
        return source.read(MAX_LINE + 1)
    chunks, size = [], 0
    deadline = time.monotonic() + INPUT_TIMEOUT
    with selectors.DefaultSelector() as selector:
        selector.register(descriptor, selectors.EVENT_READ)
        while size <= MAX_LINE:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not selector.select(timeout=remaining):
                raise TimeoutError()
            chunk = os.read(descriptor, min(65536, MAX_LINE + 1 - size))
            if not chunk:
                break
            chunks.append(chunk); size += len(chunk)
    return b"".join(chunks)


def call_once(config, name, source, output):
    """Run one bounded command-tool request using the same scoped client."""
    try:
        raw = read_command_input(source)
    except TimeoutError:
        output.write(json.dumps(failure("input_timeout", "Close the JSON input stream after sending the arguments, then retry the same operation.", "correct_input")).encode() + b"\n")
        output.flush()
        return 2
    if len(raw) > MAX_LINE:
        result = failure("input_limit", "The tool input exceeded the input budget.", "correct_input")
        status = 2
    else:
        try:
            arguments = strict_json(raw)
            result = DeliveryClient(config).call(name, arguments)
            status = 1 if "error" in result else 0
        except (ValueError, UnicodeError, RecursionError):
            result = failure("invalid_arguments", "Provide one valid JSON object within the input budget.", "correct_input")
            status = 2
        except RpcError as error:
            result = failure("invalid_arguments", error.message, "correct_input")
            status = 2
    output.write(json.dumps(result, ensure_ascii=True, allow_nan=False).encode() + b"\n")
    output.flush()
    return status


class CommandParser(argparse.ArgumentParser):
    def error(self, _):
        # Invalid options may contain credentials or arbitrary user text.
        self.exit(2, "Invalid command options. Use --help for supported options.\n")


def main(argv=None):
    parser = CommandParser(description="Restricted delivery tools over MCP stdio or one bounded JSON command.", allow_abbrev=False)
    parser.add_argument("--config-file", help="Absolute path to an owner-private JSON configuration (version 1 read/check, 2 intake, 3 context, 4 supervised return); overrides environment configuration")
    parser.add_argument("--call-tool", choices=[tool["name"] for tool in TOOLS + [STAGE_TOOL] + CONTEXT_TOOLS + [SHARE_TOOL]], help="Run one named tool with a JSON arguments object from standard input, then exit")
    args = parser.parse_args(argv)
    try:
        config = Config.from_private_file(args.config_file) if args.config_file else Config.from_env()
    except ConfigurationError as error:
        if args.call_tool:
            print(json.dumps(failure("configuration_error", str(error), "operator_action"), ensure_ascii=True, allow_nan=False))
            return 2
        print(str(error), file=sys.stderr)
        return 2
    try:
        if args.call_tool:
            return call_once(config, args.call_tool, sys.stdin.buffer, sys.stdout.buffer)
        serve(config, sys.stdin.buffer, sys.stdout.buffer)
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
