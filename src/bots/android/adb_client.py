# -*- coding: utf-8 -*-
"""
src/bots/android/adb_client.py
==============================
Giao tiep tang thap voi Android qua ADB (Wi-Fi / Tailscale IP / USB).
Tat ca lenh subprocess deu co timeout va bat ngoai le an toan (rule 02_automation_bots).
Tuan thu rule 01_architecture (< 250 dong).
"""

import os
import re
import time
import socket
import shutil
import random
import subprocess
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

from src.core.paths import ROOT_DIR, CONFIG_PATH

DEFAULT_DEVICE = "100.71.117.39:5555"
REWARDS_BTN = (202 / 720, 1048 / 1612)


def log(msg: str, level: str = "info") -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info": "[*]", "success": "[✓]", "warn": "[!]", "error": "[X]", "action": "[📱]"
    }.get(level, "[*]")
    print(f"[{timestamp}] {prefix} {msg}", flush=True)


def human_sleep(a: float = 2.0, b: float = 5.0) -> None:
    time.sleep(random.uniform(a, b))


def find_adb_path() -> str:
    """Tim kiem duong dan adb tren he thong."""
    candidates = [
        str(ROOT_DIR / "platform-tools" / "adb.exe"), str(ROOT_DIR / "adb.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Android\platform-tools\adb.exe"),
        r"C:\platform-tools\adb.exe", r"D:\platform-tools\adb.exe", r"C:\scrcpy\adb.exe"
    ]
    for c in candidates:
        if os.path.isabs(c) and os.path.exists(c):
            return c
    which_adb = shutil.which("adb")
    return which_adb if which_adb else candidates[2]


def load_default_pin() -> str:
    """Doc ma PIN mo khoa tu config.json neu co."""
    pin = "quynh1981"
    try:
        if os.path.exists(CONFIG_PATH):
            import json
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                pin = cfg.get("android_settings", {}).get("pin", pin)
    except Exception:
        pass
    return pin


def ping_host(host: str, timeout_ms: int = 1200) -> Tuple[bool, Optional[int]]:
    """Kiem tra thong mang IP qua TCP socket hoac ICMP voi timeout an toan."""
    ip = host.split(":")[0]
    port = int(host.split(":")[1]) if ":" in host else 5555
    try:
        t0 = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout_ms / 1000.0)
            s.connect((ip, port))
        return True, max(1, int((time.time() - t0) * 1000))
    except Exception:
        pass
    try:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), str(ip)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_ms / 1000 + 1.5)
        if r.returncode == 0:
            m = re.search(r"time[=<](\d+)ms", r.stdout)
            return True, int(m.group(1)) if m else 30
    except Exception:
        pass
    return False, None


def get_adb_device_state(adb_path: str, device_address: str, timeout: int = 5) -> str:
    """Lay trang thai thiet bi trong adb devices."""
    try:
        r = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=timeout)
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0] == device_address:
                return parts[1]
    except Exception:
        pass
    return "disconnected"


