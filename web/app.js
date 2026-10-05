/**
 * MICROSOFT REWARDS AUTO - CLIENT APPLICATION
 * Minimalist, high-performance, clutter-free dashboard architecture
 */

let appState = {
  profiles: [],
  isRunning: false,
  currentTask: null,
  ws: null,
  reconnectTimer: null,
  publicIp: "1.52.0.121",
  liveSearches: {
    desktopCount: 0,
    mobileCount: 0
  },
  checkingProfiles: new Set()
};

// DOM References
const profilesListBody = document.getElementById("profilesListBody") || document.getElementById("profilesGrid");
const profileCountDisplay = document.getElementById("profileCountDisplay");
const profilesBadge = document.getElementById("profilesBadge");
const connectionStatus = document.getElementById("connectionStatus");
const connStatusText = document.getElementById("connStatusText");
const botStatusPill = document.getElementById("botStatusPill");
const botStatusText = document.getElementById("botStatusText");
const terminalLogBody = document.getElementById("terminalLogBody");
const chkAutoScroll = document.getElementById("chkAutoScroll");
const activeAccountNotice = document.getElementById("activeAccountNotice");
const kpiEngineStatus = document.getElementById("kpiEngineStatus");
const kpiEngineSub = document.getElementById("kpiEngineSub");
const logCounter = document.getElementById("logCounter");

// Inspector & Points Breakdown DOM References
const pointsProfileSelect = document.getElementById("pointsProfileSelect");
const pbTodayPoints = document.getElementById("pbTodayPoints");
const pbLifetimePoints = document.getElementById("pbLifetimePoints");
const pbDesktopEarned = document.getElementById("pbDesktopEarned");
const pbDesktopBar = document.getElementById("pbDesktopBar");
const pbMobileEarned = document.getElementById("pbMobileEarned");
const pbMobileBar = document.getElementById("pbMobileBar");
const pbOffersEarned = document.getElementById("pbOffersEarned");

const metaModeBadge = document.getElementById("metaModeBadge");
const metaIpAddress = document.getElementById("metaIpAddress");
const metaDelay = document.getElementById("metaDelay");
const metaViewport = document.getElementById("metaViewport");
const metaUserAgent = document.getElementById("metaUserAgent");
const hintPlatform = document.getElementById("hintPlatform");
const hintMobile = document.getElementById("hintMobile");

// Bottom Resizable Terminal DOM References
const terminalSection = document.getElementById("terminalSection");
const terminalResizer = document.getElementById("terminalResizer");
const terminalCollapsedPreview = document.getElementById("terminalCollapsedPreview");
const previewText = document.getElementById("previewText");
const btnCollapseTerminal = document.getElementById("btnCollapseTerminal");
const btnNormalTerminal = document.getElementById("btnNormalTerminal");
const btnMaximizeTerminal = document.getElementById("btnMaximizeTerminal");

// Action Hub Buttons
const btnRunAllFull = document.getElementById("btnRunAllFull");
const btnRunAllPC = document.getElementById("btnRunAllPC");
const btnRunAllMobile = document.getElementById("btnRunAllMobile");
const btnStopAll = document.getElementById("btnStopAll");
const btnOpenAddProfile = document.getElementById("btnOpenAddProfile");
const btnOpenSettings = document.getElementById("btnOpenSettings");
const btnOpenKeywords = document.getElementById("btnOpenKeywords");
const btnClearLogs = document.getElementById("btnClearLogs");
const btnDownloadLogs = document.getElementById("btnDownloadLogs");

// Modals
const profileModal = document.getElementById("profileModal");
const profileForm = document.getElementById("profileForm");
const formProfileId = document.getElementById("formProfileId");
const formProfileName = document.getElementById("formProfileName");
const formProfilePath = document.getElementById("formProfilePath");
const profileModalTitle = document.getElementById("profileModalTitle");

const settingsModal = document.getElementById("settingsModal");
const settingsForm = document.getElementById("settingsForm");

const keywordsModal = document.getElementById("keywordsModal");
const keywordsEditor = document.getElementById("keywordsEditor");
const keywordsCountDisplay = document.getElementById("keywordsCountDisplay");
const btnSaveKeywords = document.getElementById("btnSaveKeywords");
const btnSeedKeywords = document.getElementById("btnSeedKeywords");


// ====================================================================
// INITIALIZATION
// ====================================================================
document.addEventListener("DOMContentLoaded", () => {
  initTerminalControls();
  initWebSocket();
  initPublicIp();
  loadProfiles();
  loadStatus();
  recoverLiveSearchesFromLogs();
  setupEventListeners();

  if (pointsProfileSelect) {
    pointsProfileSelect.addEventListener("change", () => {
      updateInspectorPointsUI();
    });
  }

  // Poll status every 3 seconds to keep UI in sync
  setInterval(loadStatus, 3000);
});


// ====================================================================
// WEBSOCKET LOG STREAMING
// ====================================================================
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

  if (appState.ws) {
    try { appState.ws.close(); } catch (e) {}
  }

  appState.ws = new WebSocket(wsUrl);

  appState.ws.onopen = () => {
    connectionStatus.className = "chip-status connected";
    connStatusText.innerText = "Connected :5000";
    clearTimeout(appState.reconnectTimer);
  };

  appState.ws.onmessage = (event) => {
    try {
      const entry = JSON.parse(event.data);
      appendLogLine(entry);
    } catch (e) {
      console.error("Lỗi parse log entry:", e);
    }
  };

  appState.ws.onclose = () => {
    connectionStatus.className = "chip-status disconnected";
    connStatusText.innerText = "Reconnecting...";
    appState.reconnectTimer = setTimeout(initWebSocket, 3000);
  };

  appState.ws.onerror = () => {
    connectionStatus.className = "chip-status disconnected";
  };
}

