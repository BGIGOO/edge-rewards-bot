# -*- coding: utf-8 -*-
"""
====================================================================
           MICROSOFT REWARDS ANDROID CHECK-IN BOT
   Tự động điểm danh hàng ngày trên app Microsoft Bing (Android)
   Hỗ trợ kết nối qua Tailscale IP từ xa / Wi-Fi LAN / USB
====================================================================
"""

import os
import sys
import time
import random
import subprocess
import argparse
import re
import shutil
import json
from datetime import datetime

# Đảm bảo console Windows hỗ trợ UTF-8
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_STATIC_DIR = os.path.join(SCRIPT_DIR, "web")


def find_adb_path():
    """Tự động tìm kiếm đường dẫn adb.exe trên Windows"""
    candidates = [
        # 1. Thư mục dự án nếu có
        os.path.join(SCRIPT_DIR, "platform-tools", "adb.exe"),
        os.path.join(SCRIPT_DIR, "adb.exe"),
        # 2. Android SDK tiêu chuẩn
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Android\platform-tools\adb.exe"),
        r"C:\platform-tools\adb.exe",
        r"D:\platform-tools\adb.exe",
        r"C:\scrcpy\adb.exe",
        r"D:\scrcpy\adb.exe",
    ]
    for c in candidates:
        if os.path.isabs(c) and os.path.exists(c):
            return c
    
    # Kiểm tra trong PATH
    which_adb = shutil.which("adb")
    if which_adb and os.path.exists(which_adb):
        return which_adb

    try:
        r = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            return "adb"
    except Exception:
        pass

    # Mặc định fallback SDK
    return candidates[2]


ADB_PATH = find_adb_path()
DEFAULT_DEVICE = "100.71.117.39:5555"

def load_default_pin():
    """Đọc mã PIN từ config.json nếu có, mặc định 'quynh1981'"""
    config_path = os.path.join(SCRIPT_DIR, "config.json")
    pin = "quynh1981"
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                pin = cfg.get("android_settings", {}).get("pin", pin)
    except Exception:
        pass
    return pin

# Tọa độ tương đối đo trên màn hình 720x1612 (tỷ lệ theo chiều rộng/cao)
# Nút Rewards ở trang chủ Bing
REWARDS_BTN = (202 / 720, 1048 / 1612)


def log(msg, level="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info": "[*]",
        "success": "[✓]",
        "warn": "[!]",
        "error": "[X]",
        "action": "[📱]"
    }.get(level, "[*]")
    print(f"[{timestamp}] {prefix} {msg}", flush=True)


def human_sleep(a=2.0, b=5.0):
    time.sleep(random.uniform(a, b))


def ping_host(host, timeout_ms=1200):
    """
    Ping kiểm tra xem IP Tailscale có thông mạng không.
    Trả về (True, ping_ms) hoặc (False, None).
    """
    try:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), str(host)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=(timeout_ms / 1000) + 1.5)
        if r.returncode == 0:
            m = re.search(r"time[=<](\d+)ms", r.stdout)
            ping_ms = int(m.group(1)) if m else 30
            return True, ping_ms
    except Exception:
        pass
    return False, None


def get_adb_device_state(adb_path, device_address):
    """
    Lấy trạng thái thiết bị trong danh sách `adb devices`:
    - 'device': Đã kết nối và sẵn sàng nhận lệnh
    - 'offline': Thiết bị đang ngoại tuyến / cổng stale
    - 'unauthorized': Thiết bị chưa cấp quyền gỡ lỗi USB/Wi-Fi
    - 'disconnected': Chưa có trong danh sách
    """
    try:
        r = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=5)
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


