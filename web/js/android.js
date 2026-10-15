/**
 * web/js/android.js
 * =================
 * Điều khiển thiết bị Android qua ADB: Điểm danh Bing App, Bật/Tắt màn hình, Mở/Đóng app, và xem ảnh chụp.
 * Tuân thủ rule 01_architecture (< 250 dòng) và rule 03_web_fullstack.
 */

async function runAndroidCheckin() {
  if (appState.isAndroidRunning) { alert("⚠️ Tiến trình điểm danh Android đang chạy rồi!"); return; }
  if (!confirm("Bắt đầu điểm danh trên App Microsoft Bing (Android qua ADB)?")) return;

  try {
    setButtonLoading(btnRunAndroidCheckin, true, "Đang chạy...");
    setButtonLoading(btnCardRunCheckin, true, "Đang kết nối ADB...");
    if (checkinStatusBadge) checkinStatusBadge.className = "checkin-status-badge badge-running";
    if (checkinStatusLabel) checkinStatusLabel.innerText = "⏳ Đang điểm danh...";
    if (checkinCallout) checkinCallout.className = "checkin-callout callout-running";
    if (checkinMessageText) checkinMessageText.innerText = "Đang kết nối Android và điểm danh trên App Bing...";

    await ApiService.runAndroidCheckin();
    await loadStatus();
    await loadAndroidStatus();
  } catch (err) {
    alert(`Lỗi điểm danh Android: ${err.message}`);
  } finally {
    setButtonLoading(btnRunAndroidCheckin, false);
    setButtonLoading(btnCardRunCheckin, false);
    setTimeout(loadAndroidStatus, 2500);
  }
}