function appendLogLine(entry) {
  const lineDiv = document.createElement("div");
  lineDiv.className = `terminal-line ${entry.type || "info"}`;

  // Tag chip classification
  const tagSpan = document.createElement("span");
  let tagClass = "tag-sys";
  let tagText = "SYS";

  if (entry.type === "start") { tagClass = "tag-start"; tagText = "START"; }
  else if (entry.type === "action") { tagClass = "tag-action"; tagText = "ACTION"; }
  else if (entry.type === "success") { tagClass = "tag-ok"; tagText = "OK"; }
  else if (entry.type === "warn") { tagClass = "tag-warn"; tagText = "WAIT"; }
  else if (entry.type === "error") { tagClass = "tag-err"; tagText = "ERR"; }

  tagSpan.className = `log-tag ${tagClass}`;
  tagSpan.innerText = tagText;

  const timeSpan = document.createElement("span");
  timeSpan.className = "log-time";
  timeSpan.innerText = `[${entry.time || ""}]`;

  const textSpan = document.createElement("span");
  textSpan.className = "log-content";
  textSpan.innerText = entry.text || "";

  lineDiv.appendChild(tagSpan);
  lineDiv.appendChild(timeSpan);
  lineDiv.appendChild(textSpan);

  if (previewText) {
    previewText.innerText = entry.text || "";
    previewText.className = `preview-text preview-${entry.type || "info"}`;
  }

  // Live Points Parser from streaming bot logs
  if (entry.text) {
    const pcMatch = entry.text.match(/\[(?:PC|Desktop)\s*#?(\d+)\/(\d+)\]/i);
    if (pcMatch) {
      const currentPc = parseInt(pcMatch[1], 10);
      appState.liveSearches.desktopCount = Math.max(appState.liveSearches.desktopCount, currentPc);
      updateInspectorPointsUI();
    }
    const mobMatch = entry.text.match(/\[Mobile\s*#?(\d+)\/(\d+)\]/i);
    if (mobMatch) {
      const currentMob = parseInt(mobMatch[1], 10);
      appState.liveSearches.mobileCount = Math.max(appState.liveSearches.mobileCount, currentMob);
      updateInspectorPointsUI();
    }
  }

  terminalLogBody.appendChild(lineDiv);

  // Buffer retention: Keep last 600 lines
  if (terminalLogBody.children.length > 600) {
    terminalLogBody.removeChild(terminalLogBody.firstChild);
  }

  if (logCounter) {
    logCounter.innerText = `${terminalLogBody.children.length} dòng`;
  }

  if (chkAutoScroll.checked) {
    terminalLogBody.scrollTop = terminalLogBody.scrollHeight;
  }
}


// ====================================================================
// PROFILES LIST RENDERING (Clean Minimalist Table Rows)
// ====================================================================
async function loadProfiles() {
  try {
    const res = await fetch("/api/profiles");
    if (!res.ok) throw new Error("Failed to fetch profiles");
    const data = await res.json();
    appState.profiles = data;
    renderProfiles(data);
    populatePointsProfileSelect();
  } catch (err) {
    console.error("Lỗi nạp profiles:", err);
    if (profilesListBody) {
      profilesListBody.innerHTML = `<tr><td colspan="5" class="loading-state">Không thể tải danh sách tài khoản: ${err.message}</td></tr>`;
    }
  }
}

function renderProfiles(profiles) {
  if (profileCountDisplay) {
    profileCountDisplay.innerText = profiles.length;
  }
  if (profilesBadge) {
    profilesBadge.innerText = `${profiles.length} tài khoản`;
  }

  if (!profilesListBody) return;

  if (!profiles || profiles.length === 0) {
    profilesListBody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">
          <p>Chưa có tài khoản nào được cấu hình.</p>
          <button class="btn btn-primary btn-sm mt-2" onclick="openAddProfileModal()">+ Thêm Tài Khoản Đầu Tiên</button>
        </td>
      </tr>`;
    return;
  }

  profilesListBody.innerHTML = "";

  profiles.forEach((p, idx) => {
    const isThisRunning = appState.isRunning && appState.currentTask && String(appState.currentTask.profile_id) === String(p.id);
    const isChecking = appState.checkingProfiles && appState.checkingProfiles.has(String(p.id));
    const row = document.createElement("tr");
    row.className = `profile-row ${isThisRunning ? "is-running" : ""}`;
    row.id = `profile-row-${p.id}`;

    const hasEmail = Boolean(p.email || (p.name && p.name.includes("@")));
    const isUnlogged = p.status === "unlogged" || !hasEmail;

    let statusClass = "status-ready";
    let statusText = "Sẵn sàng";

    if (isThisRunning) {
      statusClass = "status-running";
      statusText = `Đang chạy (${(appState.currentTask?.mode || "").toUpperCase()})`;
    } else if (isChecking) {
      statusClass = "status-checking";
      statusText = "Đang check...";
    } else if (isUnlogged) {
      statusClass = "status-unlogged";
      statusText = "Chưa đăng nhập";
    }

    // Quick run buttons or Stop button if running
    let runCellHtml = "";
    if (isThisRunning) {
      runCellHtml = `
        <button class="btn btn-xs btn-stop-running" onclick="stopProfile('${p.id}')" title="Dừng ngay lượt tìm kiếm của tài khoản này">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"></rect></svg>
          <span>Dừng Acc #${p.id}</span>
        </button>
      `;
    } else if (isUnlogged) {
      runCellHtml = `
        <div class="run-buttons-group">
          <button class="btn btn-xs btn-outline" data-unlogged="true" disabled title="Tài khoản chưa đăng nhập, vui lòng bấm 'Đăng nhập'">
            PC
          </button>
          <button class="btn btn-xs btn-outline" data-unlogged="true" disabled title="Tài khoản chưa đăng nhập, vui lòng bấm 'Đăng nhập'">
            Mobile
          </button>
          <button class="btn btn-xs btn-primary-soft" data-unlogged="true" disabled title="Tài khoản chưa đăng nhập, vui lòng bấm 'Đăng nhập'">
            Full (52)
          </button>
        </div>
      `;
    } else {
      const isOtherRunning = appState.isRunning;
      runCellHtml = `
        <div class="run-buttons-group">
          <button class="btn btn-xs btn-outline" onclick="runSingleProfile('${p.id}', 'desktop')" ${isOtherRunning ? "disabled" : ""} title="Tìm kiếm Desktop (31 lượt)">
            PC
          </button>
          <button class="btn btn-xs btn-outline" onclick="runSingleProfile('${p.id}', 'mobile')" ${isOtherRunning ? "disabled" : ""} title="Tìm kiếm Mobile (21 lượt)">
            Mobile
          </button>
          <button class="btn btn-xs btn-primary-soft" onclick="runSingleProfile('${p.id}', 'all')" ${isOtherRunning ? "disabled" : ""} title="Chạy cả Desktop và Mobile">
            Full (52)
          </button>
        </div>
      `;
    }

    const nameDisplay = escapeHtml(p.name);
    const pathDisplay = escapeHtml(p.path);

    // Points Column formatting
    const todayPts = p.today_points ? `${p.today_points} pts` : '--';
    const totalPts = p.total_points ? Number(p.total_points).toLocaleString() : '--';
    const pcPts = p.desktop_points || '0/90';
    const mobPts = p.mobile_points || '0/60';

    const pointsCellHtml = `
      <div class="pts-badge-cell">
        <div class="pts-today-tag">
          <span class="pts-today-val">${todayPts}</span>
          <span class="pts-label">hôm nay</span>
        </div>
        <div class="pts-breakdown-mini">
          <span class="pts-pill" title="Desktop Bing Search">💻 ${pcPts}</span>
          <span class="pts-pill" title="Mobile Bing Search">📱 ${mobPts}</span>
          <span class="pts-pill pts-total-pill" title="Tổng điểm tích lũy (Lifetime)">⭐ ${totalPts}</span>
        </div>
      </div>
    `;

    row.innerHTML = `
      <td class="col-id">
        <span class="id-badge">#${p.id}</span>
      </td>
      <td class="col-name">
        <div class="account-cell">
          <span class="account-name ${hasEmail ? "is-email" : "not-login"}" title="${nameDisplay}">
            ${hasEmail ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: -2px; margin-right: 4px; color: var(--primary);"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>` : ""}
            ${nameDisplay}
          </span>
          <span class="account-path" title="${pathDisplay}">${pathDisplay}</span>
        </div>
      </td>
      <td class="col-points">
        ${pointsCellHtml}
      </td>
      <td class="col-status">
        <span class="badge-status ${statusClass}">
          <span class="status-dot"></span>
          <span>${statusText}</span>
        </span>
      </td>
      <td class="col-quick-run">
        ${runCellHtml}
      </td>
      <td class="col-actions">
        <div class="actions-group">
          <button class="btn btn-xs btn-check ${isChecking ? 'checking' : ''}" onclick="checkProfilePoints('${p.id}')" ${isChecking || isThisRunning ? 'disabled' : ''} title="Kiểm tra số điểm thực tế trên Bing Rewards cho tài khoản này (chạy an toàn 1 tài khoản, không bị ban)">
            ${isChecking ? '<span class="spinner-mini"></span><span>Đang check...</span>' : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg><span>Check</span>'}
          </button>
          <button class="btn btn-xs btn-login ${isUnlogged ? 'btn-attention' : ''}" onclick="loginProfile('${p.id}')" title="Mở Edge độc lập để đăng nhập tài khoản">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>
            <span>Đăng nhập</span>
          </button>
          <button class="btn-icon" onclick="unlockProfile('${p.id}')" title="Giải phóng file lock & đóng Edge treo">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg>
          </button>
          <button class="btn-icon" onclick="openEditProfileModal('${p.id}', '${escapeHtml(p.name)}', '${escapeHtml(p.path)}')" title="Đổi tên hoặc thư mục lưu">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
          </button>
          <button class="btn-icon danger" onclick="deleteProfile('${p.id}')" title="Xóa tài khoản khỏi danh sách">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      </td>
    `;

    profilesListBody.appendChild(row);
  });
}


// ====================================================================
// BOT STATE SYNC & EXECUTION ENGINE
// ====================================================================
async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    
    const wasRunning = appState.isRunning;
    const prevTaskId = appState.currentTask?.profile_id;

    appState.isRunning = data.is_running;
    appState.currentTask = data.current_task;

    updateUIState();

    // Nếu trạng thái hoạt động thay đổi, cập nhật ngay giao diện profile list
    if (wasRunning !== appState.isRunning || prevTaskId !== appState.currentTask?.profile_id) {
      if (appState.profiles && appState.profiles.length > 0) {
        renderProfiles(appState.profiles);
      }
    }
  } catch (err) {
    console.error("Lỗi lấy status:", err);
  }
}

function updateUIState() {
  if (appState.isRunning && appState.currentTask) {
    botStatusPill.className = "chip-status running";
    botStatusText.innerText = `Đang chạy: ${appState.currentTask.profile_name || "Profile"}`;

    if (activeAccountNotice) {
      activeAccountNotice.innerText = `Đang chạy: ${appState.currentTask.profile_name} (Chế độ: ${appState.currentTask.mode.toUpperCase()})`;
    }

    btnRunAllFull.disabled = true;
    btnRunAllPC.disabled = true;
    btnRunAllMobile.disabled = true;
    btnStopAll.disabled = false;
  } else {
    botStatusPill.className = "chip-status idle";
    botStatusText.innerText = "Sẵn sàng (Idle)";

    if (activeAccountNotice) {
      activeAccountNotice.innerText = "Sẵn sàng nhận lệnh điều khiển";
    }

    btnRunAllFull.disabled = false;
    btnRunAllPC.disabled = false;
    btnRunAllMobile.disabled = false;
    btnStopAll.disabled = true;
  }

  // Update Live Session & Metadata Inspector
  const task = appState.currentTask;
  const isRunning = appState.isRunning && Boolean(task);

  if (metaModeBadge) {
    if (isRunning) {
      const modeStr = (task.mode || "").toUpperCase();
      let modeName = `Đang chạy: ${modeStr}`;
      if (task.mode === "desktop") modeName = "🖥️ PC Search (31 lượt)";
      else if (task.mode === "mobile") modeName = "📱 Mobile Search (21 lượt)";
      else if (task.mode === "all") modeName = "🚀 Full (PC + Mobile)";
      metaModeBadge.className = "meta-chip chip-running";
      metaModeBadge.innerText = modeName;
    } else {
      metaModeBadge.className = "meta-chip chip-idle";
      metaModeBadge.innerText = "💤 Sẵn sàng (Idle)";
    }
  }

  if (isRunning) {
    if (task.mode === "mobile") {
      if (metaUserAgent) metaUserAgent.innerText = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 EdgA/131.0.0.0";
      if (metaViewport) metaViewport.innerText = "412 × 915 (Google Pixel 7)";
      if (hintPlatform) hintPlatform.innerText = '"Android"';
      if (hintMobile) hintMobile.innerText = "?1";
    } else {
      if (metaUserAgent) metaUserAgent.innerText = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0";
      if (metaViewport) metaViewport.innerText = "1920 × 1080 (Desktop PC)";
      if (hintPlatform) hintPlatform.innerText = '"Windows"';
      if (hintMobile) hintMobile.innerText = "?0";
    }
  } else {
    if (metaUserAgent) metaUserAgent.innerText = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0";
    if (metaViewport) metaViewport.innerText = "1920 × 1080";
    if (hintPlatform) hintPlatform.innerText = '"Windows"';
    if (hintMobile) hintMobile.innerText = "?0";
  }

  updateInspectorPointsUI();

  // Update button states inside list rows
  const runButtons = document.querySelectorAll(".run-buttons-group .btn");
  runButtons.forEach(btn => {
    if (btn.dataset.unlogged === "true") {
      btn.disabled = true;
    } else {
      btn.disabled = appState.isRunning;
    }
  });
}

async function stopProfile(profileId) {
  const profile = appState.profiles.find(p => String(p.id) === String(profileId));
  const pName = profile ? profile.name : `Tài khoản #${profileId}`;

  if (!confirm(`Xác nhận DỪNG tìm kiếm / đóng tiến trình Edge cho ${pName}?`)) {
    return;
  }

  try {
    let res = await fetch(`/api/profiles/${profileId}/stop`, { method: "POST" });
    if (res.status === 404) {
      res = await fetch("/api/stop", { method: "POST" });
    }
    await res.json();
    loadStatus();
    loadProfiles();
  } catch (err) {
    alert(`Lỗi khi dừng hồ sơ: ${err.message}`);
  }
}

async function runTask(profileId, mode) {
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: profileId, mode: mode })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(`[Lỗi] ${result.message || "Không thể khởi động bot"}`);
    } else {
      loadStatus();
      loadProfiles();
    }
  } catch (err) {
    alert(`[Lỗi kết nối] ${err.message}`);
  }
}

function runSingleProfile(profileId, mode) {
  const profile = appState.profiles.find(p => String(p.id) === String(profileId));
  const hasEmail = profile && (profile.email || (profile.name && profile.name.includes("@")));
  if (profile && (profile.status === "unlogged" || !hasEmail)) {
    alert(`Tài khoản #${profileId} chưa đăng nhập!\nVui lòng bấm nút 'Đăng nhập' màu cam để đăng nhập Microsoft trước khi chạy bot.`);
    return;
  }
  runTask(profileId, mode);
}

async function stopBot() {
  if (!confirm("Xác nhận DỪNG KHẨN CẤP toàn bộ tác vụ bot đang chạy?")) {
    return;
  }
  try {
    const res = await fetch("/api/stop", { method: "POST" });
    if (res.ok) {
      loadStatus();
      loadProfiles();
    }
  } catch (err) {
    alert(`Lỗi khi gửi lệnh dừng: ${err.message}`);
  }
}

async function checkProfilePoints(profileId) {
  const profile = appState.profiles.find(p => String(p.id) === String(profileId));
  const pName = profile ? profile.name : `Tài khoản #${profileId}`;

  if (appState.checkingProfiles.has(String(profileId))) {
    return;
  }

  if (appState.isRunning && appState.currentTask && String(appState.currentTask.profile_id) === String(profileId)) {
    alert(`Tài khoản ${pName} đang chạy bot tìm kiếm!\nVui lòng đợi phiên chạy hoàn thành trước khi check điểm.`);
    return;
  }

  appState.checkingProfiles.add(String(profileId));
  renderProfiles(appState.profiles);

  try {
    const res = await fetch(`/api/profiles/${profileId}/check`, {
      method: "POST"
    });
    const result = await res.json();

    if (!res.ok || result.status === "error") {
      alert(`[Lỗi check điểm] ${result.message || "Không thể kiểm tra điểm"}`);
    } else {
      // Cập nhật profile trong danh sách hiện tại
      const updated = result.profile;
      const idx = appState.profiles.findIndex(p => String(p.id) === String(profileId));
      if (idx !== -1 && updated) {
        appState.profiles[idx] = { ...appState.profiles[idx], ...updated };
      }
      // Đồng bộ sang thanh Inspector nếu đang xem profile này
      if (pointsProfileSelect && (pointsProfileSelect.value === String(profileId) || pointsProfileSelect.value === "live")) {
        updateInspectorPointsUI();
      }
    }
  } catch (err) {
    alert(`Lỗi kết nối khi check điểm: ${err.message}`);
  } finally {
    appState.checkingProfiles.delete(String(profileId));
    renderProfiles(appState.profiles);
  }
}

async function loginProfile(profileId) {
  try {
    const res = await fetch(`/api/profiles/${profileId}/login`, { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      alert("✅ Cửa sổ Microsoft Edge đã được mở độc lập!\n\n1. Hãy đăng nhập tài khoản Microsoft trên cửa sổ đó.\n2. Sau khi xong, hãy ĐÓNG CỬA SỔ EDGE lại.\n3. Hệ thống sẽ tự động cập nhật email tài khoản vào danh sách.");
      // Bắt đầu theo dõi định kỳ để tự cập nhật giao diện khi người dùng đăng nhập xong
      let checkCount = 0;
      const pollInterval = setInterval(async () => {
        checkCount++;
        await loadProfiles();
        const p = appState.profiles.find(item => String(item.id) === String(profileId));
        if ((p && p.status === "ready" && (p.email || (p.name && p.name.includes("@")))) || checkCount > 30) {
          clearInterval(pollInterval);
        }
      }, 3000);
    } else {
      alert(`[Lỗi] ${data.message || "Không thể mở Edge"}`);
    }
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

async function unlockProfile(profileId) {
  try {
    const res = await fetch(`/api/profiles/${profileId}/unlock`, { method: "POST" });
    if (res.ok) {
      alert("🧹 Đã dọn dẹp và giải phóng file lock của Profile thành công!");
    }
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}


// ====================================================================
// MODAL: ADD / EDIT PROFILE
// ====================================================================
function openAddProfileModal() {
  formProfileId.value = "";
  formProfileName.value = "";
  formProfilePath.value = "";
  profileModalTitle.innerText = "Thêm Tài Khoản Mới";
  profileModal.classList.remove("hidden");
  formProfileName.focus();
}

function openEditProfileModal(id, name, path) {
  formProfileId.value = id;
  formProfileName.value = name;
  formProfilePath.value = path;
  profileModalTitle.innerText = `Chỉnh Sửa Tài Khoản #${id}`;
  profileModal.classList.remove("hidden");
  formProfileName.focus();
}

function closeProfileModal() {
  profileModal.classList.add("hidden");
}

profileForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = formProfileId.value.trim();
  const name = formProfileName.value.trim();
  const path = formProfilePath.value.trim();

  try {
    if (id) {
      const res = await fetch(`/api/profiles/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, path })
      });
      if (!res.ok) throw new Error("Failed to update profile");
    } else {
      const res = await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, path })
      });
      if (!res.ok) throw new Error("Failed to add profile");
    }
    closeProfileModal();
    loadProfiles();
  } catch (err) {
    alert(`Lỗi lưu tài khoản: ${err.message}`);
  }
});

async function deleteProfile(profileId) {
  if (!confirm(`Xác nhận xóa Tài Khoản #${profileId} khỏi danh sách quản lý?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/profiles/${profileId}`, { method: "DELETE" });
    if (res.ok) {
      loadProfiles();
    }
  } catch (err) {
    alert(`Lỗi xóa tài khoản: ${err.message}`);
  }
}


// ====================================================================
// MODAL: SETTINGS
// ====================================================================
async function openSettingsModal() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error("Failed to load config");
    const data = await res.json();
    
    const sc = data.search_settings || {};
    const bc = data.browser_settings || {};

    document.getElementById("cfgPcSearches").value = sc.pc_searches || 31;
    document.getElementById("cfgMobileSearches").value = sc.mobile_searches || 21;
    document.getElementById("cfgMinDelay").value = sc.min_delay_seconds || 12;
    document.getElementById("cfgMaxDelay").value = sc.max_delay_seconds || 22;
    document.getElementById("cfgEnableBatch").checked = !!sc.enable_cooldown_batches;
    document.getElementById("cfgBatchSize").value = sc.batch_size || 4;
    document.getElementById("cfgBatchCooldown").value = sc.batch_cooldown_minutes || 3;
    document.getElementById("cfgSmoothScroll").checked = sc.enable_smooth_scrolling !== false;
    document.getElementById("cfgMouseMovement").checked = sc.enable_mouse_movement !== false;
    document.getElementById("cfgClickChance").value = sc.random_click_chance !== undefined ? sc.random_click_chance : 0.25;
    
    document.getElementById("cfgHeadless").checked = !!bc.headless;
    if (bc.mobile_device_name) {
      document.getElementById("cfgMobileDevice").value = bc.mobile_device_name;
    }

    settingsModal.classList.remove("hidden");
  } catch (err) {
    alert(`Lỗi nạp cấu hình: ${err.message}`);
  }
}

function closeSettingsModal() {
  settingsModal.classList.add("hidden");
}

settingsForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    search_settings: {
      pc_searches: parseInt(document.getElementById("cfgPcSearches").value) || 31,
      mobile_searches: parseInt(document.getElementById("cfgMobileSearches").value) || 21,
      min_delay_seconds: parseInt(document.getElementById("cfgMinDelay").value) || 12,
      max_delay_seconds: parseInt(document.getElementById("cfgMaxDelay").value) || 22,
      enable_cooldown_batches: document.getElementById("cfgEnableBatch").checked,
      batch_size: parseInt(document.getElementById("cfgBatchSize").value) || 4,
      batch_cooldown_minutes: parseInt(document.getElementById("cfgBatchCooldown").value) || 3,
      enable_smooth_scrolling: document.getElementById("cfgSmoothScroll").checked,
      enable_mouse_movement: document.getElementById("cfgMouseMovement").checked,
      random_click_chance: parseFloat(document.getElementById("cfgClickChance").value) || 0.25
    },
    browser_settings: {
      headless: document.getElementById("cfgHeadless").checked,
      mobile_device_name: document.getElementById("cfgMobileDevice").value
    }
  };

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to save config");
    closeSettingsModal();
    alert("💾 Cấu hình đã được lưu thành công!");
  } catch (err) {
    alert(`Lỗi lưu cấu hình: ${err.message}`);
  }
});


// ====================================================================
// MODAL: KEYWORDS POOL
// ====================================================================
async function openKeywordsModal() {
  try {
    const res = await fetch("/api/keywords");
    if (!res.ok) throw new Error("Failed to load keywords");
    const data = await res.json();
    keywordsEditor.value = data.content || "";
    keywordsCountDisplay.innerText = data.count || 0;
    keywordsModal.classList.remove("hidden");
  } catch (err) {
    alert(`Lỗi nạp từ khóa: ${err.message}`);
  }
}

function closeKeywordsModal() {
  keywordsModal.classList.add("hidden");
}

keywordsEditor.addEventListener("input", () => {
  const lines = keywordsEditor.value.split("\n")
    .map(l => l.trim())
    .filter(l => l && !l.startsWith("#"));
  keywordsCountDisplay.innerText = lines.length;
});

btnSaveKeywords.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/keywords", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: keywordsEditor.value })
    });
    const data = await res.json();
    if (!res.ok) throw new Error("Failed to save keywords");
    closeKeywordsModal();
    alert(`💾 Đã lưu thành công kho ${data.count} từ khóa tìm kiếm!`);
  } catch (err) {
    alert(`Lỗi lưu từ khóa: ${err.message}`);
  }
});

