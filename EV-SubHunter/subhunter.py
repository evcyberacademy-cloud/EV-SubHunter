#!/usr/bin/env python3
"""Terminal CLI for EV-SubHunter."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone

from colorama import Fore, Style, init

from config import APP_NAME, FOUNDER, LEGAL_NOTICE, ORG_NAME
from scanner.exporter import save_results
from scanner.resolver import resolve_subdomains
from scanner.sources import collect_subdomains, normalize_domain
from scanner.wordlist import parse_wordlist_file


init(autoreset=True)


def banner() -> None:
    art = rf"""
{Fore.CYAN}    _______    __     _____       __    __            __           
{Fore.CYAN}   / ____/ |  / /    / ___/__  __/ /_  / /___  ______/ /____  _____
{Fore.BLUE}  / __/  | | / /_____\__ \/ / / / __ \/ __/ / / / __  / __ \/ ___/
{Fore.BLUE} / /___  | |/ /_____/__/ / /_/ / /_/ / /_/ /_/ / /_/ / /_/ / /    
{Fore.MAGENTA}/_____/  |___/     /____/\__,_/_.___/\__/\__,_/\__,_/\____/_/     
"""
    print(art)
    print(f"{Fore.WHITE}{Style.BRIGHT}{APP_NAME} {Fore.CYAN}| {ORG_NAME} | Founder: {FOUNDER}")
    print(f"{Fore.YELLOW}{LEGAL_NOTICE}\n")


def loading_screen() -> None:
    steps = [
        "Booting passive recon engine",
        "Loading premium source adapters",
        "Preparing DNS resolver threads",
        "Hardening timeout controls",
    ]
    for step in steps:
        print(f"{Fore.CYAN}[INIT]{Style.RESET_ALL} {step}", end="", flush=True)
        for _ in range(3):
            time.sleep(0.15)
            print(".", end="", flush=True)
        print(f" {Fore.GREEN}OK")


def format_seconds(seconds: float) -> str:
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"


def run_scan(domain: str, threads: int, wordlist_path: str | None = None) -> dict:
    clean_domain = normalize_domain(domain)
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    found_count = 0

    print(f"\n{Fore.WHITE}{Style.BRIGHT}[TARGET]{Style.RESET_ALL} {clean_domain}")
    print(f"{Fore.WHITE}{Style.BRIGHT}[THREADS]{Style.RESET_ALL} {threads}\n")

    def progress(event: str, payload: dict) -> None:
        nonlocal found_count
        if event == "status":
            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {payload['message']}")
        elif event == "source_done":
            print(f"{Fore.GREEN}[SOURCE]{Style.RESET_ALL} {payload['source']} returned {payload['count']} hosts")
        elif event == "source_error":
            print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} {payload['source']} unavailable: {payload['error']}")
        elif event == "resolved":
            ips = ", ".join(payload["ips"])
            completed = payload["completed"]
            total = payload["total"]
            print(f"{Fore.MAGENTA}[RESOLVED]{Style.RESET_ALL} {payload['host']} --> {ips} ({completed}/{total})")
        elif event == "unresolved":
            completed = payload["completed"]
            total = payload["total"]
            if completed % 10 == 0 or completed == total:
                print(f"{Fore.BLUE}[PROGRESS]{Style.RESET_ALL} DNS checked {completed}/{total}")

    subdomains, source_status = collect_subdomains(clean_domain, progress=progress)
    wordlist_candidates = parse_wordlist_file(wordlist_path, clean_domain) if wordlist_path else set()
    wordlist_resolved: dict[str, list[str]] = {}

    if wordlist_candidates:
        print(f"{Fore.CYAN}[WORDLIST]{Style.RESET_ALL} Checking {len(wordlist_candidates)} custom candidates")
        wordlist_resolved = resolve_subdomains(wordlist_candidates, threads=threads, progress=progress)
        subdomains.update(wordlist_resolved.keys())
        print(
            f"{Fore.GREEN}[WORDLIST]{Style.RESET_ALL} "
            f"{len(wordlist_resolved)}/{len(wordlist_candidates)} candidates resolved"
        )

    for host in sorted(subdomains):
        found_count += 1
        print(f"{Fore.GREEN}[FOUND]{Style.RESET_ALL} {host} {Fore.CYAN}#{found_count}")

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

    elapsed = time.monotonic() - start
    print(f"\n{Fore.WHITE}{Style.BRIGHT}+---------------- Scan Complete ----------------+")
    print(f"{Fore.GREEN}Found: {len(subdomains)} subdomains")
    print(f"{Fore.MAGENTA}Resolved: {len(resolved)} hosts")
    print(f"{Fore.CYAN}Timer: {format_seconds(elapsed)}")
    print(f"{Fore.YELLOW}Saved: {files['subdomains']}")
    print(f"{Fore.WHITE}{Style.BRIGHT}+-----------------------------------------------+\n")

    return {
        "target": clean_domain,
        "subdomains": subdomains,
        "resolved": resolved,
        "files": files,
        "elapsed": elapsed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EV-SubHunter - premium educational passive subdomain enumeration toolkit"
    )
    parser.add_argument("-d", "--domain", help="Target domain, example: example.com")
    parser.add_argument("-t", "--threads", type=int, default=40, help="DNS resolver threads")
    parser.add_argument("-w", "--wordlist", help="Optional custom wordlist file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    banner()
    loading_screen()

    domain = args.domain or input(f"{Fore.CYAN}Enter target domain: {Style.RESET_ALL}").strip()
    if not domain:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Target domain is required.")
        return 1

    try:
        run_scan(domain, max(1, args.threads), args.wordlist)
        return 0
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[STOPPED]{Style.RESET_ALL} Scan interrupted by user.")
        return 130
    except Exception as exc:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
