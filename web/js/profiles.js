/**
 * web/js/profiles.js
 * ==================
 * Quản lý danh sách tài khoản Edge: Thêm/Sửa/Xóa, Đăng nhập, Mở khóa, Check điểm và chạy đơn lẻ.
 * Tuân thủ rule 01_architecture (< 250 dòng) và rule 03_web_fullstack.
 */

async function loadProfiles() {
  try {
    const data = await ApiService.getProfiles();
    appState.profiles = Array.isArray(data) ? data : (data.profiles || []);
    renderProfiles(appState.profiles);
  } catch (err) {
    if (profilesListBody) {
      profilesListBody.innerHTML = `<tr><td colspan="6" class="loading-state">Không thể tải danh sách tài khoản: ${err.message}</td></tr>`;
    }
  }
}

function renderProfiles(profiles) {
  if (profileCountDisplay) profileCountDisplay.innerText = profiles.length;
  if (profilesBadge) profilesBadge.innerText = `${profiles.length} tài khoản`;
  if (!profilesListBody) return;

  if (!profiles || profiles.length === 0) {
    profilesListBody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>Chưa có tài khoản nào được cấu hình.</p><button class="btn btn-primary btn-sm mt-2" onclick="openAddProfileModal()">+ Thêm Tài Khoản Đầu Tiên</button></td></tr>`;
    return;
  }

  profilesListBody.innerHTML = "";
  profiles.forEach((p) => {
    const isThisRunning = appState.isRunning && appState.currentTask && String(appState.currentTask.profile_id) === String(p.id);
    const isChecking = appState.checkingProfiles?.has(String(p.id));
    const row = document.createElement("tr");
    row.className = `profile-row ${isThisRunning ? "is-running" : ""}`;
    row.id = `profile-row-${p.id}`;

    const hasEmail = Boolean(p.email || (p.name && p.name.includes("@")));
    const isUnlogged = p.status === "unlogged" || !hasEmail;

    let statusClass = "status-ready", statusText = "Sẵn sàng";
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

    let runCellHtml = "";
    if (isThisRunning) {
      runCellHtml = `<button class="btn btn-xs btn-stop-running" onclick="stopProfile('${p.id}')" title="Dừng lượt tìm kiếm"><svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"></rect></svg><span>Dừng Acc #${p.id}</span></button>`;
    } else if (isUnlogged) {
      runCellHtml = `<div class="run-buttons-group"><button class="btn btn-xs btn-outline" data-unlogged="true" disabled>PC</button><button class="btn btn-xs btn-outline" data-unlogged="true" disabled>Mobile</button><button class="btn btn-xs btn-primary-soft" data-unlogged="true" disabled>Full (52)</button></div>`;
    } else {
      const isOtherRunning = appState.isRunning;
      runCellHtml = `<div class="run-buttons-group"><button class="btn btn-xs btn-outline" onclick="runSingleProfile('${p.id}', 'desktop')" ${isOtherRunning ? "disabled" : ""}>PC</button><button class="btn btn-xs btn-outline" onclick="runSingleProfile('${p.id}', 'mobile')" ${isOtherRunning ? "disabled" : ""}>Mobile</button><button class="btn btn-xs btn-primary-soft" onclick="runSingleProfile('${p.id}', 'all')" ${isOtherRunning ? "disabled" : ""}>Full (52)</button></div>`;
    }

    const nameDisplay = escapeHtml(p.name);
    const pathDisplay = escapeHtml(p.path);
    const todayPts = p.today_points ? `${p.today_points} pts` : '--';
    const totalPts = p.total_points ? Number(p.total_points).toLocaleString() : '--';
    const pcPts = p.desktop_points || '0/90';
    const mobPts = p.mobile_points || '0/60';

    row.innerHTML = `
      <td class="col-id"><span class="id-badge">#${p.id}</span></td>
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
        <div class="pts-badge-cell">
          <div class="pts-today-tag"><span class="pts-today-val">${todayPts}</span><span class="pts-label">hôm nay</span></div>
          <div class="pts-breakdown-mini">
            <span class="pts-pill" title="Desktop Bing Search"><span class="pts-tag">PC</span> ${pcPts}</span>
            <span class="pts-pill" title="Mobile Bing Search"><span class="pts-tag">MOB</span> ${mobPts}</span>
            <span class="pts-pill pts-total-pill" title="Điểm khả dụng"><span class="pts-tag">TOTAL</span> ${totalPts}</span>
          </div>
        </div>
      </td>
      <td class="col-status"><span class="badge-status ${statusClass}"><span class="status-dot"></span><span>${statusText}</span></span></td>
      <td class="col-quick-run">${runCellHtml}</td>
      <td class="col-actions">
        <div class="actions-group">
          <button class="btn btn-xs btn-check ${isChecking ? 'checking' : ''}" onclick="checkProfilePoints('${p.id}')" ${isChecking || isThisRunning ? 'disabled' : ''} title="Check điểm">
            ${isChecking ? '<span class="spinner-mini"></span><span>Check...</span>' : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg><span>Check</span>'}
          </button>
          <button class="btn btn-xs btn-login ${isUnlogged ? 'btn-attention' : ''}" onclick="loginProfile('${p.id}')" title="Mở Edge đăng nhập">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg><span>Đăng nhập</span>
          </button>
          <button class="btn-icon" onclick="unlockProfile('${p.id}')" title="Mở khóa Profile"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg></button>
          <button class="btn-icon" onclick="openEditProfileModal('${p.id}', '${escapeHtml(p.name)}', '${escapeHtml(p.path)}')" title="Sửa"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg></button>
          <button class="btn-icon danger" onclick="deleteProfile('${p.id}')" title="Xóa"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
        </div>
      </td>`;
    profilesListBody.appendChild(row);
  });
}

