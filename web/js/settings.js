/**
 * web/js/settings.js
 * ==================
 * Quản lý Cài đặt hệ thống (Settings Modal), Kho từ khóa tìm kiếm (Keywords Modal & AI Seed) và Metadata IP.
 * Tuân thủ rule 01_architecture (< 250 dòng) và rule 03_web_fullstack.
 */

async function openSettingsModal() {
  try {
    const data = await ApiService.getConfig();
    const sc = data.search_settings || {};
    const bc = data.browser_settings || {};
    const ac = data.android_settings || {};

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
    if (bc.mobile_device_name) document.getElementById("cfgMobileDevice").value = bc.mobile_device_name;

    const elAndroidEnabled = document.getElementById("cfgAndroidEnabled");
    const elAndroidAuto = document.getElementById("cfgAndroidAutoRun");
    const elAndroidDev = document.getElementById("cfgAndroidDevice");
    const elAndroidPin = document.getElementById("cfgAndroidPin");
    const elAndroidPkg = document.getElementById("cfgAndroidPackage");

    if (elAndroidEnabled) elAndroidEnabled.checked = ac.enabled !== false;
    if (elAndroidAuto) elAndroidAuto.checked = ac.auto_checkin_after_search !== false;
    if (elAndroidDev) elAndroidDev.value = ac.device_address || "100.71.117.39:5555";
    if (elAndroidPin) elAndroidPin.value = ac.pin || "";
    if (elAndroidPkg) elAndroidPkg.value = ac.package_name || "com.microsoft.bing";

    settingsModal?.classList.remove("hidden");
  } catch (err) {
    alert(`Lỗi nạp cấu hình: ${err.message}`);
  }
}

function closeSettingsModal() {
  settingsModal?.classList.add("hidden");
}

settingsForm?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    search_settings: {
      pc_searches: parseInt(document.getElementById("cfgPcSearches").value, 10) || 31,
      mobile_searches: parseInt(document.getElementById("cfgMobileSearches").value, 10) || 21,
      min_delay_seconds: parseInt(document.getElementById("cfgMinDelay").value, 10) || 12,
      max_delay_seconds: parseInt(document.getElementById("cfgMaxDelay").value, 10) || 22,
      enable_cooldown_batches: document.getElementById("cfgEnableBatch").checked,
      batch_size: parseInt(document.getElementById("cfgBatchSize").value, 10) || 4,
      batch_cooldown_minutes: parseInt(document.getElementById("cfgBatchCooldown").value, 10) || 3,
      enable_smooth_scrolling: document.getElementById("cfgSmoothScroll").checked,
      enable_mouse_movement: document.getElementById("cfgMouseMovement").checked,
      random_click_chance: parseFloat(document.getElementById("cfgClickChance").value) || 0.25
    },
    browser_settings: {
      headless: document.getElementById("cfgHeadless").checked,
      mobile_device_name: document.getElementById("cfgMobileDevice").value
    },
    android_settings: {
      enabled: document.getElementById("cfgAndroidEnabled")?.checked ?? true,
      auto_checkin_after_search: document.getElementById("cfgAndroidAutoRun")?.checked ?? true,
      device_address: document.getElementById("cfgAndroidDevice")?.value.trim() || "100.71.117.39:5555",
      pin: document.getElementById("cfgAndroidPin")?.value.trim() || "",
      package_name: document.getElementById("cfgAndroidPackage")?.value.trim() || "com.microsoft.bing"
    }
  };

  try {
    await ApiService.saveConfig(payload);
    closeSettingsModal();
    alert("💾 Cấu hình đã được lưu thành công!");
    await loadAndroidStatus();
  } catch (err) {
    alert(`Lỗi lưu cấu hình: ${err.message}`);
  }
});

async function openKeywordsModal() {
  try {
    const data = await ApiService.getKeywords();
    if (keywordsEditor) keywordsEditor.value = data.content || "";
    if (keywordsCountDisplay) keywordsCountDisplay.innerText = data.count || 0;
    keywordsModal?.classList.remove("hidden");
  } catch (err) {
    alert(`Lỗi nạp từ khóa: ${err.message}`);
  }
}

function closeKeywordsModal() {
  keywordsModal?.classList.add("hidden");
}

