/**
 * web/js/state.js
 * ================
 * Quản lý trạng thái ứng dụng (appState), các DOM element references và các hàm tiện ích dùng chung.
 * Tuân thủ rule 01_architecture (< 250 dòng) và rule 03_web_fullstack.
 */

let appState = {
  profiles: [],
  isRunning: false,         // PC Bot đang chạy
  isAndroidRunning: false,  // Android Bot đang chạy
  currentTask: null,
  androidTask: null,
  screenAwake: null,        // true = Sáng/Awake, false = Tắt/Asleep
  ws: null,
  reconnectTimer: null,
  publicIp: "1.52.0.121",
  liveSearches: {
    desktopCount: 0,
    mobileCount: 0
  },
  checkingProfiles: new Set()
};

// DOM References - Profiles & Header
const profilesListBody = document.getElementById("profilesListBody") || document.getElementById("profilesGrid");
const profileCountDisplay = document.getElementById("profileCountDisplay");
const profilesBadge = document.getElementById("profilesBadge");
const connectionStatus = document.getElementById("connectionStatus");
const connStatusText = document.getElementById("connStatusText");
const botStatusPill = document.getElementById("botStatusPill");
const botStatusText = document.getElementById("botStatusText");
const activeAccountNotice = document.getElementById("activeAccountNotice");

// DOM References - Terminal Log
const terminalSection = document.getElementById("terminalSection");
const terminalResizer = document.getElementById("terminalResizer");
const terminalLogBody = document.getElementById("terminalLogBody");
const chkAutoScroll = document.getElementById("chkAutoScroll");
const terminalCollapsedPreview = document.getElementById("terminalCollapsedPreview");
const previewText = document.getElementById("previewText");
const logCounter = document.getElementById("logCounter");
const btnCollapseTerminal = document.getElementById("btnCollapseTerminal");
const btnNormalTerminal = document.getElementById("btnNormalTerminal");
const btnMaximizeTerminal = document.getElementById("btnMaximizeTerminal");
const btnClearLogs = document.getElementById("btnClearLogs");
const btnDownloadLogs = document.getElementById("btnDownloadLogs");

// DOM References - Action Hub Buttons
const btnRunAllFull = document.getElementById("btnRunAllFull");
const btnRunAllPC = document.getElementById("btnRunAllPC");
const btnRunAllMobile = document.getElementById("btnRunAllMobile");
const btnRunAndroidCheckin = document.getElementById("btnRunAndroidCheckin");
const btnStopAll = document.getElementById("btnStopAll");
const btnOpenAddProfile = document.getElementById("btnOpenAddProfile");
const btnOpenSettings = document.getElementById("btnOpenSettings");
const btnOpenKeywords = document.getElementById("btnOpenKeywords");

// DOM References - Android Component
const checkinStatusBadge = document.getElementById("checkinStatusBadge");
const checkinStatusLabel = document.getElementById("checkinStatusLabel");
const checkinDevice = document.getElementById("checkinDevice");
const checkinLastTime = document.getElementById("checkinLastTime");
const checkinAutoStatus = document.getElementById("checkinAutoStatus");
const checkinAutoToggle = document.getElementById("checkinAutoToggle");
const checkinCallout = document.getElementById("checkinCallout");
const checkinMessageText = document.getElementById("checkinMessageText");
const checkinThumbStrip = document.getElementById("checkinThumbStrip");
const checkinNoThumb = document.getElementById("checkinNoThumb");
const checkinThumbBefore = document.getElementById("checkinThumbBefore");
const checkinThumbAfter = document.getElementById("checkinThumbAfter");
const btnCardRunCheckin = document.getElementById("btnCardRunCheckin");
const btnCardRunCheckinText = document.getElementById("btnCardRunCheckinText");
const btnCardPreviewFrame = document.getElementById("btnCardPreviewFrame");
const checkinAppBadge = document.getElementById("checkinAppBadge");
const checkinAppLabel = document.getElementById("checkinAppLabel");
const checkinScreenBadge = document.getElementById("checkinScreenBadge");
const checkinScreenLabel = document.getElementById("checkinScreenLabel");
const btnToggleScreen = document.getElementById("btnToggleScreen");
const screenToggleIcon = document.getElementById("screenToggleIcon");
const screenToggleText = document.getElementById("screenToggleText");
const checkinPingDot = document.getElementById("checkinPingDot");
const checkinNetBadge = document.getElementById("checkinNetBadge");
const checkinConnStatus = document.getElementById("checkinConnStatus");
const btnCheckBingApp = document.getElementById("btnCheckBingApp");
const btnOpenBingApp = document.getElementById("btnOpenBingApp");
const btnCloseBingApp = document.getElementById("btnCloseBingApp");

// DOM References - Modals
const androidFrameModal = document.getElementById("androidFrameModal");
const imgFrameBefore = document.getElementById("imgFrameBefore");
const imgFrameAfter = document.getElementById("imgFrameAfter");
const frameDetails = document.getElementById("frameDetails");
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

// DOM References - Metadata Inspector
const metaModeBadge = document.getElementById("metaModeBadge");
const metaIpAddress = document.getElementById("metaIpAddress");
const metaDelay = document.getElementById("metaDelay");
const metaViewport = document.getElementById("metaViewport");
const metaUserAgent = document.getElementById("metaUserAgent");
const hintPlatform = document.getElementById("hintPlatform");
const hintMobile = document.getElementById("hintMobile");

/**
 * Xử lý chuỗi HTML an toàn, chống XSS
 */
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Khóa nút chống bấm đúp (Anti-Double Click) và hiển thị loading spinner
 */
function setButtonLoading(btn, isLoading, loadingText = "Đang xử lý...") {
  if (!btn) return;
  if (isLoading) {
    if (!btn.dataset.origHtml) {
      btn.dataset.origHtml = btn.innerHTML;
    }
    btn.disabled = true;
    btn.classList.add("btn-loading");
    btn.innerHTML = `<span class="spinner-mini"></span> <span>${loadingText}</span>`;
  } else {
    btn.disabled = false;
    btn.classList.remove("btn-loading");
    if (btn.dataset.origHtml) {
      btn.innerHTML = btn.dataset.origHtml;
      delete btn.dataset.origHtml;
    }
  }
}

/**
 * Hiển thị thông báo Toast / Terminal log
 */
function showToast(message, type = "info") {
  console.log(`[Toast ${type}] ${message}`);
  if (typeof appendLogLine === "function") {
    appendLogLine({
      type: type === "error" ? "error" : (type === "success" ? "success" : "info"),
      time: new Date().toLocaleTimeString(),
      text: `[Hệ thống] ${message}`
    });
  }
}

/**
 * Sao chép User-Agent vào Clipboard
 */
function copyUserAgent() {
  const ua = metaUserAgent?.innerText?.trim() || "";
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
