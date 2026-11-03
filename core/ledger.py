"""Append-only SQLite research snapshots with compare-and-swap updates."""
import copy
import json
import sqlite3
from datetime import datetime, timezone
from .research import ResearchError, analyze, canonical, digest, timestamp


def connect(path):
    db = sqlite3.connect(str(path), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript('''
    CREATE TABLE IF NOT EXISTS snapshots (
      seq INTEGER PRIMARY KEY, study TEXT NOT NULL, version INTEGER NOT NULL,
      previous_hash TEXT NOT NULL, hash TEXT NOT NULL UNIQUE, payload TEXT NOT NULL,
      created_at TEXT NOT NULL, UNIQUE(study,version));
    CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON snapshots BEGIN SELECT RAISE(ABORT,'append only'); END;
    CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON snapshots BEGIN SELECT RAISE(ABORT,'append only'); END;
    ''')
    return db


def records(db, study):
    return list(db.execute("SELECT * FROM snapshots WHERE study=? ORDER BY version", (study,)))


def unpack(row):
    return {"version": row["version"], "hash": row["hash"], "previous_hash": row["previous_hash"],
            "created_at": row["created_at"], **json.loads(row["payload"])}


def _append(db, bundle, parent, event):
    version = parent["version"] + 1 if parent else 1
    previous = parent["hash"] if parent else ""
    created = datetime.now(timezone.utc).isoformat()
    payload = {"bundle": bundle, "analysis": analyze(bundle), "event": event}
    envelope = {"study": bundle["id"], "version": version, "previous_hash": previous,
                "created_at": created, "payload": payload}
    h = digest(envelope)
    db.execute("INSERT INTO snapshots(study,version,previous_hash,hash,payload,created_at) VALUES(?,?,?,?,?,?)",
               (bundle["id"], version, previous, h, canonical(payload), created))
    return unpack(db.execute("SELECT * FROM snapshots WHERE hash=?", (h,)).fetchone())


def freeze(db, bundle):
    analyze(bundle)
    with db:
        db.execute("BEGIN IMMEDIATE")
        rows = records(db, bundle["id"])
        if rows:
            latest = unpack(rows[-1])
            if digest(latest["bundle"]) == digest(bundle):
                return latest
            raise ResearchError("Study exists. Revise it with the current version; do not overwrite history.")
        return _append(db, bundle, None, {"type": "freeze"})


def revise(db, bundle, expected_version, reason):
    analyze(bundle)
    if not isinstance(reason, str) or not reason.strip():
        raise ResearchError("Revision requires a reason")
    with db:
        db.execute("BEGIN IMMEDIATE")
        rows = records(db, bundle["id"])
        if not rows:
            raise ResearchError("Unknown study")
        parent = rows[-1]
        old = unpack(parent)["bundle"]
        if parent["version"] != expected_version:
            raise ResearchError("Version conflict: reload the latest research before revising")
        if timestamp(bundle["cutoff"]) < timestamp(old["cutoff"]):
            raise ResearchError("A revision cannot move the cutoff backward; create a separate study")
        if digest(old) == digest(bundle):
            return unpack(parent)
        return _append(db, bundle, parent, {"type": "revision", "reason": reason})


def update_evidence(db, study, event, expected_version):
    """Events replace one evidence item; dependent values become unavailable on withdrawal."""
    required = ("id", "evidence_id", "expected_evidence_hash", "cutoff", "replacement", "reason")
    if not isinstance(event, dict) or any(k not in event for k in required):
        raise ResearchError("Incomplete evidence event")
    if not isinstance(event["id"], str) or not event["id"].strip() or not isinstance(event["reason"], str) or not event["reason"].strip():
        raise ResearchError("Evidence event requires an ID and reason")
    with db:
        db.execute("BEGIN IMMEDIATE")
        rows = records(db, study)
        if not rows:
            raise ResearchError("Unknown study")
        for row in rows:
            previous_event = unpack(row)["event"]
            if previous_event.get("id") == event["id"]:
                if previous_event != {"type": "evidence_update", **event}:
                    raise ResearchError("Event ID reused with different content")
                return unpack(row)
        parent = rows[-1]
        if parent["version"] != expected_version:
            raise ResearchError("Version conflict: reload the latest research before updating")
        bundle = copy.deepcopy(unpack(parent)["bundle"])
        if timestamp(event["cutoff"]) < timestamp(bundle["cutoff"]):
            raise ResearchError("An update cannot move the cutoff backward")
        for i, ev in enumerate(bundle["evidence"]):
            if ev["id"] == event["evidence_id"]:
                if digest(ev) != event["expected_evidence_hash"]:
                    raise ResearchError("Evidence version conflict")
                replacement = event["replacement"]
                if not isinstance(replacement, dict) or replacement.get("id") != ev["id"] or replacement.get("version") == ev["version"]:
                    raise ResearchError("Replacement must preserve ID and change version")
                # New source versions never silently inherit approval of the old economics.
                if replacement.get("status") == "active":
                    raise ResearchError("Active replacement requires a full revised bundle and explicit model review")
                bundle["evidence"][i] = replacement
                break
        else:
            raise ResearchError("Unknown evidence ID")
        bundle["cutoff"] = event["cutoff"]
        return _append(db, bundle, parent, {"type": "evidence_update", **event})


def verify(db):
    studies = [r[0] for r in db.execute("SELECT DISTINCT study FROM snapshots")]
    count = 0
    for study in studies:
        previous = ""
        for version, row in enumerate(records(db, study), 1):
            payload = json.loads(row["payload"])
            envelope = {"study": study, "version": version, "previous_hash": previous,
                        "created_at": row["created_at"], "payload": payload}
            if row["version"] != version or row["previous_hash"] != previous or row["hash"] != digest(envelope):
                raise ResearchError("Ledger integrity check failed")
            if payload["bundle"]["id"] != study or analyze(payload["bundle"]) != payload["analysis"]:
                raise ResearchError("Stored analysis does not reproduce")
            previous = row["hash"]
            count += 1
    return {"status": "VERIFIED", "studies": len(studies), "snapshots": count,
            "boundary": "Local consistency, not protection from an administrator rewriting the entire database."}


def diff(before, after, path=""):
    if isinstance(before, dict) and isinstance(after, dict):
        changes = []
        for key in sorted(set(before) | set(after)):
            p = path + "/" + key
            if key not in before:
                changes.append({"path": p, "change": "added", "after": after[key]})
            elif key not in after:
                changes.append({"path": p, "change": "removed", "before": before[key]})
            else:
                changes.extend(diff(before[key], after[key], p))
        return changes
    return [] if before == after else [{"path": path, "change": "changed", "before": before, "after": after}]
