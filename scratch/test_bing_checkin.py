# -*- coding: utf-8 -*-
"""
Script kiểm tra từng bước:
1. Đảm bảo điện thoại mở khóa (sử dụng logic thông minh đã test)
2. Mở App Microsoft Bing (hoặc chuyển về Trang chủ nếu đang mở sẵn)
3. Bấm vào nút "Rewards" trên trang chủ
4. Vuốt màn hình để hiển thị thẻ "Chuỗi liên tiếp" và "Đăng ký vào (Nhận xu 5 điểm)"
5. Tự động kiểm tra trạng thái: Đã điểm danh hay Chưa điểm danh
6. Bấm nhận xu nếu chưa điểm danh và chụp ảnh đối soát
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

import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = r"C:\Users\NManh\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "100.71.117.39:5555"

# Tọa độ tương đối trên màn hình 720x1612
REWARDS_HOME_BTN = (210, 1070)    # Ô Rewards ở trang chủ Bing
HOME_TAB_BTN = (70, 1515)         # Icon Trang chủ ở thanh điều hướng dưới
CHECKIN_ROW_TAP = (360, 565)      # Vị trí hàng "Đăng ký vào" (5 điểm)

# Đọc PIN từ config.json
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
PIN = "quynh1981"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
        PIN = cfg.get("android_settings", {}).get("pin", PIN)
except Exception:
    pass


def run_adb(*args, timeout=25):
    cmd = [ADB_PATH, "-s", DEVICE, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()


def capture_screen(save_name):
    """Chụp ảnh màn hình điện thoại và lưu vào thư mục scratch"""
    remote_path = f"/data/local/tmp/{save_name}"
    local_path = os.path.join(SCRIPT_DIR, "scratch", save_name)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    run_adb("shell", "screencap", "-p", remote_path)
    subprocess.run([ADB_PATH, "-s", DEVICE, "pull", remote_path, local_path], capture_output=True, timeout=15)
    return local_path


def is_screen_awake():
    out = run_adb("shell", "dumpsys power | grep mWakefulness=")
    return "mWakefulness=Awake" in out


def is_device_locked():
    out_win = run_adb("shell", "dumpsys window | grep -E 'isKeyguardShowing|showing='")
    if "isKeyguardShowing=true" in out_win or "showing=true" in out_win:
        return True
    if "isKeyguardShowing=false" in out_win or "showing=false" in out_win:
        return False
    out_trust = run_adb("shell", "dumpsys trust | grep deviceLocked=")
    if "deviceLocked=1" in out_trust or "deviceLocked=true" in out_trust:
        return True
    return False


def get_current_app():
    return run_adb("shell", "dumpsys window | grep mCurrentFocus")


def check_if_already_checked_in(img_path):
    """
    Kiểm tra xem hàng 'Đăng ký vào' đã có dấu check xanh lá (✓) chưa.
    Dấu check có màu xanh lục đặc trưng RGB: R < 50, G > 130, B < 110.
    Vùng quét Y: 530 - 600, X: 450 - 520.
    """
    try:
        img = Image.open(img_path).convert("RGB")
        arr = np.asarray(img)
        # Cắt vùng quanh huy hiệu check-in
        patch = arr[520:610, 450:520].astype(int)
        r, g, b = patch[:, :, 0], patch[:, :, 1], patch[:, :, 2]
        # Màu xanh lá của dấu check Bing Rewards
        green = (g > 120) & (g > r + 50) & (g > b + 30)
        return green.sum() > 30
    except Exception as e:
        print(f"[!] Lỗi phân tích ảnh check-in: {e}")
        return False


def main():
    print("=======================================================")
    print("🚀 BẮT ĐẦU TEST: MỞ APP BING & ĐIỂM DANH NHẬN XU")
    print("=======================================================")

    # BƯỚC 1: ĐẢM BẢO MÀN HÌNH MỞ KHÓA
    print("\n[*] 1. Kiểm tra trạng thái điện thoại...")
    if not is_screen_awake():
        print("[*] Đang đánh thức màn hình...")
        run_adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        time.sleep(1.0)
    else:
        print("[✓] Màn hình đã sáng sẵn.")

    if is_device_locked():
        print("[*] Đang mở khóa bằng mã PIN...")
        run_adb("shell", "input", "swipe", "360", "1300", "360", "400", "300")
        time.sleep(1.0)
        if PIN:
            run_adb("shell", "input", "text", str(PIN))
            time.sleep(0.5)
            run_adb("shell", "input", "keyevent", "KEYCODE_ENTER")
            time.sleep(1.5)
        print("[✓] Đã mở khóa thành công!")
    else:
        print("[✓] Điện thoại đã mở khóa sẵn.")

    # BƯỚC 2: MỞ APP MICROSOFT BING VÀ VỀ TRANG CHỦ
    print("\n[*] 2. Kiểm tra App Microsoft Bing...")
    curr_focus = get_current_app()
    if "com.microsoft.bing" not in curr_focus:
        print("[*] Khởi chạy App Microsoft Bing...")
        run_adb("shell", "monkey", "-p", "com.microsoft.bing", "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(4.0)
    else:
        print("[✓] App Bing đang mở sẵn trên màn hình.")

    # Bấm vào icon Home để chắc chắn đang ở Trang chủ chính
    print("[*] Chuyển về màn hình Trang chủ của Bing...")
    run_adb("shell", "input", "tap", str(HOME_TAB_BTN[0]), str(HOME_TAB_BTN[1]))
    time.sleep(2.0)

    snap_home = capture_screen("step1_bing_home.png")
    print(f"[✓] Đã chụp ảnh Trang chủ: {snap_home}")

    # BƯỚC 3: BẤM VÀO NÚT REWARDS Ở TRANG CHỦ
    print(f"\n[*] 3. Bấm vào nút Rewards tại tọa độ {REWARDS_HOME_BTN}...")
    run_adb("shell", "input", "tap", str(REWARDS_HOME_BTN[0]), str(REWARDS_HOME_BTN[1]))
    print("[*] Chờ trang Rewards tải (4 giây)...")
    time.sleep(4.0)

    # BƯỚC 4: VUỐT MÀN HÌNH ĐỂ HIỂN THỊ THẺ ĐIỂM DANH
    print("[*] 4. Vuốt màn hình lên để đưa thẻ 'Chuỗi liên tiếp' vào tầm nhìn...")
    run_adb("shell", "input", "swipe", "360", "1200", "360", "600", "350")
    time.sleep(2.5)

    snap_streak = capture_screen("step2_streak_page.png")
    print(f"[✓] Đã chụp ảnh Thẻ Điểm Danh: {snap_streak}")

    # BƯỚC 5: KIỂM TRA ĐIỂM DANH & BẤM NHẬN XU
    print("\n[*] 5. Phân tích trạng thái điểm danh hôm nay...")
    is_done = check_if_already_checked_in(snap_streak)

    if is_done:
        print("🎉 [KẾT QUẢ] HÔM NAY BẠN ĐÃ ĐIỂM DANH NHẬN XU (5 ĐIỂM) RỒI!")
        print("    -> Hàng 'Đăng ký vào' đã có dấu tick xanh lá (✓).")
    else:
        print("⏳ [KẾT QUẢ] HÔM NAY CHƯA ĐIỂM DANH! Đang tiến hành bấm nhận xu...")
        print(f"[*] Bấm vào nút 'Đăng ký vào' tại {CHECKIN_ROW_TAP}...")
        run_adb("shell", "input", "tap", str(CHECKIN_ROW_TAP[0]), str(CHECKIN_ROW_TAP[1]))
        time.sleep(3.5)

        snap_after = capture_screen("step3_checkin_result.png")
        print(f"[✓] Đã chụp ảnh xác nhận sau khi bấm: {snap_after}")

        if check_if_already_checked_in(snap_after):
            print("✅ [THÀNH CÔNG] ĐÃ ĐIỂM DANH VÀ NHẬN XU THÀNH CÔNG!")
        else:
            print("⚠️ Đã gửi lệnh bấm nhận xu, vui lòng kiểm tra ảnh đối soát.")

    print("\n=======================================================")
    print("✓ HOÀN THÀNH QUY TRÌNH KIỂM TRA!")
    print(f"Ảnh 1: Trang chủ -> scratch/step1_bing_home.png")
    print(f"Ảnh 2: Trang điểm danh -> scratch/step2_streak_page.png")
    print("=======================================================")


if __name__ == "__main__":
    main()
