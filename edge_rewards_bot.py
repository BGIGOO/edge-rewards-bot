# -*- coding: utf-8 -*-
"""
====================================================================
           MICROSOFT REWARDS AUTO SEARCH BOT (EDGE)
        Mô phỏng thao tác tìm kiếm người thật - Anti-Ban
====================================================================
Hỗ trợ:
- Tự động hóa tìm kiếm Desktop (PC) & Mobile (Điện thoại)
- Profile riêng biệt (edge_profile): KHÔNG BAO GIỜ bị lỗi xung đột,
  không cần đóng Edge đang làm việc, chỉ cần đăng nhập tài khoản 1 lần!
- Gõ phím từng ký tự ngẫu nhiên (Human Typing)
- Cuộn trang, đọc kết quả, dừng nghỉ ngẫu nhiên (Human Browsing)
- Chống chặn overlay, tự động đóng pop-up thông báo của Bing
====================================================================
"""

import os
import sys
import time
import json
import random
import subprocess
import argparse
from datetime import datetime

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi UnicodeEncodeError
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("[!] Selenium chưa được cài đặt. Đang tự động cài đặt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "webdriver-manager"])
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

# Đường dẫn thư mục script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
KEYWORDS_PATH = os.path.join(SCRIPT_DIR, "keywords.txt")


def load_config():
    """Tải cấu hình từ config.json"""
    default_config = {
        "search_settings": {
            "pc_searches": 31,
            "mobile_searches": 21,
            "min_delay_seconds": 12,
            "max_delay_seconds": 22,
            "enable_cooldown_batches": True,
            "batch_size": 4,
            "batch_cooldown_minutes": 15,
            "enable_smooth_scrolling": True,
            "enable_mouse_movement": True,
            "random_click_chance": 0.35,
            "human_typing_speed_min": 0.05,
            "human_typing_speed_max": 0.15
        },
        "browser_settings": {
            "profile_directory_path": "./edge_profile",
            "headless": False,
            "mobile_device_name": "Pixel 7"
        }
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_config["search_settings"].update(loaded.get("search_settings", {}))
                default_config["browser_settings"].update(loaded.get("browser_settings", {}))
        except Exception as e:
            print(f"[!] Không đọc được config.json ({e}), dùng cấu hình mặc định.")
    return default_config


def load_keywords():
    """Tải danh sách từ khóa tìm kiếm tự nhiên"""
    keywords = []
    if os.path.exists(KEYWORDS_PATH):
        with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                kw = line.strip()
                if kw and not kw.startswith("#"):
                    keywords.append(kw)
    
    if len(keywords) < 50:
        fallback_keywords = [
            "thời tiết hôm nay tại hà nội", "tin tức công nghệ mới nhất hôm nay",
            "cách làm món sườn xào chua ngọt", "địa điểm du lịch đà lạt đẹp nhất",
            "kết quả bóng đá ngoại hạng anh", "top 10 phim chiếu rạp đáng xem",
            "hướng dẫn tự học lập trình python", "cách tối ưu hóa windows 11",
            "mẹo tiết kiệm pin laptop hiệu quả", "công thức nấu phở bò truyền thống",
            "những cuốn sách hay nên đọc một lần", "cách pha cà phê cold brew",
            "kinh nghiệm du lịch phú quốc tự túc", "tác dụng của trà xanh đối với sức khỏe",
            "bài tập yoga buổi sáng tăng năng lượng", "cách cải thiện trí nhớ và tập trung",
            "top công nghệ trí tuệ nhân tạo", "thói quen tốt trước khi đi ngủ",
            "how to learn coding fast", "best healthy breakfast recipes",
            "benefits of drinking water daily", "how do airplanes stay in the air",
            "tips for better sleep quality at night", "difference between ai and machine learning"
        ]
        keywords.extend(fallback_keywords)

    random.shuffle(keywords)
    return keywords


def get_profile_abs_path(config):
    """Lấy đường dẫn thư mục profile Edge an toàn"""
    p_path = config.get("browser_settings", {}).get("profile_directory_path", "./edge_profile")
    if not os.path.isabs(p_path):
        p_path = os.path.abspath(os.path.join(SCRIPT_DIR, p_path))
    os.makedirs(p_path, exist_ok=True)
    return p_path


def create_edge_driver(is_mobile=False, config=None):
    """Khởi tạo trình duyệt Edge với profile riêng biệt chống xung đột và chống phát hiện bot"""
    options = EdgeOptions()
    browser_cfg = config.get("browser_settings", {})
    profile_dir = get_profile_abs_path(config)

    # 1. Đường dẫn Profile riêng biệt
    options.add_argument(f"--user-data-dir={profile_dir}")

    # 2. Cờ tắt chế độ Automation & Chống Bot Detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--lang=vi-VN,vi,en-US,en")
    
    if browser_cfg.get("headless", False):
        options.add_argument("--headless=new")

    # 3. Chế độ Mobile Emulation (Chuẩn hóa thiết bị Android)
    if is_mobile:
        device_name = browser_cfg.get("mobile_device_name", "Pixel 7")
        options.add_experimental_option("mobileEmulation", {"deviceName": device_name})
        print(f"[*] Kích hoạt giả lập Android Mobile: {device_name}")
    else:
        options.add_argument("--start-maximized")

    # Khởi tạo Driver
    driver = webdriver.Edge(options=options)

    # 4. Tiêm script xóa cờ navigator.webdriver và giả lập runtime (Stealth Mode)
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                if (!window.chrome) {
                    window.chrome = {};
                }
                window.chrome.runtime = {};
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['vi-VN', 'vi', 'en-US', 'en']
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                """
            }
        )
    except Exception:
        pass

    if is_mobile:
        driver.set_window_size(412, 915)

    return driver


def dismiss_popups(driver):
    """Đóng các pop-up, banner cookie hoặc overlay của Bing che mất ô tìm kiếm"""
    try:
        # Bấm phím ESC trên trang
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass

    # Tìm và bấm nút đồng ý/đóng nếu có
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


def human_type(element, text, speed_min=0.08, speed_max=0.20):
    """Mô phỏng tốc độ gõ phím của người thật từng ký tự một"""
    for char in text:
        element.send_keys(char)
        if char == " " and random.random() < 0.25:
            time.sleep(random.uniform(0.2, 0.45))
        else:
            time.sleep(random.uniform(speed_min, speed_max))


def simulate_natural_mouse_movement(driver):
    """Mô phỏng chuyển động chuột ngẫu nhiên của người thật trên trang (Mouse Dynamics)"""
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


def simulate_human_browsing(driver, enable_scrolling=True, enable_mouse=True):
    """Mô phỏng hành vi xem trang kết quả tìm kiếm (cuộn lên cuộn xuống và di chuột tự nhiên)"""
    if not enable_scrolling:
        return
    try:
        time.sleep(random.uniform(1.0, 2.0))
        
        # Di chuyển chuột tự nhiên nếu có hỗ trợ
        if enable_mouse:
            simulate_natural_mouse_movement(driver)
            time.sleep(random.uniform(0.4, 0.9))

        # Cuộn xuống lần 1
        scroll_distance_1 = random.randint(300, 600)
        driver.execute_script(f"window.scrollBy({{ top: {scroll_distance_1}, behavior: 'smooth' }});")
        time.sleep(random.uniform(1.2, 2.5))

        # Di chuyển chuột nhẹ lần 2
        if enable_mouse and random.random() < 0.5:
            simulate_natural_mouse_movement(driver)

        # 60% tỉ lệ cuộn tiếp xuống lần 2
        if random.random() < 0.6:
            scroll_distance_2 = random.randint(200, 450)
            driver.execute_script(f"window.scrollBy({{ top: {scroll_distance_2}, behavior: 'smooth' }});")
            time.sleep(random.uniform(1.0, 2.2))

        # 40% tỉ lệ cuộn ngược lên một chút
        if random.random() < 0.4:
            driver.execute_script("window.scrollBy({ top: -200, behavior: 'smooth' });")
            time.sleep(random.uniform(0.8, 1.6))
    except Exception:
        pass


def simulate_random_result_click(driver, click_chance=0.35):
    """Mô phỏng hành vi người thật: ngẫu nhiên bấm vào bài viết kết quả tìm kiếm (CTR Engagement)"""
    if random.random() > click_chance:
        return False

    original_window = driver.current_window_handle
    try:
        # Tìm các link bài viết tự nhiên của Bing (loại trừ quảng cáo b_ad)
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

        # Chọn 1 kết quả trong top bài viết
        target_link = random.choice(valid_links[:min(len(valid_links), 4)])
        link_title = (target_link.text or "Bài viết").strip().replace("\n", " ")[:45]
        print(f"   👆 [CTR Human Action] Bấm đọc bài viết: \"{link_title}...\"")

        windows_before = set(driver.window_handles)

        # Rê chuột tới link và bấm
        try:
            ActionChains(driver).move_to_element(target_link).pause(random.uniform(0.2, 0.5)).perform()
        except Exception:
            pass

        driver.execute_script("arguments[0].click();", target_link)

        # Dừng đọc bài từ 4 đến 8 giây
        dwell_time = random.uniform(4.0, 8.0)
        time.sleep(dwell_time / 2)

        windows_after = set(driver.window_handles)
        new_windows = list(windows_after - windows_before)

        if new_windows:
            # Bài viết mở ở tab mới
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
            # Bài viết mở cùng tab
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


def check_and_prompt_first_time_login(driver):
    """Kiểm tra nếu người dùng chưa đăng nhập tài khoản Microsoft trên profile này"""
    try:
        driver.get("https://www.bing.com")
        time.sleep(2)
        dismiss_popups(driver)

        # Kiểm tra sự hiện diện của nút Sign In / Đăng nhập
        sign_in_elements = driver.find_elements(By.ID, "id_s") + driver.find_elements(By.CSS_SELECTOR, "a[id*='signin']")
        needs_login = False
        for el in sign_in_elements:
            if el.is_displayed() and ("sign in" in el.text.lower() or "đăng nhập" in el.text.lower()):
                needs_login = True
                break

        if needs_login:
            print("\n" + "=" * 65)
            print("🔔 THÔNG BÁO ĐĂNG NHẬP (Chỉ thực hiện LẦN ĐẦU TIÊN duy nhất):")
            print("   Trình duyệt Edge vừa mở lên. Bạn hãy bấm 'Sign In' (Đăng nhập)")
            print("   bằng tài khoản Microsoft Rewards của bạn trên cửa sổ Edge này.")
            print("   (Từ những lần chạy sau, tài khoản sẽ tự động lưu vĩnh viễn!)")
            print("=" * 65)
            input("👉 Sau khi bạn đã đăng nhập xong trên Edge, hãy nhấn ENTER tại đây để bắt đầu cày điểm...")
            time.sleep(2)
            dismiss_popups(driver)
    except Exception as e:
        pass


def execute_search_session(driver, keywords, num_searches, mode_name="PC", config=None):
    """Thực hiện một phiên tìm kiếm (PC hoặc Mobile)"""
    search_cfg = config.get("search_settings", {})
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
        print(f"[!] Không thể mở bing.com: {e}")

    completed = 0
    while completed < num_searches and keywords:
        kw = keywords.pop(0)
        search_idx = completed + 1
        print(f"\n[{mode_name} #{search_idx}/{num_searches}] 🔍 Đang tìm: \"{kw}\"")

        try:
            dismiss_popups(driver)

            # Tìm ô search box của Bing (hỗ trợ cả textarea và input mới của Bing)
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

            # Dùng JavaScript Focus & Click để tránh tuyệt đối lỗi ElementClickIntercepted
            driver.execute_script("arguments[0].focus(); arguments[0].click();", search_box)
            time.sleep(random.uniform(0.3, 0.6))

            # Xóa sạch nội dung cũ
            search_box.send_keys(Keys.CONTROL + "a")
            time.sleep(0.1)
            search_box.send_keys(Keys.BACKSPACE)
            time.sleep(random.uniform(0.2, 0.4))

            # Gõ phím từng ký tự tự nhiên
            human_type(search_box, kw, speed_min, speed_max)
            time.sleep(random.uniform(0.4, 0.8))

            # Nhấn Enter để bắt đầu tìm kiếm
            search_box.send_keys(Keys.ENTER)

            # 1. Mô phỏng hành vi cuộn trang và rê chuột
            simulate_human_browsing(driver, enable_scrolling=enable_scroll, enable_mouse=enable_mouse)

            # 2. Mô phỏng ngẫu nhiên click đọc bài viết kết quả (CTR Engagement)
            simulate_random_result_click(driver, click_chance=click_chance)

            completed += 1

            # Thời gian nghỉ ngẫu nhiên giữa các lượt search
            wait_time = random.uniform(min_delay, max_delay)
            print(f"   ✓ Hoàn thành #{search_idx}. Nghỉ an toàn {wait_time:.1f}s trước lượt tiếp theo...")

            # Cơ chế ngắt quãng Cooldown 15 phút chống thuật toán phạt của Microsoft
            if enable_cooldown and (completed % batch_size == 0) and completed < num_searches:
                cooldown_sec = batch_cooldown_min * 60
                print(f"\n⏳ [Cooldown Safe] Đã hoàn thành đợt {completed} lượt. Tạm dừng an toàn {batch_cooldown_min} phút chống hạn chế Bing...")
                for remaining in range(cooldown_sec, 0, -10):
                    mins, secs = divmod(remaining, 60)
                    print(f"\r   Nghỉ giải lao: {mins:02d}:{secs:02d} còn lại...", end="", flush=True)
                    time.sleep(10)
                print("\n   [✓] Hết thời gian nghỉ Cooldown! Tiếp tục đợt tìm kiếm tiếp theo...")
            else:
                time.sleep(wait_time)

        except Exception as e:
            print(f"   [!] Gặp vấn đề ở lượt này ({e}). Đang thử tải lại...")
            time.sleep(3)
            try:
                driver.get("https://www.bing.com")
                time.sleep(3)
                dismiss_popups(driver)
            except Exception:
                pass

    print(f"\n[✓] ĐÃ HOÀN TẤT {completed}/{num_searches} LƯỢT TÌM KIẾM {mode_name}!")
    return completed


def main():
    parser = argparse.ArgumentParser(description="Microsoft Rewards Auto Search Bot")
    parser.add_argument("--mode", choices=["all", "desktop", "pc", "mobile"], default=None,
                        help="Chọn chế độ chạy: desktop (pc), mobile hoặc all (cả hai)")
    parser.add_argument("--pc", "--desktop", dest="pc_flag", action="store_true",
                        help="Chỉ chạy tìm kiếm Desktop (PC)")
    parser.add_argument("--mobile", dest="mobile_flag", action="store_true",
                        help="Chỉ chạy tìm kiếm Mobile")
    args, _ = parser.parse_known_args()

    # Xác định chế độ chạy
    if args.pc_flag or (args.mode in ["desktop", "pc"]):
        selected_mode = "desktop"
    elif args.mobile_flag or (args.mode == "mobile"):
        selected_mode = "mobile"
    elif args.mode == "all":
        selected_mode = "all"
    else:
        # Nếu chạy trực tiếp không truyền tham số -> Hiển thị menu lựa chọn
        print("""
====================================================================
          MICROSOFT REWARDS AUTO SEARCH BOT (EDGE)
             Phiên bản Anti-Ban & Human Mimicking
====================================================================
👉 CHỌN CHẾ ĐỘ TÌM KIẾM BẠN MUỐN:
   [1] Chỉ tìm kiếm Desktop / PC (Khuyên dùng chạy buổi sáng/trưa)
   [2] Chỉ tìm kiếm Mobile        (Khuyên dùng chạy buổi chiều/tối)
   [3] Chạy cả hai (Desktop rồi Mobile)
====================================================================
""")
        user_choice = input("Nhập lựa chọn của bạn (1/2/3) [Mặc định: 1 - Desktop]: ").strip()
        if user_choice == "2":
            selected_mode = "mobile"
        elif user_choice == "3":
            selected_mode = "all"
        else:
            selected_mode = "desktop"

    run_pc = selected_mode in ["all", "desktop"]
    run_mobile = selected_mode in ["all", "mobile"]

    config = load_config()
    search_cfg = config.get("search_settings", {})
    pc_count = search_cfg.get("pc_searches", 31) if run_pc else 0
    mobile_count = search_cfg.get("mobile_searches", 21) if run_mobile else 0
    device_name = config.get("browser_settings", {}).get("mobile_device_name", "Pixel 7")
    profile_dir = get_profile_abs_path(config)

    print("\n" + "=" * 66)
    print("🚀 BẮT ĐẦU PHIÊN CHẠY BOT MICROSOFT REWARDS")
    print(f"[*] Chế độ đang chạy: {selected_mode.upper()}")
    print(f"[*] Thư mục Profile : {profile_dir}")
    print(f"[*] Kế hoạch chạy chi tiết:")
    if run_pc:
        print(f"   - Desktop (PC)        : {pc_count} lượt tìm kiếm")
    if run_mobile:
        print(f"   - Mobile (Android)    : {mobile_count} lượt (Thiết bị: {device_name})")
    print(f"   - Giãn cách an toàn   : {search_cfg.get('min_delay_seconds')}s - {search_cfg.get('max_delay_seconds')}s / lượt")
    print(f"   - Chế độ Cooldown     : {'BẬT (Mỗi ' + str(search_cfg.get('batch_size', 4)) + ' lượt nghỉ ' + str(search_cfg.get('batch_cooldown_minutes', 5)) + ' phút)' if search_cfg.get('enable_cooldown_batches') else 'TẮT'}")
    print(f"   - Click đọc bài (CTR) : {int(search_cfg.get('random_click_chance', 0.25) * 100)}% ngẫu nhiên")
    print(f"   - Rê chuột tự nhiên   : {'BẬT' if search_cfg.get('enable_mouse_movement', True) else 'TẮT'}")
    print("=" * 66)

    # Nạp từ khóa
    keywords = load_keywords()
    print(f"[✓] Đã nạp thành công {len(keywords)} từ khóa tìm kiếm tự nhiên.")

    total_searches_done = 0
    start_time = datetime.now()

    # ==========================
    # PHẦN 1: TÌM KIẾM DESKTOP (PC)
    # ==========================
    if run_pc and pc_count > 0:
        print("\n🖥️  [1] Đang khởi động Microsoft Edge ở chế độ Desktop (PC)...")
        pc_driver = None
        try:
            pc_driver = create_edge_driver(is_mobile=False, config=config)
            check_and_prompt_first_time_login(pc_driver)
            searches_pc = execute_search_session(pc_driver, keywords, pc_count, mode_name="PC", config=config)
            total_searches_done += searches_pc
        except Exception as e:
            print(f"[!] Lỗi trong phiên tìm kiếm PC: {e}")
        finally:
            if pc_driver:
                print("[*] Đang đóng phiên duyệt Desktop...")
                try:
                    pc_driver.quit()
                except Exception:
                    pass

        # Nếu chạy cả hai chế độ thì tạm nghỉ giữa 2 phiên
        if run_mobile and mobile_count > 0:
            transition_pause = random.uniform(8, 15)
            print(f"\n[⏳] Tạm nghỉ {transition_pause:.1f}s trước khi chuyển sang chế độ Mobile...")
            time.sleep(transition_pause)

    # ==========================
    # PHẦN 2: TÌM KIẾM MOBILE
    # ==========================
    if run_mobile and mobile_count > 0:
        step_label = "[2]" if run_pc else "[1]"
        print(f"\n📱 {step_label} Đang khởi động Microsoft Edge ở chế độ Mobile (Giả lập {device_name})...")
        mobile_driver = None
        try:
            mobile_driver = create_edge_driver(is_mobile=True, config=config)
            searches_mob = execute_search_session(mobile_driver, keywords, mobile_count, mode_name="MOBILE", config=config)
            total_searches_done += searches_mob
        except Exception as e:
            print(f"[!] Lỗi trong phiên tìm kiếm Mobile: {e}")
        finally:
            if mobile_driver:
                print("[*] Đang đóng phiên duyệt Mobile...")
                try:
                    mobile_driver.quit()
                except Exception:
                    pass

    # ==========================
    # TỔNG KẾT
    # ==========================
    duration = datetime.now() - start_time
    minutes, seconds = divmod(int(duration.total_seconds()), 60)

    print("\n" + "=" * 66)
    print("🎉 PHIÊN TÌM KIẾM ĐÃ HOÀN TẤT!")
    print(f"   - Chế độ đã chạy                  : {selected_mode.upper()}")
    print(f"   - Tổng số lượt tìm kiếm hoàn thành: {total_searches_done}")
    print(f"   - Tổng thời gian chạy             : {minutes} phút {seconds} giây")
    print(f"   - Điểm Rewards ước tính kiếm được : ~{total_searches_done * 3} điểm")
    print("=" * 66)
    print("Bạn có thể mở Microsoft Edge để kiểm tra số điểm Rewards được cộng!")
    input("\nNhấn phím ENTER để kết thúc chương trình...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Người dùng đã dừng chương trình bằng Ctrl+C.")
        sys.exit(0)
