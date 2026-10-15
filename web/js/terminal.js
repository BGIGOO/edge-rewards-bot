/**
 * web/js/terminal.js
 * ==================
 * Điều khiển giao diện Terminal Log: Phóng to/thu nhỏ/kéo thả, WebSocket stream và tải log.
 * Tuân thủ rule 01_architecture (< 250 dòng) và rule 03_web_fullstack.
 */

let terminalState = {
  mode: localStorage.getItem("terminal_mode") || "normal",
  customHeight: parseInt(localStorage.getItem("terminal_height"), 10) || 280,
  isDragging: false,
  startY: 0,
  startHeight: 0
};

function initTerminalControls() {
  if (!terminalSection || !terminalResizer) return;
  applyTerminalMode(terminalState.mode, terminalState.customHeight, false);

  btnCollapseTerminal?.addEventListener("click", (e) => { e.stopPropagation(); applyTerminalMode("collapsed"); });
  btnNormalTerminal?.addEventListener("click", (e) => { e.stopPropagation(); applyTerminalMode("normal", 280); });
  btnMaximizeTerminal?.addEventListener("click", (e) => { e.stopPropagation(); applyTerminalMode("maximized", 560); });

  terminalResizer.addEventListener("dblclick", () => {
    applyTerminalMode(terminalState.mode === "collapsed" ? "normal" : "collapsed", 280);
  });
  terminalCollapsedPreview?.addEventListener("click", () => applyTerminalMode("normal", 280));

  terminalResizer.addEventListener("mousedown", (e) => {
    terminalState.isDragging = true;
    terminalState.startY = e.clientY;
    terminalState.startHeight = terminalSection.getBoundingClientRect().height;
    document.body.style.cursor = "ns-resize";
    document.body.style.userSelect = "none";
    terminalSection.classList.add("resizing");
  });

  window.addEventListener("mousemove", (e) => {
    if (!terminalState.isDragging) return;
    const deltaY = terminalState.startY - e.clientY;
    let targetHeight = terminalState.startHeight + deltaY;

    if (targetHeight < 80) { applyTerminalMode("collapsed", 0, false); return; }
    if (targetHeight > 750) targetHeight = 750;

    terminalSection.classList.remove("collapsed");
    terminalCollapsedPreview?.classList.add("hidden");
    terminalSection.style.height = `${targetHeight}px`;
    terminalState.customHeight = targetHeight;
    updateSizeButtons("custom");
  });

  window.addEventListener("mouseup", () => {
    if (terminalState.isDragging) {
      terminalState.isDragging = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      terminalSection.classList.remove("resizing");

      const finalHeight = terminalSection.getBoundingClientRect().height;
      if (finalHeight > 80) {
        localStorage.setItem("terminal_height", finalHeight);
        localStorage.setItem("terminal_mode", "custom");
        terminalState.mode = "custom";
        terminalState.customHeight = finalHeight;
      }
    }
  });
}

function applyTerminalMode(mode, customHeight = 280, save = true) {
  if (!terminalSection) return;
  terminalSection.classList.remove("collapsed", "normal-size", "maximized", "custom", "resizing");

  if (mode === "collapsed") {
    terminalSection.classList.add("collapsed");
    terminalSection.style.height = "48px";
    terminalCollapsedPreview?.classList.remove("hidden");
  } else if (mode === "maximized") {
    terminalSection.classList.add("maximized");
    terminalSection.style.height = "560px";
    terminalCollapsedPreview?.classList.add("hidden");
  } else if (mode === "custom" && customHeight >= 100) {
    terminalSection.classList.add("custom");
    terminalSection.style.height = `${customHeight}px`;
    terminalCollapsedPreview?.classList.add("hidden");
  } else {
    terminalSection.classList.add("normal-size");
    terminalSection.style.height = "280px";
    terminalCollapsedPreview?.classList.add("hidden");
  }
  updateSizeButtons(mode);
  terminalState.mode = mode;
  if (save) {
    localStorage.setItem("terminal_mode", mode);
    if (["custom", "normal", "maximized"].includes(mode)) {
      localStorage.setItem("terminal_height", parseInt(terminalSection.style.height, 10) || 280);
    }
  }
}

