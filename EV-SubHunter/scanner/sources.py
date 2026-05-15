"""Passive subdomain sources used by EV-SubHunter.

Each source returns a set of hostnames. The module is intentionally defensive:
third-party services change often, so failures are captured and reported through
the progress callback instead of crashing the whole scan.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

import requests

from config import DEFAULT_TIMEOUT, USER_AGENT


ProgressCallback = Callable[[str, dict], None]

SUBDOMAIN_RE_TEMPLATE = r"(?:[a-zA-Z0-9_-]+\.)+{domain}"


class PassiveSourceError(Exception):
    """Raised when a passive source cannot be queried successfully."""


def normalize_domain(domain: str) -> str:
    """Return a clean domain name suitable for source lookups."""
    domain = domain.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "")
    return domain.split("/")[0].strip(".")


def extract_subdomains(text: str, domain: str) -> set[str]:
    """Extract and normalize subdomains for the requested domain."""
    escaped = re.escape(domain)
    pattern = re.compile(SUBDOMAIN_RE_TEMPLATE.format(domain=escaped), re.IGNORECASE)
    found = set()
    for match in pattern.findall(text or ""):
        host = match.lower().strip().strip("*.").rstrip(".")
        if host.endswith("." + domain) or host == domain:
            found.add(host)
    return found


def _request(url: str, *, params: dict | None = None, timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"}
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response


def query_crtsh(domain: str) -> set[str]:
    response = _request("https://crt.sh/", params={"q": f"%.{domain}", "output": "json"})
    results: set[str] = set()
    try:
        for item in response.json():
            value = item.get("name_value", "")
            results.update(extract_subdomains(value.replace("\\n", "\n"), domain))
    except ValueError:
        results.update(extract_subdomains(response.text, domain))
    return results


def query_threatcrowd(domain: str) -> set[str]:
    response = _request(
        "https://www.threatcrowd.org/searchApi/v2/domain/report/",
        params={"domain": domain},
    )
    results: set[str] = set()
    data = response.json()
    for host in data.get("subdomains", []) or []:
        results.update(extract_subdomains(str(host), domain))
    return results


def query_otx(domain: str) -> set[str]:
    response = _request(f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns")
    data = response.json()
    results: set[str] = set()
    for item in data.get("passive_dns", []) or []:
        hostname = item.get("hostname") or item.get("address") or ""
        results.update(extract_subdomains(str(hostname), domain))
    return results


def query_hackertarget(domain: str) -> set[str]:
    response = _request("https://api.hackertarget.com/hostsearch/", params={"q": domain})
    return extract_subdomains(response.text, domain)


def query_rapiddns(domain: str) -> set[str]:
    response = _request(f"https://rapiddns.io/subdomain/{domain}", params={"full": "1"})
    return extract_subdomains(response.text, domain)


SOURCES = {
    "crt.sh": query_crtsh,
    "ThreatCrowd": query_threatcrowd,
    "AlienVault OTX": query_otx,
    "HackerTarget": query_hackertarget,
    "RapidDNS": query_rapiddns,
}


def collect_subdomains(domain: str, progress: ProgressCallback | None = None) -> tuple[set[str], dict[str, str]]:
    """Query all passive sources in parallel and return deduplicated subdomains."""
    domain = normalize_domain(domain)
    all_results: set[str] = set()
    source_status: dict[str, str] = {}

    def emit(event: str, payload: dict) -> None:
        if progress:
            progress(event, payload)

    emit("status", {"message": f"Starting passive source collection for {domain}"})

    with ThreadPoolExecutor(max_workers=len(SOURCES)) as executor:
        futures = {executor.submit(func, domain): name for name, func in SOURCES.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results = future.result()
                all_results.update(results)
                source_status[name] = f"ok:{len(results)}"
                emit("source_done", {"source": name, "count": len(results)})
            except Exception as exc:  # Third-party source failures should not kill the scan.
                source_status[name] = f"error:{exc.__class__.__name__}"
                emit("source_error", {"source": name, "error": str(exc)})

    cleaned = {host for host in all_results if host.endswith("." + domain)}
    emit("status", {"message": f"Collected {len(cleaned)} unique subdomains"})
    return cleaned, source_status
