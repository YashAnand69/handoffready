"""Validate and stage an allowlisted recorded checkpoint page; never deploy it.

Recorded facts are supplied explicitly by the capture operator. This builder
checks shape, asset integrity, source provenance and immutable-record equality;
it cannot establish the semantic correctness of a claim or a genuine trial.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/replay"
STAGES = ["brief", "review", "correct", "rereview", "snapshots"]
ASSET = re.compile(r"(?:records/(?:before|after)\.(?:json|html|md)|records/before-verified-again\.json|captures/[a-zA-Z0-9_-]+\.(?:png|jpg|jpeg))\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
PRIVATE_FIELDS = {"token", "server_key", "api_key", "internal_decision_note", "human_note", "source_span", "source_text", "brief", "text", "quote", "model", "decision_history", "proposal_history", "baseline_history"}
EXPORT_FIELDS = {"schema_version", "id", "project_name", "created_at", "source_revision", "input_hash", "baseline_hash", "status", "attention_summary", "requirements", "gaps", "files", "scope_notice", "originals_notice", "snapshot_hash"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or not value.keys() <= set(required) | set(optional):
        raise ValueError("Recorded manifest has missing or non-allowlisted fields.")


def string(value, bound=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > bound:
        raise ValueError("Recorded text must be a nonempty bounded string.")


def hash_value(value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise ValueError("Expected an exact SHA-256 digest.")


def date(value):
    string(value, 100)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Recording timestamps require a timezone.")


def private_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.startswith("_") or key in PRIVATE_FIELDS:
                raise ValueError(f"Private/non-client field in recorded artifact: {key}")
            private_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            private_keys(nested)


class RecordedHTML(HTMLParser):
    """Delivery records are text/CSS only, without active or remote content."""
    allowed_tags = {"html", "head", "meta", "title", "style", "body", "main", "header", "p", "h1", "h2", "h3", "span", "div", "strong", "section", "ul", "li", "code", "footer", "details", "summary", "br"}
    allowed_attributes = {"lang", "open", "charset", "content", "name", "class"}

    def handle_starttag(self, tag, attributes):
        if tag not in self.allowed_tags or any(key not in self.allowed_attributes for key, value in attributes):
            raise ValueError("Active/network HTML is not an allowlisted recorded client projection.")
        if tag == "meta" and any(key == "name" and value not in {"viewport", "description"} for key, value in attributes):
            raise ValueError("Unknown metadata in recorded client projection.")

    def handle_data(self, data):
        if re.search(r"@import|url\s*\(", data, flags=re.IGNORECASE):
            raise ValueError("Remote/active CSS is not an allowlisted recorded client projection.")


def safe_file(base: Path, name: str) -> Path:
    path = base / name
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(base.resolve()):
        raise ValueError(f"Missing, linked or out-of-scope recorded asset: {name}")
    return path


def validate(data_path: Path) -> tuple[dict, dict[str, Path]]:
    if data_path.is_symlink() or data_path.stat().st_size > 256 * 1024:
        raise ValueError("Recorded manifest exceeds its bound or is linked.")
    data = json.loads(data_path.read_text())
    fields(data, ["version", "recorded_at", "sample_id", "actor", "prompt_version", "catalog_version", "source", "checkpoints", "snapshots", "comparison", "assets"])
    if data["version"] != "recorded-checkpoints-v1" or data["actor"] != "agent-operated synthetic demo":
        raise ValueError("Unknown recording version or incorrect actor disclosure.")
    date(data["recorded_at"])
    for key in ("sample_id", "prompt_version", "catalog_version"):
        string(data[key], 160)
    if not data["sample_id"].lower().startswith("synthetic"):
        raise ValueError("Sample identity must visibly identify its synthetic scope.")
    source = data["source"]
    fields(source, ["base_commit", "label", "module_sha256"])
    if not isinstance(source["base_commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", source["base_commit"]):
        raise ValueError("Base commit must be an existing Git commit SHA.")
    subprocess.run(["git", "cat-file", "-e", source["base_commit"] + "^{commit}"], cwd=ROOT, check=True, capture_output=True)
    if source["label"] != "base commit + local module hashes":
        raise ValueError("Uncommitted source must not be represented as a new Git commit.")
    if not isinstance(source["module_sha256"], dict) or not 1 <= len(source["module_sha256"]) <= 150:
        raise ValueError("Expected bounded candidate source module hashes.")
    for name, expected in source["module_sha256"].items():
        if not isinstance(name, str) or not re.fullmatch(r"(?:backend/handoffready|frontend/src)/[a-zA-Z0-9_/.-]+\.(?:py|ts|tsx|css)", name) or ".." in Path(name).parts:
            raise ValueError("Only candidate app source modules belong in the source identity.")
        hash_value(expected)
        if sha(safe_file(ROOT, name).read_bytes()) != expected:
            raise ValueError(f"Source changed since recorded capture: {name}")
    if not isinstance(data["checkpoints"], list) or len(data["checkpoints"]) != 5:
        raise ValueError("The recorded walkthrough needs exactly five checkpoints.")
    for index, checkpoint in enumerate(data["checkpoints"]):
        fields(checkpoint, ["id", "title", "summary", "facts", "findings"], ["screenshot"])
        if checkpoint["id"] != STAGES[index]:
            raise ValueError("Checkpoint order must follow the actual correction workflow.")
        string(checkpoint["title"], 180)
        string(checkpoint["summary"])
        if not isinstance(checkpoint["facts"], list) or len(checkpoint["facts"]) > 12:
            raise ValueError("Facts must be a bounded list.")
        for fact in checkpoint["facts"]:
            string(fact)
        if not isinstance(checkpoint["findings"], list) or len(checkpoint["findings"]) > 12:
            raise ValueError("Findings must be a bounded list.")
        for finding in checkpoint["findings"]:
            fields(finding, ["title", "status", "detail"])
            string(finding["title"], 180)
            string(finding["detail"])
            if finding["status"] not in {"pass", "fail", "unknown", "note"}:
                raise ValueError("Unknown recorded finding status.")
        if "screenshot" in checkpoint and not re.fullmatch(r"captures/[a-zA-Z0-9_-]+\.(?:png|jpg|jpeg)", checkpoint["screenshot"]):
            raise ValueError("Screenshot must be an allowlisted local capture.")
    fields(data["snapshots"], ["before", "after"])
    for descriptor in data["snapshots"].values():
        fields(descriptor, ["id", "created_at", "source_revision", "status", "snapshot_hash", "summary"])
        string(descriptor["id"], 100)
        date(descriptor["created_at"])
        string(descriptor["summary"])
        hash_value(descriptor["snapshot_hash"])
        if type(descriptor["source_revision"]) is not int or descriptor["source_revision"] < 1 or descriptor["status"] not in {"draft_with_gaps", "reviewed_with_exceptions", "reviewed"}:
            raise ValueError("Snapshot revision/state is invalid.")
    comparison = data["comparison"]
    fields(comparison, ["summary", "old_snapshot_unchanged", "originals_notice"], ["unchanged_artifact"])
    string(comparison["summary"])
    string(comparison["originals_notice"])
    if "original" not in comparison["originals_notice"].lower() or type(comparison["old_snapshot_unchanged"]) is not bool:
        raise ValueError("Original-file and immutability boundaries must be explicit.")
    if not isinstance(data["assets"], dict) or not 6 <= len(data["assets"]) <= 30:
        raise ValueError("Recorded assets must use a bounded allowlist.")
    assets = {}
    for name, expected in data["assets"].items():
        if not isinstance(name, str) or not ASSET.fullmatch(name):
            raise ValueError("Recorded asset path/type is not allowlisted.")
        hash_value(expected)
        path = safe_file(data_path.parent, name)
        if path.stat().st_size > 12 * 1024 * 1024 or sha(path.read_bytes()) != expected:
            raise ValueError(f"Recorded asset exceeds its bound or changed: {name}")
        assets[name] = path
    for which in ("before", "after"):
        for extension in ("json", "html", "md"):
            if f"records/{which}.{extension}" not in assets:
                raise ValueError("All three exact snapshot formats are required.")
        recorded = json.loads(assets[f"records/{which}.json"].read_text())
        fields(recorded, EXPORT_FIELDS)
        private_keys(recorded)
        if "synthetic" not in recorded["project_name"].lower():
            raise ValueError("Detached snapshot needs a visible synthetic-project designation.")
        for key in ("id", "created_at", "source_revision", "status", "snapshot_hash"):
            if recorded[key] != data["snapshots"][which][key]:
                raise ValueError(f"Snapshot descriptor differs from actual recorded artifact: {which}/{key}")
        original = {key: value for key, value in recorded.items() if key != "snapshot_hash"}
        canonical = json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if sha(canonical) != recorded["snapshot_hash"]:
            raise ValueError("Recorded snapshot digest is not its canonical projection identity.")
        # Historical rendered records remain their exact captured bytes. Check
        # their identity and text-only safety, not equality to a later renderer.
        for extension in ("html", "md"):
            rendered = assets[f"records/{which}.{extension}"].read_text()
            if recorded["id"] not in rendered or recorded["input_hash"] not in rendered or recorded["baseline_hash"] not in rendered:
                raise ValueError("Rendered artifact does not identify its recorded snapshot.")
            if extension == "html":
                RecordedHTML().feed(rendered)

    if data["snapshots"]["before"]["id"] == data["snapshots"]["after"]["id"]:
        raise ValueError("A replacement and fresh review must create a distinct new snapshot.")
    for checkpoint in data["checkpoints"]:
        if "screenshot" in checkpoint and checkpoint["screenshot"] not in assets:
            raise ValueError("Screenshot bytes are missing from the reviewed allowlist.")
    if comparison["old_snapshot_unchanged"]:
        if comparison.get("unchanged_artifact") != "records/before-verified-again.json" or comparison["unchanged_artifact"] not in assets:
            raise ValueError("Immutable history needs the exact later-downloaded earlier record.")
        if assets["records/before.json"].read_bytes() != assets[comparison["unchanged_artifact"]].read_bytes():
            raise ValueError("Earlier snapshot bytes changed after correction.")
    return data, assets


def build(data_path: Path, output: Path) -> dict:
    if data_path.is_symlink():
        raise ValueError("Recorded manifest must not be a symbolic link.")
    data_path, output = data_path.resolve(), output.resolve()
    if output.is_relative_to(data_path.parent) or output.is_relative_to(PAGE) or data_path.parent.is_relative_to(output) or ROOT == output or ROOT.is_relative_to(output):
        raise ValueError("Use a separate staging directory that cannot overwrite source/recorded evidence.")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Staging directory must be empty; never silently reuse stale public assets.")
    data, assets = validate(data_path)
    output.mkdir(parents=True, exist_ok=True)
    copied = {}
    for name in ("index.html", "replay.css", "replay.js"):
        path = safe_file(PAGE, name)
        if path.stat().st_size > 128 * 1024:
            raise ValueError("Static page exceeded its bound.")
        shutil.copyfile(path, output / name)
        copied[name] = sha(path.read_bytes())
    shutil.copyfile(data_path, output / "data.json")
    copied["data.json"] = sha(data_path.read_bytes())
    for name, path in assets.items():
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        copied[name] = sha(path.read_bytes())
    (output / ".nojekyll").write_text("")
    receipt = {"kind": "validated-static-recorded-checkpoints", "disclosure": "Synthetic packet; agent-operated recorded run; no browser inference", "recorded_at": data["recorded_at"], "sample_id": data["sample_id"], "prompt_version": data["prompt_version"], "source": data["source"], "old_snapshot_unchanged": data["comparison"]["old_snapshot_unchanged"], "file_sha256": copied}
    (output / "replay-verification.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    return {"output": str(output), "asset_count": len(assets), "checkpoint_count": len(data["checkpoints"]), "data_sha256": copied["data.json"], "old_snapshot_unchanged": data["comparison"]["old_snapshot_unchanged"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=PAGE / "data.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.data, args.output), indent=2))


if __name__ == "__main__":
    main()
