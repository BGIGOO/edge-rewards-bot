# -*- coding: utf-8 -*-
"""
src/bots/edge/runner.py
=======================
Dieu phoi phien chay Edge Rewards cho mot hoac nhieu tai khoan.
Tuan thu rule 01_architecture (< 250 dong) va rule 02_automation_bots.
"""

import os
import sys
import json
import time
import random
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from selenium.webdriver.common.by import By

from src.core.paths import CONFIG_PATH
from src.bots.edge.anti_detect import dismiss_popups
from src.bots.edge.browser import (
    create_edge_driver,
    get_profile_abs_path,
    kill_zombie_edge_processes,
    open_browser_for_login
)
from src.bots.edge.searcher import load_keywords, execute_search_session


def load_config() -> Dict[str, Any]:
    """Tai cau hinh tu config.json."""
    default_config = {
        "search_settings": {
            "pc_searches": 31,
            "mobile_searches": 21,
            "min_delay_seconds": 12,
            "max_delay_seconds": 22,
            "enable_cooldown_batches": True,
            "batch_size": 4,
            "batch_cooldown_minutes": 3,
            "enable_smooth_scrolling": True,
            "enable_mouse_movement": True,
            "random_click_chance": 0.25,
            "human_typing_speed_min": 0.04,
            "human_typing_speed_max": 0.1
        },
        "browser_settings": {
            "profile_directory_path": "data/profiles/edge_profile",
            "headless": False,
            "mobile_device_name": "Pixel 7"
        },
        "profiles": []
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default_config.update(cfg)
        except Exception as e:
            print(f"[!] Loi doc config.json: {e}")
    return default_config


def check_and_prompt_first_time_login(driver, profile_name: str = "Tài khoản này") -> None:
    """Kiem tra neu nguoi dung chua dang nhap tai khoan Microsoft tren profile nay."""
    try:
        driver.get("https://www.bing.com")
        time.sleep(2)
        dismiss_popups(driver)

        logged_name = None
        for sel in ["#id_n", "#id_s", ".id_text"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                txt = elem.text.strip()
                if txt and not any(k in txt.lower() for k in ["sign in", "đăng nhập", "login"]):
                    logged_name = txt
                    break
            except Exception:
                continue

        if logged_name:
            print(f"   [✓] Tai khoan Bing: \"{logged_name}\"")
        else:
            sign_in_elements = driver.find_elements(By.ID, "id_s") + driver.find_elements(By.CSS_SELECTOR, "a[id*='signin']")
            needs_login = any(el.is_displayed() and ("sign in" in el.text.lower() or "đăng nhập" in el.text.lower()) for el in sign_in_elements)
            if needs_login:
                print(f"🔔 Profile [{profile_name}] chua dang nhap. Dang cho dang nhap...")
                if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
                    try:
                        input("👉 Nhan ENTER sau khi dang nhap xong tren Edge...")
                    except Exception:
                        pass
                else:
                    time.sleep(10)
                time.sleep(2)
                dismiss_popups(driver)
    except Exception:
        pass


def run_profile_session(profile: Dict[str, Any], selected_mode: str, config: Dict[str, Any], keywords_pool: Optional[List[str]] = None) -> Dict[str, Any]:
    """Thuc hien phien tim kiem cho mot profile cu the (PC va Mobile)."""
    p_name = profile.get("name", f"Profile {profile.get('id', '1')}")
    p_dir = get_profile_abs_path(profile)

    run_pc = selected_mode in ["all", "desktop"]
    run_mobile = selected_mode in ["all", "mobile"]
    search_cfg = config.get("search_settings", {})
    pc_count = search_cfg.get("pc_searches", 31) if run_pc else 0
    mobile_count = search_cfg.get("mobile_searches", 21) if run_mobile else 0

    print(f"\n👤 BẮT ĐẦU: {p_name.upper()} | Mode: {selected_mode.upper()} | PC: {pc_count} | Mob: {mobile_count}")
    keywords = list(keywords_pool) if keywords_pool else load_keywords()
    random.shuffle(keywords)

    total_searches_done = 0
    start_time = datetime.now()

    # Tim kiem Desktop
    if run_pc and pc_count > 0:
        pc_driver = None
        try:
            pc_driver = create_edge_driver(is_mobile=False, config=config, profile_target=profile)
            check_and_prompt_first_time_login(pc_driver, profile_name=p_name)
            total_searches_done += execute_search_session(pc_driver, keywords, pc_count, mode_name="PC", config=config)
        except Exception as e:
            print(f"[!] Loi PC search ({p_name}): {e}")
        finally:
            if pc_driver:
                try:
                    pc_driver.quit()
                except Exception:
                    pass
                time.sleep(1)
                kill_zombie_edge_processes(p_dir)

        if run_mobile and mobile_count > 0:
            time.sleep(random.uniform(5, 10))

    # Tim kiem Mobile
    if run_mobile and mobile_count > 0:
        mob_driver = None
        try:
            mob_driver = create_edge_driver(is_mobile=True, config=config, profile_target=profile)
            check_and_prompt_first_time_login(mob_driver, profile_name=p_name)
            total_searches_done += execute_search_session(mob_driver, keywords, mobile_count, mode_name="MOBILE", config=config)
        except Exception as e:
            print(f"[!] Loi Mobile search ({p_name}): {e}")
        finally:
            if mob_driver:
                try:
                    mob_driver.quit()
                except Exception:
                    pass
                time.sleep(1)
                kill_zombie_edge_processes(p_dir)

    duration = datetime.now() - start_time
    return {"profile_name": p_name, "searches": total_searches_done, "duration": duration}


def main():
    parser = argparse.ArgumentParser(description="Microsoft Rewards Auto Search Bot")
    parser.add_argument("--profile", default=None, help="Chon profile: 1, 2, all...")
    parser.add_argument("--mode", choices=["all", "desktop", "pc", "mobile"], default=None)
    parser.add_argument("--pc", "--desktop", dest="pc_flag", action="store_true")
    parser.add_argument("--mobile", dest="mobile_flag", action="store_true")
    parser.add_argument("--login", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    args, _ = parser.parse_known_args()

    config = load_config()
    profiles = config.get("profiles", [])
    if not profiles:
        profiles = [{"id": "1", "name": "Profile 1", "path": "data/profiles/edge_profile"}]

    selected_profiles = profiles
    if args.profile:
        p_arg = str(args.profile).strip().lower()
        if p_arg not in ["all", "both", "tatca"]:
            matched = [p for p in profiles if str(p.get("id", "")).lower() == p_arg or p.get("name", "").lower() == p_arg]
            selected_profiles = [matched[0]] if matched else [profiles[0]]

    if args.login:
        target = selected_profiles[0]
        proc = open_browser_for_login(target, config=config)
        if proc:
            proc.wait()
        return

    mode = "desktop" if args.pc_flag or args.mode in ["desktop", "pc"] else ("mobile" if args.mobile_flag or args.mode == "mobile" else (args.mode or "all"))
    raw_keywords = load_keywords()
    for current_p in selected_profiles:
        run_profile_session(current_p, mode, config, keywords_pool=raw_keywords)
        time.sleep(2)


if __name__ == "__main__":
    main()
