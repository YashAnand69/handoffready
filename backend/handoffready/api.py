import asyncio
import hashlib
import json
import os
import secrets
import subprocess
import sys
import threading
import time
import tempfile
import unicodedata
from pathlib import Path

import psutil
from fastapi import FastAPI, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from .checks import evaluate
from .exports import projection, render
from .policy import LIMITS
from .schemas import (ApproveInput, BaselineInput, BriefInput, CreateProject, DecisionInput,
                      EmptyInput, ExportInput, RenameInput, Requirement)
from .store import Store, StoreError, canonical, digest, input_hash, invalidate, now, uid

PARSER_LOCK = threading.Lock()


def clean_name(value):
    value = str(value).replace("\\", "/").split("/")[-1]
    value = "".join(char for char in value if char.isprintable() and not unicodedata.category(char).startswith("C"))[:180].strip()
    return value or "Unnamed file"


def inspect_bounded(path, name, deadline):
    extension = Path(name).suffix.lower()
    budget = 20 if extension == ".pdf" else 5 if extension in {".png", ".jpg", ".jpeg"} else 3
    remaining = max(0, deadline - time.monotonic())
    if not PARSER_LOCK.acquire(timeout=remaining):
        return {"type": "unknown", "inspection": "blocked", "metadata": {}, "text": "", "error": "Inspection queue exceeded the batch time limit."}
    try:
        if time.monotonic() >= deadline:
            return {"type": "unknown", "inspection": "blocked", "metadata": {}, "text": "", "error": "Batch inspection time limit reached."}
        environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
        process = None
        reason = None
        try:
            with tempfile.TemporaryFile() as output_file:
                process = subprocess.Popen([sys.executable, "-m", "handoffready.parser_worker", str(path), name], stdout=output_file, stderr=subprocess.DEVNULL, env=environment)
                started = time.monotonic()
                while process.poll() is None:
                    if time.monotonic() - started > budget or time.monotonic() >= deadline:
                        reason = "File inspection exceeded its time limit."
                        break
                    try:
                        if psutil.Process(process.pid).memory_info().rss > 512 * 1024 * 1024:
                            reason = "File inspection exceeded its memory limit."
                            break
                    except psutil.NoSuchProcess:
                        break
                    time.sleep(0.05)
                if reason and process.poll() is None:
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
                process.wait(timeout=2)
                output_file.seek(0)
                output = output_file.read(512 * 1024 + 1)
        except (OSError, subprocess.SubprocessError, psutil.Error):
            reason = "File inspection worker could not complete safely."
            output = b""
        finally:
            if process is not None and process.poll() is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                process.wait(timeout=2)
        if reason:
            return {"type": "unknown", "inspection": "blocked", "metadata": {}, "text": "", "error": reason}
        try:
            result = json.loads(output)
            if not isinstance(result, dict) or len(result.get("text", "")) > 20000 or len(output) > 512 * 1024:
                raise ValueError()
            return result
        except (ValueError, TypeError):
            return {"type": "unknown", "inspection": "blocked", "metadata": {}, "text": "", "error": "Inspector returned invalid output."}
    finally:
        PARSER_LOCK.release()


def envelope(project):
    result = json.loads(canonical(project))
    result.pop("decision_history", None)
    result.pop("baseline_history", None)
    result.pop("proposal_history", None)
    for file in result["files"]:
        file.pop("_path", None)
    for job in result["jobs"]:
        job.pop("_snapshot", None)
        job.pop("_input", None)
        job.pop("_started", None)
    result["input_hash"] = input_hash(project)
    result["checks"] = result["check_results"] = evaluate(project)
    return result