class ADBClient:
    """Quan ly giao tiep lenh ADB co san co che timeout & fallback an toan."""

    def __init__(self, device: str = DEFAULT_DEVICE, pin: Optional[str] = None, package: str = "com.microsoft.bing"):
        self.device = device
        self.pin = pin if pin is not None else load_default_pin()
        self.package = package
        self.adb = find_adb_path()
        self.screen_width = 720
        self.screen_height = 1612

    def _run_adb_raw(self, *args, timeout: int = 15) -> subprocess.CompletedProcess:
        cmd = [self.adb, "-s", self.device] + list(args)
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            log(f"Lệnh ADB bị treo timeout={timeout}s: {' '.join(args)}", "warn")
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="TimeoutExpired")
        except Exception as e:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=str(e))

    def _adb_shell(self, *args, timeout: int = 15) -> str:
        r = self._run_adb_raw("shell", *args, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""

    def get_device_status(self) -> Dict[str, Any]:
        """Kiem tra toan dien tinh trang thiet bi Android."""
        net_ok, ping_ms = ping_host(self.device)
        adb_state = get_adb_device_state(self.adb, self.device)
        if net_ok and adb_state != "device":
            self._run_adb_raw("connect", self.device, timeout=3)
            adb_state = get_adb_device_state(self.adb, self.device)

        is_conn = (adb_state == "device")
        screen_awake, screen_unlocked, app_running = False, False, False
        app_status = "unreachable" if not is_conn else "closed"

        if is_conn:
            self._detect_screen_size()
            screen_awake = self.is_screen_awake()
            screen_unlocked = not self.is_device_locked() if screen_awake else False
            app_running = self.is_app_running()
            if app_running:
                focus = self._adb_shell("dumpsys", "window")
                app_status = "foreground" if self.package in focus else "background"

        return {
            "device": self.device, "connected": is_conn, "is_connected": is_conn,
            "ping_ok": net_ok, "ping_ms": ping_ms, "adb_state": adb_state,
            "screen_awake": screen_awake, "screen_unlocked": screen_unlocked,
            "app_running": app_running, "app_status": app_status,
            "screen_size": f"{self.screen_width}x{self.screen_height}",
            "message": "Thiết bị sẵn sàng" if is_conn else ("Mất kết nối ADB" if net_ok else "Mất mạng Tailscale")
        }

    def reconnect_device(self) -> bool:
        """Thu ket noi lai ADB."""
        log(f"Thu ket noi lai den {self.device}...", "info")
        self._run_adb_raw("disconnect", self.device, timeout=5)
        time.sleep(1)
        r = self._run_adb_raw("connect", self.device, timeout=10)
        return "connected" in r.stdout.lower()

    def ensure_connected(self) -> None:
        if get_adb_device_state(self.adb, self.device) != "device":
            if not self.reconnect_device():
                raise ConnectionError(f"Khong the ket noi den thiet bi ADB: {self.device}")
        self._detect_screen_size()

    def _detect_screen_size(self) -> None:
        out = self._adb_shell("wm", "size")
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            self.screen_width = int(m.group(1))
            self.screen_height = int(m.group(2))

    def is_screen_awake(self) -> bool:
        out = self._adb_shell("dumpsys", "power")
        return bool(re.search(r"mHoldingDisplaySuspendBlocker=true|mWakefulness=Awake|Display Power: state=ON", out))

    def is_device_locked(self) -> bool:
        out = self._adb_shell("dumpsys", "trust")
        m = re.search(r"mIsActive=([a-z]+)", out)
        return m.group(1) == "false" if m else True

    def unlock_device(self) -> None:
        """Danh thuc man hinh va go PIN neu can."""
        if not self.is_screen_awake():
            self._adb_shell("input", "keyevent", "KEYCODE_WAKEUP")
            time.sleep(1)
        if self.is_device_locked():
            mid_x = self.screen_width // 2
            self._adb_shell("input", "swipe", str(mid_x), str(int(self.screen_height * 0.8)),
                            str(mid_x), str(int(self.screen_height * 0.2)), "200")
            time.sleep(1)
            if self.pin:
                self._adb_shell("input", "text", self.pin)
                time.sleep(0.5)
                self._adb_shell("input", "keyevent", "KEYCODE_ENTER")
                time.sleep(1.5)

    def is_app_running(self) -> bool:
        out = self._adb_shell("pidof", self.package)
        return bool(out.strip())

    def open_app(self) -> Dict[str, Any]:
        self.ensure_connected()
        self.unlock_device()
        self._adb_shell("monkey", "-p", self.package, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(2)
        return {"success": True, "message": f"Đã mở {self.package}"}

    def close_app(self) -> Dict[str, Any]:
        self.ensure_connected()
        self._adb_shell("am", "force-stop", self.package)
        return {"success": True, "message": f"Đã đóng {self.package}"}

    def turn_on_device(self) -> Dict[str, Any]:
        self.ensure_connected()
        self.unlock_device()
        return {"success": True, "message": "Màn hình đã bật và mở khóa"}

    def turn_off_device(self) -> Dict[str, Any]:
        self.ensure_connected()
        if self.is_screen_awake():
            self._adb_shell("input", "keyevent", "KEYCODE_POWER")
        return {"success": True, "message": "Màn hình đã tắt"}

    def toggle_screen(self) -> Dict[str, Any]:
        self.ensure_connected()
        return self.turn_off_device() if self.is_screen_awake() else self.turn_on_device()

    def tap_relative(self, fx: float, fy: float, jitter: int = 8) -> None:
        x = int(fx * self.screen_width + random.uniform(-jitter, jitter))
        y = int(fy * self.screen_height + random.uniform(-jitter, jitter))
        self._adb_shell("input", "tap", str(x), str(y))
