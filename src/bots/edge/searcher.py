# -*- coding: utf-8 -*-
"""
src/bots/edge/searcher.py
=========================
Thuc hien cac phien tim kiem tren Bing (PC va Mobile emulation).
Tuan thu rule 01_architecture (< 250 dong) va rule 02_automation_bots.
"""

import os
import time
import random
from typing import List, Optional, Dict, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.core.paths import KEYWORDS_PATH
from src.bots.edge.anti_detect import (
    dismiss_popups,
    human_type,
    simulate_human_browsing,
    simulate_random_result_click
)


def load_keywords(keywords_file: Optional[str] = None, count: int = 30) -> List[str]:
    """Nap danh sach tu khoa tim kiem tu tap tin."""
    file_path = keywords_file or str(KEYWORDS_PATH)
    default_keywords = [
        "công nghệ AI mới nhất 2026", "thời tiết hôm nay", "tin tức bóng đá",
        "cách nấu món ngon mỗi ngày", "địa điểm du lịch đẹp", "mẹo sử dụng máy tính",
        "học lập trình python", "giá vàng hôm nay", "tập gym tại nhà",
        "nhạc thư giãn làm việc", "phim chiếu rạp hay", "cách làm giàu",
        "sách hay nên đọc", "lịch thi đấu cúp c1", "công thức làm bánh",
        "tối ưu windows 11", "mua sắm online", "review điện thoại mới",
        "tin chứng khoán", "lợi ích của chạy bộ", "cách tiết kiệm tiền",
        "xu hướng thời trang", "mẹo dọn nhà nhanh", "học tiếng anh giao tiếp",
        "cách chăm sóc da", "quán cà phê đẹp hà nội", "nhà hàng ngon sài gòn",
        "thực đơn giảm cân", "xe ô tô điện", "khám phá vũ trụ"
    ]

    if not os.path.exists(file_path):
        return default_keywords

    with open(file_path, "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not keywords:
        keywords = default_keywords

    random.shuffle(keywords)
    return keywords


def execute_search_session(driver,
                           keywords: List[str],
                           num_searches: int,
                           mode_name: str = "PC",
                           config: Optional[Dict[str, Any]] = None) -> int:
    """Thuc hien mot phien tim kiem tren Bing (PC hoac Mobile)."""
    cfg = config or {}
    search_cfg = cfg.get("search_settings", {})
    min_delay = search_cfg.get("min_delay_seconds", 12)
    max_delay = search_cfg.get("max_delay_seconds", 22)
    speed_min = search_cfg.get("human_typing_speed_min", 0.05)
    speed_max = search_cfg.get("human_typing_speed_max", 0.15)
    enable_cooldown = search_cfg.get("enable_cooldown_batches", True)
    batch_size = search_cfg.get("batch_size", 4)
    batch_cooldown_min = search_cfg.get("batch_cooldown_minutes", 15)
    enable_scroll = search_cfg.get("enable_smooth_scrolling", True)
    enable_mouse = search_cfg.get("enable_mouse_movement", True)
    click_chance = search_cfg.get("random_click_chance", 0.35)

    print(f"\n{'='*20} BẮT ĐẦU TÌM KIẾM {mode_name} ({num_searches} lượt) {'='*20}")

    try:
        driver.get("https://www.bing.com")
        time.sleep(2)
        dismiss_popups(driver)
    except Exception as e:
        print(f"[!] Khong the mo bing.com: {e}")

    completed = 0
    while completed < num_searches and keywords:
        kw = keywords.pop(0)
        search_idx = completed + 1
        print(f"\n[{mode_name} #{search_idx}/{num_searches}] 🔍 Đang tìm: \"{kw}\"")

        try:
            dismiss_popups(driver)

            search_box = None
            selectors = [
                (By.ID, "sb_form_q"),
                (By.NAME, "q"),
                (By.CSS_SELECTOR, "textarea[name='q']"),
                (By.CSS_SELECTOR, "input[name='q']"),
                (By.CSS_SELECTOR, "input.b_searchbox"),
                (By.CSS_SELECTOR, "input[type='search']")
            ]

            for by_type, selector in selectors:
                try:
                    search_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((by_type, selector))
                    )
                    if search_box:
                        break
                except Exception:
                    continue

            if not search_box:
                driver.get("https://www.bing.com")
                time.sleep(2)
                dismiss_popups(driver)
                search_box = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.ID, "sb_form_q"))
                )

            driver.execute_script("arguments[0].focus(); arguments[0].click();", search_box)
            time.sleep(random.uniform(0.3, 0.6))

            search_box.send_keys(Keys.CONTROL + "a")
            time.sleep(0.1)
            search_box.send_keys(Keys.BACKSPACE)
            time.sleep(random.uniform(0.2, 0.4))

            human_type(search_box, kw, speed_min, speed_max)
            time.sleep(random.uniform(0.4, 0.8))

            search_box.send_keys(Keys.ENTER)

            simulate_human_browsing(driver, enable_scrolling=enable_scroll, enable_mouse=enable_mouse)
            simulate_random_result_click(driver, click_chance=click_chance)

            completed += 1
            wait_time = random.uniform(min_delay, max_delay)
            print(f"   ✓ Hoàn thành #{search_idx}. Nghỉ an toàn {wait_time:.1f}s...")

            if enable_cooldown and (completed % batch_size == 0) and completed < num_searches:
                cooldown_sec = batch_cooldown_min * 60
                print(f"\n⏳ [Cooldown Safe] Tạm dừng {batch_cooldown_min} phút chống hạn chế Bing...")
                for remaining in range(cooldown_sec, 0, -10):
                    mins, secs = divmod(remaining, 60)
                    print(f"\r   Nghỉ giải lao: {mins:02d}:{secs:02d} còn lại...", end="", flush=True)
                    time.sleep(10)
                print("\n   [✓] Tiếp tục đợt tìm kiếm tiếp theo...")
            else:
                time.sleep(wait_time)

        except Exception as e:
            print(f"   [!] Gặp vấn đề ở lượt này ({e}). Đang tải lại...")
            time.sleep(3)
            try:
                driver.get("https://www.bing.com")
                time.sleep(3)
                dismiss_popups(driver)
            except Exception:
                pass

    print(f"\n[✓] ĐÃ HOÀN TẤT {completed}/{num_searches} LƯỢT TÌM KIẾM {mode_name}!")
    return completed