btnSeedKeywords.addEventListener("click", () => {
  const sampleKeywords = [
    "thời tiết hôm nay tại hà nội", "tin tức thời sự vtv hôm nay",
    "cách làm sườn xào chua ngọt ngon mềm", "địa điểm du lịch đà lạt đẹp nhất",
    "kết quả bóng đá ngoại hạng anh mới nhất", "top 10 phim chiếu rạp đáng xem",
    "hướng dẫn tự học lập trình python", "cách tối ưu hóa windows 11",
    "mẹo tiết kiệm pin laptop hiệu quả", "công thức nấu phở bò truyền thống",
    "những cuốn sách hay nên đọc một lần", "cách pha cà phê cold brew ngon",
    "kinh nghiệm du lịch phú quốc tự túc", "tác dụng của trà xanh đối với sức khỏe",
    "bài tập yoga buổi sáng tăng năng lượng", "cách cải thiện trí nhớ và tập trung",
    "top công nghệ trí tuệ nhân tạo hiện nay", "thói quen tốt trước khi đi ngủ",
    "cách làm bánh mì bơ tỏi tại nhà", "giá vàng hôm nay 9999",
    "lịch thi đấu cúp c1 châu âu", "cách trồng cây phong thủy trong nhà",
    "how to learn coding fast for beginners", "best healthy breakfast recipes",
    "benefits of drinking water daily", "how do airplanes stay in the air",
    "tips for better sleep quality at night", "difference between ai and machine learning",
    "history of the ancient roman empire", "best books to read in your lifetime",
    "how to speak with confidence in public", "simple morning routine for high productivity"
  ];

  const currentLines = keywordsEditor.value.split("\n").map(l => l.trim());
  const existingSet = new Set(currentLines.map(l => l.toLowerCase()));
  let added = 0;

  for (const kw of sampleKeywords) {
    if (!existingSet.has(kw.toLowerCase())) {
      currentLines.push(kw);
      existingSet.add(kw.toLowerCase());
      added++;
    }
  }

  keywordsEditor.value = currentLines.filter(l => l).join("\n");
  keywordsCountDisplay.innerText = existingSet.size;
  alert(`✨ Đã bổ sung thêm ${added} từ khóa mẫu tự nhiên vào danh sách! Bấm 'Lưu' để áp dụng.`);
});