async function loadAndroidStatus() {
  try {
    const data = await ApiService.getAndroidStatus();
    const latest = data.latest || {}, config = data.config || {}, devStatus = data.device_status || {};
    const status = latest.status || "pending", isRunning = Boolean(data.is_running);

    if (checkinDevice) checkinDevice.innerText = config.device_address || latest.device || "100.71.117.39:5555";
    if (checkinLastTime) checkinLastTime.innerText = latest.created_at || "Chưa có log điểm danh";

    const isAuto = config.auto_checkin_after_search !== false;
    if (checkinAutoToggle) checkinAutoToggle.checked = isAuto;
    if (checkinAutoStatus) {
      checkinAutoStatus.innerText = isAuto ? "Bật sau Search" : "Chạy thủ công";
      checkinAutoStatus.className = `switch-label-text ${isAuto ? "status-pill-active" : ""}`;
    }

    // Network & ADB
    const pingOk = Boolean(devStatus.ping_ok), pingMs = devStatus.ping_ms, adbState = devStatus.adb_state || "disconnected";
    if (checkinPingDot) {
      checkinPingDot.style.background = pingOk ? "#10B981" : "#EF4444";
      checkinPingDot.title = pingOk ? `Mạng Tailscale (${pingMs}ms)` : "Mất mạng Tailscale";
    }
    if (checkinNetBadge) {
      checkinNetBadge.innerText = pingOk ? `Tailscale (${pingMs}ms)` : "Mất Tailscale";
      checkinNetBadge.style.color = pingOk ? "#047857" : "#DC2626";
      checkinNetBadge.style.background = pingOk ? "#DCFCE7" : "#FEE2E2";
    }
    if (checkinConnStatus) {
      if (!pingOk) checkinConnStatus.innerHTML = '<span style="color:#DC2626; font-weight:600;">✗ Mất VPN</span>';
      else if (adbState === "device") checkinConnStatus.innerHTML = '<span style="color:#10B981; font-weight:600;">✓ Sẵn sàng ADB</span>';
      else if (adbState === "offline") checkinConnStatus.innerHTML = '<span style="color:#D97706; font-weight:600;">! ADB Offline</span>';
      else checkinConnStatus.innerHTML = '<span style="color:#DC2626; font-weight:600;">✗ Cổng 5555 đóng</span>';
    }

    // Screen State
    appState.screenAwake = devStatus.screen_awake;
    if (checkinScreenBadge && checkinScreenLabel) {
      checkinScreenBadge.className = "checkin-status-badge";
      if (appState.screenAwake === true) {
        checkinScreenBadge.classList.add("badge-screen-awake");
        checkinScreenLabel.innerText = "🟢 Màn hình: Bật";
      } else if (appState.screenAwake === false) {
        checkinScreenBadge.classList.add("badge-screen-asleep");
        checkinScreenLabel.innerText = "⚪ Màn hình: Tắt";
      } else {
        checkinScreenBadge.classList.add("badge-idle");
        checkinScreenLabel.innerText = "⚪ Màn hình: --";
      }
    }

    if (btnToggleScreen && screenToggleIcon && screenToggleText) {
      const awake = appState.screenAwake === true;
      btnToggleScreen.className = `btn-app-action btn-screen-toggle ${awake ? "btn-screen-off" : "btn-screen-on"}`;
      screenToggleIcon.innerText = awake ? "💤" : "⚡";
      screenToggleText.innerText = awake ? "Tắt Màn Hình (OFF)" : "Bật ĐT (ON)";
    }

    // App State
    const appSt = devStatus.app_status || "unknown";
    if (checkinAppBadge && checkinAppLabel) {
      const appMap = {
        foreground: ["badge-app-fg", "🟢 App: Đang mở"],
        background: ["badge-app-bg", "🟡 App: Chạy ngầm"],
        closed: ["badge-app-closed", "⚪ App: Đã tắt"]
      };
      const [cls, txt] = appMap[appSt] || ["badge-app-unreachable", "🔴 App: Mất kết nối"];
      checkinAppBadge.className = `checkin-status-badge ${cls}`;
      checkinAppLabel.innerText = txt;
    }

    // Checkin Status Badges & Buttons
    if (isRunning) {
      if (checkinStatusBadge) checkinStatusBadge.className = "checkin-status-badge badge-running";
      if (checkinStatusLabel) checkinStatusLabel.innerText = "⏳ Đang điểm danh...";
      if (checkinCallout) checkinCallout.className = "checkin-callout callout-running";
      if (checkinMessageText) checkinMessageText.innerText = "Bot đang điều khiển App Bing trên Android...";
      [btnCardRunCheckin, btnRunAndroidCheckin, btnOpenBingApp, btnCloseBingApp, btnCheckBingApp, btnToggleScreen].forEach(b => { if (b) b.disabled = true; });
    } else {
      [btnOpenBingApp, btnCloseBingApp, btnCheckBingApp, btnToggleScreen].forEach(b => { if (b) b.disabled = false; });
      if (btnCardRunCheckin) btnCardRunCheckin.disabled = false;

      if (status === "completed") {
        if (checkinStatusBadge) checkinStatusBadge.className = "checkin-status-badge badge-success";
        if (checkinStatusLabel) checkinStatusLabel.innerText = "✓ Đã điểm danh hôm nay";
        if (checkinCallout) checkinCallout.className = "checkin-callout callout-success";
        if (checkinMessageText) checkinMessageText.innerText = (devStatus.message ? `${devStatus.message} • ` : "") + (latest.message || "Điểm danh hoàn tất!");
        if (btnCardRunCheckinText) btnCardRunCheckinText.innerText = "🔄 Điểm Danh Lại";
      } else if (status === "failed" || status === "error") {
        if (checkinStatusBadge) checkinStatusBadge.className = "checkin-status-badge badge-error";
        if (checkinStatusLabel) checkinStatusLabel.innerText = "! Lỗi / Chưa xong";
        if (checkinCallout) checkinCallout.className = "checkin-callout callout-error";
        if (checkinMessageText) checkinMessageText.innerText = devStatus.message || latest.message || "Lỗi hoặc không tìm thấy nút Rewards.";
        if (btnCardRunCheckinText) btnCardRunCheckinText.innerText = "⚡ Thử Lại Ngay";
      } else {
        if (checkinStatusBadge) checkinStatusBadge.className = "checkin-status-badge badge-idle";
        if (checkinStatusLabel) checkinStatusLabel.innerText = "Chưa điểm danh";
        if (checkinCallout) checkinCallout.className = "checkin-callout callout-idle";
        if (checkinMessageText) checkinMessageText.innerText = devStatus.message || "Sẵn sàng điểm danh tích streak trên App Bing.";
        if (btnCardRunCheckinText) btnCardRunCheckinText.innerText = "📱 Điểm Danh Ngay";
      }
    }

    // Screenshots with anti-cache timestamp
    const hasFrames = Boolean(latest.frame_before || latest.frame_after);
    const t = Date.now();
    if (checkinThumbStrip && checkinNoThumb) {
      checkinThumbStrip.classList.toggle("hidden", !hasFrames);
      checkinNoThumb.classList.toggle("hidden", hasFrames);
      if (hasFrames) {
        if (checkinThumbBefore) checkinThumbBefore.src = `/screenshots/android_checkin_before.png?t=${t}`;
        if (checkinThumbAfter) checkinThumbAfter.src = `/screenshots/android_checkin_after.png?t=${t}`;
      }
    }
    if (btnCardPreviewFrame) btnCardPreviewFrame.style.display = hasFrames ? "inline-flex" : "none";
    if (frameDetails) {
      frameDetails.innerHTML = `Trạng thái: <strong>${status.toUpperCase()}</strong> • Thiết bị: <code>${latest.device || "100.71.117.39:5555"}</code> • Ghi nhận: <em>${latest.created_at || "Hôm nay"}</em><br><small style="color:#9CA3AF;">${latest.message || ""}</small>`;
    }
  } catch (e) { console.error("Lỗi Android status:", e); }
}

