<p align="center">
  <img src="https://img.shields.io/badge/EV--CYBER--ACADEMY-Premium%20Recon%20Toolkit-red?style=for-the-badge">
</p>

<h1 align="center">EV-SubHunter</h1>

<p align="center">
  Production-Style Passive Subdomain Enumeration Toolkit
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?style=flat-square">
  <img src="https://img.shields.io/badge/Platform-Kali%20Linux-black?style=flat-square">
  <img src="https://img.shields.io/badge/Framework-Flask-green?style=flat-square">
  <img src="https://img.shields.io/badge/Founder-VimalTheHacker-red?style=flat-square">
</p>

---

# 🔥 EV-SubHunter

**EV-CYBER-ACADEMY** premium educational reconnaissance toolkit  
Founder: **VimalTheHacker**

EV-SubHunter is a modern production-style student toolkit for passive subdomain enumeration in:

- Cybersecurity labs
- CTF environments
- Authorized bug bounty learning
- Reconnaissance demonstrations

The project includes:
- ⚡ Premium Terminal Scanner
- 🌐 Modern Flask Web Dashboard
- 📊 Live Progress Tracking
- 💾 Export System
- 📁 Results History

> ⚠️ Legal use only: run this tool only against systems you own, lab targets, CTF scopes, or bug bounty programs where you have explicit authorization.

---

# ✨ Highlights

- 🎯 Animated terminal CLI
- 🌐 Password-protected web dashboard
- 📡 Passive recon sources
- ⚡ Multi-threaded collection
- 🧠 Automatic deduplication
- 🌍 DNS resolution checking
- 📊 Live scan progress
- 💾 Automatic exports
- 📁 Organized results history
- 🎨 Premium cybersecurity UI
- 🐍 Beginner-readable Python code
- 🛡️ Kali Linux compatible

---


---

# 📂 Project Structure

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

---

# ⚡ Installation

```bash
chmod +x start.sh
./start.sh
```

Launcher Menu:

```text
1) Launch Web Dashboard
2) Launch Terminal CLI
3) Install/Update Dependencies
```

The launcher automatically:
- Creates `.venv`
- Installs dependencies
- Avoids Kali Linux PEP 668 issues

---

# 🌐 Web Dashboard

Start dashboard:

```bash
./start.sh
```

Choose:

```text
1) Launch Web Dashboard
```

Open browser:

```text
http://127.0.0.1:5000
```

Default Password:

```text
adminsubhunter
```

Change password:

```bash
export EVSUBHUNTER_PASSWORD="your-strong-password"
./start.sh
```

---

# 💻 Terminal Usage

Interactive Mode:

```bash
./start.sh
```

Direct CLI Mode:

```bash
source .venv/bin/activate
python subhunter.py -d example.com -t 40
```

With Custom Wordlist:

```bash
python subhunter.py -d example.com -w wordlist.txt -t 40
```

---

# 📡 Example Output

```text
[FOUND] api.example.com #1
[FOUND] dev.example.com #2
[RESOLVED] admin.example.com --> 104.x.x.x
```

---

# 📁 Results System

Every scan is automatically saved:

```text
results/target.com/subdomains.txt
results/target.com/resolved.json
results/target.com/metadata.json
results/history.json
```

Stored metadata includes:
- Target
- Timestamp
- Total subdomains
- Resolved hosts
- Source status
- Export paths

Dashboard Features:
- Export results
- Delete scan history
- Grouped target history

---

# ⚙️ Configuration

Environment Variables:

```text
EVSUBHUNTER_PASSWORD       Dashboard password
EVSUBHUNTER_SECRET_KEY     Flask session secret
EVSUBHUNTER_HOST           Dashboard host
EVSUBHUNTER_PORT           Dashboard port
EVSUBHUNTER_THREADS        Default resolver threads
EVSUBHUNTER_TIMEOUT        HTTP timeout
```

---

# 🧠 Educational Scope

EV-SubHunter performs:
- Passive reconnaissance
- DNS resolution
- Educational automation

The tool DOES NOT include:
- Exploitation
- Account attacks
- Takeover automation
- Intrusive scanning
- Destructive functionality

Approved environments:
- Cybersecurity labs
- CTF targets
- Owned infrastructure
- Authorized bug bounty scopes
- Classroom demonstrations

---

# 👨‍💻 Credits

Built for **EV-CYBER-ACADEMY** students.

Founder: **VimalTheHacker**

---

<p align="center">
  Made for Practical Cybersecurity Learning 🚀
</p>