// ====================================================================
// TERMINAL ACTIONS
// ====================================================================
btnClearLogs.addEventListener("click", async () => {
  try {
    await fetch("/api/logs/clear", { method: "POST" });
    terminalLogBody.innerHTML = `
      <div class="terminal-line line-system">
        <span class="log-tag tag-sys">SYS</span>
        <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
        <span class="log-content">Terminal log buffer cleared.</span>
      </div>`;
    if (logCounter) logCounter.innerText = "1 entries";
    if (previewText) {
      previewText.innerText = "Terminal log buffer cleared.";
      previewText.className = "preview-text";
    }
  } catch (err) {}
});

btnDownloadLogs.addEventListener("click", () => {
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
});


// ====================================================================
// TERMINAL RESIZING & SIZING MODES (Phóng to / Thu nhỏ / Kéo thả)
// ====================================================================
let terminalState = {
  mode: localStorage.getItem("terminal_mode") || "normal", // "collapsed", "normal", "maximized", "custom"
  customHeight: parseInt(localStorage.getItem("terminal_height")) || 280,
  isDragging: false,
  startY: 0,
  startHeight: 0
};

function initTerminalControls() {
  if (!terminalSection || !terminalResizer) return;

  applyTerminalMode(terminalState.mode, terminalState.customHeight, false);

  if (btnCollapseTerminal) {
    btnCollapseTerminal.addEventListener("click", (e) => {
      e.stopPropagation();
      applyTerminalMode("collapsed");
    });
  }
  if (btnNormalTerminal) {
    btnNormalTerminal.addEventListener("click", (e) => {
      e.stopPropagation();
      applyTerminalMode("normal", 280);
    });
  }
  if (btnMaximizeTerminal) {
    btnMaximizeTerminal.addEventListener("click", (e) => {
      e.stopPropagation();
      applyTerminalMode("maximized", 560);
    });
  }

  // Double click resizer or collapsed preview to toggle expand/collapse
  terminalResizer.addEventListener("dblclick", () => {
    if (terminalState.mode === "collapsed") {
      applyTerminalMode("normal", 280);
    } else {
      applyTerminalMode("collapsed");
    }
  });

  if (terminalCollapsedPreview) {
    terminalCollapsedPreview.addEventListener("click", () => {
      applyTerminalMode("normal", 280);
    });
  }

  // Drag resizer
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
    const deltaY = terminalState.startY - e.clientY; // dragging up increases height
    let targetHeight = terminalState.startHeight + deltaY;

    // Clamping: min 48px, max 750px
    if (targetHeight < 80) {
      applyTerminalMode("collapsed", 0, false);
      return;
    }
    if (targetHeight > 750) targetHeight = 750;

    terminalSection.classList.remove("collapsed");
    if (terminalCollapsedPreview) terminalCollapsedPreview.classList.add("hidden");
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
    if (terminalCollapsedPreview) terminalCollapsedPreview.classList.remove("hidden");
    updateSizeButtons("collapsed");
  } else if (mode === "maximized") {
    terminalSection.classList.add("maximized");
    terminalSection.style.height = "560px";
    if (terminalCollapsedPreview) terminalCollapsedPreview.classList.add("hidden");
    updateSizeButtons("maximized");
  } else if (mode === "custom" && customHeight >= 100) {
    terminalSection.classList.add("custom");
    terminalSection.style.height = `${customHeight}px`;
    if (terminalCollapsedPreview) terminalCollapsedPreview.classList.add("hidden");
    updateSizeButtons("custom");
  } else {
    // Normal / default mode (280px)
    terminalSection.classList.add("normal-size");
    terminalSection.style.height = "280px";
    if (terminalCollapsedPreview) terminalCollapsedPreview.classList.add("hidden");
    updateSizeButtons("normal");
  }

  terminalState.mode = mode;
  if (save) {
    localStorage.setItem("terminal_mode", mode);
    if (mode === "custom" || mode === "normal" || mode === "maximized") {
      localStorage.setItem("terminal_height", parseInt(terminalSection.style.height) || 280);
    }
  }
}

