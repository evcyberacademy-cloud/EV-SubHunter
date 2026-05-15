# EV-SubHunter

**EV-CYBER-ACADEMY** premium educational reconnaissance toolkit  
Founder: **VimalTheHacker**

EV-SubHunter is a production-style student toolkit for passive subdomain enumeration in cybersecurity labs, CTF environments, and authorized bug bounty learning. It includes a polished terminal scanner and a modern Flask dashboard with live progress, exports, and scan history.

> Legal use only: run this tool only against systems you own, lab targets, CTF scopes, or bug bounty programs where you have explicit authorization.

## Highlights

- Terminal CLI with animated ASCII banner, colored output, progress updates, counters, timer, and automatic exports
- Flask dashboard with password login, session handling, live scan console, progress bar, statistics cards, export panel, and recent history
- Passive sources: `crt.sh`, `ThreatCrowd`, `AlienVault OTX`, `HackerTarget`, and `RapidDNS`
- Multi-threaded passive source collection and DNS resolution
- Optional custom wordlist checking from the CLI or dashboard
- Automatic deduplication and resolved IP capture
- Kali, Ubuntu, and Debian friendly `.venv` launcher to avoid PEP 668 package issues
- Beginner-readable modular Python code

## Screenshots

Add product screenshots in the `screenshots/` directory:

- `screenshots/login.png`
- `screenshots/dashboard.png`
- `screenshots/cli.png`

## Project Structure

```text
EV-SubHunter/
├── subhunter.py
├── dashboard.py
├── requirements.txt
├── README.md
├── start.sh
├── config.py
├── scanner/
│   ├── sources.py
│   ├── resolver.py
│   └── exporter.py
├── templates/
│   ├── login.html
│   └── dashboard.html
├── static/
│   ├── style.css
│   ├── app.js
│   └── logo.png
├── results/
└── screenshots/
```

## Installation

```bash
chmod +x start.sh
./start.sh
```

Choose:

```text
1) Launch Web Dashboard
2) Launch Terminal CLI
3) Install/Update Dependencies
```

The launcher automatically creates `.venv` and installs dependencies inside it.

## Web Dashboard

Start the dashboard:

```bash
./start.sh
```

Select option `1`, then open:

```text
http://127.0.0.1:5000
```

Default password:

```text
adminsubhunter
```

Change the dashboard password:

```bash
export EVSUBHUNTER_PASSWORD="your-strong-password"
./start.sh
```

## Terminal Usage

Interactive launcher:

```bash
./start.sh
```

Direct CLI:

```bash
source .venv/bin/activate
python subhunter.py -d example.com -t 40
```

With a custom wordlist:

```bash
python subhunter.py -d example.com -w wordlist.txt -t 40
```

Example output:

```text
[FOUND] api.example.com #1
[FOUND] dev.example.com #2
[RESOLVED] admin.example.com --> 104.x.x.x
```

## Results

Every scan is saved automatically:

```text
results/target.com/subdomains.txt
results/target.com/resolved.json
results/target.com/metadata.json
results/history.json
```

Metadata includes the target, timestamp, total subdomains, resolved host count, source status, and file paths.

The dashboard history is grouped as one target node per domain. Use **Export** to download `subdomains.txt` or **Delete** to remove that target's saved results.

## Configuration

Environment variables:

```text
EVSUBHUNTER_PASSWORD       Dashboard password
EVSUBHUNTER_SECRET_KEY     Flask session secret
EVSUBHUNTER_HOST           Dashboard host, default 127.0.0.1
EVSUBHUNTER_PORT           Dashboard port, default 5000
EVSUBHUNTER_THREADS        Default DNS resolver threads
EVSUBHUNTER_TIMEOUT        HTTP source timeout
```

## Educational Scope

EV-SubHunter performs passive reconnaissance and DNS resolution only. It does not include exploitation, account attacks, takeover automation, destructive actions, or intrusive scanning modules.

Approved learning environments:

- Cybersecurity labs
- CTF targets
- Owned domains
- Authorized bug bounty scopes
- Classroom demonstrations

## Credits

Built for **EV-CYBER-ACADEMY** students.  
Founder: **VimalTheHacker**
