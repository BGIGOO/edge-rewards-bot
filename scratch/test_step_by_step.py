# -*- coding: utf-8 -*-
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

import numpy as np
from PIL import Image

ADB_PATH = r"C:\Users\NManh\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "100.71.117.39:5555"
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_adb(*args, timeout=25):
    cmd = [ADB_PATH, "-s", DEVICE, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def capture_screen(save_name):
    remote = f"/data/local/tmp/{save_name}"
    local = os.path.join(SCRIPT_DIR, "scratch", save_name)
    run_adb("shell", "screencap", "-p", remote)
    subprocess.run([ADB_PATH, "-s", DEVICE, "pull", remote, local], capture_output=True, timeout=15)
    return local

def main():
    print("=======================================================")
    print("🚀 BẮT ĐẦU TEST TỪNG BƯỚC: MỞ BING & VÀO ĐIỂM DANH NHẬN XU")
    print("=======================================================")

    print("\n[*] 1. Kiểm tra màn hình điện thoại...")
    wake = run_adb("shell", "dumpsys power | grep mWakefulness=")
    if "mWakefulness=Awake" not in wake:
        print("  -> Màn hình đang tắt, gửi lệnh bật màn hình...")
        run_adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        time.sleep(1.0)
    else:
        print("  -> [✓] Màn hình đã sáng sẵn.")

    # Kiểm tra khóa
    lock_info = run_adb("shell", "dumpsys window | grep -E 'isKeyguardShowing|showing='")
    if "isKeyguardShowing=true" in lock_info or "showing=true" in lock_info:
        print("  -> Màn hình đang khóa, tiến hành mở khóa...")
        run_adb("shell", "input", "swipe", "360", "1300", "360", "400", "300")
        time.sleep(1.0)
        run_adb("shell", "input", "text", "quynh1981")
        time.sleep(0.5)
        run_adb("shell", "input", "keyevent", "KEYCODE_ENTER")
        time.sleep(1.5)
    else:
        print("  -> [✓] Màn hình đã mở khóa sẵn.")

    print("\n[*] 2. Khởi động ứng dụng Microsoft Bing...")
    run_adb("shell", "monkey", "-p", "com.microsoft.bing", "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(4.0)

    # Đưa về Trang chủ (Home)
    print("  -> Chạm icon Trang chủ (dưới cùng góc trái)...")
    run_adb("shell", "input", "tap", "70", "1515")
    time.sleep(2.0)

    step1_path = capture_screen("step1_bing_home_live.png")
    print(f"  -> [✓] Đã chụp ảnh màn hình Trang chủ: {step1_path}")

    print("\n[*] 3. Bấm vào thẻ Rewards ở trang chủ Bing (tọa độ 210, 1050)...")
    run_adb("shell", "input", "tap", "210", "1050")
    print("  -> Chờ 4.5 giây để trang Rewards tải...")
    time.sleep(4.5)

    print("\n[*] 4. Vuốt màn hình lên để đưa khu vực 'Chuỗi liên tiếp' vào tầm nhìn...")
    run_adb("shell", "input", "swipe", "360", "1200", "360", "600", "350")
    time.sleep(2.5)

    step2_path = capture_screen("step2_streak_page_live.png")
    print(f"  -> [✓] Đã chụp ảnh màn hình khu vực Điểm danh: {step2_path}")

    print("\n[*] 5. Phân tích trạng thái điểm danh...")
    img = Image.open(step2_path).convert("RGB")
    arr = np.asarray(img)
    strip = arr[500:800, 450:520].astype(int)
    r, g, b = strip[:, :, 0], strip[:, :, 1], strip[:, :, 2]
    green_mask = (g > 120) & (g > r + 50) & (g > b + 30)
    green_px = int(green_mask.sum())

    print(f"  -> Số pixel xanh lá phát hiện trên hàng 'Đăng ký vào': {green_px}")

    if green_px > 50:
        print("🎉 [KẾT QUẢ] HÔM NAY ĐÃ ĐIỂM DANH XONG! (Đã có dấu tick xanh ✓)")
    else:
        print("⏳ [KẾT QUẢ] HÔM NAY CHƯA ĐIỂM DANH! Đang tiến hành bấm nhận xu...")
        run_adb("shell", "input", "tap", "360", "670")
        time.sleep(3.0)
        step3_path = capture_screen("step3_result_live.png")
        print(f"  -> [✓] Đã chụp ảnh xác nhận sau khi bấm: {step3_path}")

    print("\n=======================================================")
    print("✓ HOÀN THÀNH TEST BƯỚC MỞ BING & VÀO ĐIỂM DANH!")
    print("=======================================================")

if __name__ == "__main__":
    main()
