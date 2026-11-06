"""Backend-owned delivery coordination; proposals never change human review."""

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import threading
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .policy import LIMITS
from .store import StoreError, canonical, digest, input_hash, now, uid, invalidate
from .summary import build_summary


SCHEMA_VERSION = 4
DEFAULT_LIMITS = {
    "jobs": 10, "receipts_per_job": 60, "staging_bytes": 100 * 1024 * 1024,
    "file_bytes": LIMITS["file_bytes"], "operations_per_job": 1000,
    "result_bytes": 64 * 1024, "blockers_per_job": 100,
}


def _text(value, field, maximum=256):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(not c.isprintable() for c in value):
        raise StoreError("delivery_invalid_input", f"Invalid {field}.", 422)
    return value


@dataclass(frozen=True)
class DeliveryBinding:
    """Configured transport identity. The API must obtain it from trusted config."""

    server: str
    room: str
    thread: str | None = None

    def __post_init__(self):
        _text(self.server, "server", 1024)
        parts = urlsplit(self.server)
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
            raise StoreError("delivery_invalid_input", "Invalid server identity.", 422)
        _text(self.room, "room")
        if self.thread is not None:
            _text(self.thread, "thread")

    def key(self):
        return digest({"server": self.server, "room": self.room, "thread": self.thread})