function updateSizeButtons(activeMode) {
  btnCollapseTerminal?.classList.toggle("active", activeMode === "collapsed");
  btnNormalTerminal?.classList.toggle("active", activeMode === "normal");
  btnMaximizeTerminal?.classList.toggle("active", activeMode === "maximized");
}

function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
  if (appState.ws) { try { appState.ws.close(); } catch (e) { } }

  appState.ws = new WebSocket(wsUrl);
  appState.ws.onopen = () => {
    if (connectionStatus) connectionStatus.className = "chip-status connected";
    if (connStatusText) connStatusText.innerText = "Connected :5000";
    clearTimeout(appState.reconnectTimer);
  };
  appState.ws.onmessage = (event) => {
    try { appendLogLine(JSON.parse(event.data)); } catch (e) { console.error("Lỗi log:", e); }
  };
  appState.ws.onclose = () => {
    if (connectionStatus) connectionStatus.className = "chip-status disconnected";
    if (connStatusText) connStatusText.innerText = "Reconnecting...";
    appState.reconnectTimer = setTimeout(initWebSocket, 3000);
  };
  appState.ws.onerror = () => {
    if (connectionStatus) connectionStatus.className = "chip-status disconnected";
  };
}

function appendLogLine(entry) {
  if (!terminalLogBody) return;
  const lineDiv = document.createElement("div");
  lineDiv.className = `terminal-line ${entry.type || "info"}`;

  const tagMap = { start: ["tag-start", "START"], action: ["tag-action", "ACTION"], success: ["tag-ok", "OK"], warn: ["tag-warn", "WAIT"], error: ["tag-err", "ERR"] };
  const [tagClass, tagText] = tagMap[entry.type] || ["tag-sys", "SYS"];

  const tagSpan = document.createElement("span");
  tagSpan.className = `log-tag ${tagClass}`;
  tagSpan.innerText = tagText;

  const timeSpan = document.createElement("span");
  timeSpan.className = "log-time";
  timeSpan.innerText = `[${entry.time || ""}]`;

  const textSpan = document.createElement("span");
  textSpan.className = "log-content";
  textSpan.innerText = entry.text || "";

  [tagSpan, timeSpan, textSpan].forEach(el => lineDiv.appendChild(el));

  if (previewText) {
    previewText.innerText = entry.text || "";
    previewText.className = `preview-text preview-${entry.type || "info"}`;
  }

  // Live Points Parser
  if (entry.text) {
    const pcMatch = entry.text.match(/\[(?:PC|Desktop)\s*#?(\d+)\/(\d+)\]/i);
    if (pcMatch) appState.liveSearches.desktopCount = Math.max(appState.liveSearches.desktopCount, parseInt(pcMatch[1], 10));
    const mobMatch = entry.text.match(/\[Mobile\s*#?(\d+)\/(\d+)\]/i);
    if (mobMatch) appState.liveSearches.mobileCount = Math.max(appState.liveSearches.mobileCount, parseInt(mobMatch[1], 10));
  }

  terminalLogBody.appendChild(lineDiv);
  if (terminalLogBody.children.length > 600) terminalLogBody.removeChild(terminalLogBody.firstChild);
  if (logCounter) logCounter.innerText = `${terminalLogBody.children.length} dòng`;
  if (chkAutoScroll && chkAutoScroll.checked) terminalLogBody.scrollTop = terminalLogBody.scrollHeight;
}

async function clearTerminalLogs() {
  try {
    await ApiService.clearLogs();
    if (terminalLogBody) {
      terminalLogBody.innerHTML = `
        <div class="terminal-line line-system">
          <span class="log-tag tag-sys">SYS</span>
          <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
          <span class="log-content">Terminal log buffer cleared.</span>
        </div>`;
    }
    if (logCounter) logCounter.innerText = "1 entries";
    if (previewText) {
      previewText.innerText = "Terminal log buffer cleared.";
      previewText.className = "preview-text";
    }
  } catch (err) { }
}

function downloadTerminalLogs() {
  if (!terminalLogBody) return;
  const lines = Array.from(terminalLogBody.querySelectorAll(".terminal-line")).map(el => {
    const time = el.querySelector(".log-time")?.innerText || "";
    const text = el.querySelector(".log-content")?.innerText || "";
    return `${time} ${text}`;
  });

  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `rewards_terminal_log_${new Date().toISOString().slice(0, 10)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