class AndroidBingCheckinBot:
    def __init__(self, device=DEFAULT_DEVICE, pin=None, package="com.microsoft.bing"):
        self.device = device
        self.host = device.split(":")[0] if ":" in device else device
        self.port = device.split(":")[1] if ":" in device else "5555"
        self.pin = pin or os.environ.get("BING_BOT_PIN") or load_default_pin()
        self.package = package
        self.adb = find_adb_path()
        self.screen_width = 720
        self.screen_height = 1612

    def _run_adb_raw(self, *args, timeout=25):
        cmd = [self.adb, "-s", self.device, *args]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def _adb_shell(self, *args, timeout=25):
        """Chạy lệnh adb shell, tự động kết nối lại nếu rớt mạng Tailscale"""
        try:
            r = self._run_adb_raw("shell", *args, timeout=timeout)
        except (subprocess.TimeoutExpired, OSError) as e:
            log(f"ADB Shell timeout hoặc lỗi I/O ({e}), đang nối lại thiết bị...", "warn")
            r = None

        if r is None or r.returncode != 0 or "device not found" in (r.stderr or "") or "device offline" in (r.stderr or ""):
            self.ensure_connected()
            r = self._run_adb_raw("shell", *args, timeout=timeout)

        if r.returncode != 0:
            err = (r.stderr or "").strip()
            raise RuntimeError(f"Lệnh adb shell thất bại ({' '.join(args)}): {err}")
        return (r.stdout or "").strip()

    def get_device_status(self):
        """
        Kiểm tra trạng thái kết nối mạng Tailscale, ADB và app Bing (nhanh, không block):
        - ping_ok: bool
        - ping_ms: int or None
        - adb_state: 'device' | 'offline' | 'unauthorized' | 'disconnected'
        - is_connected: bool
        - app_status: 'foreground' | 'background' | 'closed' | 'unreachable'
        - app_running: bool
        - app_foreground: bool
        - screen_unlocked: bool or None
        - message: str
        """
        # 1. Kiểm tra mạng Tailscale (ping nhanh trong 800ms)
        is_ping, ping_ms = ping_host(self.host, timeout_ms=800)
        if not is_ping:
            return {
                "ping_ok": False,
                "ping_ms": None,
                "adb_state": "disconnected",
                "is_connected": False,
                "app_status": "unreachable",
                "app_running": False,
                "app_foreground": False,
                "screen_unlocked": None,
                "message": f"Không thể ping tới IP Tailscale ({self.host}). Vui lòng mở VPN Tailscale trên máy tính & điện thoại!"
            }

        # 2. Kiểm tra trạng thái ADB hiện tại từ daemon
        adb_state = get_adb_device_state(self.adb, self.device)

        if adb_state != "device":
            desc = "Cổng ADB 5555 chưa mở" if adb_state == "disconnected" else f"ADB {adb_state}"
            return {
                "ping_ok": True,
                "ping_ms": ping_ms,
                "adb_state": adb_state,
                "is_connected": False,
                "app_status": "unreachable",
                "app_running": False,
                "app_foreground": False,
                "screen_unlocked": None,
                "message": f"Mạng Tailscale thông tốt ({ping_ms}ms), nhưng {desc}. Hãy bật 'Gỡ lỗi qua Wi-Fi' trên điện thoại!"
            }

        # 3. Đã kết nối ADB -> Kiểm tra màn hình & ứng dụng Bing
        is_run = self.is_app_running()
        is_fg = self.is_app_foreground() if is_run else False
        unlocked = self.is_screen_unlocked()

        if is_fg:
            app_status = "foreground"
            app_desc = "App Bing đang mở trên màn hình điện thoại"
        elif is_run:
            app_status = "background"
            app_desc = "App Bing đang chạy ngầm trong bộ nhớ"
        else:
            app_status = "closed"
            app_desc = "App Bing đang tắt (chưa mở)"

        return {
            "ping_ok": True,
            "ping_ms": ping_ms,
            "adb_state": "device",
            "is_connected": True,
            "app_status": app_status,
            "app_running": is_run,
            "app_foreground": is_fg,
            "screen_unlocked": unlocked,
            "message": app_desc
        }

    def reconnect_device(self):
        """Chủ động kết nối lại thiết bị ADB qua Tailscale"""
        is_ping, ping_ms = ping_host(self.host, timeout_ms=800)
        if not is_ping:
            return {
                "success": False,
                "message": f"Không thể ping IP Tailscale ({self.host}). Hãy mở VPN Tailscale trên máy tính & điện thoại!"
            }

        try:
            # Ngắt kết nối cũ nếu có để làm sạch trạng thái
            subprocess.run([self.adb, "disconnect", self.device], capture_output=True, timeout=3)
            r = subprocess.run([self.adb, "connect", self.device], capture_output=True, text=True, timeout=5)
            time.sleep(0.5)
            state = get_adb_device_state(self.adb, self.device)
            if state == "device":
                self._detect_screen_size()
                return {
                    "success": True,
                    "message": f"Kết nối ADB thành công tới {self.device} qua Tailscale (Độ trễ: {ping_ms}ms)!"
                }
            else:
                return {
                    "success": False,
                    "message": f"Ping Tailscale OK ({ping_ms}ms) nhưng không thể mở ADB qua cổng {self.port}. Hãy bật 'Gỡ lỗi qua Wi-Fi' trên điện thoại."
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": f"Ping Tailscale OK ({ping_ms}ms) nhưng cổng ADB {self.port} không phản hồi. Hãy bật 'Gỡ lỗi qua Wi-Fi' trên điện thoại."
            }
        except Exception as e:
            return {"success": False, "message": f"Lỗi khi kết nối ADB: {e}"}

    def ensure_connected(self, max_retries=1):
        """Đảm bảo thiết bị đã kết nối qua ADB Tailscale/Wi-Fi"""
        log(f"Kiểm tra kết nối tới thiết bị {self.device}...", "action")

        # Bước 1: Kiểm tra ping Tailscale trước
        is_ping, ping_ms = ping_host(self.host, timeout_ms=800)
        if not is_ping:
            raise ConnectionError(
                f"Mất kết nối mạng Tailscale tới {self.host}! Vui lòng bật VPN Tailscale trên máy tính và điện thoại."
            )
        log(f"Mạng Tailscale phản hồi tốt (Độ trễ: {ping_ms}ms).", "info")

        # Bước 2: Kiểm tra trạng thái ADB
        state = get_adb_device_state(self.adb, self.device)
        if state == "device":
            test = self._run_adb_raw("shell", "echo", "alive", timeout=5)
            if test.returncode == 0 and "alive" in test.stdout:
                log(f"Thiết bị {self.device} đã sẵn sàng!", "success")
                self._detect_screen_size()
                return True

        if state == "offline":
            log(f"Thiết bị ở trạng thái offline, ngắt kết nối...", "warn")
            try:
                subprocess.run([self.adb, "disconnect", self.device], capture_output=True, timeout=3)
            except Exception:
                pass

        log(f"Đang kết nối lại ADB tới {self.device}...", "warn")
        try:
            subprocess.run([self.adb, "connect", self.device], capture_output=True, text=True, timeout=5)
            time.sleep(0.8)
        except subprocess.TimeoutExpired:
            raise ConnectionError(
                f"Ping Tailscale OK ({ping_ms}ms) nhưng cổng ADB 5555 không phản hồi. Hãy bật 'Gỡ lỗi qua Wi-Fi' trên điện thoại!"
            )
        except Exception as e:
            raise ConnectionError(f"Lỗi khi kết nối ADB: {e}")

        # Kiểm tra lần cuối
        final_state = get_adb_device_state(self.adb, self.device)
        if final_state == "device":
            log(f"Kết nối thành công tới {self.device}!", "success")
            self._detect_screen_size()
            return True

        raise ConnectionError(
            f"Không thể kết nối cổng ADB {self.device} qua Tailscale (trạng thái: {final_state}). "
            f"Vui lòng bật 'Gỡ lỗi không dây (Wireless Debugging)' trên điện thoại!"
        )

    def _detect_screen_size(self):
        """Tự động phát hiện độ phân giải màn hình thực tế của điện thoại"""
        try:
            out = self._run_adb_raw("shell", "wm", "size", timeout=8).stdout
            for line in out.splitlines():
                if "Physical size:" in line:
                    dims = line.split(":")[-1].strip().split("x")
                    self.screen_width = int(dims[0])
                    self.screen_height = int(dims[1])
                    log(f"Độ phân giải màn hình: {self.screen_width}x{self.screen_height}", "info")
                    return
        except Exception:
            pass
        self.screen_width = 720
        self.screen_height = 1612

    def is_screen_awake(self):
        """Kiểm tra màn hình đang SÁNG hay TẮT qua PowerManager Service (Áp dụng từ test_wake_and_capture.py)"""
        try:
            out = self._run_adb_raw("shell", "dumpsys power | grep mWakefulness=", timeout=8).stdout
            return "mWakefulness=Awake" in out
        except Exception:
            pass
        return True

    def is_device_locked(self):
        """
        Kiểm tra điện thoại ĐANG KHÓA (Lockscreen) hay ĐÃ MỞ KHÓA (Áp dụng từ test_wake_and_capture.py):
        - isKeyguardShowing=true / showing=true: Đang khóa
        - deviceLocked=1: Đang khóa
        """
        try:
            out_win = self._run_adb_raw("shell", "dumpsys window | grep -E 'isKeyguardShowing|showing='", timeout=8).stdout
            if "isKeyguardShowing=true" in out_win or "showing=true" in out_win:
                return True
            if "isKeyguardShowing=false" in out_win or "showing=false" in out_win:
                return False

            out_trust = self._run_adb_raw("shell", "dumpsys trust | grep deviceLocked=", timeout=8).stdout
            if "deviceLocked=1" in out_trust or "deviceLocked=true" in out_trust:
                return True
        except Exception:
            pass
        return False

    def is_screen_unlocked(self):
        """Kiểm tra màn hình đã mở khóa hoàn toàn chưa (màn hình sáng + không bị khóa)"""
        return self.is_screen_awake() and (not self.is_device_locked())

    def unlock_device(self):
        """Tự động kiểm tra thông minh trước khi đánh thức & mở khóa (Áp dụng từ test_wake_and_capture.py)"""
        # BƯỚC 1: KIỂM TRA NGUỒN MÀN HÌNH
        awake = self.is_screen_awake()
        if not awake:
            log("Phát hiện màn hình đang TẮT (Asleep). Đang gửi lệnh đánh thức (KEYCODE_WAKEUP)...", "action")
            self._adb_shell("input", "keyevent", "KEYCODE_WAKEUP")
            time.sleep(1.0)
        else:
            log("Phát hiện màn hình ĐÃ SÁNG SẴN (Awake) -> Bỏ qua lệnh bật màn hình.", "info")

        # BƯỚC 2: KIỂM TRA MÀN HÌNH KHÓA (KEYGUARD)
        locked = self.is_device_locked()
        if locked:
            log("Phát hiện điện thoại ĐANG KHÓA (Lockscreen active). Vuốt màn hình lên và nhập mã PIN...", "action")
            self._adb_shell("input", "swipe", "360", "1300", "360", "400", "300")
            time.sleep(1.0)
            if self.pin:
                log("Nhập mã PIN mở khóa...", "action")
                self._adb_shell("input", "text", str(self.pin))
                time.sleep(0.5)
                self._adb_shell("input", "keyevent", "KEYCODE_ENTER")
                time.sleep(1.5)

            # Xác nhận trạng thái mở khóa
            if not self.is_device_locked():
                log("Đã nhập PIN và mở khóa điện thoại thành công!", "success")
            else:
                log("Cảnh báo: Thiết bị vẫn báo khóa, thử gửi ENTER lại...", "warn")
                self._adb_shell("input", "keyevent", "KEYCODE_ENTER")
                time.sleep(1.0)
        else:
            log("Phát hiện điện thoại ĐÃ MỞ KHÓA SẴN HOÀN TOÀN (Unlocked)! Bỏ qua vuốt và gõ PIN.", "success")

    def is_app_running(self):
        """Kiểm tra package Bing có tiến trình đang chạy không"""
        try:
            r = self._run_adb_raw("shell", "pidof", self.package, timeout=6)
            if r.returncode == 0 and r.stdout.strip():
                return True
            # Fallback ps
            r2 = self._run_adb_raw("shell", "ps", "-A", timeout=6)
            return self.package in r2.stdout
        except Exception:
            return False

    def is_app_foreground(self):
        """Kiểm tra ứng dụng Bing có đang hiển thị trực tiếp trên màn hình không"""
        try:
            r = self._run_adb_raw("shell", "dumpsys", "window", "windows", timeout=6)
            if r.returncode == 0 and any(
                ("mCurrentFocus" in line or "mFocusedApp" in line) and self.package in line
                for line in r.stdout.splitlines()
            ):
                return True
            r2 = self._run_adb_raw("shell", "dumpsys", "activity", "activities", timeout=6)
            if r2.returncode == 0 and any(
                ("mResumedActivity" in line or "topResumedActivity" in line) and self.package in line
                for line in r2.stdout.splitlines()
            ):
                return True
        except Exception:
            pass
        return False

    def open_app(self):
        """Mở ứng dụng Microsoft Bing trên điện thoại"""
        self.ensure_connected()
        self.unlock_device()
        log(f"Đang mở ứng dụng {self.package}...", "action")
        self._adb_shell("monkey", "-p", self.package, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(2.5)
        is_fg = self.is_app_foreground()
        is_run = self.is_app_running()
        if is_fg or is_run:
            log(f"Ứng dụng {self.package} đã được mở thành công!", "success")
            return {"success": True, "message": "Đã mở App Bing thành công!", "foreground": is_fg}
        return {"success": False, "message": "Đã gửi lệnh mở nhưng chưa xác nhận được tiến trình.", "foreground": False}

    def close_app(self):
        """Tắt (buộc dừng) ứng dụng Bing trên điện thoại"""
        self.ensure_connected()
        log(f"Đang tắt (buộc dừng) ứng dụng {self.package}...", "action")
        self._adb_shell("am", "force-stop", self.package)
        time.sleep(1.0)
        is_run = self.is_app_running()
        if not is_run:
            log(f"Ứng dụng {self.package} đã được tắt hoàn toàn!", "success")
            return {"success": True, "message": "Đã tắt App Bing thành công!"}
        return {"success": False, "message": "Gửi lệnh force-stop nhưng ứng dụng vẫn còn chạy."}

    def capture_screenshot(self, save_path=None):
        """
        Chụp ảnh màn hình qua ADB và lưu vào save_path hoặc trả về PIL Image.
        Sử dụng /data/local/tmp/ luôn có quyền ghi không cần storage permission.
        """
        remote_tmp = "/data/local/tmp/checkin_snap.png"
        local_target = save_path or os.path.join(SCRIPT_DIR, "scratch", "checkin_snap.png")
        os.makedirs(os.path.dirname(os.path.abspath(local_target)), exist_ok=True)

        try:
            # 1. Chụp ảnh lưu tạm trên điện thoại
            self._adb_shell("screencap", "-p", remote_tmp, timeout=15)
            # 2. Kéo ảnh về PC
            r = subprocess.run([self.adb, "-s", self.device, "pull", remote_tmp, local_target],
                               capture_output=True, text=True, timeout=25)
            if r.returncode == 0 and os.path.exists(local_target) and os.path.getsize(local_target) > 5000:
                img = Image.open(local_target).convert("RGB")
                return img
            else:
                log(f"Lỗi pull ảnh: {r.stderr}", "warn")
        except Exception as e:
            log(f"Lỗi chụp ảnh qua ADB ({e})", "warn")

        return None

    def tap_relative(self, fx, fy, jitter=8):
        """Tap theo tọa độ tỷ lệ (0-1) kèm jitter ngẫu nhiên mô phỏng người thật"""
        x = int(fx * self.screen_width + random.uniform(-jitter, jitter))
        y = int(fy * self.screen_height + random.uniform(-jitter, jitter))
        self._adb_shell("input", "tap", str(x), str(y))
        log(f"Tap người dùng: ({x}, {y})", "info")

    def find_today_circle(self, img):
        """
        Thuật toán phân tích Computer Vision:
        Tìm vòng tròn ngày hôm nay (viền cam) trong thẻ điểm danh.
        - Vòng tròn đã điểm danh: có dấu check màu trắng ở tâm.
        - Vòng tròn hôm nay: viền cam, chưa có dấu check, là vòng đầu tiên chưa hoàn thành từ trái qua.
        """
        w, h = img.size
        arr = np.asarray(img)
        r = arr[:, :, 0].astype(int)
        g = arr[:, :, 1].astype(int)
        b = arr[:, :, 2].astype(int)

        # Ngưỡng màu cam của viền thẻ điểm danh Bing
        orange = (r > 190) & (g > 95) & (g < 205) & (b < 130)

        # Quét dải từ 15% đến 70% chiều cao màn hình sau khi vuốt
        y0, y1 = int(h * 0.15), int(h * 0.70)
        band = orange[y0:y1, :]
        colsum = band.sum(axis=0)

        if colsum.max() == 0:
            log("Không phát hiện dải màu cam của thẻ điểm danh trong vùng quét.", "warn")
            return None

        thresh = colsum.max() * 0.22
        groups = []
        in_g = False
        start = 0

        for x, v in enumerate(colsum):
            if v > thresh and not in_g:
                in_g = True
                start = x
            elif v <= thresh and in_g:
                in_g = False
                groups.append((start, x))
        if in_g:
            groups.append((start, len(colsum)))

        groups = [(a, z) for a, z in groups if z - a > 10]
        groups.sort()

        log(f"Phát hiện {len(groups)} vòng tròn ngày trong thẻ điểm danh.", "info")
        if not groups:
            return None

        for a, z in groups:
            cx = (a + z) // 2
            col = band[:, a:z]
            rowsum = col.sum(axis=1)
            cy = y0 + int(np.argmax(rowsum))

            # Kiểm tra tâm vòng tròn: nếu có màu trắng (>215) thì đã có dấu tick check
            x0, x1 = max(cx - 10, 0), min(cx + 11, w)
            yy0, yy1 = max(cy - 10, 0), min(cy + 11, h)
            patch = arr[yy0:yy1, x0:x1].astype(int)
            white_ratio = ((patch[:, :, 0] > 215) & (patch[:, :, 1] > 215) & (patch[:, :, 2] > 215)).mean()

            done = white_ratio >= 0.02
            log(f"  • Vòng tròn tại ({cx}, {cy}): {'[✓ ĐÃ ĐIỂM DANH]' if done else '[⏳ CHƯA ĐIỂM DANH - HÔM NAY]'}")
            if not done:
                return cx, cy

        return None

    def check_daily_streak_status(self, img):
        """
        Kiểm tra trạng thái thẻ 'Chuỗi liên tiếp' trên App Bing phiên bản mới (Việt Nam):
        - Quét vùng hàng đầu tiên 'Đăng ký vào' (Check-in 5 điểm)
        - Phát hiện dấu checkmark màu xanh lá đặc trưng (✓) tại vị trí huy hiệu
        Trả về (already_done: bool, tap_coords: tuple (x, y))
        """
        w, h = img.size
        arr = np.asarray(img)

        # Vùng huy hiệu dấu check của hàng 'Đăng ký vào'
        # X: 60% - 75% chiều rộng (khoảng 440 - 530 trên 720p)
        # Y: 30% - 50% chiều cao sau khi vuốt (khoảng 500 - 800 trên 1612p)
        x0, x1 = int(w * 0.61), int(w * 0.73)
        y0, y1 = int(h * 0.31), int(h * 0.50)

        patch = arr[y0:y1, x0:x1].astype(int)
        r, g, b = patch[:, :, 0], patch[:, :, 1], patch[:, :, 2]
        green_mask = (g > 120) & (g > r + 50) & (g > b + 30)
        green_pixels = int(green_mask.sum())

        card_tap_x = int(w * 0.50)
        card_tap_y = int(h * 0.417)  # ~ 672 trên 1612p

        if green_pixels > 50:
            log(f"Phát hiện dấu check xanh lá ({green_pixels} px) trên hàng 'Đăng ký vào' -> Đã điểm danh!", "success")
            return True, (card_tap_x, card_tap_y)

        log(f"Hàng 'Đăng ký vào' chưa có dấu check xanh lá ({green_pixels} px) -> Chưa điểm danh hôm nay.", "info")
        return False, (card_tap_x, card_tap_y)

    def execute_checkin(self):
        """Quy trình tự động hóa điểm danh đầy đủ"""
        log("=======================================================", "action")
        log("🚀 BẮT ĐẦU QUY TRÌNH ĐIỂM DANH APP BING ANDROID", "action")
        log(f"Thiết bị mục tiêu: {self.device}", "info")
        log("=======================================================", "action")

        # 1. Kết nối & Mở khóa
        self.ensure_connected()
        self.unlock_device()

        # Đặt thời gian sáng màn hình lâu hơn (10 phút) tránh tắt giữa chừng
        try:
            self._adb_shell("settings", "put", "system", "screen_off_timeout", "600000")
        except Exception:
            pass

        # 2. Khởi chạy App Bing
        log(f"Mở ứng dụng {self.package}...", "action")
        self._adb_shell("monkey", "-p", self.package, "-c", "android.intent.category.LAUNCHER", "1")
        human_sleep(4.0, 5.5)

        # Đảm bảo chuyển về Trang chủ (Home tab)
        home_btn_x = int(70 / 720 * self.screen_width)
        home_btn_y = int(1515 / 1612 * self.screen_height)
        self._adb_shell("input", "tap", str(home_btn_x), str(home_btn_y))
        human_sleep(2.0, 3.0)

        # 3. Bấm vào nút Rewards ở trang chủ
        log("Bấm nút 'Rewards' trên giao diện chính của Bing...", "action")
        self.tap_relative(*REWARDS_BTN)
        human_sleep(4.5, 6.0)

        # 4. Vuốt màn hình lên để hiển thị thẻ điểm danh
        log("Vuốt màn hình lên để đưa thẻ 'Chuỗi liên tiếp' vào tầm nhìn...", "action")
        mid_x = self.screen_width // 2
        swipe_from_y = int(self.screen_height * 0.74)
        swipe_to_y = int(self.screen_height * 0.37)
        self._adb_shell("input", "swipe", str(mid_x), str(swipe_from_y), str(mid_x), str(swipe_to_y), "350")
        human_sleep(2.5, 3.5)

        # 5. Chụp ảnh màn hình trước khi điểm danh
        frame_before_path = os.path.join(WEB_STATIC_DIR, "android_checkin_before.png")
        log("Chụp ảnh màn hình để phân tích trạng thái điểm danh...", "action")
        img_before = None
        for attempt in range(3):
            img_before = self.capture_screenshot(frame_before_path)
            if img_before is not None:
                break
            log(f"Chụp màn hình lần {attempt+1} không thành công, thử lại...", "warn")
            time.sleep(2.0)

        if img_before is None:
            raise RuntimeError("Không thể chụp màn hình điện thoại để định vị điểm danh!")

        log(f"Đã lưu ảnh kiểm tra: {frame_before_path}", "info")

        # 6. Kiểm tra trạng thái điểm danh
        already_done, coords = self.check_daily_streak_status(img_before)
        if not already_done and coords is None:
            # Thử lại bằng thuật toán fallback tìm vòng tròn cũ
            legacy_coords = self.find_today_circle(img_before)
            if legacy_coords is not None:
                coords = legacy_coords
                already_done = False
            else:
                already_done = True

        if already_done:
            log("🎉 Hôm nay bạn đã điểm danh nhận xu (5 điểm) rồi!", "success")
            return {
                "success": True,
                "already_done": True,
                "message": "Hôm nay đã được điểm danh từ trước.",
                "frame_before": "/static/android_checkin_before.png",
                "frame_after": "/static/android_checkin_before.png"
            }

        cx, cy = coords
        log(f"🎯 Nhận diện nút 'Đăng ký vào' tại ({cx}, {cy}). Tiến hành bấm nhận xu...", "action")
        tap_x = int(cx + random.uniform(-6, 6))
        tap_y = int(cy + random.uniform(-6, 6))
        self._adb_shell("input", "tap", str(tap_x), str(tap_y))
        human_sleep(3.5, 5.0)

        # 7. Chụp ảnh màn hình xác nhận kết quả
        frame_after_path = os.path.join(WEB_STATIC_DIR, "android_checkin_after.png")
        log("Chụp ảnh màn hình đối soát kết quả sau khi bấm...", "action")
        img_after = self.capture_screenshot(frame_after_path)

        success = True
        if img_after is not None:
            done_after, _ = self.check_daily_streak_status(img_after)
            if done_after:
                log("✅ [THÀNH CÔNG] Đã điểm danh và nhận xu thành công trên App Bing!", "success")
            else:
                log("⚠️ Đã gửi lệnh bấm nhận xu, đang chờ máy chủ Bing ghi nhận điểm.", "warn")

        return {
            "success": success,
            "already_done": False,
            "message": "Điểm danh hoàn tất thành công!",
            "coordinates": (cx, cy),
            "frame_before": "/static/android_checkin_before.png",
            "frame_after": "/static/android_checkin_after.png"
        }


def run_checkin_flow(device=DEFAULT_DEVICE, pin=None, package="com.microsoft.bing"):
    bot = AndroidBingCheckinBot(device=device, pin=pin, package=package)
    return bot.execute_checkin()


def main():
    parser = argparse.ArgumentParser(description="Tự động điểm danh Microsoft Rewards trên app Bing Android")
    parser.add_argument("--device", default=DEFAULT_DEVICE, help=f"Địa chỉ ADB thiết bị (mặc định: {DEFAULT_DEVICE})")
    parser.add_argument("--package", default="com.microsoft.bing", help="Package name của app Bing")
    parser.add_argument("--pin", default=None, help="Mã PIN mở khóa điện thoại (hoặc qua biến môi trường BING_BOT_PIN)")
    parser.add_argument("--test-screen", action="store_true", help="Chỉ kiểm tra kết nối và chụp ảnh thử")
    parser.add_argument("--status", action="store_true", help="Kiểm tra trạng thái kết nối & App Bing (JSON)")
    parser.add_argument("--open-app", action="store_true", help="Mở ứng dụng Microsoft Bing trên điện thoại")
    parser.add_argument("--close-app", action="store_true", help="Tắt (buộc dừng) ứng dụng Bing trên điện thoại")
    args = parser.parse_args()

    bot = AndroidBingCheckinBot(device=args.device, pin=args.pin, package=args.package)

    if args.status:
        import json
        st = bot.get_device_status()
        print(json.dumps(st, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.open_app:
        res = bot.open_app()
        sys.exit(0 if res.get("success") else 1)

    if args.close_app:
        res = bot.close_app()
        sys.exit(0 if res.get("success") else 1)

    if args.test_screen:
        bot.ensure_connected()
        test_path = os.path.join(SCRIPT_DIR, "test_device_screen.png")
        img = bot.capture_screenshot(test_path)
        if img:
            log(f"Đã chụp ảnh thử thành công: {test_path} ({img.size[0]}x{img.size[1]})", "success")
            sys.exit(0)
        else:
            log("Lỗi chụp ảnh thử!", "error")
            sys.exit(1)

    try:
        res = bot.execute_checkin()
        if res.get("success"):
            sys.exit(0)
        else:
            sys.exit(2)
    except Exception as e:
        log(f"Lỗi quy trình điểm danh: {e}", "error")
        sys.exit(1)


if __name__ == "__main__":
    main()
