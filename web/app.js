/**
 * web/app.js
 * ==========
 * Điều phối chính (Main Coordinator) của ứng dụng giao diện Microsoft Rewards Auto.
 * Khởi tạo hệ thống, đồng bộ trạng thái bot chu kỳ và quản lý sự kiện điều khiển chung.
 * Tuân thủ rule 01_architecture (< 250 dòng) và rule 03_web_fullstack.
 */

async function loadStatus() {
  try {
    const data = await ApiService.getStatus();
    const wasRunning = appState.isRunning;
    const wasAndroidRunning = appState.isAndroidRunning;
    const prevTaskId = appState.currentTask?.profile_id;

    appState.isRunning = Boolean(data.pc_is_running !== undefined ? data.pc_is_running : data.is_running);
    appState.isAndroidRunning = Boolean(data.android_is_running);
    appState.currentTask = data.current_task;
    appState.androidTask = data.android_task;

    updateUIState();

    if (wasRunning !== appState.isRunning || wasAndroidRunning !== appState.isAndroidRunning || prevTaskId !== appState.currentTask?.profile_id) {
      if (appState.profiles?.length > 0) renderProfiles(appState.profiles);
      loadAndroidStatus();
    }
  } catch (err) {
    console.error("Lỗi lấy status:", err);
  }
}

function updateUIState() {
  if (appState.isRunning && appState.currentTask) {
    if (botStatusPill) botStatusPill.className = "chip-status running";
    if (botStatusText) botStatusText.innerText = `Đang chạy: ${appState.currentTask.profile_name || "Profile"}`;
    if (activeAccountNotice) activeAccountNotice.innerText = `Đang chạy: ${appState.currentTask.profile_name} (${(appState.currentTask.mode || "").toUpperCase()})`;
    if (btnRunAllFull) btnRunAllFull.disabled = true;
    if (btnRunAllPC) btnRunAllPC.disabled = true;
    if (btnRunAllMobile) btnRunAllMobile.disabled = true;
  } else {
    if (botStatusPill) botStatusPill.className = "chip-status idle";
    if (botStatusText) botStatusText.innerText = "Sẵn sàng (Idle)";
    if (activeAccountNotice) activeAccountNotice.innerText = "Sẵn sàng nhận lệnh điều khiển";
    if (btnRunAllFull) btnRunAllFull.disabled = false;
    if (btnRunAllPC) btnRunAllPC.disabled = false;
    if (btnRunAllMobile) btnRunAllMobile.disabled = false;
  }

  if (btnStopAll) {
    btnStopAll.disabled = !(appState.isRunning || appState.isAndroidRunning);
  }

  // Metadata Inspector
  const task = appState.currentTask;
  const isRunning = appState.isRunning && Boolean(task);

  if (metaModeBadge) {
    if (isRunning) {
      let modeName = `Đang chạy: ${(task.mode || "").toUpperCase()}`;
      if (task.mode === "desktop") modeName = "PC Search (31 lượt)";
      else if (task.mode === "mobile") modeName = "Mobile Search (21 lượt)";
      else if (task.mode === "all") modeName = "Full (PC + Mobile)";
      metaModeBadge.className = "meta-chip chip-running";
      metaModeBadge.innerText = modeName;
    } else {
      metaModeBadge.className = "meta-chip chip-idle";
      metaModeBadge.innerText = "Sẵn sàng (Idle)";
    }
  }

  if (isRunning && task.mode === "mobile") {
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

  // Update quick run buttons in profile table
  const runButtons = document.querySelectorAll(".run-buttons-group .btn");
  runButtons.forEach(btn => {
    btn.disabled = btn.dataset.unlogged === "true" ? true : appState.isRunning;
  });
}

async function runTask(profileId, mode) {
  try {
    await ApiService.runTask(profileId, mode);
    await loadStatus();
    await loadProfiles();
  } catch (err) {
    alert(`[Lỗi] ${err.message}`);
  }
}

async function stopBot() {
  if (!confirm("Xác nhận DỪNG KHẨN CẤP toàn bộ tác vụ bot đang chạy?")) return;
  try {
    await ApiService.stopBot();
    await loadStatus();
    await loadProfiles();
  } catch (err) {
    alert(`Lỗi khi dừng bot: ${err.message}`);
  }
}

function setupEventListeners() {
  btnRunAllFull?.addEventListener("click", () => runTask("all", "all"));
  btnRunAllPC?.addEventListener("click", () => runTask("all", "desktop"));
  btnRunAllMobile?.addEventListener("click", () => runTask("all", "mobile"));
  btnStopAll?.addEventListener("click", stopBot);

  btnOpenAddProfile?.addEventListener("click", openAddProfileModal);
  btnOpenSettings?.addEventListener("click", openSettingsModal);
  btnOpenKeywords?.addEventListener("click", openKeywordsModal);

  if (btnRunAndroidCheckin) {
    btnRunAndroidCheckin.addEventListener("click", runAndroidCheckin);
  }

  btnClearLogs?.addEventListener("click", clearTerminalLogs);
  btnDownloadLogs?.addEventListener("click", downloadTerminalLogs);
}

document.addEventListener("DOMContentLoaded", () => {
  initTerminalControls();
  initWebSocket();
  initPublicIp();
  loadProfiles();
  loadStatus();
  loadAndroidStatus();
  recoverLiveSearchesFromLogs();
  setupEventListeners();

  setInterval(loadStatus, 3000);
});
