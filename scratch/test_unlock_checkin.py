import sys, os, time, subprocess

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from android_checkin import AndroidBingCheckinBot

ADB_PATH = r"C:\Users\NManh\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "100.71.117.39:5555"

print("[*] 1. Khóa màn hình điện thoại (KEYCODE_POWER)...")
subprocess.run([ADB_PATH, "-s", DEVICE, "shell", "input", "keyevent", "KEYCODE_POWER"], capture_output=True)
time.sleep(2.0)

bot = AndroidBingCheckinBot(device=DEVICE)
print(f"[*] PIN được load: {bot.pin}")
print(f"[*] Trạng thái trước khi unlock:")
print(f"    - Màn hình sáng: {bot.is_screen_awake()}")
print(f"    - Bị khóa: {bot.is_device_locked()}")

print("\n[*] 2. Chạy unlock_device() từ android_checkin.py...")
bot.unlock_device()

print(f"\n[*] 3. Trạng thái sau khi unlock:")
print(f"    - Màn hình sáng: {bot.is_screen_awake()}")
print(f"    - Bị khóa: {bot.is_device_locked()}")

if bot.is_screen_awake() and not bot.is_device_locked():
    print("✅ [THÀNH CÔNG] Điện thoại đã được đánh thức và mở khóa hoàn toàn!")
else:
    print("❌ [THẤT BẠI] Điện thoại vẫn chưa mở khóa.")
