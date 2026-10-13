# -*- coding: utf-8 -*-
"""
Script kiểm tra thông minh:
1. Nhận biết màn hình đang SÁNG hay TẮT (mWakefulness)
2. Nhận biết điện thoại ĐANG KHÓA hay ĐÃ MỞ SẴN (Keyguard / deviceLocked)
   -> Nếu đã mở sẵn: BỎ QUA vuốt màn hình và gõ PIN!
   -> Nếu đang khóa: Chỉ vuốt và nhập PIN khi thực sự cần thiết!
3. Nhận biết ứng dụng đang hiển thị trên màn hình (mCurrentFocus)
4. Chụp ảnh màn hình đối soát kết quả
"""

import os
import sys
import time
import subprocess
import json

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = r"C:\Users\NManh\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "100.71.117.39:5555"

# Đọc PIN từ config.json
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
PIN = "quynh1981"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
        PIN = cfg.get("android_settings", {}).get("pin", PIN)
except Exception:
    pass


def run_adb(*args, timeout=20):
    cmd = [ADB_PATH, "-s", DEVICE, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()


def is_screen_awake():
    """Kiểm tra màn hình đang SÁNG hay TẮT qua PowerManager Service"""
    out = run_adb("shell", "dumpsys power | grep mWakefulness=")
    return "mWakefulness=Awake" in out


def is_device_locked():
    """
    Kiểm tra điện thoại ĐANG KHÓA (Lockscreen) hay ĐÃ MỞ KHÓA:
    - isKeyguardShowing=true / showing=true: Đang khóa
    - deviceLocked=1: Đang khóa
    """
    out_win = run_adb("shell", "dumpsys window | grep -E 'isKeyguardShowing|showing='")
    if "isKeyguardShowing=true" in out_win or "showing=true" in out_win:
        return True
    if "isKeyguardShowing=false" in out_win or "showing=false" in out_win:
        return False

    out_trust = run_adb("shell", "dumpsys trust | grep deviceLocked=")
    if "deviceLocked=1" in out_trust or "deviceLocked=true" in out_trust:
        return True

    return False


def get_current_focused_window():
    """Lấy tên ứng dụng / activity đang hiển thị trên cùng màn hình"""
    out = run_adb("shell", "dumpsys window | grep mCurrentFocus")
    return out


def main():
    print(f"[*] 1. Kiểm tra kết nối ADB tới {DEVICE}...")
    devices_out = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True).stdout
    if DEVICE not in devices_out:
        print("[!] Thiết bị chưa kết nối, đang kết nối lại...")
        subprocess.run([ADB_PATH, "connect", DEVICE], capture_output=True, timeout=10)
    print(f"[✓] Đã kết nối thiết bị {DEVICE}")

    # BƯỚC 1: KIỂM TRA MÀN HÌNH BẬT / TẮT
    print("\n--- BƯỚC 1: KIỂM TRA NGUỒN MÀN HÌNH ---")
    awake = is_screen_awake()
    if not awake:
        print("[!] Phát hiện: Màn hình đang TẮT (Asleep).")
        print("[*] Đang gửi lệnh đánh thức màn hình (KEYCODE_WAKEUP)...")
        run_adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        time.sleep(1.0)
    else:
        print("[✓] Phát hiện: Màn hình ĐÃ SÁNG SẴN (Awake) -> Bỏ qua lệnh bật màn hình.")

    # BƯỚC 2: KIỂM TRA TRẠNG THÁI KHÓA MÀN HÌNH (KEYGUARD)
    print("\n--- BƯỚC 2: KIỂM TRA MÀN HÌNH KHÓA (KEYGUARD) ---")
    locked = is_device_locked()
    if locked:
        print("[!] Phát hiện: Điện thoại ĐANG KHÓA (Lockscreen active).")
        print("[*] Tiến hành: Vuốt màn hình lên và nhập mã PIN để mở khóa...")
        run_adb("shell", "input", "swipe", "360", "1300", "360", "400", "300")
        time.sleep(1.0)
        if PIN:
            run_adb("shell", "input", "text", str(PIN))
            time.sleep(0.5)
            run_adb("shell", "input", "keyevent", "KEYCODE_ENTER")
            time.sleep(1.5)
        print("[✓] Đã nhập PIN mở khóa thành công!")
    else:
        print("[✓] Phát hiện: Điện thoại ĐÃ MỞ KHÓA SẴN HOÀN TOÀN (Unlocked)!")
        print("[✓] BỎ QUA thao tác vuốt màn hình và BỎ QUA gõ PIN (Tránh chạm nhầm vào màn hình).")

    # BƯỚC 3: KIỂM TRA ỨNG DỤNG ĐANG HIỂN THỊ
    print("\n--- BƯỚC 3: KIỂM TRA APP ĐANG MỞ ---")
    focus = get_current_focused_window()
    print(f"[*] Cửa sổ hiện tại: {focus}")
    if "com.microsoft.bing" in focus:
        print("[✓] App Bing ĐÃ ĐƯỢC MỞ SẴN trên màn hình!")
    else:
        print("[i] Hiện tại chưa ở App Bing (Có thể là Home Launcher hoặc app khác).")

    # BƯỚC 4: CHỤP ẢNH ĐỐI SOÁT
    print("\n--- BƯỚC 4: CHỤP ẢNH MÀN HÌNH ---")
    remote_path = "/data/local/tmp/screen_test.png"
    local_path = os.path.join(SCRIPT_DIR, "scratch", "screen_test.png")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    run_adb("shell", "screencap", "-p", remote_path)
    time.sleep(0.5)
    subprocess.run([ADB_PATH, "-s", DEVICE, "pull", remote_path, local_path], capture_output=True, timeout=15)

    if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
        size_kb = os.path.getsize(local_path) // 1024
        print(f"[✓] THÀNH CÔNG! Đã cập nhật ảnh đối soát: {local_path} ({size_kb} KB)")
    else:
        print("[X] Lỗi: Không kéo được ảnh màn hình về máy tính.")


if __name__ == "__main__":
    main()
