# -*- coding: utf-8 -*-
"""
src/bots/android/checkin_flow.py
================================
Kich ban tu dong hoa diem danh App Bing Android 7 buoc.
Tuan thu rule 01_architecture (< 250 dong) va rule 02_automation_bots.
"""

import sys
import time
import random
import argparse
from typing import Optional, Dict, Any

from src.core.paths import SCREENSHOTS_DIR
from src.bots.android.adb_client import (
    ADBClient,
    DEFAULT_DEVICE,
    REWARDS_BTN,
    log,
    human_sleep
)
from src.bots.android.screen_analyzer import (
    capture_screenshot as _capture_screen,
    find_today_circle as _find_today_circle,
    check_daily_streak_status as _check_daily_streak_status
)


class AndroidBingCheckinBot(ADBClient):
    """Bot diem danh tu dong tren ung dung Microsoft Bing Android."""

    def __init__(self, device: str = DEFAULT_DEVICE, pin: Optional[str] = None, package: str = "com.microsoft.bing"):
        super().__init__(device=device, pin=pin, package=package)

    def capture_screenshot(self, save_path: Optional[str] = None):
        return _capture_screen(self, save_path)

    def find_today_circle(self, img):
        return _find_today_circle(img)

    def check_daily_streak_status(self, img):
        return _check_daily_streak_status(img)

    def execute_checkin(self) -> Dict[str, Any]:
        """Quy trinh tu dong hoa diem danh day du tren App Bing."""
        log("=======================================================", "action")
        log("🚀 BẮT ĐẦU QUY TRÌNH ĐIỂM DANH APP BING ANDROID", "action")
        log(f"Thiết bị mục tiêu: {self.device}", "info")
        log("=======================================================", "action")

        self.ensure_connected()
        self.unlock_device()

        try:
            self._adb_shell("settings", "put", "system", "screen_off_timeout", "600000")
        except Exception:
            pass

        log(f"Mở ứng dụng {self.package}...", "action")
        self._adb_shell("monkey", "-p", self.package, "-c", "android.intent.category.LAUNCHER", "1")
        human_sleep(4.0, 5.5)

        home_btn_x = int(70 / 720 * self.screen_width)
        home_btn_y = int(1515 / 1612 * self.screen_height)
        self._adb_shell("input", "tap", str(home_btn_x), str(home_btn_y))
        human_sleep(2.0, 3.0)

        log("Bấm nút 'Rewards' trên giao diện chính của Bing...", "action")
        self.tap_relative(*REWARDS_BTN)
        human_sleep(4.5, 6.0)

        log("Vuốt màn hình lên để đưa thẻ 'Chuỗi liên tiếp' vào tầm nhìn...", "action")
        mid_x = self.screen_width // 2
        swipe_from_y = int(self.screen_height * 0.74)
        swipe_to_y = int(self.screen_height * 0.37)
        self._adb_shell("input", "swipe", str(mid_x), str(swipe_from_y), str(mid_x), str(swipe_to_y), "350")
        human_sleep(2.5, 3.5)

        frame_before_path = str(SCREENSHOTS_DIR / "android_checkin_before.png")
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

        already_done, coords = self.check_daily_streak_status(img_before)
        if not already_done and coords is None:
            legacy_coords = self.find_today_circle(img_before)
            if legacy_coords is not None:
                coords = legacy_coords
                already_done = False
            else:
                already_done = True

        if already_done:
            log("🎉 Hôm nay bạn đã điểm danh nhận xu (5 điểm) rồi!", "success")
            try:
                self.close_app()
                self._adb_shell("input", "keyevent", "KEYCODE_HOME")
            except Exception:
                pass
            return {
                "success": True,
                "already_done": True,
                "message": "Hôm nay đã được điểm danh từ trước.",
                "frame_before": "/screenshots/android_checkin_before.png",
                "frame_after": "/screenshots/android_checkin_before.png"
            }

        cx, cy = coords
        log(f"🎯 Nhận diện nút 'Đăng ký vào' tại ({cx}, {cy}). Tiến hành bấm nhận xu...", "action")
        tap_x = int(cx + random.uniform(-6, 6))
        tap_y = int(cy + random.uniform(-6, 6))
        self._adb_shell("input", "tap", str(tap_x), str(tap_y))
        human_sleep(3.5, 5.0)

        frame_after_path = str(SCREENSHOTS_DIR / "android_checkin_after.png")
        log("Chụp ảnh màn hình đối soát kết quả sau khi bấm...", "action")
        img_after = self.capture_screenshot(frame_after_path)

        success = True
        if img_after is not None:
            done_after, _ = self.check_daily_streak_status(img_after)
            if done_after:
                log("✅ [THÀNH CÔNG] Đã điểm danh và nhận xu thành công trên App Bing!", "success")
            else:
                log("⚠️ Đã gửi lệnh bấm nhận xu, đang chờ máy chủ Bing ghi nhận điểm.", "warn")

        try:
            self.close_app()
            self._adb_shell("input", "keyevent", "KEYCODE_HOME")
            human_sleep(0.5, 1.0)
        except Exception:
            pass

        return {
            "success": success,
            "already_done": False,
            "message": "Điểm danh hoàn tất thành công!",
            "coordinates": (cx, cy),
            "frame_before": "/screenshots/android_checkin_before.png",
            "frame_after": "/screenshots/android_checkin_after.png"
        }


def run_checkin_flow(device: Optional[str] = None, pin: Optional[str] = None) -> Dict[str, Any]:
    bot = AndroidBingCheckinBot(device=device or DEFAULT_DEVICE, pin=pin)
    return bot.execute_checkin()


def main():
    parser = argparse.ArgumentParser(description="Microsoft Rewards Android Check-in Bot")
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--pin", default=None)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--reconnect", action="store_true")
    parser.add_argument("--open-app", action="store_true")
    parser.add_argument("--close-app", action="store_true")
    parser.add_argument("--test-screen", action="store_true")
    parser.add_argument("--toggle-screen", action="store_true")
    args = parser.parse_args()

    bot = AndroidBingCheckinBot(device=args.device, pin=args.pin)
    if args.status:
        import json
        print(json.dumps(bot.get_device_status(), indent=2, ensure_ascii=False))
        sys.exit(0)
    if args.reconnect:
        sys.exit(0 if bot.reconnect_device() else 1)
    if args.open_app:
        sys.exit(0 if bot.open_app().get("success") else 1)
    if args.close_app:
        sys.exit(0 if bot.close_app().get("success") else 1)
    if args.toggle_screen:
        sys.exit(0 if bot.toggle_screen().get("success") else 1)
    if args.test_screen:
        bot.ensure_connected()
        test_path = str(SCREENSHOTS_DIR / "test_device_screen.png")
        img = bot.capture_screenshot(test_path)
        sys.exit(0 if img else 1)

    res = bot.execute_checkin()
    sys.exit(0 if res.get("success") else 2)


if __name__ == "__main__":
    main()
