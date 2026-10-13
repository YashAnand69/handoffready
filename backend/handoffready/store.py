import hashlib
import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .policy import INSPECTION_REVISION, LIMITS


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return uuid.uuid4().hex


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def input_hash(project):
    return digest({"brief": project["brief"]["sha256"] if project["brief"] else None, "baseline": project["baseline"]["hash"], "files": sorted([
        {"id": f["id"], "name": f["name"], "sha256": f["sha256"], "type": f["type"], "inspection": f["inspection"], "metadata": f["metadata"], "text_hash": hashlib.sha256(f["text"].encode()).hexdigest()}
        for f in project["files"]], key=lambda f: f["id"]), "inspector": INSPECTION_REVISION})


def invalidate(project):
    for decision in project["decisions"]:
        if decision["review_state"] != "stale":
            project.setdefault("decision_history", []).append(dict(decision))
        decision["review_state"] = "stale"
    if "decision_history" in project:
        project["decision_history"] = project["decision_history"][-200:]
    project["proposals"] = []


class StoreError(Exception):
    def __init__(self, code, message, status=409):
        self.code, self.message, self.status = code, message, status


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.directory, 0o700)
        self.files = self.directory / "files"
        self.files.mkdir(exist_ok=True, mode=0o700)
        self.lock = threading.RLock()
        self.database = self.directory / "handoff.sqlite3"
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, body TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS exports (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, json TEXT NOT NULL, md TEXT NOT NULL, html TEXT NOT NULL)")
        os.chmod(self.database, 0o600)
        with self.lock, self.connection() as db:
            for row in db.execute("SELECT id, body FROM projects").fetchall():
                project = json.loads(row[1])
                changed = False
                for job in project["jobs"]:
                    if job["state"] in {"queued", "running"}:
                        job.update(state="interrupted", stage="interrupted after restart", error="Restart interrupted this job. Retry explicitly.")
                        changed = True
                changed = self._reconcile_originals(project) or changed
                if changed:
                    project["revision"] += 1
                    db.execute("UPDATE projects SET body=? WHERE id=?", (canonical(project), row[0]))
            registered = {f["_path"] for row in db.execute("SELECT body FROM projects") for f in json.loads(row[0])["files"]}
            for path in self.files.iterdir():
                if path.name not in registered:
                    path.unlink(missing_ok=True)

    def _original_error(self, file):
        """Verify recorded identity without loading an unbounded original into memory."""
        path = self.files / file["_path"]
        try:
            if path.is_symlink() or not path.is_file():
                return "Stored original is unavailable. Replace the file before reviewing."
            if not 0 <= file["size"] <= LIMITS["file_bytes"] or path.stat().st_size != file["size"]:
                return "Stored original bytes changed. Replace the file before reviewing."
            sha, received = hashlib.sha256(), 0
            with path.open("rb") as original:
                while chunk := original.read(65536):
                    received += len(chunk)
                    if received > file["size"]:
                        return "Stored original bytes changed. Replace the file before reviewing."
                    sha.update(chunk)
            if received != file["size"] or sha.hexdigest() != file["sha256"]:
                return "Stored original bytes changed. Replace the file before reviewing."
        except OSError:
            return "Stored original is unavailable. Replace the file before reviewing."
        return None

    def _reconcile_originals(self, project):
        damaged = [(file, error) for file in project["files"] if (error := self._original_error(file))]
        changed = [(file, error) for file, error in damaged if file["inspection"] != "blocked" or file["metadata"] or file["text"] or file.get("error") != error]
        if not changed:
            return False
        if project["proposals"]:
            history = project.setdefault("proposal_history", [])
            history.append({"recorded_at": now(), "input_hash": input_hash(project), "proposals": json.loads(canonical(project["proposals"]))})
            project["proposal_history"] = history[-20:]
        for file, error in changed:
            # The expected identity is provenance; never replace it with damaged bytes.
            file.update(inspection="blocked", metadata={}, text="", error=error)
        invalidate(project)
        return True

    def reconcile_originals(self, project_id):
        """Recheck evidence before consuming it; a change advances the revision."""
        return self.mutate(project_id, None, lambda project, db: self._reconcile_originals(project))

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.database, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, project_id, db=None):
        if db is None:
            with self.connection() as connection:
                return self.get(project_id, connection)
        row = db.execute("SELECT body FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            raise StoreError("not_found", "Project no longer exists.", 404)
        return json.loads(row[0])

    def list(self):
        with self.connection() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT body FROM projects")]

    def create(self, name, limit):
        with self.lock, self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT count(*) FROM projects").fetchone()[0] >= limit:
                raise StoreError("project_limit", "Delete a project before creating another.")
            project = {"id": uid(), "name": name.strip(), "revision": 1, "brief": None,
                       "baseline": {"id": uid(), "state": "draft", "hash": digest([]), "requirements": []},
                       "files": [], "proposals": [], "decisions": [], "jobs": [], "exports": [], "created_at": now()}
            db.execute("INSERT INTO projects VALUES (?,?)", (project["id"], canonical(project)))
            return project

    def mutate(self, project_id, revision, callback):
        with self.lock, self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            project = self.get(project_id, db)
            if revision is not None and project["revision"] != revision:
                raise StoreError("revision_conflict", "The project changed. Refresh before saving.")
            before = canonical(project)
            callback(project, db)
            if canonical(project) != before:
                project["revision"] += 1
                db.execute("UPDATE projects SET body=? WHERE id=?", (canonical(project), project_id))
            return project

    def delete(self, project_id, revision):
        paths = []
        with self.lock, self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            project = self.get(project_id, db)
            if project["revision"] != revision:
                raise StoreError("revision_conflict", "The project changed. Refresh before deleting.")
            db.execute("DELETE FROM exports WHERE project_id=?", (project_id,))
            db.execute("DELETE FROM projects WHERE id=?", (project_id,))
            paths = [self.files / file["_path"] for file in project["files"]]
        # Commit registration removal first. An interrupted purge leaves orphans for
        # startup cleanup, never database pointers to already-deleted original bytes.
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def storage_size(self, db):
        return sum(f["size"] for row in db.execute("SELECT body FROM projects") for f in json.loads(row[0])["files"])