async function checkBingAppStatus(showAlert = false) {
  setButtonLoading(btnCheckBingApp, true, "Đang check...");
  try {
    await loadAndroidStatus();
    if (showAlert) {
      const data = await ApiService.getAndroidStatus(), ds = data.device_status || {};
      let info = `[KẾT QUẢ KIỂM TRA ĐIỆN THOẠI]\n\n`;
      info += `• Mạng Tailscale: ${ds.ping_ok ? `Đã kết nối (${ds.ping_ms}ms)` : "Mất kết nối"}\n`;
      info += `• Cổng ADB: ${ds.adb_state}\n`;
      if (ds.screen_awake !== null) info += `• Màn hình: ${ds.screen_awake ? "BẬT (Awake)" : "TẮT (Asleep)"}\n`;
      info += `• App Bing: ${String(ds.app_status || "unknown").toUpperCase()} (${ds.message || ""})\n`;
      alert(info);
    }
  } catch (e) {
    if (showAlert) alert(`Lỗi kiểm tra: ${e.message}`);
  } finally {
    setButtonLoading(btnCheckBingApp, false);
  }
}

async function openBingApp() {
  setButtonLoading(btnOpenBingApp, true, "Đang mở...");
  try {
    const res = await ApiService.openAndroidApp();
    alert(`[Thành công] ${res.message || "Đã mở App Bing!"}`);
    await loadAndroidStatus();
  } catch (e) {
    alert(`Lỗi mở App: ${e.message}`);
  } finally {
    setButtonLoading(btnOpenBingApp, false);
  }
}

async function closeBingApp() {
  setButtonLoading(btnCloseBingApp, true, "Đang tắt...");
  try {
    const res = await ApiService.closeAndroidApp();
    alert(`[Thành công] ${res.message || "Đã tắt App Bing!"}`);
    await loadAndroidStatus();
  } catch (e) {
    alert(`Lỗi tắt App: ${e.message}`);
  } finally {
    setButtonLoading(btnCloseBingApp, false);
  }
}

async function toggleScreenPhone() {
  setButtonLoading(btnToggleScreen, true, "Đang xử lý...");
  try {
    const res = appState.screenAwake ? await ApiService.turnOffAndroidScreen() : await ApiService.turnOnAndroidScreen();
    alert(`[Điện Thoại] ${res.message || "Thao tác thành công!"}`);
  } catch (e) {
    alert(`Lỗi thao tác điện thoại: ${e.message}`);
  } finally {
    setButtonLoading(btnToggleScreen, false);
    await loadAndroidStatus();
  }
}

async function reconnectAndroidDevice() {
  try {
    if (checkinConnStatus) checkinConnStatus.innerText = "Đang kết nối lại...";
    const res = await ApiService.reconnectAndroid();
    alert(`[Kết nối] ${res.message}`);
    await loadAndroidStatus();
  } catch (e) {
    alert(`Lỗi kết nối: ${e.message}`);
  }
}

async function toggleAutoCheckin(enabled) {
  try {
    await ApiService.saveConfig({ android_settings: { auto_checkin_after_search: enabled } });
    if (checkinAutoStatus) {
      checkinAutoStatus.innerText = enabled ? "Bật sau Search" : "Chạy thủ công";
      checkinAutoStatus.className = `switch-label-text ${enabled ? "status-pill-active" : ""}`;
    }
  } catch (e) { console.error("Lỗi toggle auto checkin:", e); }
}

function openFrameModal() {
  if (androidFrameModal) {
    const t = Date.now();
    if (imgFrameBefore) imgFrameBefore.src = `/screenshots/android_checkin_before.png?t=${t}`;
    if (imgFrameAfter) imgFrameAfter.src = `/screenshots/android_checkin_after.png?t=${t}`;
    androidFrameModal.classList.remove("hidden");
  }
}

function closeFrameModal() {
  androidFrameModal?.classList.add("hidden");
}
