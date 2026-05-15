"""Custom wordlist support for EV-SubHunter.

The wordlist feature builds candidate hostnames and only keeps entries that
resolve. This keeps passive results clean while still supporting student labs
where instructors provide words like admin, dev, staging, and api.
"""

from __future__ import annotations

import re
from pathlib import Path

from scanner.sources import normalize_domain


LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$", re.IGNORECASE)


def parse_wordlist_text(text: str, domain: str, *, limit: int = 5000) -> set[str]:
    """Convert pasted wordlist text into candidate hostnames."""
    clean_domain = normalize_domain(domain)
    candidates: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip().lower()
        if not line or line.startswith("#"):
            continue
        line = line.replace("https://", "").replace("http://", "").split("/")[0].strip(".")
        if not line:
            continue

        if line.endswith("." + clean_domain):
            candidates.add(line)
        elif "." not in line and LABEL_RE.match(line):
            candidates.add(f"{line}.{clean_domain}")

        if len(candidates) >= limit:
            break

    return candidates


def parse_wordlist_file(path: str, domain: str, *, limit: int = 5000) -> set[str]:
    """Load a local wordlist file and return candidate hostnames."""
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    return parse_wordlist_text(text, domain, limit=limit)
