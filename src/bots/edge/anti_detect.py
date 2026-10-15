# -*- coding: utf-8 -*-
"""
src/bots/edge/anti_detect.py
============================
Mo phong hanh vi nguoi dung tu nhien: go phim, cuon trang, di chuot, click doc bai.
Tuan thu rule 01_architecture (< 250 dong) va rule 02_automation_bots.
"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def dismiss_popups(driver) -> None:
    """Dong cac pop-up, banner cookie hoac overlay cua Bing che mat o tim kiem."""
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass

    dismiss_selectors = [
        "#bnp_btn_accept",
        "#bnp_close_link",
        "button[id*='bnp']",
        ".bnp_btn_accept"
    ]
    for sel in dismiss_selectors:
        try:
            btn = driver.find_elements(By.CSS_SELECTOR, sel)
            if btn and btn[0].is_displayed():
                driver.execute_script("arguments[0].click();", btn[0])
                time.sleep(0.5)
                break
        except Exception:
            pass


def human_type(element, text: str, speed_min: float = 0.08, speed_max: float = 0.20) -> None:
    """Mo phong toc do go phim cua nguoi that tung ky tu mot."""
    for char in text:
        element.send_keys(char)
        if char == " " and random.random() < 0.25:
            time.sleep(random.uniform(0.2, 0.45))
        else:
            time.sleep(random.uniform(speed_min, speed_max))


def simulate_natural_mouse_movement(driver) -> None:
    """Mo phong chuyen dong chuot ngau nhien tren trang (Mouse Dynamics)."""
    try:
        action = ActionChains(driver)
        candidates = driver.find_elements(By.CSS_SELECTOR, "h2, p, a, div.b_title, span")
        visible_elements = [el for el in candidates[:15] if el.is_displayed()]

        if visible_elements:
            chosen = random.sample(visible_elements, min(len(visible_elements), random.randint(2, 3)))
            for target in chosen:
                action.move_to_element_with_offset(target, random.randint(-10, 10), random.randint(-5, 5))
                action.pause(random.uniform(0.15, 0.40))
            action.perform()
    except Exception:
        pass


def simulate_human_browsing(driver, enable_scrolling: bool = True, enable_mouse: bool = True) -> None:
    """Mo phong hanh vi cuon trang va di chuot tu nhien."""
    if not enable_scrolling:
        return
    try:
        time.sleep(random.uniform(1.0, 2.0))

        if enable_mouse:
            simulate_natural_mouse_movement(driver)
            time.sleep(random.uniform(0.4, 0.9))

        scroll_distance_1 = random.randint(300, 600)
        driver.execute_script(f"window.scrollBy({{ top: {scroll_distance_1}, behavior: 'smooth' }});")
        time.sleep(random.uniform(1.2, 2.5))

        if enable_mouse and random.random() < 0.5:
            simulate_natural_mouse_movement(driver)

        if random.random() < 0.6:
            scroll_distance_2 = random.randint(200, 450)
            driver.execute_script(f"window.scrollBy({{ top: {scroll_distance_2}, behavior: 'smooth' }});")
            time.sleep(random.uniform(1.0, 2.2))

        if random.random() < 0.4:
            driver.execute_script("window.scrollBy({ top: -200, behavior: 'smooth' });")
            time.sleep(random.uniform(0.8, 1.6))
    except Exception:
        pass


def simulate_random_result_click(driver, click_chance: float = 0.35) -> bool:
    """Mo phong hanh vi ngau nhien bam vao bai viet ket qua tim kiem (CTR Engagement)."""
    if random.random() > click_chance:
        return False

    original_window = driver.current_window_handle
    try:
        result_links = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a, .b_algo .b_title a, #b_results .b_algo a")
        valid_links = []
        for link in result_links[:8]:
            try:
                href = link.get_attribute("href")
                if href and link.is_displayed() and not href.startswith("javascript:") and "microsoft.com/rewards" not in href:
                    valid_links.append(link)
            except Exception:
                continue

        if not valid_links:
            return False

        target_link = random.choice(valid_links[:min(len(valid_links), 4)])
        link_title = (target_link.text or "Bài viết").strip().replace("\n", " ")[:45]
        print(f"   👆 [CTR Human Action] Bấm đọc bài viết: \"{link_title}...\"")

        windows_before = set(driver.window_handles)

        try:
            ActionChains(driver).move_to_element(target_link).pause(random.uniform(0.2, 0.5)).perform()
        except Exception:
            pass

        driver.execute_script("arguments[0].click();", target_link)

        dwell_time = random.uniform(4.0, 8.0)
        time.sleep(dwell_time / 2)

        windows_after = set(driver.window_handles)
        new_windows = list(windows_after - windows_before)

        if new_windows:
            new_tab = new_windows[0]
            driver.switch_to.window(new_tab)
            try:
                driver.execute_script(f"window.scrollBy({{ top: {random.randint(250, 600)}, behavior: 'smooth' }});")
            except Exception:
                pass
            time.sleep(dwell_time / 2)
            try:
                driver.close()
            except Exception:
                pass
            driver.switch_to.window(original_window)
        else:
            try:
                driver.execute_script(f"window.scrollBy({{ top: {random.randint(250, 600)}, behavior: 'smooth' }});")
            except Exception:
                pass
            time.sleep(dwell_time / 2)
            driver.back()
            time.sleep(random.uniform(1.2, 2.0))

        print(f"      [✓] Đã đọc xong bài viết ({dwell_time:.1f}s), quay lại Bing tiếp tục.")
        return True
    except Exception:
        try:
            driver.switch_to.window(original_window)
        except Exception:
            pass
        return False
