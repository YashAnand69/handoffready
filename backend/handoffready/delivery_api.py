"""Explicitly enabled, conversation-scoped delivery reads.

The local operator creates the binding. Agent credentials cannot select another
conversation, change scope, save human assessments, or authorize sharing.
"""

import base64
import binascii
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass, field
from pathlib import Path

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .checks import evaluate_selection
from .delivery import DeliveryBinding, DeliveryService
from .policy import LIMITS
from .schemas import Payload, SelectionPreviewInput
from .store import StoreError, digest, input_hash


IDENTIFIER = r"[A-Za-z0-9_-]{1,100}"
SCOPED_PATH = re.compile(rf"/api/v1/delivery/jobs/{IDENTIFIER}/(status|preview|receipts|questions(?:/{IDENTIFIER}/replies)?)\Z")

STAGE_CONTENT_CHARACTERS = 4 * ((LIMITS["file_bytes"] + 2) // 3)
STAGE_REQUEST_BYTES = STAGE_CONTENT_CHARACTERS + 8192
SHARE_AGENT_PATH = re.compile(rf"/api/v1/delivery/jobs/{IDENTIFIER}/shares/{IDENTIFIER}/(material|issue)\Z")
STAGE_PATH = re.compile(rf"/api/v1/delivery/jobs/{IDENTIFIER}/receipts\Z")


@dataclass(frozen=True)
class DeliveryConfig:
    binding_id: str
    binding: DeliveryBinding
    token: str = field(repr=False)
    destination: dict | None = None

    @classmethod
    def parse(cls, value):
        if not isinstance(value, dict) or set(value) - {"binding_id", "server", "room", "thread", "token", "destination"}:
            raise ValueError("Use an explicit delivery binding configuration.")
        binding_id, token = value.get("binding_id"), value.get("token")
        if not isinstance(binding_id, str) or re.fullmatch(IDENTIFIER, binding_id) is None:
            raise ValueError("Invalid delivery binding identifier.")
        if not isinstance(token, str) or not 16 <= len(token) <= 4096 or any(not 33 <= ord(c) <= 126 for c in token):
            raise ValueError("Invalid delivery credential.")
        from .delivery_share import validate_destination
        destination=validate_destination(value["destination"]) if "destination" in value else None
        return cls(binding_id, DeliveryBinding(value.get("server"), value.get("room"), value.get("thread")), token, destination)

    @classmethod
    def load_file(cls, filename):
        """Load only an explicit owner-private regular file; never echo its data."""
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
            def unique_pairs(items):
                result = {}
                for key, value in items:
                    if key in result:
                        raise ValueError()
                    result[key] = value
                return result
            value = json.loads(raw, object_pairs_hook=unique_pairs)
            cls.parse(value)
            return value
        except (OSError, ValueError, TypeError, StoreError, RecursionError):
            raise ValueError("Delivery configuration must be a valid owner-private JSON file at an absolute path (permissions 600).") from None

    def permits(self, request):
        match = SCOPED_PATH.fullmatch(request.url.path)
        permitted_method = match is not None and request.method == ("GET" if match[1] == "status" else "POST")
        share_match=SHARE_AGENT_PATH.fullmatch(request.url.path)
        permitted_method = permitted_method or (self.destination is not None and share_match is not None and request.method == ("GET" if share_match[1] == "material" else "POST"))
        return permitted_method and secrets.compare_digest(request.headers.get("x-delivery-token", "").encode(), self.token.encode()) and secrets.compare_digest(request.headers.get("x-delivery-binding", "").encode(), self.binding_id.encode())


class CreateDeliveryInput(Payload):
    project_id: str = Field(pattern=rf"^{IDENTIFIER}$")
    operation_key: str = Field(min_length=1, max_length=128)


class DeliveryPreviewInput(SelectionPreviewInput):
    requirement_id: str = Field(pattern=rf"^{IDENTIFIER}$")
    expected_revision: int = Field(strict=True, ge=1, le=2**53 - 1)


class DeliveryStageInput(Payload):
    operation_key: str = Field(min_length=1, max_length=128)
    source_id: str = Field(min_length=1, max_length=256)
    filename: str = Field(min_length=1, max_length=200)
    content_base64: str = Field(min_length=1, max_length=STAGE_CONTENT_CHARACTERS)


class PacketPreviewInput(Payload):
    receipt_ids: list[Annotated[str, Field(pattern=rf"^{IDENTIFIER}$")]] = Field(min_length=1, max_length=30)
    expected_revision: int = Field(strict=True, ge=1, le=2**53 - 1)
    input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def unique_receipts(self):
        if len(set(self.receipt_ids)) != len(self.receipt_ids):
            raise ValueError("Receipt identifiers must be unique.")
        return self


class PacketConfirmInput(PacketPreviewInput):
    operation_key: str = Field(min_length=1, max_length=128)
    manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_complete: bool

    @model_validator(mode="after")
    def complete_confirmation(self):
        if self.confirmed_complete is not True:
            raise ValueError("Explicit complete-packet confirmation is required.")
        return self


class ContextQuestionInput(Payload):
    operation_key: str = Field(min_length=1, max_length=128)
    expected_revision: int = Field(ge=1, le=2**53-1)
    input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_context_epoch: int = Field(ge=0, le=2**53-1)
    requirement_id: str = Field(pattern=rf"^{IDENTIFIER}$")
    file_ids: list[Annotated[str, Field(pattern=rf"^{IDENTIFIER}$")]] = Field(max_length=30)
    question: str = Field(min_length=1, max_length=1000)
    source_ref: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def unique_files(self):
        if len(set(self.file_ids)) != len(self.file_ids):
            raise ValueError("File identifiers must be unique.")
        return self


class ContextReplyInput(Payload):
    operation_key: str = Field(min_length=1, max_length=128)
    question_input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_ref: str = Field(min_length=1, max_length=256)
    reported_speaker: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=2000)


