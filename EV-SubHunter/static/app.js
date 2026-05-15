const scanForm = document.querySelector("#scanForm");
const domainInput = document.querySelector("#domainInput");
const threadsInput = document.querySelector("#threadsInput");
const wordlistInput = document.querySelector("#wordlistInput");
const wordlistFile = document.querySelector("#wordlistFile");
const scanButton = document.querySelector("#scanButton");
const statusPill = document.querySelector("#statusPill");
const foundCount = document.querySelector("#foundCount");
const resolvedCount = document.querySelector("#resolvedCount");
const progressText = document.querySelector("#progressText");
const targetText = document.querySelector("#targetText");
const progressBar = document.querySelector("#progressBar");
const consoleOutput = document.querySelector("#consoleOutput");
const scannerDot = document.querySelector("#scannerDot");
const exportPath = document.querySelector("#exportPath");
const exportButton = document.querySelector("#exportButton");
const historyList = document.querySelector("#historyList");

let activeScanId = null;
let seenEvents = 0;
let pollTimer = null;

function addConsoleLine(text, className = "") {
  if (consoleOutput.querySelector(".console-muted")) {
    consoleOutput.innerHTML = "";
  }
  const line = document.createElement("p");
  line.textContent = text;
  if (className) line.className = className;
  consoleOutput.appendChild(line);
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function eventText(item) {
  const payload = item.payload || {};
  if (item.event === "found") return `[FOUND] ${payload.host} #${payload.count}`;
  if (item.event === "resolved") return `[RESOLVED] ${payload.host} --> ${(payload.ips || []).join(", ")}`;
  if (item.event === "source_done") return `[SOURCE] ${payload.source} returned ${payload.count} hosts`;
  if (item.event === "source_error") return `[WARN] ${payload.source} unavailable: ${payload.error}`;
  if (item.event === "wordlist_done") return `[WORDLIST] ${payload.resolved}/${payload.candidates} custom candidates resolved`;
  if (item.event === "complete") return `[DONE] ${payload.message}`;
  if (item.event === "error") return `[ERROR] ${payload.message}`;
  if (payload.message) return `[INFO] ${payload.message}`;
  return `[${item.event.toUpperCase()}] ${JSON.stringify(payload)}`;
}

function updateScanUI(scan) {
  statusPill.textContent = scan.status;
  targetText.textContent = scan.target || "-";
  foundCount.textContent = scan.found || scan.subdomains.length || 0;
  resolvedCount.textContent = scan.resolved_count || Object.keys(scan.resolved || {}).length;
  progressText.textContent = `${scan.progress || 0}%`;
  progressBar.style.width = `${scan.progress || 0}%`;

  scan.events.slice(seenEvents).forEach((item) => addConsoleLine(eventText(item)));
  seenEvents = scan.events.length;

  if (scan.status === "running") {
    scannerDot.classList.add("active");
    scanButton.disabled = true;
  } else {
    scannerDot.classList.remove("active");
    scanButton.disabled = false;
  }

  if (scan.status === "complete" && scan.files && scan.files.subdomains) {
    exportPath.textContent = scan.files.subdomains;
    exportButton.href = `/export/${encodeURIComponent(scan.target)}`;
    exportButton.classList.remove("disabled");
    window.clearInterval(pollTimer);
    loadHistory();
  }

  if (scan.status === "error") {
    window.clearInterval(pollTimer);
  }
}

async function pollScan() {
  if (!activeScanId) return;
  const response = await fetch(`/api/scan/${activeScanId}`);
  if (!response.ok) {
    addConsoleLine("[ERROR] Unable to load scan status");
    window.clearInterval(pollTimer);
    return;
  }
  updateScanUI(await response.json());
}

async function loadHistory() {
  const response = await fetch("/api/history");
  if (!response.ok) return;
  const history = await response.json();
  historyList.innerHTML = "";

  if (!history.length) {
    historyList.innerHTML = `<p class="console-muted">No previous scans yet.</p>`;
    return;
  }

  history.forEach((item) => {
    const row = document.createElement("div");
    row.className = "history-item";
    const details = document.createElement("div");
    const target = document.createElement("strong");
    const meta = document.createElement("span");
    const actions = document.createElement("div");
    const exportLink = document.createElement("a");
    const deleteButton = document.createElement("button");
    const wordlistStats = item.wordlist_stats || {};
    const wordlistText = wordlistStats.enabled
      ? ` · wordlist ${wordlistStats.resolved}/${wordlistStats.candidates}`
      : "";

    target.textContent = item.target;
    meta.textContent = `${item.total_subdomains} found · ${item.resolved_hosts} resolved${wordlistText} · ${item.timestamp}`;
    exportLink.className = "secondary-button";
    exportLink.href = `/export/${encodeURIComponent(item.target)}`;
    exportLink.textContent = "Export";
    deleteButton.className = "danger-button";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => deleteTarget(item.target));

    details.append(target, meta);
    actions.className = "history-actions";
    actions.append(exportLink, deleteButton);
    row.append(details, actions);
    historyList.appendChild(row);
  });
}

async function deleteTarget(target) {
  const confirmed = window.confirm(`Delete saved results for ${target}?`);
  if (!confirmed) return;

  const response = await fetch(`/api/history/${encodeURIComponent(target)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    addConsoleLine(`[ERROR] Unable to delete ${target}`);
    return;
  }

  addConsoleLine(`[DELETE] Removed target node ${target}`);
  if (targetText.textContent === target) {
    exportPath.textContent = "Results deleted.";
    exportButton.classList.add("disabled");
    exportButton.href = "#";
  }
  loadHistory();
}

wordlistFile.addEventListener("change", async () => {
  const file = wordlistFile.files && wordlistFile.files[0];
  if (!file) return;
  const text = await file.text();
  wordlistInput.value = text;
  addConsoleLine(`[WORDLIST] Loaded ${file.name}`);
});

scanForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const domain = domainInput.value.trim();
  const threads = Number(threadsInput.value || 40);
  const wordlist = wordlistInput.value.trim();
  if (!domain) return;

  consoleOutput.innerHTML = "";
  addConsoleLine(`[INIT] Launching scan for ${domain}`);
  if (wordlist) addConsoleLine("[WORDLIST] Custom wordlist enabled");
  exportButton.classList.add("disabled");
  exportButton.href = "#";
  exportPath.textContent = "Scan running...";
  seenEvents = 0;

  const response = await fetch("/api/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain, threads, wordlist }),
  });

  const data = await response.json();
  if (!response.ok) {
    addConsoleLine(`[ERROR] ${data.error || "Unable to start scan"}`);
    return;
  }

  activeScanId = data.scan_id;
  scanButton.disabled = true;
  statusPill.textContent = "running";
  scannerDot.classList.add("active");
  window.clearInterval(pollTimer);
  pollTimer = window.setInterval(pollScan, 900);
  pollScan();
});

loadHistory();
