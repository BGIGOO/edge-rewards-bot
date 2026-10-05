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
import io
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
        # 3. Lệnh trong PATH
        "adb"
    ]
    for c in candidates:
        if os.path.isabs(c) and os.path.exists(c):
            return c
    # Thử gọi 'adb' xem có trong PATH không
    try:
        r = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return "adb"
    except Exception:
        pass
    # Mặc định fallback
    return candidates[2]


ADB_PATH = find_adb_path()
DEFAULT_DEVICE = "100.71.117.39:5555"

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


class AndroidBingCheckinBot:
    def __init__(self, device=DEFAULT_DEVICE, pin=None, package="com.microsoft.bing"):
        self.device = device
        self.pin = pin or os.environ.get("BING_BOT_PIN")
        self.package = package
        self.adb = find_adb_path()
        self.screen_width = 720
        self.screen_height = 1612

    def _run_adb_raw(self, *args, timeout=30):
        cmd = [self.adb, "-s", self.device, *args]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def _adb_shell(self, *args, timeout=30):
        """Chạy lệnh adb shell, tự động kết nối lại nếu rớt mạng Tailscale"""
        try:
            r = self._run_adb_raw("shell", *args, timeout=timeout)
        except (subprocess.TimeoutExpired, OSError) as e:
            log(f"ADB Shell timeout hoặc lỗi I/O ({e}), đang nối lại thiết bị...", "warn")
            r = None

        if r is None or r.returncode != 0 or "device not found" in (r.stderr or ""):
            self.ensure_connected()
            r = self._run_adb_raw("shell", *args, timeout=timeout)

        if r.returncode != 0:
            err = (r.stderr or "").strip()
            raise RuntimeError(f"Lệnh adb shell thất bại ({' '.join(args)}): {err}")
        return (r.stdout or "").strip()

    def ensure_connected(self, max_retries=3):
        """Đảm bảo thiết bị đã kết nối qua ADB Tailscale/Wi-Fi"""
        log(f"Kiểm tra kết nối tới thiết bị {self.device}...", "action")
        for i in range(max_retries):
            try:
                # Kiểm tra danh sách thiết bị
                res = subprocess.run([self.adb, "devices"], capture_output=True, text=True, timeout=10)
                if self.device in res.stdout and "device" in res.stdout:
                    # Ping thử lệnh echo
                    test = self._run_adb_raw("shell", "echo", "alive", timeout=10)
                    if test.returncode == 0:
                        log(f"Thiết bị {self.device} đã sẵn sàng!", "success")
                        self._detect_screen_size()
                        return True

                log(f"Đang kết nối lại tới {self.device} (lần {i+1}/{max_retries})...", "warn")
                subprocess.run([self.adb, "connect", self.device], capture_output=True, text=True, timeout=15)
                time.sleep(2)
            except Exception as e:
                log(f"Lỗi khi kết nối lần {i+1}: {e}", "warn")
                time.sleep(3)

        # Kiểm tra lần cuối
        res = subprocess.run([self.adb, "devices"], capture_output=True, text=True, timeout=10)
        if self.device in res.stdout:
            log(f"Kết nối thành công tới {self.device}!", "success")
            self._detect_screen_size()
            return True
        raise ConnectionError(f"Không thể kết nối tới điện thoại {self.device} qua Tailscale!")

    def _detect_screen_size(self):
        """Tự động phát hiện độ phân giải màn hình thực tế của điện thoại"""
        try:
            out = self._run_adb_raw("shell", "wm", "size", timeout=10).stdout
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

    def is_screen_unlocked(self):
        """Kiểm tra màn hình đã mở khóa chưa"""
        try:
            out = self._adb_shell("dumpsys", "window")
            return "mDreamingLockscreen=false" in out or "mShowingDream=false" in out
        except Exception:
            return True

    def unlock_device(self):
        """Tự động đánh thức và mở khóa điện thoại (nếu có PIN)"""
        if self.is_screen_unlocked():
            log("Điện thoại đã được mở khóa sẵn.", "info")
            return

        log("Màn hình đang khóa, tiến hành đánh thức và mở khóa...", "action")
        # Đánh thức màn hình
        self._adb_shell("input", "keyevent", "KEYCODE_WAKEUP")
        human_sleep(1.0, 1.5)

        # Vuốt màn hình lên để mở màn hình nhập PIN / hình vẽ
        mid_x = self.screen_width // 2
        start_y = int(self.screen_height * 0.85)
        end_y = int(self.screen_height * 0.35)
        self._adb_shell("input", "swipe", str(mid_x), str(start_y), str(mid_x), str(end_y), "300")
        human_sleep(1.0, 1.5)

        if self.pin:
            log("Nhập mã PIN mở khóa (ẩn bảo mật)...", "action")
            # Gửi mã pin qua lệnh adb trực tiếp
            subprocess.run([self.adb, "-s", self.device, "shell", "input", "text", str(self.pin)],
                           capture_output=True, timeout=20)
            human_sleep(0.5, 1.0)
            self._adb_shell("input", "keyevent", "KEYCODE_ENTER")
            human_sleep(1.5, 2.0)
        else:
            log("Không có mã PIN, thử mở khóa bằng vuốt thông thường...", "info")

        if not self.is_screen_unlocked():
            log("Cảnh báo: Chưa xác nhận được trạng thái mở khóa.", "warn")
        else:
            log("Điện thoại đã mở khóa thành công!", "success")

    def capture_screenshot(self, save_path=None):
        """
        Chụp ảnh màn hình qua ADB và lưu vào save_path hoặc trả về PIL Image.
        Tối ưu hóa chạy qua đường hầm Tailscale trên Windows: chụp vào /sdcard/ rồi pull về.
        """
        remote_tmp = "/sdcard/checkin_snap.png"
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
        orange = (r > 200) & (g > 105) & (g < 200) & (b < 120)

        # Vùng thẻ điểm danh thường nằm ở khoảng 25% - 46% chiều cao màn hình sau 1 lần vuốt
        y0, y1 = int(h * 0.25), int(h * 0.46)
        band = orange[y0:y1, :]
        colsum = band.sum(axis=0)

        if colsum.max() == 0:
            log("Không phát hiện dải màu cam của thẻ điểm danh trong vùng quét.", "warn")
            return None

        thresh = colsum.max() * 0.25
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

        groups = [(a, z) for a, z in groups if z - a > 12]
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
        human_sleep(5.0, 7.0)

        # 3. Bấm vào nút Rewards ở trang chủ
        log("Bấm nút 'Rewards' trên giao diện chính của Bing...", "action")
        self.tap_relative(*REWARDS_BTN)
        human_sleep(4.0, 6.0)

        # 4. Vuốt màn hình lên để hiển thị thẻ điểm danh
        log("Vuốt màn hình lên để đưa thẻ điểm danh vào tầm nhìn...", "action")
        mid_x = self.screen_width // 2
        swipe_from_y = int(self.screen_height * 0.75)
        swipe_to_y = int(self.screen_height * 0.30)
        self._adb_shell("input", "swipe", str(mid_x), str(swipe_from_y), str(mid_x), str(swipe_to_y), "400")
        human_sleep(2.5, 4.0)

        # 5. Chụp ảnh màn hình trước khi điểm danh
        frame_before_path = os.path.join(WEB_STATIC_DIR, "android_checkin_before.png")
        log("Chụp ảnh màn hình để phân tích vị trí nút điểm danh...", "action")
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

        # 6. Tìm vị trí ngày hôm nay
        coords = self.find_today_circle(img_before)
        if coords is None:
            log("🎉 Không tìm thấy ngày chưa điểm danh — Hôm nay bạn đã điểm danh rồi!", "success")
            return {
                "success": True,
                "already_done": True,
                "message": "Hôm nay đã được điểm danh từ trước.",
                "frame_before": "/static/android_checkin_before.png",
                "frame_after": "/static/android_checkin_before.png"
            }

        cx, cy = coords
        log(f"🎯 Phát hiện nút điểm danh hôm nay tại ({cx}, {cy}). Tiến hành bấm...", "action")
        # Tap có lệch ngẫu nhiên vài pixel như tay người
        tap_x = int(cx + random.uniform(-6, 6))
        tap_y = int(cy + random.uniform(-6, 6))
        self._adb_shell("input", "tap", str(tap_x), str(tap_y))
        human_sleep(3.5, 5.5)

        # 7. Chụp ảnh màn hình xác nhận kết quả
        frame_after_path = os.path.join(WEB_STATIC_DIR, "android_checkin_after.png")
        log("Chụp ảnh màn hình đối soát kết quả sau khi bấm...", "action")
        img_after = self.capture_screenshot(frame_after_path)

        success = True
        if img_after is not None:
            remaining = self.find_today_circle(img_after)
            if remaining is None:
                log("✅ [THÀNH CÔNG] Đã điểm danh thành công trên App Bing! Vòng tròn đã có dấu tick.", "success")
            else:
                log("⚠️ Vẫn còn vị trí chưa tick, có thể mạng hơi trễ hoặc cần kiểm tra lại.", "warn")

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
    args = parser.parse_args()

    bot = AndroidBingCheckinBot(device=args.device, pin=args.pin, package=args.package)

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
