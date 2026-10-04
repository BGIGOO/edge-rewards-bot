/**
 * REWARDS POP HUB - CLIENT APPLICATION ARCHITECTURE
 * Style: Playful Geometric Design System (Neo-Pop / Memphis Sticker Vibe)
 * Warm Cream Paper Canvas • Hard Pop Shadows • Candy Buttons
 */

let appState = {
  profiles: [],
  isRunning: false,
  currentTask: null,
  ws: null,
  reconnectTimer: null
};

// DOM References
const profilesGrid = document.getElementById("profilesGrid");
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
  loadProfiles();
  loadStatus();
  setupEventListeners();

  // Poll status every 3 seconds to keep UI in sync
  setInterval(loadStatus, 3000);
});


// ====================================================================
// WEBSOCKET LOG STREAMING (Retro-Arcade Terminal Engine)
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

  terminalLogBody.appendChild(lineDiv);

  // Buffer retention: Keep last 600 lines
  if (terminalLogBody.children.length > 600) {
    terminalLogBody.removeChild(terminalLogBody.firstChild);
  }

  if (logCounter) {
    logCounter.innerText = `${terminalLogBody.children.length} entries`;
  }

  if (chkAutoScroll.checked) {
    terminalLogBody.scrollTop = terminalLogBody.scrollHeight;
  }
}


// ====================================================================
// PROFILES STICKER CARDS RENDERING (Confetti Color Rotation)
// ====================================================================
async function loadProfiles() {
  try {
    const res = await fetch("/api/profiles");
    if (!res.ok) throw new Error("Failed to fetch profiles");
    const data = await res.json();
    appState.profiles = data;
    renderProfiles(data);
  } catch (err) {
    console.error("Lỗi nạp profiles:", err);
    profilesGrid.innerHTML = `<div class="loading-state">Không thể tải danh sách tài khoản: ${err.message}</div>`;
  }
}