function updateSizeButtons(activeMode) {
  if (btnCollapseTerminal) btnCollapseTerminal.classList.toggle("active", activeMode === "collapsed");
  if (btnNormalTerminal) btnNormalTerminal.classList.toggle("active", activeMode === "normal");
  if (btnMaximizeTerminal) btnMaximizeTerminal.classList.toggle("active", activeMode === "maximized");
}


// ====================================================================
// EVENT LISTENERS
// ====================================================================
function setupEventListeners() {
  btnRunAllFull.addEventListener("click", () => runTask("all", "all"));
  btnRunAllPC.addEventListener("click", () => runTask("all", "desktop"));
  btnRunAllMobile.addEventListener("click", () => runTask("all", "mobile"));
  btnStopAll.addEventListener("click", stopBot);

  btnOpenAddProfile.addEventListener("click", openAddProfileModal);
  btnOpenSettings.addEventListener("click", openSettingsModal);
  btnOpenKeywords.addEventListener("click", openKeywordsModal);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


// ====================================================================
// POINTS BREAKDOWN & SESSION METADATA INSPECTOR HELPERS
// ====================================================================
async function initPublicIp() {
  try {
    const res = await fetch("https://api.ipify.org?format=json");
    if (res.ok) {
      const data = await res.json();
      if (data.ip) {
        appState.publicIp = data.ip;
        if (metaIpAddress) metaIpAddress.innerText = data.ip;
      }
    }
  } catch (e) {
    // Keep fallback IP
  }
}

async function recoverLiveSearchesFromLogs() {
  try {
    const res = await fetch("/api/logs");
    if (res.ok) {
      const logs = await res.json();
      logs.forEach(l => {
        const text = l.text || "";
        const pcMatch = text.match(/\[(?:PC|Desktop)\s*#?(\d+)\/(\d+)\]/i);
        if (pcMatch) {
          appState.liveSearches.desktopCount = Math.max(appState.liveSearches.desktopCount, parseInt(pcMatch[1], 10));
        }
        const mobMatch = text.match(/\[Mobile\s*#?(\d+)\/(\d+)\]/i);
        if (mobMatch) {
          appState.liveSearches.mobileCount = Math.max(appState.liveSearches.mobileCount, parseInt(mobMatch[1], 10));
        }
      });
      updateInspectorPointsUI();
    }
  } catch (e) {}
}

function populatePointsProfileSelect() {
  if (!pointsProfileSelect) return;
  const currentVal = pointsProfileSelect.value;
  pointsProfileSelect.innerHTML = `<option value="live">● Đang chạy (Live Tracker)</option>`;
  if (appState.profiles && appState.profiles.length > 0) {
    appState.profiles.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.innerText = `Acc #${p.id} - ${p.name}`;
      pointsProfileSelect.appendChild(opt);
    });
  }
  if (currentVal && Array.from(pointsProfileSelect.options).some(o => o.value === currentVal)) {
    pointsProfileSelect.value = currentVal;
  }
  updateInspectorPointsUI();
}

function updateInspectorPointsUI() {
  const selectVal = pointsProfileSelect ? pointsProfileSelect.value : "live";
  let desktopStr = "0/90";
  let mobileStr = "0/60";
  let offersEarned = 0;
  let todayTotal = 0;
  let lifetimeTotal = 0;

  if (selectVal === "live") {
    const currentPid = appState.currentTask?.profile_id;
    const runningProfile = currentPid ? appState.profiles.find(p => String(p.id) === String(currentPid)) : null;

    if (runningProfile) {
      todayTotal = runningProfile.today_points || 0;
      lifetimeTotal = runningProfile.total_points || 0;
      desktopStr = runningProfile.desktop_points || "0/90";
      mobileStr = runningProfile.mobile_points || "0/60";
      offersEarned = runningProfile.offers_points || 0;
    } else {
      const pcEarned = Math.min(90, appState.liveSearches.desktopCount * 3);
      const mobEarned = Math.min(60, appState.liveSearches.mobileCount * 3);
      desktopStr = `${pcEarned}/90`;
      mobileStr = `${mobEarned}/60`;
      todayTotal = pcEarned + mobEarned;
    }
  } else {
    const profile = appState.profiles.find(p => String(p.id) === String(selectVal));
    if (profile) {
      todayTotal = profile.today_points || 0;
      lifetimeTotal = profile.total_points || 0;
      desktopStr = profile.desktop_points || "0/90";
      mobileStr = profile.mobile_points || "0/60";
      offersEarned = profile.offers_points || 0;
    }
  }

  // Parse numerator/denominator an toàn
  const parseFrac = (str, defMax) => {
    if (!str || typeof str !== "string") return { cur: 0, max: defMax };
    const parts = str.split("/").map(s => parseInt(s.trim(), 10));
    return { cur: isNaN(parts[0]) ? 0 : parts[0], max: isNaN(parts[1]) ? defMax : parts[1] };
  };

  const pcFrac = parseFrac(desktopStr, 90);
  const mobFrac = parseFrac(mobileStr, 60);

  if (pbTodayPoints) pbTodayPoints.innerText = todayTotal;
  if (pbLifetimePoints) pbLifetimePoints.innerText = lifetimeTotal ? lifetimeTotal.toLocaleString() : "0";
  if (pbDesktopEarned) pbDesktopEarned.innerText = pcFrac.cur;
  if (pbMobileEarned) pbMobileEarned.innerText = mobFrac.cur;
  if (pbOffersEarned) pbOffersEarned.innerText = offersEarned;

  if (pbDesktopBar) {
    const pcPct = pcFrac.max > 0 ? Math.min(100, Math.round((pcFrac.cur / pcFrac.max) * 100)) : 0;
    pbDesktopBar.style.width = `${pcPct}%`;
  }
  if (pbMobileBar) {
    const mobPct = mobFrac.max > 0 ? Math.min(100, Math.round((mobFrac.cur / mobFrac.max) * 100)) : 0;
    pbMobileBar.style.width = `${mobPct}%`;
  }
}

function copyUserAgent() {
  const ua = document.getElementById("metaUserAgent")?.innerText?.trim() || "";
  if (!ua) return;
  navigator.clipboard.writeText(ua).then(() => {
    const btn = document.getElementById("btnCopyUA");
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = `<span style="color: #10B981; font-weight: 700;">✓ Đã copy</span>`;
      setTimeout(() => { btn.innerHTML = orig; }, 2000);
    }
  }).catch(() => {
    alert("Đã chép User-Agent vào clipboard!");
  });
}
