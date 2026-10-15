/**
 * web/js/api.js
 * =============
 * Tầng dịch vụ giao tiếp Backend API (ApiService).
 * Gom toàn bộ các lệnh fetch() với cơ chế xử lý lỗi try/catch tập trung và hiển thị cảnh báo.
 * Tuân thủ rule 01_architecture (< 250 dòng) và rule 03_web_fullstack.
 */

const ApiService = {
  /**
   * Helper gửi request HTTP với xử lý JSON và báo lỗi tập trung
   */
  async request(url, options = {}) {
    try {
      const res = await fetch(url, options);
      const contentType = res.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");
      const data = isJson ? await res.json() : await res.text();

      if (!res.ok) {
        const errorMsg = (data && data.message) || `HTTP Lỗi ${res.status}: ${res.statusText}`;
        throw new Error(errorMsg);
      }
      return data;
    } catch (err) {
      console.error(`[ApiService] Lỗi request ${url}:`, err);
      showToast(`Lỗi gọi API [${url}]: ${err.message}`, "error");
      throw err;
    }
  },

  // --- Profiles Endpoints ---
  async getProfiles() {
    return this.request("/api/profiles");
  },

  async addProfile(payload) {
    return this.request("/api/profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  },

  async updateProfile(id, payload) {
    return this.request(`/api/profiles/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  },

  async deleteProfile(id) {
    return this.request(`/api/profiles/${id}`, { method: "DELETE" });
  },

  async unlockProfile(id) {
    return this.request(`/api/profiles/${id}/unlock`, { method: "POST" });
  },

  async loginProfile(id) {
    return this.request(`/api/profiles/${id}/login`, { method: "POST" });
  },

  async checkProfilePoints(id) {
    return this.request(`/api/profiles/${id}/check`, { method: "POST" });
  },

  async stopProfile(id) {
    try {
      return await this.request(`/api/profiles/${id}/stop`, { method: "POST" });
    } catch (e) {
      return await this.request("/api/stop", { method: "POST" });
    }
  },

  // --- PC Bot Edge Endpoints ---
  async runTask(profileId, mode) {
    return this.request("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: profileId, mode: mode })
    });
  },

  async stopBot() {
    return this.request("/api/stop", { method: "POST" });
  },

  async getStatus() {
    return this.request("/api/status");
  },

  // --- Config & Settings ---
  async getConfig() {
    return this.request("/api/config");
  },

  async saveConfig(payload) {
    return this.request("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  },

  // --- Keywords & AI Seed ---
  async getKeywords() {
    return this.request("/api/keywords");
  },

  async saveKeywords(content) {
    return this.request("/api/keywords", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content })
    });
  },

  async generateAiKeywords(count = 50, currentContent = "") {
    return this.request("/api/keywords/generate-ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count, current_content: currentContent })
    });
  },

  // --- Terminal Logs & History ---
  async getLogs() {
    return this.request("/api/logs");
  },

  async clearLogs() {
    return this.request("/api/logs/clear", { method: "POST" });
  },

  async getHistory() {
    return this.request("/api/history");
  },

  // --- Android ADB Check-in ---
  async runAndroidCheckin() {
    return this.request("/api/android/checkin", { method: "POST" });
  },

  async stopAndroidCheckin() {
    return this.request("/api/android/stop", { method: "POST" });
  },

  async getAndroidStatus() {
    return this.request("/api/android/status");
  },

  async openAndroidApp() {
    return this.request("/api/android/app/open", { method: "POST" });
  },

  async closeAndroidApp() {
    return this.request("/api/android/app/close", { method: "POST" });
  },

  async turnOnAndroidScreen() {
    return this.request("/api/android/screen/on", { method: "POST" });
  },

  async turnOffAndroidScreen() {
    return this.request("/api/android/screen/off", { method: "POST" });
  },

  async toggleAndroidScreen() {
    return this.request("/api/android/screen/toggle", { method: "POST" });
  },

  async reconnectAndroid() {
    return this.request("/api/android/connect", { method: "POST" });
  },

  async getMetadata() {
    return this.request("/api/metadata");
  }
};
