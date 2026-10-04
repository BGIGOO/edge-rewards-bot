# -*- coding: utf-8 -*-
"""
====================================================================
      MICROSOFT REWARDS BOT - AUDITOR & SUPERVISOR AGENT
      Agent độc lập kiểm tra & giám sát các tiêu chuẩn Anti-Ban
====================================================================
Chức năng:
- Tự động quét và đánh giá tĩnh 5 cơ chế chống phát hiện bot trong codebase.
- Kiểm tra tính hợp lệ của cấu hình config.json, keywords.txt và mã nguồn.
- Chấm điểm an toàn (Safety Score) trước khi bot vận hành thực tế.
====================================================================
"""

import os
import sys
import json
import re
import py_compile

# Đảm bảo in tiếng Việt không lỗi font
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
BOT_FILE = os.path.join(SCRIPT_DIR, "edge_rewards_bot.py")
KEYWORDS_FILE = os.path.join(SCRIPT_DIR, "keywords.txt")


class AuditorAgent:
    def __init__(self):
        self.results = []
        self.score = 0
        self.max_score = 5

    def log_check(self, name, status, details, recommendation=None):
        self.results.append({
            "name": name,
            "status": status,
            "details": details,
            "recommendation": recommendation
        })
        if status == "PASS":
            self.score += 1

    def run_audit(self):
        print("\n" + "=" * 70)
        print("🕵️‍♂️  AUDITOR AGENT: BẮT ĐẦU THANH TRA CÁC TIÊU CHUẨN ANTI-DETECTION")
        print("=" * 70)

        # 1. Kiểm tra file cơ bản
        if not os.path.exists(BOT_FILE) or not os.path.exists(CONFIG_FILE):
            print("[❌ CRITICAL] Không tìm thấy file edge_rewards_bot.py hoặc config.json!")
            return False

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        with open(BOT_FILE, "r", encoding="utf-8") as f:
            code = f.read()

        search_cfg = config.get("search_settings", {})
        browser_cfg = config.get("browser_settings", {})

        # -------------------------------------------------------------
        # TIÊU CHUẨN 1: Cooldown Batches (Chống hạn chế 15 phút của Bing)
        # -------------------------------------------------------------
        cooldown_enabled = search_cfg.get("enable_cooldown_batches", False)
        batch_size = search_cfg.get("batch_size", 0)
        cooldown_min = search_cfg.get("batch_cooldown_minutes", 0)

        has_cooldown_logic = "cooldown_sec = batch_cooldown_min * 60" in code and "enable_cooldown" in code

        if cooldown_enabled and batch_size <= 5 and cooldown_min >= 5 and has_cooldown_logic:
            note = " (Lưu ý: Nếu tài khoản bị Microsoft phạt hard-cooldown, nên tăng lên 15 phút)" if cooldown_min < 15 else ""
            self.log_check(
                "Tiêu chuẩn 1: Cooldown Batches",
                "PASS",
                f"Đã bật (Mỗi {batch_size} lượt nghỉ {cooldown_min} phút). Logic đếm ngược trong code hoàn chỉnh.{note}"
            )
        else:
            self.log_check(
                "Tiêu chuẩn 1: Cooldown Batches",
                "WARN",
                f"Cooldown={cooldown_enabled}, Batch Size={batch_size}, Cooldown Min={cooldown_min}p.",
                "Khuyến nghị: Bật enable_cooldown_batches=true, batch_size<=4, cooldown>=5-15 phút."
            )

        # -------------------------------------------------------------
        # TIÊU CHUẨN 2: Giãn cách an toàn (Quy tắc 6 giây & Tốc độ gõ)
        # -------------------------------------------------------------
        min_delay = search_cfg.get("min_delay_seconds", 0)
        max_delay = search_cfg.get("max_delay_seconds", 0)
        typing_min = search_cfg.get("human_typing_speed_min", 0)
        typing_max = search_cfg.get("human_typing_speed_max", 0)

        delay_safe = min_delay >= 10 and max_delay > min_delay
        typing_safe = 0.03 <= typing_min <= 0.10 and typing_max <= 0.25

        if delay_safe and typing_safe and "human_type(" in code:
            self.log_check(
                "Tiêu chuẩn 2: Giãn cách & Tốc độ gõ phím",
                "PASS",
                f"Delay an toàn: {min_delay}s - {max_delay}s (Vượt ngưỡng 6s của Bing). Tốc độ gõ: {typing_min}s - {typing_max}s."
            )
        else:
            self.log_check(
                "Tiêu chuẩn 2: Giãn cách & Tốc độ gõ phím",
                "WARN",
                f"Delay={min_delay}-{max_delay}s, Typing={typing_min}-{typing_max}s.",
                "Khuyến nghị: min_delay_seconds tối thiểu 10s để không bị Bing tính 0 điểm."
            )

        # -------------------------------------------------------------
        # TIÊU CHUẨN 3: Tỷ lệ Click đọc bài (CTR Engagement)
        # -------------------------------------------------------------
        click_chance = search_cfg.get("random_click_chance", 0)
        has_click_func = "def simulate_random_result_click" in code
        handles_tabs = "window_handles" in code and "driver.switch_to.window" in code
        called_in_loop = "simulate_random_result_click(driver" in code

        if has_click_func and handles_tabs and called_in_loop and (0.2 <= click_chance <= 0.5):
            self.log_check(
                "Tiêu chuẩn 3: Click đọc kết quả ngẫu nhiên (CTR)",
                "PASS",
                f"Đã kích hoạt tỷ lệ click {int(click_chance * 100)}%. Có cơ chế xử lý đa tab và dừng đọc tự nhiên."
            )
        else:
            self.log_check(
                "Tiêu chuẩn 3: Click đọc kết quả ngẫu nhiên (CTR)",
                "FAIL",
                f"Hàm click={has_click_func}, Tỷ lệ click={click_chance}.",
                "Khuyến nghị: Đảm bảo có simulate_random_result_click với tỷ lệ 30-40%."
            )

        # -------------------------------------------------------------
        # TIÊU CHUẨN 4: Chuẩn hóa thiết bị Mobile sang Android
        # -------------------------------------------------------------
        device_name = browser_cfg.get("mobile_device_name", "")
        is_android_device = any(dev in device_name.lower() for dev in ["pixel", "samsung", "galaxy", "nexus"])
        has_mobile_emulation = "mobileEmulation" in code and "set_window_size" in code

        if is_android_device and has_mobile_emulation:
            self.log_check(
                "Tiêu chuẩn 4: Giả lập Mobile chuẩn Android",
                "PASS",
                f"Thiết bị di động: {device_name} (Android). Tránh xung đột chữ ký phần cứng của iOS trên Windows."
            )
        else:
            self.log_check(
                "Tiêu chuẩn 4: Giả lập Mobile chuẩn Android",
                "WARN",
                f"Thiết bị hiện tại: {device_name}.",
                "Khuyến nghị: Dùng thiết bị Android như 'Pixel 7' hoặc 'Samsung Galaxy S20 Ultra'."
            )

        # -------------------------------------------------------------
        # TIÊU CHUẨN 5: Chuyển động chuột & Stealth Script
        # -------------------------------------------------------------
        has_action_chains = "ActionChains" in code and "move_to_element" in code
        has_mouse_func = "simulate_natural_mouse_movement" in code
        has_stealth_cdp = "Page.addScriptToEvaluateOnNewDocument" in code and "navigator" in code

        if has_action_chains and has_mouse_func and has_stealth_cdp:
            self.log_check(
                "Tiêu chuẩn 5: Chuyển động chuột & Tẩy cờ WebDriver",
                "PASS",
                "Đã tích hợp ActionChains rê chuột ngẫu nhiên và tiêm CDP script ẩn danh webdriver/plugins."
            )
        else:
            self.log_check(
                "Tiêu chuẩn 5: Chuyển động chuột & Tẩy cờ WebDriver",
                "FAIL",
                f"ActionChains={has_action_chains}, MouseFunc={has_mouse_func}, Stealth={has_stealth_cdp}.",
                "Khuyến nghị: Đảm bảo có di chuyển chuột thật và script ghi đè navigator.webdriver."
            )

        # -------------------------------------------------------------
        # IN KẾT QUẢ ĐÁNH GIÁ TỔNG QUAN
        # -------------------------------------------------------------
        print("\n📊 BẢNG ĐÁNH GIÁ CHI TIẾT TỪ AGENT GIÁM SÁT:\n")
        for idx, item in enumerate(self.results, 1):
            badge = "✅ [PASS]" if item["status"] == "PASS" else ("⚠️  [WARN]" if item["status"] == "WARN" else "❌ [FAIL]")
            print(f"{idx}. {badge} {item['name']}")
            print(f"   • Chi tiết   : {item['details']}")
            if item["recommendation"]:
                print(f"   • Góp ý      : {item['recommendation']}")
            print()

        # Kiểm tra biên dịch cú pháp
        print("-" * 70)
        try:
            py_compile.compile(BOT_FILE, doraise=True)
            print("🔍 Kiểm tra cú pháp Python: ✅ HỢP LỆ (Không có lỗi SyntaxError)")
        except Exception as e:
            print(f"🔍 Kiểm tra cú pháp Python: ❌ LỖI ({e})")
            return False

        # Kiểm tra từ khóa
        if os.path.exists(KEYWORDS_FILE):
            with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            print(f"🔍 Kiểm tra danh sách từ khóa: ✅ SẴN SÀNG ({len(lines)} từ khóa hợp lệ)")

        print("=" * 70)
        print(f"🎯 TỔNG KẾT ĐỘ AN TOÀN: {self.score}/{self.max_score} TIÊU CHUẨN ĐẠT MỨC CAO NHẤT!")
        if self.score == self.max_score:
            print("🛡️  ĐÁNH GIÁ CỦA AGENT: BOT ĐÃ ĐẠT MỨC AN TOÀN TỐI ĐA (READY TO RUN)!")
        else:
            print("⚠️  ĐÁNH GIÁ CỦA AGENT: CẦN ĐIỀU CHỈNH CÁC MỤC CẢNH BÁO ĐỂ ĐẠT AN TOÀN TUYỆT ĐỐI.")
        print("=" * 70 + "\n")
        return self.score == self.max_score


if __name__ == "__main__":
    agent = AuditorAgent()
    success = agent.run_audit()
    sys.exit(0 if success else 1)