class DeliveryService:
    def __init__(self, store, *, limits=None):
        self.store = store
        # One preparation owner per Store, including same-process reattachment.
        with store.lock:
            if not hasattr(store, "delivery_prepare_lock"):
                store.delivery_prepare_lock = threading.Lock()
            self.prepare_lock = store.delivery_prepare_lock
        self.limits = {**DEFAULT_LIMITS, **(limits or {})}
        if set(self.limits) != set(DEFAULT_LIMITS) or any(type(value) is not int or value < 1 for value in self.limits.values()):
            raise ValueError("Delivery limits must be positive integers with known names.")
        self.root = store.directory / "integration"
        self.staging = self.root / "staging"
        self.outgoing = self.root / "outgoing"
        with store.lock, store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='delivery_schema'").fetchone()
            if exists:
                rows = db.execute("SELECT version FROM delivery_schema").fetchall()
                if len(rows) != 1 or rows[0][0] not in {1, 2, 3, SCHEMA_VERSION}:
                    raise StoreError("delivery_schema_unsupported", "This delivery schema needs a compatible application version.")
            else:
                for statement in (
                    "CREATE TABLE delivery_schema (version INTEGER NOT NULL)",
                    "CREATE TABLE delivery_jobs (id TEXT PRIMARY KEY, binding TEXT NOT NULL UNIQUE, server TEXT NOT NULL, room TEXT NOT NULL, thread TEXT, project_id TEXT NOT NULL, created_at TEXT NOT NULL)",
                    "CREATE TABLE delivery_operations (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, kind TEXT NOT NULL, operation_key TEXT NOT NULL, payload_digest TEXT NOT NULL, result TEXT NOT NULL, UNIQUE(job_id, kind, operation_key))",
                    "CREATE TABLE delivery_receipts (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, source_id TEXT NOT NULL, filename TEXT NOT NULL, sha256 TEXT NOT NULL, size INTEGER NOT NULL, relative_path TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(job_id, source_id))",
                    "CREATE TABLE delivery_blockers (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, requirement_id TEXT NOT NULL, message TEXT NOT NULL, input_hash TEXT NOT NULL, source_revision INTEGER NOT NULL, created_at TEXT NOT NULL)",
                ):
                    db.execute(statement)
                db.execute("INSERT INTO delivery_schema (version) VALUES (?)", (1,))
            if db.execute("SELECT version FROM delivery_schema").fetchone()[0] == 1:
                db.execute("CREATE TABLE delivery_packets (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, manifest_hash TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)")
                db.execute("UPDATE delivery_schema SET version=?", (2,))
            if db.execute("SELECT version FROM delivery_schema").fetchone()[0] == 2:
                from .delivery_context import install_context_schema
                install_context_schema(db)
                db.execute("UPDATE delivery_schema SET version=?", (3,))
            if db.execute("SELECT version FROM delivery_schema").fetchone()[0] == 3:
                from .delivery_share import install_share_schema
                install_share_schema(db)
                db.execute("UPDATE delivery_schema SET version=?", (SCHEMA_VERSION,))
        for directory in (self.root, self.staging, self.outgoing):
            if directory.is_symlink():
                raise StoreError("delivery_staging_invalid", "Integration storage must not be a symbolic link.")
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(directory, 0o700)
        with self.prepare_lock:
            self._recover_preparations()
        from .delivery_context import DeliveryContext
        self.context = DeliveryContext(self)
        from .delivery_share import DeliveryShare
        self.shares = DeliveryShare(self)
        # Migration must also reconcile persisted inspector/source anchors.
        with store.lock, store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            for project_id, body in db.execute("SELECT id, body FROM projects").fetchall():
                project = json.loads(body)
                if store._sync_delivery_context(project, db):
                    project["revision"] += 1
                    project["updated_at"] = now()
                    db.execute("UPDATE projects SET body=? WHERE id=?", (canonical(project), project_id))

    def _recover_preparations(self):
        """Remove only this module's abandoned copies, never receipt/original bytes.

        The supported launcher holds exclusive_directory before constructing the
        Store. The shared preparation lock also prevents reattachment in the same
        process from deleting an active copy. Refuse unknown contents rather than
        expanding cleanup into unrelated operator files.
        """
        try:
            for path in self.root.iterdir():
                if re.fullmatch(r"packet-[a-z0-9_]{8}", path.name) is None:
                    continue
                info = path.lstat()
                if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise OSError("Unrecognized preparation directory")
                for child in path.iterdir():
                    item = child.lstat()
                    if (re.fullmatch(r"[a-f0-9]{32}", child.name) is None or not stat.S_ISREG(item.st_mode)
                            or item.st_uid != os.getuid() or item.st_nlink != 1):
                        raise OSError("Unrecognized preparation contents")
                if not shutil.rmtree.avoids_symlink_attacks:
                    raise OSError("Safe preparation recovery is unavailable")
                shutil.rmtree(path)
        except OSError:
            raise StoreError("delivery_storage_failure", "Temporary packet recovery needs operator attention. Existing receipts and originals were kept.") from None

    def _job(self, db, job_id, binding):
        _text(job_id, "job")
        if not isinstance(binding, DeliveryBinding):
            raise StoreError("delivery_binding_refused", "A configured delivery binding is required.", 403)
        row = db.execute("SELECT id, project_id, created_at FROM delivery_jobs WHERE id=? AND binding=?", (job_id, binding.key())).fetchone()
        if row is None:
            raise StoreError("delivery_binding_refused", "This delivery is not available in this conversation.", 403)
        self.store.get(row[1], db)
        return {"id": row[0], "project_id": row[1], "created_at": row[2]}

    def _operation(self, db, job, kind, key, payload, expected_revision, expected_hash, apply):
        replay = self._replay(db, job, kind, key, payload)
        if replay is not None:
            return replay
        payload_digest = digest(payload)
        count = db.execute("SELECT COUNT(*) FROM delivery_operations WHERE job_id=?", (job["id"],)).fetchone()[0]
        if count >= self.limits["operations_per_job"]:
            raise StoreError("delivery_operation_limit", "This delivery has reached its operation limit.", 413)
        project = self.store.get(job["project_id"], db)
        current_hash = input_hash(project)
        if expected_revision is not None and project["revision"] != expected_revision:
            raise StoreError("revision_conflict", "The project changed. Refresh before continuing.")
        if expected_hash is not None and current_hash != expected_hash:
            raise StoreError("delivery_input_conflict", "The packet changed. Refresh before continuing.")
        operation_id = uid()
        result = {"operation_id": operation_id, "state": "succeeded", "source_revision": project["revision"], "input_hash": current_hash, "result": apply(project), "retry_advice": "none"}
        encoded = canonical(result)
        if len(encoded.encode()) > self.limits["result_bytes"]:
            raise StoreError("delivery_result_limit", "The operation result exceeds its storage limit.", 413)
        db.execute("INSERT INTO delivery_operations (id, job_id, kind, operation_key, payload_digest, result) VALUES (?,?,?,?,?,?)", (operation_id, job["id"], kind, key, payload_digest, encoded))
        return result

    def _replay(self, db, job, kind, key, payload):
        _text(key, "operation key", 128)
        payload_digest = digest(payload)
        previous = db.execute("SELECT payload_digest, result FROM delivery_operations WHERE job_id=? AND kind=? AND operation_key=?", (job["id"], kind, key)).fetchone()
        if previous:
            if previous[0] != payload_digest:
                raise StoreError("delivery_operation_conflict", "This operation key was already used with different input.")
            return json.loads(previous[1])
        return None

    def create_job(self, binding, project_id, operation_key):
        if not isinstance(binding, DeliveryBinding):
            raise StoreError("delivery_binding_refused", "A configured delivery binding is required.", 403)
        _text(project_id, "project")
        with self.store.lock, self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self.store.get(project_id, db)
            row = db.execute("SELECT id, project_id FROM delivery_jobs WHERE binding=?", (binding.key(),)).fetchone()
            if row and row[1] != project_id:
                raise StoreError("delivery_binding_conflict", "This conversation already belongs to another delivery.")
            linked = db.execute("SELECT id, binding FROM delivery_jobs WHERE project_id=?", (project_id,)).fetchone()
            if linked and linked[1] != binding.key():
                raise StoreError("delivery_project_binding_conflict", "This handoff already belongs to another delivery room.")
            if row:
                job = self._job(db, row[0], binding)
            else:
                if db.execute("SELECT COUNT(*) FROM delivery_jobs").fetchone()[0] >= self.limits["jobs"]:
                    raise StoreError("delivery_job_limit", "The delivery job limit has been reached.", 413)
                job = {"id": uid(), "project_id": project_id, "created_at": now()}
                db.execute("INSERT INTO delivery_jobs (id, binding, server, room, thread, project_id, created_at) VALUES (?,?,?,?,?,?,?)", (job["id"], binding.key(), binding.server, binding.room, binding.thread, project_id, job["created_at"]))
                db.execute("INSERT INTO delivery_context_jobs (job_id,epoch) VALUES (?,?)", (job["id"],0))
            return self._operation(db, job, "create", operation_key, {"project_id": project_id}, None, None, lambda project: {"job_id": job["id"], "project_id": project_id})

    def get_job(self, job_id, binding):
        with self.store.lock, self.store.connection() as db:
            return self._job(db, job_id, binding)

    def status(self, job_id, binding):
        with self.store.lock, self.store.connection() as db:
            job = self._job(db, job_id, binding)
            self.store.reconcile_originals(job["project_id"])
            context = self.context.read_project(job["project_id"])
            project = self.store.get(job["project_id"], db)
            current_hash = input_hash(project)
            receipts = db.execute("SELECT id, sha256, size FROM delivery_receipts WHERE job_id=?", (job_id,)).fetchall()
            count = len(receipts)
            last = self._last_packet(db, job_id)
            considered = set(last["considered_receipt_ids"]) if last else set()
            pending = [row for row in receipts if row[0] not in considered]
            unavailable = sum(self._receipt_availability(job_id, row[0], row[1], row[2]) != "available" for row in pending)
            requirements = [{"id": row["id"], "title": row["title"], "checks": [
                {key: value for key, value in check.items() if key not in {"needle", "instruction"}}
                for check in row["checks"]]} for row in project["baseline"]["requirements"]]
            allowed_metadata = {"width_px", "height_px", "format", "frames", "nonopaque_pixels", "alpha_min", "alpha_max", "metadata_only", "view_box", "pages", "decoded_content_bytes", "extractor", "extractor_version", "encoding", "characters"}
            files = [{**{key: row[key] for key in ("id", "name", "type", "sha256", "size", "inspection")}, "metadata": {key: value for key, value in row["metadata"].items() if key in allowed_metadata}} for row in project["files"]]
            summary = build_summary(project)
            state, actor, action = "human_review", "local_reviewer", "Review the proposed file mapping and assess the current packet in the local desk."
            if not summary["baseline_approved"]:
                state, action = "scope_review", "Confirm the checklist in the local desk before checking delivery evidence."
            elif unavailable:
                state, action = "intake_repair", "Recover or replace unavailable staged attachments before confirming the packet."
            elif pending:
                state, action = "awaiting_packet_confirmation", "New attachments await local confirmation of the complete replacement packet. Earlier reviews do not cover pending files."
            elif not files:
                state, actor, action = "awaiting_packet", "teammate", "Supply the declared delivery files; no committed evidence is available yet."
            elif any(row["inspection"] != "inspected" for row in files):
                state, action = "packet_problem", "Inspect blocked originals and replace unsupported or damaged evidence."
            elif context and any(row["state"] == "pending" for row in context["questions"]):
                waiting = [row for row in context["questions"] if row["state"] == "pending"]
                state = "clarification_pending"
                if any(row["replies"] or row["legacy"] for row in waiting):
                    actor, action = "local_reviewer", "Check the unverified conversation context beside its requirement, then resolve it in the local desk. Earlier readiness does not cover this pending context."
                else:
                    actor, action = "teammate", "Answer the pending clarification in the delivery room. No scope change or assessment has been recorded."
            elif summary["needs_work_count"] or any(row["failed_check_count"] and not row["is_exception"] for row in summary["rows"]):
                state, actor, action = "needs_correction", "teammate", "Resolve the current saved review findings and supply a corrected packet."
            elif summary["status"] in {"reviewed", "reviewed_with_exceptions"}:
                state, action = "ready_to_prepare_record", "Current review is recorded. The local reviewer may preview a record and separately choose whether to share it."
            elif summary["stale_review_count"]:
                state, action = "review_required", "The packet changed. Review its current evidence again; previous review is historical."
            questions = context["questions"] if context else []
            returns = self.shares.read_project(job["project_id"])
            current_return = next((item for item in returns if item["is_current"] and item["state"] in {"authorized", "issued_unverified", "operator_confirmed"}), None)
            if state == "ready_to_prepare_record" and current_return:
                if current_return["state"] == "authorized":
                    state, actor, action = "awaiting_record_return", "agent", "An exact frozen record is locally authorized. Consume its one-use permission through the configured return tool; never send on a replay or guess a destination."
                elif current_return["state"] == "issued_unverified":
                    state, actor, action = "return_verification_required", "local_reviewer", "A send permission was issued, but delivery is unverified. Check the room and exact returned file; do not resend blindly."
                else:
                    state, actor, action = "record_return_operator_confirmed", "local_reviewer", "Returned bytes match and the operator checked the destination. This is operator confirmation, not independent transport proof or client acceptance."
            return {"job_id": job_id, "project_id": job["project_id"], "source_revision": project["revision"], "input_hash": current_hash, "state": state, "next_actor": actor, "next_action": action, "staged_receipts": count, "pending_receipts": len(pending), "unavailable_receipts": unavailable, "requirements": requirements, "files": files, "review_summary": {key: summary[key] for key in ("status", "current_review_count", "stale_review_count", "unreviewed_count", "needs_work_count", "failed_check_count", "unknown_check_count")},
                    "context_epoch": context["context_epoch"] if context else 0,
                    "pending_context_count": sum(row["state"] == "pending" for row in questions),
                    "questions": [{key: row[key] for key in ("question_id","requirement_id","state","source_revision","input_hash")} for row in questions],
                    "blockers": [{"id": row["question_id"], "requirement_id": row["requirement_id"], "state": "proposed" if row["state"] == "pending" else row["state"]} for row in questions], "returns": [{key: item[key] for key in ("intent_id", "state", "source_revision", "is_current", "artifact_sha256", "filename")} for item in returns], "approval": "local_human_review_required"}

    def propose_blocker(self, job_id, binding, operation_key, *, expected_revision, expected_hash, requirement_id, message):
        _text(requirement_id, "requirement")
        _text(message, "blocker message", 1000)
        if type(expected_revision) is not int or expected_revision < 1 or not isinstance(expected_hash, str) or re.fullmatch(r"[a-f0-9]{64}", expected_hash) is None:
            raise StoreError("delivery_invalid_input", "A current revision and input hash are required.", 422)
        payload = {"requirement_id": requirement_id, "message": message, "expected_revision": expected_revision, "expected_hash": expected_hash}
        with self.store.lock, self.store.connection() as db:
            job = self._job(db, job_id, binding)
            replay = self._replay(db, job, "propose_blocker", operation_key, payload)
            if replay is not None:
                return replay
            self.store.reconcile_originals(job["project_id"])
            db.execute("BEGIN IMMEDIATE")
            def apply(project):
                if requirement_id not in {item["id"] for item in project["baseline"]["requirements"]}:
                    raise StoreError("delivery_requirement_missing", "The requirement is not in the current checklist.", 422)
                if db.execute("SELECT COUNT(*) FROM delivery_blockers WHERE job_id=?", (job_id,)).fetchone()[0] >= self.limits["blockers_per_job"]:
                    raise StoreError("delivery_blocker_limit", "This delivery has reached its proposal limit.", 413)
                blocker_id = uid()
                db.execute("INSERT INTO delivery_blockers (id, job_id, requirement_id, message, input_hash, source_revision, created_at) VALUES (?,?,?,?,?,?,?)", (blocker_id, job_id, requirement_id, message, input_hash(project), project["revision"], now()))
                self.context.record_legacy(db,job,project,blocker_id,requirement_id,message,project["revision"],input_hash(project))
                return {"blocker_id": blocker_id, "state": "proposed", "requirement_id": requirement_id}
            return self._operation(db, job, "propose_blocker", operation_key, payload, expected_revision, expected_hash, apply)

    def stage_receipt(self, job_id, binding, operation_key, *, source_id, filename, content):
        _text(source_id, "source identity")
        _text(filename, "filename", 200)
        if filename in {".", ".."} or re.search(r"[/\\]", filename):
            raise StoreError("delivery_invalid_input", "Use a filename without a path.", 422)
        if not isinstance(content, bytes) or not content or len(content) > self.limits["file_bytes"]:
            raise StoreError("delivery_file_limit", "The attachment is empty or exceeds its byte limit.", 413)
        sha = hashlib.sha256(content).hexdigest()
        payload = {"source_id": source_id, "filename": filename, "sha256": sha, "size": len(content)}
        created_path = None
        try:
            with self.store.lock, self.store.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                job = self._job(db, job_id, binding)
                def apply(project):
                    nonlocal created_path
                    existing = db.execute("SELECT id, filename, sha256, size FROM delivery_receipts WHERE job_id=? AND source_id=?", (job_id, source_id)).fetchone()
                    if existing:
                        if (existing[1], existing[2], existing[3]) != (filename, sha, len(content)):
                            raise StoreError("delivery_source_conflict", "This source identity already names different attachment bytes.")
                        return {"receipt_id": existing[0], **payload, "state": "received"}
                    count = db.execute("SELECT COUNT(*) FROM delivery_receipts WHERE job_id=?", (job_id,)).fetchone()[0]
                    total = db.execute("SELECT COALESCE(SUM(size),0) FROM delivery_receipts").fetchone()[0]
                    if count >= self.limits["receipts_per_job"] or total + len(content) > self.limits["staging_bytes"]:
                        raise StoreError("delivery_staging_limit", "Pending attachments exceed the staging budget.", 413)
                    receipt_id = uid()
                    directory = self.staging / job_id
                    if directory.is_symlink():
                        raise StoreError("delivery_staging_invalid", "Attachment staging is unavailable.")
                    directory.mkdir(mode=0o700, exist_ok=True)
                    created_path = directory / receipt_id
                    descriptor = os.open(created_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                    with os.fdopen(descriptor, "wb") as target:
                        target.write(content)
                        target.flush()
                        os.fsync(target.fileno())
                    db.execute("INSERT INTO delivery_receipts (id, job_id, source_id, filename, sha256, size, relative_path, created_at) VALUES (?,?,?,?,?,?,?,?)", (receipt_id, job_id, source_id, filename, sha, len(content), str(Path(job_id) / receipt_id), now()))
                    return {"receipt_id": receipt_id, **payload, "state": "received"}
                result = self._operation(db, job, "stage_receipt", operation_key, payload, None, None, apply)
                receipt_id = result["result"]["receipt_id"]
                result["availability"] = self._receipt_availability(job_id, receipt_id, sha, len(content))
                if result["availability"] != "available":
                    result["retry_advice"] = "operator_action"
                return result
        except BaseException:
            if created_path is not None:
                try:
                    with self.store.lock, self.store.connection() as check:
                        registered = check.execute("SELECT 1 FROM delivery_receipts WHERE job_id=? AND relative_path=?", (job_id, str(Path(job_id) / created_path.name))).fetchone()
                    if registered is None:
                        created_path.unlink(missing_ok=True)
                except Exception:
                    raise StoreError("delivery_commit_unknown", "Attachment outcome is unknown. Preserve the operation key and check receipts before retrying.") from None
            raise

    def _receipt_availability(self, job_id, receipt_id, sha, size):
        directory = self.staging / job_id
        path = directory / receipt_id
        try:
            if directory.is_symlink() or path.is_symlink() or not path.is_file():
                return "unavailable"
            if path.stat().st_size != size or size > self.limits["file_bytes"]:
                return "changed"
            with path.open("rb") as source:
                actual = hashlib.sha256()
                read = 0
                while chunk := source.read(65536):
                    read += len(chunk)
                    if read > size:
                        return "changed"
                    actual.update(chunk)
            return "available" if read == size and actual.hexdigest() == sha else "changed"
        except OSError:
            return "unavailable"


    def _last_packet(self, db, job_id):
        row = db.execute("SELECT body FROM delivery_packets WHERE job_id=? ORDER BY rowid DESC LIMIT 1", (job_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def _receipts(self, db, job_id):
        return [{"receipt_id": row[0], "source_id": row[1], "filename": row[2], "sha256": row[3], "size": row[4]}
                for row in db.execute("SELECT id, source_id, filename, sha256, size FROM delivery_receipts WHERE job_id=? ORDER BY id", (job_id,))]

    def list_receipts(self, job_id, binding):
        with self.store.lock, self.store.connection() as db:
            job = self._job(db, job_id, binding)
            self.store.reconcile_originals(job["project_id"])
            project = self.store.get(job["project_id"], db)
            last = self._last_packet(db, job_id)
            considered = set(last["considered_receipt_ids"]) if last else set()
            receipts = [{**row, "availability": self._receipt_availability(job_id, row["receipt_id"], row["sha256"], row["size"]),
                         "considered": row["receipt_id"] in considered} for row in self._receipts(db, job_id)]
            return {"job_id": job_id, "source_revision": project["revision"], "input_hash": input_hash(project),
                    "receipts": receipts, "pending_count": sum(not row["considered"] for row in receipts), "last_packet": last}

    def context_for_project(self, project_id, binding):
        with self.store.lock, self.store.connection() as db:
            self.store.get(project_id, db)
            row = db.execute("SELECT id FROM delivery_jobs WHERE project_id=? AND binding=?", (project_id, binding.key())).fetchone()
            return self.list_receipts(row[0], binding) if row else None

    def _packet_inputs(self, receipt_ids, expected_revision, expected_hash):
        if (not isinstance(receipt_ids, list) or not 1 <= len(receipt_ids) <= LIMITS["files"]
            or any(not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,100}", value) is None for value in receipt_ids)
            or len(set(receipt_ids)) != len(receipt_ids) or type(expected_revision) is not int or not 1 <= expected_revision <= 2**53-1
            or not isinstance(expected_hash, str) or re.fullmatch(r"[a-f0-9]{64}", expected_hash) is None):
            raise StoreError("delivery_invalid_input", "Choose a bounded unique packet and its current revision/hash.", 422)

    def _packet_preview(self, db, job, binding, receipt_ids, expected_revision, expected_hash):
        project = self.store.get(job["project_id"], db)
        if project["revision"] != expected_revision or input_hash(project) != expected_hash:
            raise StoreError("revision_conflict", "The project changed. Refresh before confirming this packet.")
        all_rows = self._receipts(db, job["id"])
        rows = [row for row in all_rows if row["receipt_id"] in receipt_ids]
        if len(rows) != len(receipt_ids):
            raise StoreError("delivery_receipt_missing", "Select only receipts received for this delivery.", 422)
        keys = [unicodedata.normalize("NFC", row["filename"]).casefold() for row in rows]
        if len(set(keys)) != len(keys):
            raise StoreError("delivery_filename_collision", "Packet filenames must be unique, including case and Unicode equivalents.", 422)
        if sum(row["size"] for row in rows) > LIMITS["packet_bytes"]:
            raise StoreError("delivery_packet_limit", "The complete packet exceeds its byte budget.", 413)
        if any(self._receipt_availability(job["id"], row["receipt_id"], row["sha256"], row["size"]) != "available" for row in rows):
            raise StoreError("delivery_receipt_unavailable", "A selected attachment changed or is missing. Recover it before confirming.")
        current = {row["name"]: row for row in project["files"]}
        incoming = {row["filename"]: row for row in rows}
        changes = {"added": [], "replaced": [], "removed": [], "unchanged": []}
        for name, row in incoming.items():
            old = current.get(name)
            kind = "added" if old is None else "unchanged" if old["sha256"] == row["sha256"] and old["size"] == row["size"] and old["inspection"] == "inspected" else "replaced"
            changes[kind].append(name)
        changes["removed"] = sorted(set(current) - set(incoming))
        # Legacy manual uploads can contain repeated filenames. Collapsing the
        # lookup must never make their removal look like an unchanged packet.
        seen = set()
        for file in project["files"]:
            if file["name"] in seen:
                changes["removed"].append(file["name"])
            seen.add(file["name"])
        considered = [row["receipt_id"] for row in all_rows]
        fingerprint = digest({"binding": binding.key(), "job_id": job["id"], "receipts": rows, "considered": all_rows,
                              "expected_revision": expected_revision, "input_hash": expected_hash})
        return {"job_id": job["id"], "source_revision": expected_revision, "input_hash": expected_hash,
                "manifest_hash": fingerprint, "receipts": rows, "considered_receipt_ids": considered,
                "excluded_receipts": [row for row in all_rows if row["receipt_id"] not in receipt_ids],
                "excluded_receipt_ids": sorted(set(considered) - set(receipt_ids)), "total_bytes": sum(row["size"] for row in rows),
                "changes": changes, "review_will_be_stale": any(changes[key] for key in ("added", "replaced", "removed")), "replaces_entire_packet": True}

    def preview_packet(self, job_id, binding, *, receipt_ids, expected_revision, expected_hash):
        self._packet_inputs(receipt_ids, expected_revision, expected_hash)
        with self.store.lock, self.store.connection() as db:
            job = self._job(db, job_id, binding)
            self.store.reconcile_originals(job["project_id"])
            return self._packet_preview(db, job, binding, receipt_ids, expected_revision, expected_hash)

    def _copy_receipt(self, job_id, row, destination):
        # Open every component without following symlinks. Identity is checked on
        # the actual bytes copied, not merely the earlier receipt metadata.
        descriptors = []
        try:
            parent = os.open(self.staging, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            descriptors.append(parent)
            directory = os.open(job_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            descriptors.append(directory)
            descriptor = os.open(row["receipt_id"], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(descriptor, "rb") as source, destination.open("xb") as target:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size != row["size"]:
                    raise StoreError("delivery_receipt_unavailable", "A selected attachment is unavailable.")
                sha, size = hashlib.sha256(), 0
                while chunk := source.read(65536):
                    size += len(chunk)
                    if size > row["size"] or size > self.limits["file_bytes"]:
                        raise StoreError("delivery_receipt_unavailable", "A selected attachment changed.")
                    sha.update(chunk); target.write(chunk)
                target.flush(); os.fsync(target.fileno())
                if size != row["size"] or sha.hexdigest() != row["sha256"]:
                    raise StoreError("delivery_receipt_unavailable", "A selected attachment changed.")
            destination.chmod(0o600)
        except OSError:
            raise StoreError("delivery_storage_failure", "Attachment preparation could not complete. The current packet was kept.") from None
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    def confirm_packet(self, job_id, binding, operation_key, *, receipt_ids, expected_revision, expected_hash, manifest_hash, inspect_file):
        self._packet_inputs(receipt_ids, expected_revision, expected_hash)
        if not isinstance(manifest_hash, str) or re.fullmatch(r"[a-f0-9]{64}", manifest_hash) is None:
            raise StoreError("delivery_invalid_input", "A reviewed packet manifest is required.", 422)
        payload = {"receipt_ids": sorted(receipt_ids), "expected_revision": expected_revision, "expected_hash": expected_hash, "manifest_hash": manifest_hash}
        with self.prepare_lock:
            with self.store.lock, self.store.connection() as db:
                job = self._job(db, job_id, binding)
                replay = self._replay(db, job, "confirm_packet", operation_key, payload)
                if replay is not None:
                    return replay
            preview = self.preview_packet(job_id, binding, receipt_ids=receipt_ids, expected_revision=expected_revision, expected_hash=expected_hash)
            if preview["manifest_hash"] != manifest_hash:
                raise StoreError("delivery_manifest_changed", "New attachments arrived or this selection changed. Preview the full packet again.")
            # No abandoned scratch is admitted alongside the next bounded packet.
            self._recover_preparations()
            created_paths, old_paths, committed, result = [], [], False, None
            with tempfile.TemporaryDirectory(prefix="packet-", dir=self.root) as temporary:
                prepared = []
                deadline = time.monotonic() + 120
                for row in preview["receipts"]:
                    path = Path(temporary) / row["receipt_id"]
                    self._copy_receipt(job_id, row, path)
                    try:
                        inspection = inspect_file(path, row["filename"], deadline)
                    except Exception:
                        raise StoreError("delivery_inspection_failed", "Packet inspection failed. The existing packet was kept.", 422) from None
                    if inspection.get("inspection") != "inspected":
                        raise StoreError("delivery_inspection_failed", "A selected file could not be safely inspected. Correct it before confirming the packet.", 422)
                    prepared.append({**row, "prepared_path": path, "inspection_result": inspection})
                if sum(len(row["inspection_result"].get("text", "")) for row in prepared) > LIMITS["packet_text_characters"]:
                    raise StoreError("delivery_packet_limit", "The complete packet exceeds its extracted text budget.", 413)
                try:
                    with self.store.lock, self.store.connection() as db:
                        db.execute("BEGIN IMMEDIATE")
                        job = self._job(db, job_id, binding)
                        replay = self._replay(db, job, "confirm_packet", operation_key, payload)
                        if replay is not None:
                            return replay
                        project = self.store.get(job["project_id"], db)
                        # Reconcile while owning this transaction, then refuse a
                        # changed original without keeping a new false receipt.
                        if self.store._reconcile_originals(project):
                            raise StoreError("revision_conflict", "Original evidence changed. Refresh the desk before confirming.")
                        fresh = self._packet_preview(db, job, binding, receipt_ids, expected_revision, expected_hash)
                        if fresh["manifest_hash"] != manifest_hash:
                            raise StoreError("delivery_manifest_changed", "The received packet changed. Preview again.")
                        if db.execute("SELECT COUNT(*) FROM delivery_operations WHERE job_id=?", (job_id,)).fetchone()[0] >= self.limits["operations_per_job"]:
                            raise StoreError("delivery_operation_limit", "This delivery has reached its operation limit.", 413)
                        if self.store.storage_size(db) - sum(row["size"] for row in project["files"]) + fresh["total_bytes"] > LIMITS["storage_bytes"]:
                            raise StoreError("storage_limit", "Delete data before adding more original bytes.", 413)
                        old = {row["name"]: row for row in project["files"]}
                        new_files = []
                        for row in prepared:
                            existing = old.get(row["filename"])
                            if existing and existing["sha256"] == row["sha256"] and existing["size"] == row["size"] and existing["inspection"] == "inspected":
                                new_files.append(existing)
                                continue
                            storage_name = uid()
                            target = self.store.files / storage_name
                            created_paths.append(target)
                            with row["prepared_path"].open("rb") as source, target.open("xb") as output:
                                os.chmod(target, 0o600)
                                while chunk := source.read(65536): output.write(chunk)
                                output.flush(); os.fsync(output.fileno())
                            new_files.append({"id": uid(), "name": row["filename"], "_path": storage_name, "sha256": row["sha256"], "size": row["size"],
                                              **{key: row["inspection_result"].get(key, default) for key, default in (("type", "unknown"), ("inspection", "blocked"), ("metadata", {}), ("text", ""), ("error", None))}})
                        changed = fresh["review_will_be_stale"]
                        if changed:
                            if project["proposals"]:
                                history = project.setdefault("proposal_history", [])
                                history.append({"recorded_at": now(), "input_hash": input_hash(project), "proposals": json.loads(canonical(project["proposals"]))})
                                project["proposal_history"] = history[-20:]
                            retained = {row["_path"] for row in new_files}
                            old_paths = [self.store.files / row["_path"] for row in project["files"] if row["_path"] not in retained]
                            project["files"] = new_files
                            invalidate(project)
                            self.store._sync_delivery_context(project, db)
                            project["revision"] += 1
                            project["updated_at"] = now()
                            db.execute("UPDATE projects SET body=? WHERE id=?", (canonical(project), project["id"]))
                        packet_id = uid()
                        packet = {"packet_id": packet_id, "receipt_ids": sorted(receipt_ids), "considered_receipt_ids": fresh["considered_receipt_ids"],
                                  "source_revision": project["revision"], "input_hash": input_hash(project)}
                        result = {"operation_id": uid(), "state": "succeeded", "source_revision": project["revision"], "input_hash": input_hash(project),
                                  "result": {"packet_id": packet_id, "changed": changed, "file_ids": [row["id"] for row in new_files], "manifest_hash": manifest_hash}, "retry_advice": "none"}
                        if len(canonical(result).encode()) > self.limits["result_bytes"]:
                            raise StoreError("delivery_result_limit", "The operation result exceeds its storage limit.", 413)
                        db.execute("INSERT INTO delivery_packets (id,job_id,manifest_hash,body,created_at) VALUES (?,?,?,?,?)", (packet_id,job_id,manifest_hash,canonical(packet),now()))
                        db.execute("INSERT INTO delivery_operations (id,job_id,kind,operation_key,payload_digest,result) VALUES (?,?,?,?,?,?)", (result["operation_id"],job_id,"confirm_packet",operation_key,digest(payload),canonical(result)))
                    committed = True
                except BaseException:
                    # A commit exception is not proof of rollback. A separate
                    # connection may establish a committed operation; failed
                    # reconciliation retains all possibly registered bytes.
                    try:
                        with self.store.lock, self.store.connection() as check:
                            replay = self._replay(check, self._job(check, job_id, binding), "confirm_packet", operation_key, payload)
                            registered = {row["_path"] for entry in check.execute("SELECT body FROM projects") for row in json.loads(entry[0])["files"]}
                        if replay is not None:
                            result, committed = replay, True
                        else:
                            for path in created_paths:
                                if path.name not in registered: path.unlink(missing_ok=True)
                    except Exception:
                        raise StoreError("delivery_commit_unknown", "Packet outcome is unknown. Keep the same operation and inspect current status before retrying.") from None
                    if not committed:
                        raise
                if committed:
                    for path in old_paths:
                        try: path.unlink(missing_ok=True)
                        except OSError: pass
                    return result
