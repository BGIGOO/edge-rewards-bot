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
            "pc_searches": 32,
            "mobile_searches": 22,
            "min_delay_seconds": 10,
            "max_delay_seconds": 18,
            "enable_cooldown_batches": False,
            "batch_size": 4,
            "batch_cooldown_minutes": 15,
            "enable_smooth_scrolling": True,
            "human_typing_speed_min": 0.08,
            "human_typing_speed_max": 0.20
        },
        "browser_settings": {
            "profile_directory_path": "./edge_profile",
            "headless": False,
            "mobile_device_name": "iPhone 12 Pro"
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

    # 3. Chế độ Mobile Emulation
    if is_mobile:
        device_name = browser_cfg.get("mobile_device_name", "iPhone 12 Pro")
        options.add_experimental_option("mobileEmulation", {"deviceName": device_name})
        print(f"[*] Kích hoạt giả lập Mobile: {device_name}")
    else:
        options.add_argument("--start-maximized")

    # Khởi tạo Driver
    driver = webdriver.Edge(options=options)

    # 4. Tiêm script xóa cờ navigator.webdriver (Stealth Mode)
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.navigator.chrome = {
                    runtime: {},
                };
                """
            }
        )
    except Exception:
        pass

    if is_mobile:
        driver.set_window_size(430, 932)

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


def simulate_human_browsing(driver, enable_scrolling=True):
    """Mô phỏng hành vi xem trang kết quả tìm kiếm (cuộn lên cuộn xuống tự nhiên)"""
    if not enable_scrolling:
        return
    try:
        time.sleep(random.uniform(1.2, 2.5))
        
        # Cuộn xuống lần 1
        scroll_distance_1 = random.randint(300, 600)
        driver.execute_script(f"window.scrollBy({{ top: {scroll_distance_1}, behavior: 'smooth' }});")
        time.sleep(random.uniform(1.5, 3.0))

        # 60% tỉ lệ cuộn tiếp xuống lần 2
        if random.random() < 0.6:
            scroll_distance_2 = random.randint(200, 450)
            driver.execute_script(f"window.scrollBy({{ top: {scroll_distance_2}, behavior: 'smooth' }});")
            time.sleep(random.uniform(1.0, 2.5))

        # 40% tỉ lệ cuộn ngược lên một chút
        if random.random() < 0.4:
            driver.execute_script("window.scrollBy({ top: -200, behavior: 'smooth' });")
            time.sleep(random.uniform(0.8, 1.8))
    except Exception:
        pass


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
    min_delay = search_cfg.get("min_delay_seconds", 10)
    max_delay = search_cfg.get("max_delay_seconds", 18)
    speed_min = search_cfg.get("human_typing_speed_min", 0.08)
    speed_max = search_cfg.get("human_typing_speed_max", 0.20)
    enable_cooldown = search_cfg.get("enable_cooldown_batches", False)
    batch_size = search_cfg.get("batch_size", 4)
    batch_cooldown_min = search_cfg.get("batch_cooldown_minutes", 15)

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

            # Mô phỏng hành vi cuộn trang đọc kết quả
            simulate_human_browsing(driver, search_cfg.get("enable_smooth_scrolling", True))

            completed += 1

            # Thời gian nghỉ ngẫu nhiên giữa các lượt search
            wait_time = random.uniform(min_delay, max_delay)
            print(f"   ✓ Hoàn thành #{search_idx}. Nghỉ {wait_time:.1f}s trước lượt tiếp theo...")

            # Cơ chế ngắt quãng Cooldown nếu tài khoản bị Microsoft giới hạn
            if enable_cooldown and (completed % batch_size == 0) and completed < num_searches:
                cooldown_sec = batch_cooldown_min * 60
                print(f"\n⏳ [Cooldown Safe] Đã hoàn thành {completed} lượt. Tạm dừng an toàn {batch_cooldown_min} phút chống hạn chế...")
                for remaining in range(cooldown_sec, 0, -10):
                    mins, secs = divmod(remaining, 60)
                    print(f"\r   Nghỉ giải lao: {mins:02d}:{secs:02d} còn lại...", end="", flush=True)
                    time.sleep(10)
                print("\n   [✓] Tiếp tục đợt tìm kiếm tiếp theo!")
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
    print("""
====================================================================
          MICROSOFT REWARDS AUTO SEARCH BOT (EDGE)
             Phiên bản Anti-Ban & Human Mimicking
====================================================================
    """)
    config = load_config()
    search_cfg = config.get("search_settings", {})
    pc_count = search_cfg.get("pc_searches", 32)
    mobile_count = search_cfg.get("mobile_searches", 22)

    profile_dir = get_profile_abs_path(config)
    print(f"[*] Thư mục Profile lưu trữ: {profile_dir}")
    print(f"[*] Kế hoạch chạy:")
    print(f"   - Tìm kiếm PC (Desktop) : {pc_count} lượt")
    print(f"   - Tìm kiếm Mobile        : {mobile_count} lượt")
    print(f"   - Giãn cách an toàn      : {search_cfg.get('min_delay_seconds')}s - {search_cfg.get('max_delay_seconds')}s / lượt")
    print(f"   - Chế độ Cooldown 15p    : {'BẬT' if search_cfg.get('enable_cooldown_batches') else 'TẮT (Chạy liên tục có giãn cách tự nhiên)'}")
    print("=" * 66)

    # Nạp từ khóa
    keywords = load_keywords()
    print(f"[✓] Đã nạp thành công {len(keywords)} từ khóa tìm kiếm tự nhiên.")

    total_searches_done = 0
    start_time = datetime.now()

    # ==========================
    # PHẦN 1: TÌM KIẾM DESKTOP (PC)
    # ==========================
    if pc_count > 0:
        print("\n🚀 [1/2] Đang khởi động Microsoft Edge ở chế độ Desktop...")
        pc_driver = None
        try:
            pc_driver = create_edge_driver(is_mobile=False, config=config)
            
            # Kiểm tra đăng nhập nếu là lần đầu tiên
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

        # Nghỉ giữa phiên Desktop và Mobile
        transition_pause = random.uniform(6, 12)
        print(f"\n[⏳] Tạm nghỉ {transition_pause:.1f}s trước khi chuyển sang chế độ Mobile...")
        time.sleep(transition_pause)

    # ==========================
    # PHẦN 2: TÌM KIẾM MOBILE
    # ==========================
    if mobile_count > 0:
        print("\n📱 [2/2] Đang khởi động Microsoft Edge ở chế độ Mobile (Giả lập iPhone)...")
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
    print("🎉 TẤT CẢ CÁC NHIỆM VỤ ĐÃ HOÀN TẤT!")
    print(f"   - Tổng số lượt tìm kiếm thực hiện: {total_searches_done}")
    print(f"   - Thời gian chạy                  : {minutes} phút {seconds} giây")
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
