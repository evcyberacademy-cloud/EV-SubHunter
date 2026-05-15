"""DNS resolution utilities for EV-SubHunter."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

import dns.resolver

from config import DEFAULT_THREADS


ProgressCallback = Callable[[str, dict], None]


def resolve_host(hostname: str, timeout: float = 4.0) -> list[str]:
    """Resolve A records for a hostname and return IP addresses."""
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    answers = resolver.resolve(hostname, "A")
    return sorted({answer.address for answer in answers})


def resolve_subdomains(
    subdomains: set[str],
    *,
    threads: int = DEFAULT_THREADS,
    progress: ProgressCallback | None = None,
) -> dict[str, list[str]]:
    """Resolve subdomains concurrently and report live progress."""
    resolved: dict[str, list[str]] = {}
    total = len(subdomains)
    completed = 0

    def emit(event: str, payload: dict) -> None:
        if progress:
            progress(event, payload)

    if not subdomains:
        return resolved

    emit("status", {"message": f"Resolving DNS for {total} discovered hosts"})

    with ThreadPoolExecutor(max_workers=max(1, threads)) as executor:
        futures = {executor.submit(resolve_host, host): host for host in sorted(subdomains)}
        for future in as_completed(futures):
            host = futures[future]
            completed += 1
            try:
                ips = future.result()
                if ips:
                    resolved[host] = ips
                    emit("resolved", {"host": host, "ips": ips, "completed": completed, "total": total})
            except Exception:
                emit("unresolved", {"host": host, "completed": completed, "total": total})

    emit("status", {"message": f"Resolved {len(resolved)} hosts"})
    return resolved
