# -*- coding: utf-8 -*-
"""
src/api/task_manager.py
=======================
Quan ly tac vu nen (Background Tasks), tien trinh chay va hang doi log.
Tuan thu rule 01_architecture (< 250 dong) va rule 03_web_fullstack.
"""

import sys
import json
import asyncio
from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.core.paths import ROOT_DIR
from src.core.db import save_android_checkin_result
from src.bots.edge.runner import load_config
from src.bots.edge.browser import get_profile_abs_path, kill_zombie_edge_processes


async def _stream_process_logs(process, add_log_fn) -> None:
    """Doc dong stdout/stderr theo thoi gian thuc va gan nhan log tuong ung."""
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        decoded = line.decode("utf-8", errors="replace").rstrip()
        if decoded:
            ltype = "info"
            if any(k in decoded for k in ["[X]", "[!]", "Lỗi", "Error"]):
                ltype = "error"
            elif any(k in decoded for k in ["[✓]", "thành công", "HOÀN TẤT"]):
                ltype = "success"
            elif any(k in decoded for k in ["⏳", "[*]", "Tạm nghỉ"]):
                ltype = "warn"
            elif any(k in decoded for k in ["🖥️", "📱", "👆", "Tap", "Vuốt"]):
                ltype = "action"
            add_log_fn(decoded, ltype)