function renderProfiles(profiles) {
  if (profileCountDisplay) {
    profileCountDisplay.innerText = profiles.length;
  }
  if (profilesBadge) {
    profilesBadge.innerText = `${profiles.length} PROFILES`;
  }

  if (!profiles || profiles.length === 0) {
    profilesGrid.innerHTML = `
      <div class="loading-state">
        <p>Chưa có tài khoản nào được cấu hình.</p>
        <button class="btn btn-candy btn-sm mt-2" onclick="openAddProfileModal()">+ Thêm Tài Khoản Đầu Tiên</button>
      </div>`;
    return;
  }

  profilesGrid.innerHTML = "";

  // Hand-Drawn Post-It & Marker Color Palettes for Account Badges
  const avatarColors = ["#fef08a", "#fbcfe8", "#d1fae5", "#bae6fd"];
  const avatarTextColors = ["#854d0e", "#9d174d", "#065f46", "#0369a1"];

  profiles.forEach((p, idx) => {
    const isThisRunning = appState.isRunning && appState.currentTask && String(appState.currentTask.profile_id) === String(p.id);
    const card = document.createElement("div");
    card.className = `profile-sticker-card ${isThisRunning ? "running" : ""}`;
    card.id = `profile-card-${p.id}`;

    const statusClass = isThisRunning ? "status-running" : "status-ready";
    const statusText = isThisRunning ? "ĐANG TÌM KIẾM" : "SẴN SÀNG";

    const colIdx = idx % 4;
    const bgCol = avatarColors[colIdx] || "#fef08a";
    const txtCol = avatarTextColors[colIdx] || "#854d0e";

    // Action segments: If this profile is running, show prominent "🛑 DỪNG TÌM KIẾM" button!
    let segmentsHtml = "";
    if (isThisRunning) {
      segmentsHtml = `
        <div class="card-run-segments running-mode">
          <button class="btn btn-stop-running-task" onclick="stopProfile('${p.id}')" title="Dừng ngay lượt tìm kiếm của tài khoản này">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect></svg>
            <span>🛑 DỪNG TÌM KIẾM (ACC #${p.id})</span>
          </button>
        </div>
      `;
    } else {
      const isOtherRunning = appState.isRunning;
      segmentsHtml = `
        <div class="card-run-segments">
          <button class="btn btn-segment" onclick="runSingleProfile('${p.id}', 'desktop')" ${isOtherRunning ? "disabled" : ""} title="Tìm kiếm Desktop (31 lượt)">
            🖥️ PC (31)
          </button>
          <button class="btn btn-segment" onclick="runSingleProfile('${p.id}', 'mobile')" ${isOtherRunning ? "disabled" : ""} title="Tìm kiếm Mobile (21 lượt)">
            📱 Mob (21)
          </button>
          <button class="btn btn-segment btn-segment-full" onclick="runSingleProfile('${p.id}', 'all')" ${isOtherRunning ? "disabled" : ""} title="Chạy cả Desktop và Mobile">
            ⚡ Full (52)
          </button>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="tape-strip"></div>
      <div class="card-identity-row">
        <div class="identity-left">
          <div class="profile-avatar-pill" style="background-color: ${bgCol}; color: ${txtCol};">#${p.id}</div>
          <div class="identity-text">
            <span class="account-name-title" title="${escapeHtml(p.name)}">${escapeHtml(p.name)}</span>
            <span class="account-path-code">${escapeHtml(p.path)}</span>
          </div>
        </div>
        <span class="card-status-pill ${statusClass}">${statusText}</span>
      </div>

      ${segmentsHtml}

      <div class="card-utilities-row">
        <button class="btn btn-login-edge" onclick="loginProfile('${p.id}')" title="Mở Edge độc lập để đăng nhập tài khoản lần đầu hoặc kiểm tra điểm">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>
          <span>🔑 Đăng Nhập Edge</span>
        </button>
        <button class="btn-icon-circle danger-subtle" onclick="stopProfile('${p.id}')" title="Dừng tìm kiếm hoặc đóng tiến trình Edge của tài khoản này">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect></svg>
        </button>
        <button class="btn-icon-circle" onclick="unlockProfile('${p.id}')" title="Giải phóng file lock và đóng tiến trình treo nếu có">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 2l-2 2m-14 14l-2 2m18-18l-4 4m-10 10l-4 4m14-14l-2 2m-6 6l-2 2"></path></svg>
        </button>
        <button class="btn-icon-circle" onclick="openEditProfileModal('${p.id}', '${escapeHtml(p.name)}', '${escapeHtml(p.path)}')" title="Đổi tên hoặc thư mục lưu">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
        </button>
        <button class="btn-icon-circle danger" onclick="deleteProfile('${p.id}')" title="Xóa tài khoản khỏi danh sách">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        </button>
      </div>
    `;

    profilesGrid.appendChild(card);
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

    // Nếu trạng thái hoạt động thay đổi, cập nhật ngay giao diện profile card để hiện/ẩn nút Dừng
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
    botStatusText.innerText = `Active: ${appState.currentTask.profile_name || "Profile"}`;

    if (kpiEngineStatus) {
      kpiEngineStatus.innerText = "RUNNING";
      kpiEngineStatus.className = "chip-val text-pink";
    }
    if (kpiEngineSub) {
      kpiEngineSub.innerText = `ACC ${appState.currentTask.current_index}/${appState.currentTask.total_profiles}`;
    }
    if (activeAccountNotice) {
      activeAccountNotice.innerText = `Đang chạy: ${appState.currentTask.profile_name} (Chế độ: ${appState.currentTask.mode.toUpperCase()})`;
    }

    btnRunAllFull.disabled = true;
    btnRunAllPC.disabled = true;
    btnRunAllMobile.disabled = true;
    btnStopAll.disabled = false;
  } else {
    botStatusPill.className = "chip-status idle";
    botStatusText.innerText = "Ready (Idle)";

    if (kpiEngineStatus) {
      kpiEngineStatus.innerText = "READY";
      kpiEngineStatus.className = "chip-val text-mint";
    }
    if (kpiEngineSub) {
      kpiEngineSub.innerText = "WAITING";
    }
    if (activeAccountNotice) {
      activeAccountNotice.innerText = "Sẵn sàng nhận lệnh điều khiển";
    }

    btnRunAllFull.disabled = false;
    btnRunAllPC.disabled = false;
    btnRunAllMobile.disabled = false;
    btnStopAll.disabled = true;
  }

  // Update button states inside cards
  const segmentButtons = profilesGrid.querySelectorAll(".btn-segment");
  segmentButtons.forEach(btn => {
    btn.disabled = appState.isRunning;
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

async function loginProfile(profileId) {
  try {
    const res = await fetch(`/api/profiles/${profileId}/login`, { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      alert("✅ Cửa sổ Microsoft Edge đã được mở độc lập!\n\nBạn hãy đăng nhập tài khoản Microsoft trên cửa sổ đó. Khi xong, hãy đóng cửa sổ Edge lại.");
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
