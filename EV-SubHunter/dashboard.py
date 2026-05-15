#!/usr/bin/env python3
"""Flask dashboard for EV-SubHunter."""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for

from config import APP_NAME, RESULTS_DIR, WEB_HOST, WEB_PASSWORD, WEB_PORT, WEB_SECRET_KEY
from scanner.exporter import delete_target_results, load_history, save_results
from scanner.resolver import resolve_subdomains
from scanner.sources import collect_subdomains, normalize_domain
from scanner.wordlist import parse_wordlist_text


app = Flask(__name__)
app.secret_key = WEB_SECRET_KEY

SCANS: dict[str, dict] = {}
SCAN_LOCK = threading.Lock()


def authenticated() -> bool:
    return bool(session.get("authenticated"))


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if password == WEB_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid password")
    if authenticated():
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not authenticated():
        return redirect(url_for("login"))
    return render_template("dashboard.html", app_name=APP_NAME)


def append_event(scan_id: str, event: str, payload: dict) -> None:
    with SCAN_LOCK:
        scan = SCANS.get(scan_id)
        if not scan:
            return
        item = {
            "event": event,
            "payload": payload,
            "time": datetime.now(timezone.utc).isoformat(),
        }
        scan["events"].append(item)
        scan["updated_at"] = item["time"]


def run_background_scan(scan_id: str, domain: str, threads: int, wordlist_text: str = "") -> None:
    clean_domain = normalize_domain(domain)
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()

    def progress(event: str, payload: dict) -> None:
        append_event(scan_id, event, payload)
        with SCAN_LOCK:
            scan = SCANS[scan_id]
            if event == "source_done":
                scan["sources_completed"] += 1
            elif event == "resolved":
                scan["resolved"][payload["host"]] = payload["ips"]
            elif event in {"resolved", "unresolved"}:
                scan["dns_completed"] = payload.get("completed", scan["dns_completed"])
                scan["dns_total"] = payload.get("total", scan["dns_total"])

    try:
        append_event(scan_id, "status", {"message": f"Scan started for {clean_domain}"})
        subdomains, source_status = collect_subdomains(clean_domain, progress=progress)
        wordlist_candidates = parse_wordlist_text(wordlist_text, clean_domain) if wordlist_text else set()
        wordlist_resolved: dict[str, list[str]] = {}

        if wordlist_candidates:
            append_event(
                scan_id,
                "status",
                {"message": f"Checking {len(wordlist_candidates)} custom wordlist candidates"},
            )
            wordlist_resolved = resolve_subdomains(wordlist_candidates, threads=threads, progress=progress)
            subdomains.update(wordlist_resolved.keys())
            append_event(
                scan_id,
                "wordlist_done",
                {"candidates": len(wordlist_candidates), "resolved": len(wordlist_resolved)},
            )

        with SCAN_LOCK:
            scan = SCANS[scan_id]
            scan["subdomains"] = sorted(subdomains)
            scan["found"] = len(subdomains)
            scan["dns_total"] = len(subdomains)

        for index, host in enumerate(sorted(subdomains), start=1):
            append_event(scan_id, "found", {"host": host, "count": index})

        resolved = resolve_subdomains(subdomains, threads=threads, progress=progress)
        resolved.update(wordlist_resolved)
        finished_at = datetime.now(timezone.utc).isoformat()
        files = save_results(
            clean_domain,
            subdomains,
            resolved,
            source_status=source_status,
            wordlist_stats={
                "enabled": bool(wordlist_candidates),
                "candidates": len(wordlist_candidates),
                "resolved": len(wordlist_resolved),
            },
            started_at=started_at,
            finished_at=finished_at,
        )

        with SCAN_LOCK:
            scan = SCANS[scan_id]
            scan["status"] = "complete"
            scan["files"] = files
            scan["elapsed"] = round(time.monotonic() - start, 2)
            scan["resolved"] = resolved
            scan["resolved_count"] = len(resolved)
        append_event(scan_id, "complete", {"message": "Scan complete", "files": files})
    except Exception as exc:
        with SCAN_LOCK:
            SCANS[scan_id]["status"] = "error"
            SCANS[scan_id]["error"] = str(exc)
        append_event(scan_id, "error", {"message": str(exc)})


@app.post("/api/scan")
def start_scan():
    if not authenticated():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    domain = normalize_domain(data.get("domain", ""))
    threads = int(data.get("threads", 40))
    wordlist_text = str(data.get("wordlist", ""))[:250_000]
    if not domain or "." not in domain:
        return jsonify({"error": "Enter a valid domain"}), 400

    scan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with SCAN_LOCK:
        SCANS[scan_id] = {
            "id": scan_id,
            "target": domain,
            "status": "running",
            "created_at": now,
            "updated_at": now,
            "events": [],
            "subdomains": [],
            "resolved": {},
            "found": 0,
            "resolved_count": 0,
            "dns_completed": 0,
            "dns_total": 0,
            "sources_completed": 0,
            "files": {},
            "elapsed": 0,
            "error": "",
            "wordlist_enabled": bool(wordlist_text.strip()),
        }

    thread = threading.Thread(
        target=run_background_scan,
        args=(scan_id, domain, max(1, threads), wordlist_text),
        daemon=True,
    )
    thread.start()
    return jsonify({"scan_id": scan_id})


@app.get("/api/scan/<scan_id>")
def scan_status(scan_id: str):
    if not authenticated():
        return jsonify({"error": "unauthorized"}), 401
    with SCAN_LOCK:
        scan = SCANS.get(scan_id)
        if not scan:
            return jsonify({"error": "scan not found"}), 404
        progress = 0
        if scan["dns_total"]:
            progress = int((scan["dns_completed"] / scan["dns_total"]) * 100)
        elif scan["sources_completed"]:
            progress = min(45, scan["sources_completed"] * 9)
        if scan["status"] == "complete":
            progress = 100
        payload = dict(scan)
        payload["progress"] = progress
    return jsonify(payload)


@app.get("/api/history")
def history():
    if not authenticated():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(load_history())


@app.delete("/api/history/<path:target>")
def delete_history_target(target: str):
    if not authenticated():
        return jsonify({"error": "unauthorized"}), 401
    safe_target = normalize_domain(target)
    deleted = delete_target_results(safe_target)
    return jsonify({"target": safe_target, "deleted": deleted})


@app.get("/export/<path:target>")
def export(target: str):
    if not authenticated():
        return redirect(url_for("login"))
    safe_target = normalize_domain(target)
    path = RESULTS_DIR / safe_target / "subdomains.txt"
    if not path.exists():
        return jsonify({"error": "export not found"}), 404
    return send_file(Path(path), as_attachment=True, download_name=f"{safe_target}-subdomains.txt")


if __name__ == "__main__":
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, threaded=True)
