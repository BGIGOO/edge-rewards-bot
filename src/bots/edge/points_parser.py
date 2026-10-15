# -*- coding: utf-8 -*-
"""
src/bots/edge/points_parser.py
==============================
Boc tach thong tin diem thuong tu modal Points breakdown va trang rewards.bing.com.
Kiem tra diem cho tung tai khoan rieng biet o che do headless an toan.
Tuan thu rule 01_architecture (< 250 dong) va rule 02_automation_bots.
"""

import re
import json
import time
from typing import Dict, Any, Optional

from selenium.webdriver.common.by import By

from src.core.paths import CONFIG_PATH
from src.core.db import update_profile_db, init_db
from src.bots.edge.browser import create_edge_driver, get_profile_abs_path, kill_zombie_edge_processes


def parse_rewards_breakdown_text(text: str) -> Dict[str, Any]:
    """Phan tich noi dung text tu modal Points breakdown (ho tro tieng Anh & Viet)."""
    result = {
        "today_points": 0,
        "desktop_points": "0/90",
        "mobile_points": "0/60",
        "offers_points": 0,
        "lifetime_points": 0,
        "total_points": 0
    }
    if not text:
        return result

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        line_lower = line.lower()

        # 1. Today's points
        if "today's points" in line_lower or "điểm hôm nay" in line_lower:
            m = re.search(r"(\d[\d,]*)", line[13:])
            if m:
                result["today_points"] = int(m.group(1).replace(",", ""))
            elif i + 1 < len(lines):
                next_m = re.match(r"^(\d[\d,]*)$", lines[i+1])
                if next_m:
                    result["today_points"] = int(next_m.group(1).replace(",", ""))

        # 2. Lifetime points
        if line_lower in ["lifetime", "tổng", "tích lũy", "tổng điểm"]:
            if i + 1 < len(lines):
                m = re.search(r"(\d[\d,]*)", lines[i+1])
                if m:
                    result["lifetime_points"] = int(m.group(1).replace(",", ""))
        elif "lifetime" in line_lower or "tổng tích lũy" in line_lower:
            m = re.search(r"(\d[\d,]*)", line)
            if m and not line_lower.startswith("lifetime"):
                result["lifetime_points"] = int(m.group(1).replace(",", ""))

        # 3. Desktop Bing search
        if any(k in line_lower for k in ["desktop bing search", "pc bing search", "tìm kiếm trên pc", "tìm kiếm desktop"]):
            if i + 1 < len(lines) and "/" in lines[i+1]:
                result["desktop_points"] = lines[i+1].strip()
            else:
                m = re.search(r"(\d+\s*/\s*\d+)", line)
                if m:
                    result["desktop_points"] = m.group(1).replace(" ", "")
        elif line_lower in ["bing search", "tìm kiếm bing"]:
            if i + 1 < len(lines) and "/" in lines[i+1]:
                result["desktop_points"] = lines[i+1].strip()
            else:
                m = re.search(r"(\d+\s*/\s*\d+)", line)
                if m:
                    result["desktop_points"] = m.group(1).replace(" ", "")

        # 4. Mobile Bing search
        if any(k in line_lower for k in ["mobile bing search", "tìm kiếm trên di động", "tìm kiếm mobile"]):
            if i + 1 < len(lines) and "/" in lines[i+1]:
                result["mobile_points"] = lines[i+1].strip()
            else:
                m = re.search(r"(\d+\s*/\s*\d+)", line)
                if m:
                    result["mobile_points"] = m.group(1).replace(" ", "")

        # 5. Offers
        if line_lower in ["offers", "ưu đãi", "nhiệm vụ khác"]:
            if i + 1 < len(lines) and re.match(r"^\d+$", lines[i+1]):
                result["offers_points"] = int(lines[i+1])
            else:
                m = re.search(r"(\d+)", line)
                if m:
                    result["offers_points"] = int(m.group(1))

    return result


def check_profile_points(profile_dict: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kiem tra diem thuong thuc te cho 1 tai khoan o che do Headless an toan."""
    if not profile_dict:
        return {"success": False, "message": "Không tìm thấy thông tin profile"}

    init_db()
    p_id = profile_dict.get("id")
    p_name = profile_dict.get("name", f"Profile {p_id}")
    profile_dir = get_profile_abs_path(profile_dict)

    kill_zombie_edge_processes(profile_dir)

    if config is None and CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = config or {}

    cfg_copy = json.loads(json.dumps(cfg))
    cfg_copy.setdefault("browser_settings", {})["headless"] = True

    driver = None
    try:
        driver = create_edge_driver(is_mobile=False, config=cfg_copy, profile_target=profile_dict)
        driver.set_page_load_timeout(25)
        driver.get("https://rewards.bing.com/earn")
        time.sleep(3.5)

        cur_url = driver.current_url.lower()
        if "login.live.com" in cur_url or "signup" in cur_url:
            update_profile_db(p_id, status="unlogged")
            return {
                "success": False,
                "status": "unlogged",
                "message": f"Tài khoản {p_name} chưa đăng nhập hoặc phiên đã hết hạn."
            }

        available_points = 0
        try:
            header_elems = driver.find_elements(
                By.CSS_SELECTOR,
                "header p, nav p, [role='navigation'] p, div[class*='gap-2'] p, header [class*='text-']"
            )
            for el in header_elems:
                t = el.text.strip().replace(",", "")
                if t.isdigit() and int(t) > 0:
                    available_points = int(t)
                    break
        except Exception:
            pass

        dialog_text = ""
        try:
            breakdown_btns = driver.find_elements(
                By.XPATH,
                '//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "breakdown") or contains(text(), "Chi tiết điểm") or contains(@aria-label, "breakdown")]'
            )
            if breakdown_btns:
                driver.execute_script("arguments[0].click();", breakdown_btns[0])
                time.sleep(1.8)
                dialogs = driver.find_elements(By.CSS_SELECTOR, '[role="dialog"], [class*="modal"]')
                if dialogs:
                    dialog_text = dialogs[0].text
        except Exception:
            pass

        if not dialog_text:
            try:
                dialog_text = driver.find_element(By.TAG_NAME, "body").text
            except Exception:
                pass

        parsed = parse_rewards_breakdown_text(dialog_text)

        if available_points == 0:
            try:
                driver.get("https://rewards.bing.com/dashboard")
                time.sleep(2.5)
                body_text = driver.find_element(By.TAG_NAME, "body").text
                lines = [l.strip() for l in body_text.splitlines() if l.strip()]
                for idx, line in enumerate(lines):
                    if any(k in line.lower() for k in ["available points", "điểm khả dụng", "điểm hiện có"]):
                        if idx + 1 < len(lines):
                            m = re.search(r"(\d[\d,]*)", lines[idx+1])
                            if m:
                                available_points = int(m.group(1).replace(",", ""))
                                break
            except Exception:
                pass

        if available_points > 0:
            parsed["total_points"] = available_points
            parsed["available_points"] = available_points
        elif parsed.get("lifetime_points", 0) > 0 and parsed["total_points"] == 0:
            parsed["total_points"] = parsed["lifetime_points"]

        updated = update_profile_db(
            p_id,
            total_points=parsed["total_points"],
            today_points=parsed["today_points"],
            desktop_points=parsed["desktop_points"],
            mobile_points=parsed["mobile_points"],
            offers_points=parsed["offers_points"],
            status="ready"
        )

        return {
            "success": True,
            "message": "Kiểm tra điểm thành công",
            "data": parsed,
            "profile": updated
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi kiểm tra điểm: {str(e)}"
        }
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        time.sleep(1)
        kill_zombie_edge_processes(profile_dir)
