"""Central configuration for EV-SubHunter.

Values here are intentionally simple so students can understand and tune the
tool without hunting through the whole codebase.
"""

from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "EV-SubHunter"
ORG_NAME = "EV-CYBER-ACADEMY"
FOUNDER = "VimalTheHacker"

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"

DEFAULT_TIMEOUT = int(os.getenv("EVSUBHUNTER_TIMEOUT", "12"))
DEFAULT_THREADS = int(os.getenv("EVSUBHUNTER_THREADS", "40"))
USER_AGENT = os.getenv(
    "EVSUBHUNTER_USER_AGENT",
    "EV-SubHunter/1.0 Educational Recon Toolkit",
)

WEB_HOST = os.getenv("EVSUBHUNTER_HOST", "127.0.0.1")
WEB_PORT = int(os.getenv("EVSUBHUNTER_PORT", "5000"))
WEB_SECRET_KEY = os.getenv("EVSUBHUNTER_SECRET_KEY", "change-me-in-production")
WEB_PASSWORD = os.getenv("EVSUBHUNTER_PASSWORD", "adminsubhunter").strip()

LEGAL_NOTICE = (
    "Use EV-SubHunter only for CTFs, labs, and targets where you have explicit "
    "authorization. This toolkit performs passive reconnaissance only."
)