keywordsEditor?.addEventListener("input", () => {
  const lines = keywordsEditor.value.split("\n")
    .map(l => l.trim())
    .filter(l => l && !l.startsWith("#"));
  if (keywordsCountDisplay) keywordsCountDisplay.innerText = lines.length;
});

btnSaveKeywords?.addEventListener("click", async () => {
  setButtonLoading(btnSaveKeywords, true, "Đang lưu...");
  try {
    const data = await ApiService.saveKeywords(keywordsEditor.value);
    if (keywordsCountDisplay && data.count !== undefined) {
      keywordsCountDisplay.innerText = data.count;
    }
    closeKeywordsModal();
    alert(`💾 Đã lưu thành công kho ${data.count} từ khóa tìm kiếm!`);
  } catch (err) {
    alert(`Lỗi lưu từ khóa: ${err.message}`);
  } finally {
    setButtonLoading(btnSaveKeywords, false);
  }
});

btnSeedKeywords?.addEventListener("click", async () => {
  if (btnSeedKeywords.disabled) return;
  const btnSeedKeywordsText = document.getElementById("btnSeedKeywordsText");
  const aiKeywordsStatus = document.getElementById("aiKeywordsStatus");
  const originalText = btnSeedKeywordsText?.innerText || "✨ AI Thêm 50 Từ Khóa Mới";

  setButtonLoading(btnSeedKeywords, true, "Đang gọi AI...");
  if (aiKeywordsStatus) {
    aiKeywordsStatus.style.color = "#38BDF8";
    aiKeywordsStatus.innerText = "Đang tạo...";
  }

  try {
    const data = await ApiService.generateAiKeywords(50, keywordsEditor.value);
    const newKws = data.new_keywords || [];

    if (data.updated_content !== undefined) {
      keywordsEditor.value = data.updated_content;
      if (keywordsCountDisplay) keywordsCountDisplay.innerText = data.total_count || 0;
    } else {
      const currentVal = keywordsEditor.value.trim();
      keywordsEditor.value = currentVal ? `${currentVal}\n${newKws.join("\n")}` : newKws.join("\n");
      const allValid = keywordsEditor.value.split("\n").filter(l => l.trim() && !l.trim().startsWith("#"));
      if (keywordsCountDisplay) keywordsCountDisplay.innerText = allValid.length;
    }

    if (aiKeywordsStatus) {
      aiKeywordsStatus.style.color = "#10B981";
      aiKeywordsStatus.innerText = `+${newKws.length} từ mới!`;
      setTimeout(() => { if (aiKeywordsStatus) aiKeywordsStatus.innerText = ""; }, 5000);
    }
    keywordsEditor.scrollTop = keywordsEditor.scrollHeight;
    alert(`🎉 Thành công! AI đã sinh ${newKws.length} từ khóa mới!\nTổng kho hiện tại: ${keywordsCountDisplay?.innerText || 0} từ khóa.`);
  } catch (err) {
    alert(`❌ Lỗi AI tạo từ khóa: ${err.message}`);
    if (aiKeywordsStatus) {
      aiKeywordsStatus.style.color = "#EF4444";
      aiKeywordsStatus.innerText = "Lỗi!";
    }
  } finally {
    setButtonLoading(btnSeedKeywords, false);
    if (btnSeedKeywordsText) btnSeedKeywordsText.innerText = originalText;
  }
});

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
  } catch (e) { }
}

async function recoverLiveSearchesFromLogs() {
  try {
    const logs = await ApiService.getLogs();
    if (Array.isArray(logs)) {
      logs.forEach(l => {
        const text = l.text || "";
        const pcMatch = text.match(/\[(?:PC|Desktop)\s*#?(\d+)\/(\d+)\]/i);
        if (pcMatch) appState.liveSearches.desktopCount = Math.max(appState.liveSearches.desktopCount, parseInt(pcMatch[1], 10));
        const mobMatch = text.match(/\[Mobile\s*#?(\d+)\/(\d+)\]/i);
        if (mobMatch) appState.liveSearches.mobileCount = Math.max(appState.liveSearches.mobileCount, parseInt(mobMatch[1], 10));
      });
    }
  } catch (e) { }
}

function populatePointsProfileSelect() { }
function updateInspectorPointsUI() { }
