"""Result export helpers for EV-SubHunter."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from config import RESULTS_DIR
from scanner.sources import normalize_domain


def target_result_dir(domain: str) -> Path:
    """Return the result directory for a target and create it if needed."""
    clean_domain = normalize_domain(domain)
    path = RESULTS_DIR / clean_domain
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_results(
    domain: str,
    subdomains: set[str],
    resolved: dict[str, list[str]],
    source_status: dict[str, str] | None = None,
    wordlist_stats: dict | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> dict[str, str]:
    """Write scan outputs to the results directory."""
    clean_domain = normalize_domain(domain)
    out_dir = target_result_dir(clean_domain)
    now = datetime.now(timezone.utc).isoformat()
    finished = finished_at or now

    subdomain_file = out_dir / "subdomains.txt"
    resolved_file = out_dir / "resolved.json"
    metadata_file = out_dir / "metadata.json"

    subdomain_file.write_text("\n".join(sorted(subdomains)) + ("\n" if subdomains else ""), encoding="utf-8")
    resolved_file.write_text(json.dumps(resolved, indent=2, sort_keys=True), encoding="utf-8")

    metadata = {
        "target": clean_domain,
        "timestamp": finished,
        "started_at": started_at,
        "finished_at": finished,
        "total_subdomains": len(subdomains),
        "resolved_hosts": len(resolved),
        "source_status": source_status or {},
        "wordlist_stats": wordlist_stats or {"enabled": False, "candidates": 0, "resolved": 0},
        "files": {
            "subdomains": str(subdomain_file),
            "resolved": str(resolved_file),
            "metadata": str(metadata_file),
        },
    }
    metadata_file.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    history_file = RESULTS_DIR / "history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []
    history.insert(0, metadata)
    history_file.write_text(json.dumps(history[:25], indent=2), encoding="utf-8")

    return {
        "directory": str(out_dir),
        "subdomains": str(subdomain_file),
        "resolved": str(resolved_file),
        "metadata": str(metadata_file),
    }


def load_history(limit: int = 10) -> list[dict]:
    """Load recent scan history grouped as one node per target."""
    history_file = RESULTS_DIR / "history.json"
    if not history_file.exists():
        return []
    try:
        history = json.loads(history_file.read_text(encoding="utf-8"))
        nodes = []
        seen_targets = set()
        for item in history:
            target = item.get("target")
            if not target or target in seen_targets:
                continue
            seen_targets.add(target)
            nodes.append(item)
            if len(nodes) >= limit:
                break
        return nodes
    except json.JSONDecodeError:
        return []


def delete_target_results(domain: str) -> bool:
    """Delete a target result directory and remove it from history."""
    clean_domain = normalize_domain(domain)
    target_dir = (RESULTS_DIR / clean_domain).resolve()
    results_root = RESULTS_DIR.resolve()
    if results_root not in target_dir.parents:
        return False

    deleted = False
    if target_dir.exists():
        shutil.rmtree(target_dir)
        deleted = True

    history_file = RESULTS_DIR / "history.json"
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []
        filtered = [item for item in history if item.get("target") != clean_domain]
        history_file.write_text(json.dumps(filtered, indent=2), encoding="utf-8")
        deleted = True

    return deleted