class ContextResolveInput(Payload):
    operation_key: str = Field(min_length=1, max_length=128)
    expected_revision: int = Field(ge=1, le=2**53-1)
    input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_context_epoch: int = Field(ge=0, le=2**53-1)
    action: Literal["accept", "dismiss", "withdraw"]
    covered_reply_ids: list[Annotated[str, Field(pattern=rf"^{IDENTIFIER}$")]] = Field(max_length=200)
    used_reply_ids: list[Annotated[str, Field(pattern=rf"^{IDENTIFIER}$")]] = Field(max_length=200)
    reason: str = Field(min_length=1, max_length=1000)
    confirmed_reviewed: bool

    @model_validator(mode="after")
    def reviewed_confirmation(self):
        if self.confirmed_reviewed is not True:
            raise ValueError("Explicit review of the current conversation context is required.")
        return self


def install_delivery_routes(app, config, response, inspect_file):
    store = app.state.store
    with store.connection() as db:
        persisted = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='delivery_schema'").fetchone() is not None
    service = DeliveryService(store) if config is not None or persisted else None
    app.state.delivery_service = service
    from .delivery_share_api import install_share_routes
    install_share_routes(app,service,config,response)

    @app.get("/api/v1/projects/{project_id}/delivery")
    def delivery_context(project_id: str):
        if service is None or config is None:
            return response({"enabled": False, "job": None})
        return response({"enabled": True, "job": service.context_for_project(project_id, config.binding)})

    @app.get("/api/v1/projects/{project_id}/delivery-context")
    def local_delivery_context(project_id: str):
        return response({"enabled": config is not None, "job": service.context.read_project(project_id) if service is not None else None})

    if service is None or config is None:
        return

    @app.post("/api/v1/delivery/jobs")
    def create_delivery(payload: CreateDeliveryInput):
        # General local-session authentication is enforced by API middleware.
        return response(service.create_job(config.binding, payload.project_id, payload.operation_key), 201)

    @app.get("/api/v1/delivery/jobs/{job_id}/status")
    def delivery_status(job_id: str):
        return response(service.status(job_id, config.binding))

    @app.post("/api/v1/delivery/jobs/{job_id}/preview")
    def delivery_preview(job_id: str, payload: DeliveryPreviewInput):
        with store.lock:
            job = service.get_job(job_id, config.binding)
            store.reconcile_originals(job["project_id"])
            project = store.get(job["project_id"])
            if payload.expected_revision != project["revision"] or payload.input_hash != input_hash(project):
                raise StoreError("stale_preview", "The packet changed. Refresh before previewing this selection.")
            if project["baseline"]["state"] != "approved":
                raise StoreError("baseline_not_approved", "The local reviewer must confirm the checklist first.")
            requirement = next((row for row in project["baseline"]["requirements"] if row["id"] == payload.requirement_id), None)
            if requirement is None:
                raise StoreError("requirement_not_found", "Requirement is not current.", 404)
            files = {row["id"]: row for row in project["files"]}
            if not set(payload.file_ids) <= files.keys():
                raise StoreError("invalid_files", "Choose registered files from this packet.", 422)
            ids = sorted(payload.file_ids)
            return response({"preview": True, "assessment_saved": False, "approval": "local_human_review_required", "job_id": job_id,
                             "requirement_id": payload.requirement_id, "source_revision": project["revision"], "input_hash": payload.input_hash,
                             "file_ids": ids, "selection_hash": digest(ids),
                             "checks": [{key: ("Human assessment is required in the local desk." if key == "reason" and check["kind"] == "manual" else value)
                                         for key, value in check.items() if key != "expected" or check["kind"] != "literal_text"}
                                        for check in evaluate_selection(requirement, [files[file_id] for file_id in ids])]})


    @app.post("/api/v1/delivery/jobs/{job_id}/receipts")
    def stage_delivery_receipt(job_id: str, payload: DeliveryStageInput):
        # Only staging is available to the scoped assistant. It cannot commit.
        try:
            content = base64.b64decode(payload.content_base64, validate=True)
        except (binascii.Error, ValueError):
            raise StoreError("delivery_invalid_base64", "Provide a valid encoded attachment within the file budget.", 422) from None
        if not content or len(content) > LIMITS["file_bytes"]:
            raise StoreError("delivery_file_limit", "The attachment is empty or exceeds its byte limit.", 413)
        return response(service.stage_receipt(job_id, config.binding, payload.operation_key,
                        source_id=payload.source_id, filename=payload.filename, content=content), 201)

    @app.get("/api/v1/delivery/jobs/{job_id}/receipts")
    def delivery_receipts(job_id: str):
        return response(service.list_receipts(job_id, config.binding))

    @app.post("/api/v1/delivery/jobs/{job_id}/packet-preview")
    def preview_delivery_packet(job_id: str, payload: PacketPreviewInput):
        return response(service.preview_packet(job_id, config.binding, receipt_ids=payload.receipt_ids,
                        expected_revision=payload.expected_revision, expected_hash=payload.input_hash))

    @app.post("/api/v1/delivery/jobs/{job_id}/packet-confirm")
    def confirm_delivery_packet(job_id: str, payload: PacketConfirmInput):
        return response(service.confirm_packet(job_id, config.binding, payload.operation_key,
                        receipt_ids=payload.receipt_ids, expected_revision=payload.expected_revision,
                        expected_hash=payload.input_hash, manifest_hash=payload.manifest_hash,
                        inspect_file=inspect_file))

    @app.post("/api/v1/delivery/jobs/{job_id}/questions")
    def propose_delivery_question(job_id: str, payload: ContextQuestionInput):
        return response(service.context.propose_question(job_id, config.binding, payload.operation_key,
                        expected_revision=payload.expected_revision, expected_hash=payload.input_hash,
                        expected_epoch=payload.expected_context_epoch, requirement_id=payload.requirement_id,
                        file_ids=payload.file_ids, question=payload.question, source_ref=payload.source_ref), 201)

    @app.post("/api/v1/delivery/jobs/{job_id}/questions/{question_id}/replies")
    def record_delivery_reply(job_id: str, question_id: str, payload: ContextReplyInput):
        return response(service.context.record_reply(job_id, config.binding, payload.operation_key,
                        question_id=question_id, question_input_hash=payload.question_input_hash,
                        source_ref=payload.source_ref, reported_speaker=payload.reported_speaker, text=payload.text), 201)

    @app.post("/api/v1/delivery/jobs/{job_id}/questions/{question_id}/resolve")
    def resolve_delivery_question(job_id: str, question_id: str, payload: ContextResolveInput):
        return response(service.context.resolve(job_id, config.binding, payload.operation_key,
                        question_id=question_id, expected_revision=payload.expected_revision, expected_hash=payload.input_hash,
                        expected_epoch=payload.expected_context_epoch, action=payload.action,
                        covered_reply_ids=payload.covered_reply_ids, used_reply_ids=payload.used_reply_ids, reason=payload.reason))
