"""Shot 2: OpenCode trajectory capture. Stdlib only. Read-only DB access.

Pipeline: probe -> load (export JSON preferred, or read-only sqlite) ->
redact -> normalize to trajectory.v1 -> canonical bytes + sha256 -> JSONL.
"""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

from src.redact import redact

SCHEMA_VERSION = "1.0"

# ponytail: residual secret check after redact(); extend patterns here if FPs/FNs matter.
_SECRET_RESIDUAL = [
    re.compile(r"sk-[A-Za-z0-9-_]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def _resolve_bin(name):
    import shutil  # ponytail: stdlib which; npm shims need .cmd on win32
    found = shutil.which(name) or shutil.which(name + ".cmd")
    if found:
        return found
    for d in (os.path.expandvars(r"%APPDATA%\npm"), r"C:\Users\pithu\AppData\Roaming\npm"):
        for ext in ("", ".cmd", ".ps1", ".exe"):
            c = os.path.join(d, name + ext)
            if c and os.path.exists(c):
                return c
    return name


def probe(opencode_bin="opencode"):
    """Real OpenCode compatibility probe. Returns version/db/export support."""
    opencode_bin = _resolve_bin(opencode_bin)
    out = {"opencode_bin": opencode_bin}
    try:
        r = subprocess.run([opencode_bin, "--version"], capture_output=True,
                           text=True, timeout=30)
        out["opencode_version"] = (r.stdout or r.stderr or "").strip().splitlines()
        out["opencode_version"] = out["opencode_version"][0] if out["opencode_version"] else "unknown"
    except Exception as e:  # pragma: no cover - env dependent
        out["opencode_version"] = f"unavailable: {e}"
    try:
        r = subprocess.run([opencode_bin, "db", "path"], capture_output=True,
                           text=True, timeout=30)
        out["db_path"] = (r.stdout or "").strip().splitlines()[0]
    except Exception as e:
        out["db_path"] = f"unavailable: {e}"
    try:
        r = subprocess.run([opencode_bin, "export", "--help"], capture_output=True,
                           text=True, timeout=30)
        out["export_sanitize"] = "--sanitize" in (r.stdout or "") + (r.stderr or "")
    except Exception:
        out["export_sanitize"] = False
    return out


def open_ro(db_path):
    """Read-only open. Never writes to opencode.db."""
    return sqlite3.connect("file:" + db_path + "?mode=ro", uri=True)


def load_session(db_path, session_id):
    """Load one session + messages + parts via read-only sqlite3."""
    con = open_ro(db_path)
    con.row_factory = sqlite3.Row
    try:
        s = con.execute("SELECT id, title, agent, model, directory, time_created"
                        " FROM session WHERE id=?", (session_id,)).fetchone()
        if s is None:
            raise ValueError(f"session not found: {session_id}")
        session = dict(s)
        messages = []
        for m in con.execute("SELECT id, data FROM message WHERE session_id=? ORDER BY rowid",
                             (session_id,)):
            d = json.loads(m["data"])
            d["_id"] = m["id"]
            messages.append(d)
        parts = []
        for p in con.execute("SELECT id, message_id, data FROM part WHERE session_id=? ORDER BY rowid",
                             (session_id,)):
            d = json.loads(p["data"])
            d["_id"] = p["id"]
            d["_message_id"] = p["message_id"]
            parts.append(d)
        perms = [dict(r) for r in con.execute(
            "SELECT action, resource FROM permission WHERE project_id IN"
            " (SELECT project_id FROM session WHERE id=?)", (session_id,))]
        return {"session": session, "messages": messages, "parts": parts,
                "permissions": perms}
    finally:
        con.close()


def load_export_file(path):
    """Load `opencode export --sanitize` JSON. Handles {info, messages[]} shape."""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    head = d.get("info", d.get("session"))  # export uses info; fixture uses session
    if head is not None and "messages" in d:
        msgs, parts = [], []
        for m in d["messages"]:
            info = m.get("info", m)
            for p in m.get("parts", []):
                p["_message_id"] = info.get("id", "")
                parts.append(p)
            msgs.append(info)
        return {"session": head, "messages": msgs, "parts": parts,
                "permissions": d.get("permissions", []), "export": True}
    return d  # already in loader shape


def _model_of(session):
    m = session.get("model", "")
    if isinstance(m, str) and m.strip().startswith("{"):  # sqlite stores JSON text
        try:
            m = json.loads(m)
        except json.JSONDecodeError:
            pass
    if isinstance(m, dict):
        return m.get("providerID", "opencode"), m.get("id", "unknown")
    return "opencode", str(m or "unknown")


def scan_residual(text):
    """Post-redaction secret scan. Returns matched pattern count (0 = clean)."""
    return sum(1 for rx in _SECRET_RESIDUAL if rx.search(text))


def normalize(record, source="opencode", license="MIT", opencode_version="",
              captured_at=None):
    """Normalize loader/export record to trajectory.v1 (redacted, deterministic)."""
    session = record.get("session", {})
    sid = str(session.get("id", "unknown"))
    provider, model = _model_of(session)
    by_msg = {}
    for p in record.get("parts", []):
        by_msg.setdefault(str(p.get("_message_id", "")), []).append(p)

    messages, tool_calls, errors = [], [], []
    for m in record.get("messages", []):
        role = str(m.get("role", "assistant"))
        texts = [p.get("text", "") for p in by_msg.get(str(m.get("id", m.get("_id", ""))), [])
                 if p.get("type") in ("text", "reasoning") and p.get("text")]
        content = redact("\n".join(texts)[:8000])
        messages.append({"role": role, "content": content})
        for p in by_msg.get(str(m.get("id", m.get("_id", ""))), []):
            t = p.get("type", "")
            if t == "tool":
                st = p.get("state", {}) if isinstance(p.get("state"), dict) else {}
                status = str(st.get("status", ""))
                err = redact(str(st.get("error", ""))[:2000]) if st.get("error") else ""
                # file changes / commands surface as tool calls (v1 has no sub-fields)
                tool_calls.append({
                    "call_id": str(p.get("callID", p.get("_id", ""))),
                    "name": redact(str(p.get("tool", "unknown"))),
                    "input": redact(json.dumps(st.get("input", {}), sort_keys=True)[:4000]),
                    "output": redact(str(st.get("output", st.get("title", "")))[:4000]),
                    "status": status,
                    "error": err,
                })
                if status == "error" or err:
                    errors.append(err or status)
            elif t == "patch":  # file diffs -> artifact-grade tool call
                tool_calls.append({
                    "call_id": str(p.get("_id", "")),
                    "name": "patch",
                    "input": "",
                    "output": redact(json.dumps(p.get("files", []), sort_keys=True)[:4000]),
                    "status": "done",
                    "error": "",
                })
            elif t == "step-finish" and str(p.get("reason", "")) not in ("", "stop", "tool"):
                errors.append(redact(str(p.get("reason", ""))[:500]))

    prov = {"source": source, "license": license, "session_id": sid,
            "opencode_version": str(opencode_version or session.get("version", "")),
            "sanitized": True,
            "captured_at": captured_at or datetime.now(timezone.utc).isoformat()}
    traj = {"session_id": sid, "schema_version": SCHEMA_VERSION,
            "provider": provider, "model": model,
            "messages": messages, "tool_calls": tool_calls,
            "test_result": None,
            "resolved": None,  # selection (Shot 3) decides
            "provenance": {"source": source, "license": license}}
    blob = canonical({"trajectory": traj, "provenance_full": prov,
                      "errors": errors, "permissions": record.get("permissions", [])})
    if scan_residual(blob.decode("utf-8", "replace")):
        raise ValueError("residual secret detected after redaction; refusing to emit")
    return traj, prov, errors


def canonical(obj):
    """Deterministic serialization: sorted keys, compact separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def to_artifact(trajectory_id, kind, content):
    body = redact(str(content))
    h = sha256(body.encode("utf-8"))
    return {"artifact_id": f"{trajectory_id}:{kind}:{h[:12]}",
            "trajectory_id": trajectory_id, "schema_version": SCHEMA_VERSION,
            "kind": kind, "sha256": h, "content_redacted": body,
            "provenance": {"source": "opencode", "license": "MIT"}}


def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(canonical(obj).decode("utf-8") + "\n")


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