class BotTaskManager:
    """Dieu phoi cac tien trinh chay bot PC va Android song song khong chan Web server."""

    def __init__(self):
        self.pc_is_running = False
        self.pc_process = None
        self.pc_task_info: Optional[Dict[str, Any]] = None
        self.pc_stop_requested = False

        self.android_is_running = False
        self.android_process = None
        self.android_task_info: Optional[Dict[str, Any]] = None
        self.android_stop_requested = False

        self.log_history = deque(maxlen=600)
        self.active_websockets = set()

    @property
    def is_running(self) -> bool:
        return self.pc_is_running or self.android_is_running

    @property
    def current_process(self):
        return self.pc_process or self.android_process

    @property
    def current_task_info(self):
        return self.pc_task_info or self.android_task_info

    def add_log(self, text: str, log_type: str = "info") -> None:
        entry = {"time": datetime.now().strftime("%H:%M:%S"), "text": text, "type": log_type}
        self.log_history.append(entry)
        try:
            asyncio.create_task(self.broadcast_log(entry))
        except RuntimeError:
            pass

    async def broadcast_log(self, entry: dict) -> None:
        if not self.active_websockets:
            return
        dead_ws = set()
        payload = json.dumps(entry, ensure_ascii=False)
        for ws in self.active_websockets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_ws.add(ws)
        for ws in dead_ws:
            self.active_websockets.discard(ws)

    async def run_bot_sequence(self, profiles_to_run: List[Dict[str, Any]], mode: str) -> None:
        if self.pc_is_running:
            self.add_log("⚠️ Tiến trình tìm kiếm PC đang chạy rồi, vui lòng chờ...", "warn")
            return

        self.pc_is_running = True
        self.pc_stop_requested = False
        total = len(profiles_to_run)
        self.add_log(f"🚀 [HỆ THỐNG] Bắt đầu tìm kiếm PC cho {total} tài khoản. Chế độ: {mode.upper()}", "start")

        for idx, profile in enumerate(profiles_to_run):
            if self.pc_stop_requested:
                self.add_log("🛑 [HỆ THỐNG] Đã hủy chuỗi tác vụ PC!", "warn")
                break

            p_id = str(profile.get("id", idx + 1))
            p_name = profile.get("name", f"Profile {p_id}")
            p_dir = get_profile_abs_path(profile)

            self.pc_task_info = {
                "profile_id": p_id, "profile_name": p_name,
                "current_index": idx + 1, "total_profiles": total,
                "mode": mode, "status": "running"
            }
            self.add_log(f"▶️ [BƯỚC {idx + 1}/{total}] BẮT ĐẦU: {p_name}", "start")

            cmd = [sys.executable, "-u", str(ROOT_DIR / "edge_rewards_bot.py"), "--profile", p_id, "--mode", mode, "--non-interactive"]
            try:
                self.pc_process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=str(ROOT_DIR)
                )
                await _stream_process_logs(self.pc_process, self.add_log)
                await self.pc_process.wait()
                exit_code = self.pc_process.returncode

                if self.pc_stop_requested:
                    self.add_log(f"🛑 Đã hủy {p_name}.", "warn")
                    break
                self.add_log(f"✅ [HOÀN TẤT] {p_name} thành công!" if exit_code == 0 else f"⚠️ {p_name} kết thúc mã {exit_code}.", "success" if exit_code == 0 else "warn")
            except Exception as e:
                self.add_log(f"❌ [LỖI TIẾN TRÌNH] {p_name}: {e}", "error")
            finally:
                self.pc_process = None
                kill_zombie_edge_processes(p_dir)

            if idx < total - 1 and not self.pc_stop_requested:
                self.add_log("⏳ Tạm dừng 15s trước tài khoản tiếp theo...", "warn")
                for _ in range(15):
                    if self.pc_stop_requested:
                        break
                    await asyncio.sleep(1)

        self.pc_is_running = False
        self.pc_task_info = None

        try:
            cfg = load_config()
            android_cfg = cfg.get("android_settings", {})
            if android_cfg.get("enabled", True) and android_cfg.get("auto_checkin_after_search", True) and not self.pc_stop_requested:
                if not self.android_is_running:
                    self.add_log("⏳ Chuyển tiếp sang điểm danh tự động trên App Bing Android...", "action")
                    await asyncio.sleep(2)
                    asyncio.create_task(self.run_android_checkin())
        except Exception as _ae:
            self.add_log(f"⚠️ Lỗi tự động điểm danh Android: {_ae}", "warn")

        self.add_log("🎉 [HỆ THỐNG] Toàn bộ tác vụ tìm kiếm PC đã kết thúc!\n", "success")

    async def run_android_checkin(self, device=None, pin=None, package=None) -> bool:
        if self.android_is_running:
            self.add_log("⚠️ Điểm danh Android đang chạy rồi, vui lòng chờ...", "warn")
            return False

        self.android_is_running = True
        self.android_stop_requested = False

        cfg = load_config()
        android_cfg = cfg.get("android_settings", {})
        dev = device or android_cfg.get("device_address", "100.71.117.39:5555")
        pkg = package or android_cfg.get("package_name", "com.microsoft.bing")
        p_pin = pin or android_cfg.get("pin", "")

        self.android_task_info = {"profile_id": "android", "profile_name": f"Bing App ({dev})", "mode": "android_checkin", "status": "running"}
        self.add_log(f"📱 [ANDROID] BẮT ĐẦU ĐIỂM DANH APP BING ({dev})", "start")

        cmd = [sys.executable, "-u", str(ROOT_DIR / "android_checkin.py"), "--device", dev, "--package", pkg]
        if p_pin:
            cmd.extend(["--pin", str(p_pin)])

        success = False
        try:
            self.android_process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=str(ROOT_DIR)
            )
            await _stream_process_logs(self.android_process, self.add_log)
            await self.android_process.wait()
            code = self.android_process.returncode
            success = (code == 0)

            msg = "Điểm danh thành công!" if success else f"Kết thúc mã {code}"
            self.add_log("🎉 [THÀNH CÔNG] Đã điểm danh App Bing Android!" if success else f"⚠️ Điểm danh Android kết thúc mã {code}.", "success" if success else "warn")
            save_android_checkin_result("completed" if success else "failed", msg, "/screenshots/android_checkin_before.png", "/screenshots/android_checkin_after.png", dev)
        except Exception as e:
            self.add_log(f"❌ [LỖI ANDROID] {e}", "error")
            save_android_checkin_result("error", str(e), device=dev)
        finally:
            self.android_process = None
            self.android_is_running = False
            self.android_task_info = None

        return success

    def stop_pc_bot(self) -> None:
        self.pc_stop_requested = True
        if self.pc_process:
            try:
                self.pc_process.terminate()
            except Exception:
                pass
        self.pc_is_running = False
        self.pc_task_info = None
        self.add_log("🛑 [HỆ THỐNG] Đã yêu cầu dừng tác vụ tìm kiếm PC!", "error")
        try:
            for p in load_config().get("profiles", []):
                kill_zombie_edge_processes(get_profile_abs_path(p))
        except Exception:
            pass

    def stop_android_bot(self) -> None:
        self.android_stop_requested = True
        if self.android_process:
            try:
                self.android_process.terminate()
            except Exception:
                pass
        self.android_is_running = False
        self.android_task_info = None
        self.add_log("🛑 [HỆ THỐNG] Đã yêu cầu dừng tác vụ điểm danh Android!", "warn")

    def stop_bot(self) -> None:
        if self.pc_is_running:
            self.stop_pc_bot()
        if self.android_is_running:
            self.stop_android_bot()


task_mgr = BotTaskManager()