def validate_requirements(requirements, brief):
    if len({r["id"] for r in requirements}) != len(requirements):
        raise StoreError("duplicate_requirement", "Requirement IDs must be unique.", 422)
    for requirement in requirements:
        if not requirement["title"].strip():
            raise StoreError("empty_title", "Requirement titles cannot be blank.", 422)
        if requirement["origin"] == "human_added":
            if not requirement["human_note"].strip() or requirement["quote"] is not None or requirement["source_id"] is not None:
                raise StoreError("manual_source", "Human additions require an explanatory note and no invented source quotation.", 422)
            requirement["source_span"] = None
        else:
            quote = requirement["quote"]
            if not brief or requirement["source_id"] != brief["id"] or not quote or brief["text"].count(quote) != 1:
                raise StoreError("invalid_source_quote", "Each model suggestion must quote one exact, unique passage from the current brief.", 422)
            start = brief["text"].index(quote)
            requirement["source_span"] = {"source_unit_id": brief["id"], "source_text_sha256": brief["sha256"], "start_cp": start, "end_cp": start + len(quote), "quote": quote}


def preserve_baseline(project, reason):
    history = project.setdefault("baseline_history", [])
    history.append({"recorded_at": now(), "reason": reason, "baseline": json.loads(canonical(project["baseline"])), "source": json.loads(canonical(project["brief"]))})
    project["baseline_history"] = history[-20:]


def preserve_proposals(project):
    if project["proposals"]:
        history = project.setdefault("proposal_history", [])
        history.append({"recorded_at": now(), "input_hash": input_hash(project), "proposals": json.loads(canonical(project["proposals"]))})
        project["proposal_history"] = history[-20:]