function runSingleProfile(profileId, mode) {
  const profile = appState.profiles.find(p => String(p.id) === String(profileId));
  const hasEmail = profile && (profile.email || (profile.name && profile.name.includes("@")));
  if (profile && (profile.status === "unlogged" || !hasEmail)) {
    alert(`Tài khoản #${profileId} chưa đăng nhập!\nVui lòng bấm 'Đăng nhập' trước khi chạy bot.`);
    return;
  }
  runTask(profileId, mode);
}

async function stopProfile(profileId) {
  const p = appState.profiles.find(item => String(item.id) === String(profileId));
  const name = p ? p.name : `#${profileId}`;
  if (!confirm(`Xác nhận DỪNG tìm kiếm / đóng Edge cho ${name}?`)) return;

  try {
    await ApiService.stopProfile(profileId);
    await loadStatus();
    await loadProfiles();
  } catch (err) {
    alert(`Lỗi khi dừng profile: ${err.message}`);
  }
}

async function checkProfilePoints(profileId) {
  if (appState.checkingProfiles?.has(String(profileId))) return;
  if (appState.isRunning && appState.currentTask && String(appState.currentTask.profile_id) === String(profileId)) {
    alert("Tài khoản đang chạy tìm kiếm, vui lòng đợi xong trước khi check điểm!");
    return;
  }

  appState.checkingProfiles.add(String(profileId));
  renderProfiles(appState.profiles);

  try {
    const res = await ApiService.checkProfilePoints(profileId);
    if (res.status === "success" && res.profile) {
      const idx = appState.profiles.findIndex(p => String(p.id) === String(profileId));
      if (idx !== -1) appState.profiles[idx] = { ...appState.profiles[idx], ...res.profile };
    }
  } catch (err) {
    alert(`Lỗi check điểm: ${err.message}`);
  } finally {
    appState.checkingProfiles.delete(String(profileId));
    renderProfiles(appState.profiles);
  }
}

async function loginProfile(profileId) {
  try {
    await ApiService.loginProfile(profileId);
    alert("✅ Đã mở Microsoft Edge!\n1. Hãy đăng nhập tài khoản Microsoft trên cửa sổ đó.\n2. Xong thì ĐÓNG CỬA SỔ Edge lại.\n3. Hệ thống sẽ tự nhận diện email.");
    let count = 0;
    const poll = setInterval(async () => {
      count++;
      await loadProfiles();
      const p = appState.profiles.find(item => String(item.id) === String(profileId));
      if ((p && p.status === "ready" && (p.email || p.name?.includes("@"))) || count > 30) {
        clearInterval(poll);
      }
    }, 3000);
  } catch (err) {
    alert(`Lỗi mở Edge đăng nhập: ${err.message}`);
  }
}

async function unlockProfile(profileId) {
  try {
    await ApiService.unlockProfile(profileId);
    alert("🧹 Đã giải phóng file lock của Profile thành công!");
  } catch (err) {
    alert(`Lỗi mở khóa: ${err.message}`);
  }
}

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
  profileModal?.classList.add("hidden");
}

async function deleteProfile(profileId) {
  if (!confirm(`Xác nhận xóa Tài Khoản #${profileId}?`)) return;
  try {
    await ApiService.deleteProfile(profileId);
    await loadProfiles();
  } catch (err) {
    alert(`Lỗi xóa: ${err.message}`);
  }
}

profileForm?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = formProfileId.value.trim();
  const name = formProfileName.value.trim();
  const path = formProfilePath.value.trim();
  try {
    if (id) {
      await ApiService.updateProfile(id, { name, path });
    } else {
      await ApiService.addProfile({ name, path });
    }
    closeProfileModal();
    await loadProfiles();
  } catch (err) {
    alert(`Lỗi lưu tài khoản: ${err.message}`);
  }
});