def create_app(data_dir=None, model_adapter=None, port=8877):
    directory = data_dir or os.environ.get("HANDOFFREADY_DATA", str(Path.home() / "Library/Application Support/HandoffReady"))
    store = Store(directory)
    app = FastAPI(title="HandoffReady local API", docs_url=None, redoc_url=None)
    app.state.store = store
    app.state.token = secrets.token_urlsafe(32)
    app.state.model_lock = threading.Lock()
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    allowed_origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}", "http://127.0.0.1:5174"}
    app.add_middleware(CORSMiddleware, allow_origins=list(allowed_origins), allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type", "X-Handoff-Token", "If-Match"])

    def response(data, status=200):
        return JSONResponse({"data": data, "meta": {"schema_version": "v1"}}, status_code=status)

    @app.exception_handler(StoreError)
    async def domain_error(request, error):
        return JSONResponse({"error": {"code": error.code, "message": error.message}}, status_code=error.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # Pydantic's raw errors can include uploaded/private input, so return field locations only.
        return JSONResponse({"error": {"code": "invalid_fields", "message": "Some fields are invalid.", "fields": [".".join(str(item) for item in e["loc"]) for e in error.errors()]}}, status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request, error):
        return JSONResponse({"error": {"code": "request_rejected", "message": "The request could not be accepted. Check its format and limits."}}, status_code=error.status_code)

    @app.middleware("http")
    async def security(request, call_next):
        if request.headers.get("host") not in allowed_hosts:
            return JSONResponse({"error": {"code": "host_rejected", "message": "Use the configured loopback address."}}, status_code=403)
        path = request.url.path
        if path.startswith("/api/"):
            if path != "/api/v1/bootstrap" and request.method != "OPTIONS":
                if not secrets.compare_digest(request.headers.get("x-handoff-token", "").encode("utf-8"), app.state.token.encode("utf-8")):
                    return JSONResponse({"error": {"code": "token_required", "message": "Reload the local app to establish a session."}}, status_code=403)
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                if request.headers.get("origin") not in allowed_origins:
                    return JSONResponse({"error": {"code": "origin_rejected", "message": "Mutation requires the local application origin."}}, status_code=403)
                try:
                    length = int(request.headers.get("content-length", "0"))
                except ValueError:
                    length = LIMITS["request_bytes"] + 1
                request_limit = LIMITS["request_bytes"] if request.headers.get("content-type", "").startswith("multipart/form-data") else 256 * 1024
                if length > request_limit:
                    return JSONResponse({"error": {"code": "request_limit", "message": "Request exceeds the upload budget."}}, status_code=413)
                received = 0
                receive = request._receive
                async def bounded_receive():
                    nonlocal received
                    message = await receive()
                    received += len(message.get("body", b""))
                    if received > request_limit:
                        request.state.body_limit_hit = True
                        raise StoreError("request_limit", "Request exceeds the upload budget.", 413)
                    return message
                request._receive = bounded_receive
            segments = path.split("/")
            if request.method != "OPTIONS" and len(segments) >= 5 and segments[3] == "projects" and segments[4]:
                try:
                    await asyncio.to_thread(store.reconcile_originals, segments[4])
                except StoreError as error:
                    return JSONResponse({"error": {"code": error.code, "message": error.message}}, status_code=error.status)
            result = await call_next(request)
            if getattr(request.state, "body_limit_hit", False):
                result = JSONResponse({"error": {"code": "request_limit", "message": "Request exceeds the upload budget."}}, status_code=413)
            result.headers["Cache-Control"] = "no-store"
            result.headers["X-Content-Type-Options"] = "nosniff"
            return result
        result = await call_next(request)
        result.headers["X-Content-Type-Options"] = "nosniff"
        result.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        return result

    def revision(request):
        value = request.headers.get("if-match")
        if value is None:
            raise StoreError("precondition_required", "Refresh and supply the current project revision.", 428)
        value = value.strip('"').removeprefix("project-r")
        if not 1 <= len(value) <= 20 or not value.isascii() or not value.isdigit():
            raise StoreError("invalid_revision", "Invalid project revision.", 422)
        return int(value)

    def adapter():
        if model_adapter is not None:
            return model_adapter
        from . import model
        return model

    @app.get("/api/v1/bootstrap")
    def bootstrap():
        return response({"token": app.state.token, "runtime": "local", "schema_version": "v1"})

    @app.get("/api/v1/capabilities")
    def capabilities():
        try:
            model = adapter().ready()
        except Exception:
            model = {"ready": False, "message": "Local model is unavailable."}
        return response({"limits": LIMITS, "supported_types": ["png", "jpeg", "svg", "pdf", "text", "markdown"], "model": model, "runtime": "local", "inspection_mode": "bounded_synchronous", "encrypted_at_rest": False})

    @app.get("/api/v1/projects")
    def projects():
        return response([{key: project[key] for key in ("id", "name", "revision", "created_at")} for project in store.list()])

    @app.post("/api/v1/projects")
    def create(payload: CreateProject):
        if not payload.name.strip():
            raise StoreError("empty_name", "Give the project a name.", 422)
        return response(envelope(store.create(payload.name, LIMITS["projects"])), 201)

    @app.get("/api/v1/projects/{project_id}")
    def get_project(project_id):
        return response(envelope(store.get(project_id)))

    @app.get("/api/v1/projects/{project_id}/audit-history")
    def audit_history(project_id):
        project = store.get(project_id)
        return response({"private": True, "baseline_history": project.get("baseline_history", []), "proposal_history": project.get("proposal_history", []), "decision_history": project.get("decision_history", []), "limits": {"baseline_snapshots": 20, "proposal_batches": 20, "decisions": 200}, "notice": "Private local audit records. Source text and internal review notes are excluded from client exports. Older records beyond these caps and inactive original bytes are not retained."})

    @app.put("/api/v1/projects/{project_id}/brief")
    def put_brief(project_id, payload: BriefInput, request: Request):
        text = payload.text.replace("\r\n", "\n").replace("\r", "\n")
        if not text.strip():
            raise StoreError("empty_brief", "The brief cannot be blank.", 422)
        def update(project, db):
            if project["brief"] and project["brief"]["text"] == text and project["brief"]["label"] == payload.source_label:
                return
            preserve_baseline(project, "brief changed")
            preserve_proposals(project)
            project["brief"] = {"id": uid(), "text": text, "label": payload.source_label, "sha256": hashlib.sha256(text.encode()).hexdigest()}
            project["baseline"] = {"id": uid(), "state": "draft", "hash": digest([]), "requirements": []}
            invalidate(project)
        return response(envelope(store.mutate(project_id, revision(request), update)))

    @app.put("/api/v1/projects/{project_id}/baseline")
    def put_baseline(project_id, payload: BaselineInput, request: Request):
        requirements = [r.model_dump(exclude_none=True) for r in payload.requirements]
        # The contract explicitly represents null quotation/source for manual additions.
        for requirement in requirements:
            requirement.setdefault("quote", None)
            requirement.setdefault("source_id", None)
        def update(project, db):
            validate_requirements(requirements, project["brief"])
            if canonical(requirements) == canonical(project["baseline"]["requirements"]):
                return
            preserve_baseline(project, "checklist edited")
            preserve_proposals(project)
            project["baseline"] = {"id": uid(), "state": "draft", "hash": digest(requirements), "requirements": requirements}
            invalidate(project)
        return response(envelope(store.mutate(project_id, revision(request), update)))

    @app.post("/api/v1/projects/{project_id}/baseline/approve")
    def approve(project_id, payload: ApproveInput, request: Request):
        def update(project, db):
            baseline = project["baseline"]
            ids = [r["id"] for r in baseline["requirements"]]
            if not ids or payload.baseline_hash != baseline["hash"] or sorted(payload.reviewed_requirement_ids) != sorted(ids):
                raise StoreError("baseline_review_required", "Review every current requirement before approving.")
            validate_requirements(baseline["requirements"], project["brief"])
            baseline["state"] = "approved"
        return response(envelope(store.mutate(project_id, revision(request), update)))

    async def upload(project_id, request, replacement=None):
        expected_revision = revision(request)
        project = store.get(project_id)
        if project["revision"] != expected_revision:
            raise StoreError("revision_conflict", "Project changed. Refresh before uploading.")
        form = await request.form(max_files=30, max_fields=0, max_part_size=1024)
        uploads = [value for key, value in form.multi_items() if isinstance(value, UploadFile) or hasattr(value, "filename")]
        if len(uploads) == 0 or (replacement and len(uploads) != 1):
            await form.close()
            raise StoreError("upload_required", "Select files to upload.", 422)
        old = next((f for f in project["files"] if f["id"] == replacement), None) if replacement else None
        if replacement and not old:
            await form.close()
            raise StoreError("file_not_found", "File no longer exists.", 404)
        active = [f for f in project["files"] if f["id"] != replacement]
        if len(active) + len(uploads) > LIMITS["files"]:
            await form.close()
            raise StoreError("file_count_limit", "A packet supports at most 30 files.", 413)
        staged, total, committed = [], sum(f["size"] for f in active), False
        try:
            for file in uploads:
                file_id, storage_name = uid(), uid()
                path = store.files / storage_name
                name, size, sha = clean_name(file.filename), 0, hashlib.sha256()
                staged.append({"id": file_id, "name": name, "_path": storage_name})
                with path.open("xb") as target:
                    os.chmod(path, 0o600)
                    while chunk := await file.read(65536):
                        size += len(chunk)
                        total += len(chunk)
                        if size > LIMITS["file_bytes"] or total > LIMITS["packet_bytes"]:
                            raise StoreError("byte_limit", "File or packet byte budget exceeded.", 413)
                        sha.update(chunk)
                        target.write(chunk)
                staged[-1].update(size=size, sha256=sha.hexdigest())
            deadline = time.monotonic() + 120
            for file in staged:
                result = await asyncio.to_thread(inspect_bounded, store.files / file["_path"], file["name"], deadline)
                file.update({key: result.get(key, default) for key, default in (("type", "unknown"), ("inspection", "blocked"), ("metadata", {}), ("text", ""), ("error", None))})
            if sum(len(f["text"]) for f in active + staged) > LIMITS["packet_text_characters"]:
                raise StoreError("packet_text_limit", "Extracted packet text exceeds 100,000 characters.", 413)
            def update(current, db):
                current_active = [f for f in current["files"] if f["id"] != replacement]
                if store.storage_size(db) - (old["size"] if old else 0) + sum(f["size"] for f in staged) > LIMITS["storage_bytes"]:
                    raise StoreError("storage_limit", "Delete data before adding more original bytes.", 413)
                preserve_proposals(current)
                current["files"] = current_active + staged
                invalidate(current)
            updated = store.mutate(project_id, expected_revision, update)
            committed = True
            if old:
                try:
                    (store.files / old["_path"]).unlink(missing_ok=True)
                except OSError:
                    pass  # Startup orphan cleanup handles leftovers without unregistering valid new bytes.
            return response(envelope(updated), 201)
        except Exception:
            if not committed:
                for file in staged:
                    (store.files / file["_path"]).unlink(missing_ok=True)
            raise
        finally:
            await form.close()

    @app.post("/api/v1/projects/{project_id}/files")
    async def files(project_id, request: Request):
        return await upload(project_id, request)

    @app.get("/api/v1/projects/{project_id}/files/{file_id}/preview")
    def file_preview(project_id, file_id):
        project = store.get(project_id)
        file = next((f for f in project["files"] if f["id"] == file_id), None)
        if not file:
            raise StoreError("file_not_found", "File no longer exists.", 404)
        if file["inspection"] != "inspected" or file["type"] not in {"png", "jpeg"}:
            raise StoreError("preview_unsupported", "Only inspected PNG/JPEG files have an inline visual preview.", 415)
        path = store.files / file["_path"]
        try:
            if path.stat().st_size != file["size"] or file["size"] > LIMITS["file_bytes"]:
                raise StoreError("original_changed", "Stored bytes changed. Replace the file before reviewing.", 409)
            with path.open("rb") as original:
                data = original.read(LIMITS["file_bytes"] + 1)
        except OSError:
            raise StoreError("original_unavailable", "Original file is unavailable. Replace it before reviewing.", 409)
        # Rechecking the immutable identity prevents serving modified on-disk content.
        if len(data) != file["size"] or len(data) > LIMITS["file_bytes"] or hashlib.sha256(data).hexdigest() != file["sha256"]:
            raise StoreError("original_changed", "Stored bytes changed. Replace the file before reviewing.", 409)
        return Response(data, media_type="image/png" if file["type"] == "png" else "image/jpeg", headers={"Content-Security-Policy": "default-src 'none'; sandbox", "Content-Disposition": "inline"})

    @app.post("/api/v1/projects/{project_id}/files/{file_id}/replacement")
    async def replace(project_id, file_id, request: Request):
        return await upload(project_id, request, file_id)

    @app.patch("/api/v1/projects/{project_id}/files/{file_id}")
    def rename(project_id, file_id, payload: RenameInput, request: Request):
        current = store.get(project_id)
        original = next((f for f in current["files"] if f["id"] == file_id), None)
        if not original:
            raise StoreError("file_not_found", "File no longer exists.", 404)
        expected_revision = revision(request)
        if current["revision"] != expected_revision:
            raise StoreError("revision_conflict", "Project changed. Refresh before renaming.")
        name = clean_name(payload.display_name)
        inspection = inspect_bounded(store.files / original["_path"], name, time.monotonic() + 120)
        def update(project, db):
            file = next((f for f in project["files"] if f["id"] == file_id), None)
            if not file:
                raise StoreError("file_not_found", "File no longer exists.", 404)
            preserve_proposals(project)
            file["name"] = name
            file.update({key: inspection.get(key, default) for key, default in (("type", "unknown"), ("inspection", "blocked"), ("metadata", {}), ("text", ""), ("error", None))})
            invalidate(project)
        return response(envelope(store.mutate(project_id, expected_revision, update)))

    @app.delete("/api/v1/projects/{project_id}/files/{file_id}")
    def remove_file(project_id, file_id, request: Request):
        removed = []
        def update(project, db):
            removed.extend(f for f in project["files"] if f["id"] == file_id)
            if not removed:
                raise StoreError("file_not_found", "File no longer exists.", 404)
            preserve_proposals(project)
            project["files"] = [f for f in project["files"] if f["id"] != file_id]
            invalidate(project)
        updated = store.mutate(project_id, revision(request), update)
        for file in removed:
            try:
                (store.files / file["_path"]).unlink(missing_ok=True)
            except OSError:
                pass
        return response(envelope(updated))

    @app.put("/api/v1/projects/{project_id}/decisions/{requirement_id}")
    def decide(project_id, requirement_id, payload: DecisionInput, request: Request):
        def update(project, db):
            if project["baseline"]["state"] != "approved":
                raise StoreError("baseline_not_approved", "Approve the checklist before saving decisions.")
            if requirement_id not in {r["id"] for r in project["baseline"]["requirements"]}:
                raise StoreError("requirement_not_found", "Requirement is not current.", 404)
            if payload.input_hash != input_hash(project):
                raise StoreError("stale_input", "Inputs changed. Review current files before saving.")
            if len(set(payload.file_ids)) != len(payload.file_ids) or not set(payload.file_ids) <= {f["id"] for f in project["files"]}:
                raise StoreError("invalid_files", "Choose unique active files from this project.", 422)
            if payload.human_disposition == "not_applicable" and not payload.internal_decision_note.strip():
                raise StoreError("note_required", "Explain why the requirement does not apply.", 422)
            existing = next((d for d in project["decisions"] if d["requirement_id"] == requirement_id), None)
            if existing:
                project.setdefault("decision_history", []).append(existing)
                project["decision_history"] = project["decision_history"][-200:]
            project["decisions"] = [d for d in project["decisions"] if d["requirement_id"] != requirement_id]
            project["decisions"].append({"requirement_id": requirement_id, **payload.model_dump()})
        return response(envelope(store.mutate(project_id, revision(request), update)))

    def run_job(project_id, job_id):
        try:
            captured = {}
            def start(project, db):
                job = next(j for j in project["jobs"] if j["id"] == job_id)
                if job["state"] != "queued":
                    raise StoreError("job_cancelled", "Job is no longer queued.")
                job.update(state="running", stage="local model inference")
                captured.update(json.loads(canonical(job)))
            store.mutate(project_id, None, start)
            remaining = 120 - (time.monotonic() - captured["_started"])
            if remaining <= 0 or not app.state.model_lock.acquire(timeout=max(0, remaining)):
                raise StoreError("model_job_timeout", "Model queue exceeded the 120-second job budget.")
            try:
                current = store.get(project_id)
                job = next(j for j in current["jobs"] if j["id"] == job_id)
                if job["state"] != "running":
                    return
                values = captured["_input"]
                deadline = captured["_started"] + 120
                result = adapter().extract(values["brief"], deadline=deadline) if captured["kind"] == "extract" else adapter().match(values["brief"], values["requirements"], values["files"], deadline=deadline)
            finally:
                app.state.model_lock.release()
            if time.monotonic() - captured["_started"] > 120:
                raise StoreError("model_job_timeout", "Job exceeded its total budget; result discarded.")
            def publish(project, db):
                job = next(j for j in project["jobs"] if j["id"] == job_id)
                if job["state"] != "running":
                    return
                current_snapshot = digest({"brief": project["brief"]["sha256"], "baseline_id": project["baseline"]["id"]}) if captured["kind"] == "extract" and project["brief"] else input_hash(project)
                if current_snapshot != captured["_snapshot"]:
                    job.update(state="superseded", stage="inputs changed", error="Result discarded because inputs changed.")
                    return
                if captured["kind"] == "extract":
                    requirements = []
                    for raw in result.get("requirements", []):
                        raw = {**raw, "id": uid(), "origin": "model_suggested", "source_id": project["brief"]["id"], "human_note": ""}
                        validated = Requirement.model_validate(raw).model_dump(exclude_none=True)
                        requirements.append(validated)
                    if not 1 <= len(requirements) <= LIMITS["requirements"]:
                        raise StoreError("invalid_model_output", "Model returned no valid bounded requirements.", 422)
                    validate_requirements(requirements, project["brief"])
                    # Explicit extract requests replace draft suggestions only, never approved baselines.
                    if project["baseline"]["state"] == "approved":
                        job.update(state="superseded", stage="baseline approved", error="Approved checklist was preserved.")
                        return
                    preserve_baseline(project, "model suggestions replaced draft")
                    preserve_proposals(project)
                    project["baseline"] = {"id": uid(), "state": "draft", "hash": digest(requirements), "requirements": requirements}
                    invalidate(project)
                else:
                    ids = {r["id"] for r in project["baseline"]["requirements"]}
                    files = {f["id"]: f for f in project["files"]}
                    proposals = []
                    for proposal in result.get("proposals", []):
                        if proposal.get("requirement_id") not in ids or len(proposal.get("candidates", [])) > 30:
                            raise StoreError("invalid_model_output", "Model returned unknown requirement IDs.", 422)
                        for candidate in proposal.get("candidates", []):
                            file = files.get(candidate.get("file_id"))
                            quote = candidate.get("quote")
                            if not file or file["inspection"] != "inspected" or (file["text"] and quote is None) or (quote is not None and (not quote or len(quote) > 500 or file["text"].count(quote) != 1)):
                                raise StoreError("invalid_model_evidence", "Model returned invalid file evidence.", 422)
                            if not isinstance(candidate.get("reason"), str) or not candidate["reason"].strip() or len(candidate["reason"]) > 2000:
                                raise StoreError("invalid_model_output", "Model returned invalid explanation.", 422)
                            if quote:
                                start = file["text"].index(quote)
                                candidate["source_span"] = {"source_unit_id": file["id"], "source_text_sha256": hashlib.sha256(file["text"].encode()).hexdigest(), "start_cp": start, "end_cp": start + len(quote), "quote": quote}
                        proposals.append({"id": uid(), "requirement_id": proposal["requirement_id"], "candidates": proposal["candidates"], "coverage": str(proposal.get("coverage", "model proposal"))[:2000], "model": result.get("model", {})})
                    if len({p["requirement_id"] for p in proposals}) != len(proposals):
                        raise StoreError("invalid_model_output", "Model returned duplicate requirement mappings.", 422)
                    proposed = {p["requirement_id"] for p in proposals}
                    for missing in ids - proposed:
                        proposals.append({"id": uid(), "requirement_id": missing, "candidates": [], "coverage": "Not proposed by this run. Review manually.", "model": result.get("model", {})})
                    preserve_proposals(project)
                    project["proposals"] = proposals
                job.update(state="succeeded", stage="completed", model=result.get("model", {}), completed_at=now())
            store.mutate(project_id, None, publish)
        except Exception as error:
            code = getattr(error, "code", "model_failed")
            safe_message = str(getattr(error, "message", "Local model job failed. Review manually or retry explicitly."))[:500]
            try:
                def fail(project, db):
                    job = next(j for j in project["jobs"] if j["id"] == job_id)
                    if job["state"] in {"queued", "running"}:
                        job.update(state="failed", stage="failed", error=safe_message, error_code=code)
                store.mutate(project_id, None, fail)
            except StoreError:
                pass  # Deleted projects must never be recreated by a late response.

    @app.post("/api/v1/projects/{project_id}/jobs/{kind}")
    def start_job(project_id, kind, payload: EmptyInput, request: Request):
        if kind not in {"extract", "match"}:
            raise StoreError("unsupported_job", "This release inspects files during bounded upload; use extract or match.", 422)
        job_id = uid()
        def update(project, db):
            if not project["brief"]:
                raise StoreError("brief_required", "Save a brief first.")
            if any(j["state"] in {"queued", "running"} for j in project["jobs"]):
                raise StoreError("job_active", "Finish or cancel the active job before starting another.")
            if len(project["jobs"]) >= 100:
                raise StoreError("job_history_limit", "This project has reached its 100-job history limit. Export and create a new project.")
            if kind == "match" and project["baseline"]["state"] != "approved":
                raise StoreError("baseline_not_approved", "Approve the checklist before matching.")
            if kind == "extract" and project["baseline"]["state"] == "approved":
                raise StoreError("approved_baseline", "Make the baseline draft before replacing suggestions.")
            project["jobs"].append({"id": job_id, "kind": kind, "state": "queued", "stage": "queued", "error": None, "created_at": now(),
                                    "_started": time.monotonic(), "_snapshot": digest({"brief": project["brief"]["sha256"], "baseline_id": project["baseline"]["id"]}) if kind == "extract" else input_hash(project),
                                    "_input": {"brief": project["brief"], "requirements": project["baseline"]["requirements"], "files": [{key: f[key] for key in ("id", "name", "type", "inspection", "metadata", "text")} for f in project["files"]]}})
        project = store.mutate(project_id, revision(request), update)
        worker = threading.Thread(target=run_job, args=(project_id, job_id), daemon=True)
        worker.start()
        return response({"job": next(j for j in envelope(project)["jobs"] if j["id"] == job_id), "revision": project["revision"]}, 202)

    @app.get("/api/v1/projects/{project_id}/jobs/{job_id}")
    def get_job(project_id, job_id):
        project = envelope(store.get(project_id))
        job = next((j for j in project["jobs"] if j["id"] == job_id), None)
        if not job:
            raise StoreError("job_not_found", "Job not found.", 404)
        return response({**job, "revision": project["revision"]})

    @app.post("/api/v1/projects/{project_id}/jobs/{job_id}/cancel")
    def cancel_job(project_id, job_id, payload: EmptyInput, request: Request):
        def update(project, db):
            job = next((j for j in project["jobs"] if j["id"] == job_id), None)
            if not job:
                raise StoreError("job_not_found", "Job not found.", 404)
            if job["state"] in {"queued", "running"}:
                job.update(state="cancelled", stage="cancelled", error="Application result cancelled; model server may still finish its request.")
        return response(envelope(store.mutate(project_id, revision(request), update)))

    @app.post("/api/v1/projects/{project_id}/exports")
    def export(project_id, payload: ExportInput, request: Request):
        summary = {}
        def update(project, db):
            if payload.input_hash != input_hash(project):
                raise StoreError("stale_input", "Inputs changed. Preview the current packet before exporting.")
            if len(project["exports"]) >= 100:
                raise StoreError("export_history_limit", "This project has reached its 100-export limit. Create a new project before making more snapshots.")
            value = projection(project, payload.acknowledge_unresolved)
            value["snapshot_hash"] = digest(value)
            formats = render(value)
            db.execute("INSERT INTO exports VALUES (?,?,?,?,?)", (value["id"], project_id, formats["json"], formats["md"], formats["html"]))
            summary.update({"id": value["id"], "created_at": value["created_at"], "snapshot_hash": value["snapshot_hash"], "status": value["status"], "gaps": value["gaps"], "preview": value})
            project["exports"].append(summary)
        project = store.mutate(project_id, revision(request), update)
        return response({"export": summary, "revision": project["revision"]}, 201)

    @app.get("/api/v1/projects/{project_id}/handoff-preview")
    def handoff_preview(project_id):
        project = store.get(project_id)
        value = projection(project, True)
        value["id"], value["created_at"] = None, None
        return response(value)

    @app.get("/api/v1/projects/{project_id}/exports/{export_id}/{format}")
    def download(project_id, export_id, format):
        if format not in {"json", "md", "html"}:
            raise StoreError("unsupported_format", "Choose JSON, Markdown or HTML.", 404)
        with store.connection() as db:
            row = db.execute("SELECT json,md,html FROM exports WHERE id=? AND project_id=?", (export_id, project_id)).fetchone()
        if not row:
            raise StoreError("export_not_found", "Export not found.", 404)
        return Response(row[("json", "md", "html").index(format)], media_type={"json": "application/json", "md": "text/markdown", "html": "text/html"}[format], headers={"Content-Disposition": f'attachment; filename="handoff-{export_id}.{format}"', "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox"})

    @app.delete("/api/v1/projects/{project_id}")
    def delete(project_id, request: Request):
        store.delete(project_id, revision(request))
        return response({"deleted": True})

    frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app
