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
import shutil
import subprocess
import argparse
from datetime import datetime

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi UnicodeEncodeError
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
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
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
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
    from webdriver_manager.microsoft import EdgeChromiumDriverManager

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
        },
        "profiles": [
            {
                "id": "1",
                "name": "Tài khoản 1 (Chính)",
                "path": "./edge_profile"
            },
            {
                "id": "2",
                "name": "Tài khoản 2 (Phụ)",
                "path": "./edge_profile_2"
            }
        ]
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_config["search_settings"].update(loaded.get("search_settings", {}))
                default_config["browser_settings"].update(loaded.get("browser_settings", {}))
                if "profiles" in loaded and isinstance(loaded["profiles"], list):
                    default_config["profiles"] = loaded["profiles"]
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


def get_profile_abs_path(target=None, base_dir=SCRIPT_DIR):
    """Lấy đường dẫn thư mục profile Edge an toàn (hỗ trợ config, profile dict hoặc đường dẫn chuỗi)"""
    p_path = "./edge_profile"
    if isinstance(target, str):
        p_path = target
    elif isinstance(target, dict):
        p_path = (target.get("path")
                  or target.get("profile_path")
                  or target.get("browser_settings", {}).get("profile_directory_path", "./edge_profile"))

    p_path = os.path.expandvars(p_path)
    if not os.path.isabs(p_path):
        p_path = os.path.abspath(os.path.join(base_dir, p_path))
    os.makedirs(p_path, exist_ok=True)
    return p_path


def sync_profile_from_system(profile):
    """Tự động đồng bộ cookie/session từ Edge gốc của máy vào thư mục profile bot nếu có"""
    if not isinstance(profile, dict):
        return
    profile_dir_name = profile.get("profile_directory")
    if not profile_dir_name:
        return

    user_data = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
    src_profile = os.path.join(user_data, profile_dir_name)
    if not os.path.exists(src_profile):
        return

    target_dir = get_profile_abs_path(profile)
    dst_profile = os.path.join(target_dir, profile_dir_name)
    os.makedirs(os.path.join(dst_profile, "Network"), exist_ok=True)

    # 1. Đồng bộ Local State (chỉ chép nếu chưa có)
    local_state_src = os.path.join(user_data, "Local State")
    local_state_dst = os.path.join(target_dir, "Local State")
    try:
        if os.path.exists(local_state_src) and not os.path.exists(local_state_dst):
            shutil.copy2(local_state_src, local_state_dst)
    except Exception:
        pass

    # 2. Đồng bộ các file session quan trọng nếu chưa có
    for fname in ["Preferences", "Secure Preferences", "Web Data", "Login Data"]:
        fsrc = os.path.join(src_profile, fname)
        fdst = os.path.join(dst_profile, fname)
        if os.path.exists(fsrc) and not os.path.exists(fdst):
            try:
                shutil.copy2(fsrc, fdst)
            except Exception:
                pass

    # 3. Đồng bộ Cookies nếu chưa có
    c_src = os.path.join(src_profile, "Network", "Cookies")
    c_dst = os.path.join(dst_profile, "Network", "Cookies")
    if os.path.exists(c_src) and not os.path.exists(c_dst):
        try:
            shutil.copy2(c_src, c_dst)
        except Exception:
            pass


def kill_zombie_edge_processes(profile_dir=None):
    """
    Tự động quét và đóng các tiến trình msedge.exe hoặc msedgedriver.exe chạy ngầm
    đang khóa thư mục profile_dir của bot (tránh lỗi xung đột lock file code 32).
    Tuyệt đối không ảnh hưởng đến trình duyệt Edge cá nhân của người dùng.
    """
    try:
        # 1. Đóng msedgedriver mồ côi (nếu có từ phiên trước)
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name = 'msedgedriver.exe'\" | Stop-Process -Force -ErrorAction SilentlyContinue"],
            capture_output=True,
            timeout=5
        )

        # 2. Đóng các tiến trình msedge đang chạy với profile_dir này
        if profile_dir:
            norm_dir_win = os.path.abspath(profile_dir).replace("/", "\\")
            norm_dir_fwd = os.path.abspath(profile_dir).replace("\\", "/")
            folder_name = os.path.basename(os.path.normpath(profile_dir))

            ps_script = (
                f"$procs = Get-CimInstance Win32_Process -Filter \"Name = 'msedge.exe'\" | "
                f"Where-Object {{ $_.CommandLine -like '*{folder_name}*' -or $_.CommandLine -like '*{norm_dir_win}*' -or $_.CommandLine -like '*{norm_dir_fwd}*' }}; "
                f"foreach ($p in $procs) {{ Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }}"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                timeout=8
            )

            # Xóa file cổng giao tiếp tạm nếu còn sót lại từ lần tắt đột ngột trước
            port_file = os.path.join(norm_dir_win, "DevToolsActivePort")
            if os.path.exists(port_file):
                try:
                    os.remove(port_file)
                except Exception:
                    pass
            time.sleep(1)
    except Exception:
        pass


def open_browser_for_login(target_profile, config=None):
    """Mở trình duyệt Edge gốc với profile chỉ định để người dùng đăng nhập tài khoản hoặc kiểm tra điểm Rewards"""
    p_name = target_profile.get("name", "Profile")
    p_dir = get_profile_abs_path(target_profile)
    kill_zombie_edge_processes(p_dir)
    print(f"\n{'='*65}")
    print(f"🔑 ĐANG MỞ MICROSOFT EDGE CHO [{p_name}]")
    print(f"   Thư mục Profile: {p_dir}")
    print(f"   Trang đích: https://rewards.bing.com")
    print("   👉 Hãy đăng nhập hoặc kiểm tra điểm. Đóng cửa sổ Edge khi hoàn tất.")
    print(f"{'='*65}\n")

    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ]
    msedge_exe = next((p for p in edge_paths if os.path.exists(p)), "msedge")
    cmd = [
        msedge_exe,
        f"--user-data-dir={p_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://rewards.bing.com"
    ]
    if isinstance(target_profile, dict) and target_profile.get("profile_directory"):
        cmd.append(f"--profile-directory={target_profile['profile_directory']}")

    try:
        proc = subprocess.Popen(cmd)
        return proc
    except Exception as e:
        print(f"[!] Không thể mở Microsoft Edge: {e}")
        return None


def create_edge_driver(is_mobile=False, config=None, profile_target=None):
    """Khởi tạo trình duyệt Edge với profile riêng biệt chống xung đột và chống phát hiện bot"""
    options = EdgeOptions()
    browser_cfg = config.get("browser_settings", {}) if config else {}
    target_prof = profile_target if profile_target is not None else config

    profile_dir = get_profile_abs_path(target_prof)

    # Đảm bảo giải phóng mọi tiến trình Edge treo cũ đang chiếm dụng profile này trước khi khởi động
    kill_zombie_edge_processes(profile_dir)

    # Tự động đồng bộ session từ Edge nếu cần
    sync_profile_from_system(target_prof)

    # 1. Đường dẫn Profile riêng biệt
    options.add_argument(f"--user-data-dir={profile_dir}")
    if isinstance(target_prof, dict) and target_prof.get("profile_directory"):
        options.add_argument(f"--profile-directory={target_prof['profile_directory']}")

    # 2. Cờ tắt chế độ Automation & Chống Bot Detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
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

    # Khởi tạo Driver với cơ chế tự phục hồi (Self-Healing Retry nếu gặp tiến trình treo)
    driver = None
    for attempt in range(2):
        try:
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            break
        except Exception as e_mgr:
            try:
                driver = webdriver.Edge(options=options)
                break
            except Exception as e_direct:
                if attempt == 0:
                    print(f"[!] Profile đang bị khóa bởi tiến trình trước, đang tự động giải phóng và thử lại...")
                    kill_zombie_edge_processes(profile_dir)
                    time.sleep(1.5)
                else:
                    raise e_direct

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


def check_and_prompt_first_time_login(driver, profile_name="Tài khoản này"):
    """Kiểm tra nếu người dùng chưa đăng nhập tài khoản Microsoft trên profile này"""
    try:
        driver.get("https://www.bing.com")
        time.sleep(2)
        dismiss_popups(driver)

        # Lấy thông tin tài khoản hiện tại trên Bing nếu đã đăng nhập
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
            print(f"   [✓] Tài khoản Bing đang kết nối: \"{logged_name}\"")
        else:
            # Kiểm tra sự hiện diện của nút Sign In / Đăng nhập
            sign_in_elements = driver.find_elements(By.ID, "id_s") + driver.find_elements(By.CSS_SELECTOR, "a[id*='signin']")
            needs_login = False
            for el in sign_in_elements:
                if el.is_displayed() and ("sign in" in el.text.lower() or "đăng nhập" in el.text.lower()):
                    needs_login = True
                    break

            if needs_login:
                print("\n" + "=" * 65)
                print(f"🔔 THÔNG BÁO ĐĂNG NHẬP ({profile_name}):")
                print(f"   Trình duyệt Edge vừa mở profile [{profile_name}].")
                print("   Bạn hãy bấm 'Sign In' (Đăng nhập) bằng tài khoản Microsoft Rewards tương ứng.")
                print("   (Chỉ cần đăng nhập 1 LẦN DUY NHẤT, từ lần sau bot tự nhớ vĩnh viễn!)")
                print("=" * 65)
                if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
                    try:
                        input("👉 Sau khi bạn đã đăng nhập xong trên Edge, hãy nhấn ENTER tại đây để bắt đầu cày điểm...")
                    except Exception:
                        pass
                else:
                    print("👉 Đang chạy không tương tác (Web UI/Background). Tạm dừng 10s cho đăng nhập...")
                    time.sleep(10)
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


def run_profile_session(profile, selected_mode, config, keywords_pool=None):
    """Thực hiện phiên tìm kiếm cho một tài khoản / profile cụ thể"""
    profile_name = profile.get("name", f"Profile {profile.get('id', '1')}")
    profile_dir = get_profile_abs_path(profile)

    run_pc = selected_mode in ["all", "desktop"]
    run_mobile = selected_mode in ["all", "mobile"]

    search_cfg = config.get("search_settings", {})
    pc_count = search_cfg.get("pc_searches", 31) if run_pc else 0
    mobile_count = search_cfg.get("mobile_searches", 21) if run_mobile else 0
    device_name = config.get("browser_settings", {}).get("mobile_device_name", "Pixel 7")

    print("\n" + "=" * 66)
    print(f"👤 BẮT ĐẦU PHIÊN CHẠY CHO: {profile_name.upper()}")
    print(f"[*] Thư mục Profile   : {profile_dir}")
    print(f"[*] Chế độ đang chạy  : {selected_mode.upper()}")
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

    # Nạp danh sách từ khóa riêng cho profile này (xáo trộn)
    if keywords_pool:
        keywords = list(keywords_pool)
    else:
        keywords = load_keywords()
    random.shuffle(keywords)
    print(f"[✓] Đã chuẩn bị {len(keywords)} từ khóa tìm kiếm tự nhiên cho {profile_name}.")

    total_searches_done = 0
    start_time = datetime.now()

    # ==========================
    # PHẦN 1: TÌM KIẾM DESKTOP (PC)
    # ==========================
    if run_pc and pc_count > 0:
        print(f"\n🖥️  [{profile_name}] Đang khởi động Microsoft Edge ở chế độ Desktop (PC)...")
        pc_driver = None
        try:
            pc_driver = create_edge_driver(is_mobile=False, config=config, profile_target=profile)
            check_and_prompt_first_time_login(pc_driver, profile_name=profile_name)
            searches_pc = execute_search_session(pc_driver, keywords, pc_count, mode_name="PC", config=config)
            total_searches_done += searches_pc
        except Exception as e:
            print(f"[!] Lỗi trong phiên tìm kiếm PC ({profile_name}): {e}")
        finally:
            if pc_driver:
                print(f"[*] Đang đóng phiên duyệt Desktop của {profile_name}...")
                try:
                    pc_driver.quit()
                except Exception:
                    pass
                time.sleep(1)
                kill_zombie_edge_processes(profile_dir)

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
        print(f"\n📱 [{profile_name}] {step_label} Đang khởi động Microsoft Edge ở chế độ Mobile (Giả lập {device_name})...")
        mobile_driver = None
        try:
            mobile_driver = create_edge_driver(is_mobile=True, config=config, profile_target=profile)
            check_and_prompt_first_time_login(mobile_driver, profile_name=profile_name)
            searches_mob = execute_search_session(mobile_driver, keywords, mobile_count, mode_name="MOBILE", config=config)
            total_searches_done += searches_mob
        except Exception as e:
            print(f"[!] Lỗi trong phiên tìm kiếm Mobile ({profile_name}): {e}")
        finally:
            if mobile_driver:
                print(f"[*] Đang đóng phiên duyệt Mobile của {profile_name}...")
                try:
                    mobile_driver.quit()
                except Exception:
                    pass
                time.sleep(1)
                kill_zombie_edge_processes(profile_dir)

    duration = datetime.now() - start_time
    minutes, seconds = divmod(int(duration.total_seconds()), 60)
    print(f"\n[✓] Hoàn thành cho {profile_name}: {total_searches_done} lượt tìm kiếm ({minutes} phút {seconds} giây).")
    return {
        "profile_name": profile_name,
        "searches": total_searches_done,
        "duration": duration
    }


def main():
    parser = argparse.ArgumentParser(description="Microsoft Rewards Auto Search Bot")
    parser.add_argument("--profile", default=None,
                        help="Chọn profile tài khoản: 1, 2, 3, 4, all (hoặc theo id/tên)")
    parser.add_argument("--mode", choices=["all", "desktop", "pc", "mobile"], default=None,
                        help="Chọn chế độ chạy: desktop (pc), mobile hoặc all (cả hai)")
    parser.add_argument("--pc", "--desktop", dest="pc_flag", action="store_true",
                        help="Chỉ chạy tìm kiếm Desktop (PC)")
    parser.add_argument("--mobile", dest="mobile_flag", action="store_true",
                        help="Chỉ chạy tìm kiếm Mobile")
    parser.add_argument("--login", action="store_true",
                        help="Mở trình duyệt Edge để đăng nhập tài khoản / kiểm tra điểm")
    parser.add_argument("--non-interactive", action="store_true",
                        help="Chạy ở chế độ tự động không chờ nhấn phím Enter")
    args, _ = parser.parse_known_args()

    config = load_config()
    profiles = config.get("profiles", [])
    if not profiles:
        default_p = config.get("browser_settings", {}).get("profile_directory_path", "./edge_profile")
        profiles = [
            {"id": "1", "name": "Tài khoản 1 (Chính)", "path": default_p},
            {"id": "2", "name": "Tài khoản 2 (Phụ)", "path": "./edge_profile_2"}
        ]

    # 1. Xác định profile cần chạy
    selected_profiles = []
    if args.profile:
        p_arg = str(args.profile).strip().lower()
        if p_arg in ["all", "both", "tatca", "ca2", "tat_ca"]:
            selected_profiles = profiles
        else:
            # Khớp theo id hoặc tên
            matched = [p for p in profiles if str(p.get("id", "")).lower() == p_arg or p.get("name", "").lower() == p_arg]
            if matched:
                selected_profiles = [matched[0]]
            elif p_arg.isdigit() and 1 <= int(p_arg) <= len(profiles):
                selected_profiles = [profiles[int(p_arg) - 1]]
            elif p_arg.isdigit() and int(p_arg) == len(profiles) + 1:
                selected_profiles = profiles
            else:
                print(f"[!] Không nhận diện được profile '{args.profile}', dùng mặc định Profile 1.")
                selected_profiles = [profiles[0]]
    else:
        # Hiển thị menu chọn Profile
        print("""
====================================================================
          MICROSOFT REWARDS AUTO SEARCH BOT (EDGE)
             Phiên bản Anti-Ban & Đa Tài Khoản
====================================================================
👉 BƯỚC 1: CHỌN TÀI KHOẢN / PROFILE TÌM KIẾM:""")
        for idx, p in enumerate(profiles, 1):
            p_name = p.get("name", f"Profile {p.get('id', idx)}")
            p_path = p.get("path", "")
            print(f"   [{idx}] {p_name} ({p_path})")
        all_idx = len(profiles) + 1
        print(f"   [{all_idx}] Chạy lần lượt TẤT CẢ các tài khoản trên")
        print("====================================================================")
        p_choice = input(f"Nhập lựa chọn tài khoản (1-{all_idx}) [Mặc định: 1]: ").strip()
        if p_choice == str(all_idx) or p_choice.lower() in ["all", "both", "tatca", "ca2"]:
            selected_profiles = profiles
        elif p_choice.isdigit() and 1 <= int(p_choice) <= len(profiles):
            selected_profiles = [profiles[int(p_choice) - 1]]
        else:
            selected_profiles = [profiles[0]]

    # Nếu là chế độ đăng nhập tài khoản (--login)
    if args.login:
        target = selected_profiles[0] if selected_profiles else profiles[0]
        proc = open_browser_for_login(target, config=config)
        if proc:
            try:
                proc.wait()
            except KeyboardInterrupt:
                pass
        return

    # 2. Xác định chế độ chạy (Mode)
    if args.pc_flag or (args.mode in ["desktop", "pc"]):
        selected_mode = "desktop"
    elif args.mobile_flag or (args.mode == "mobile"):
        selected_mode = "mobile"
    elif args.mode == "all":
        selected_mode = "all"
    else:
        # Nếu chưa truyền tham số mode -> Hiển thị menu lựa chọn
        print("""
====================================================================
👉 BƯỚC 2: CHỌN CHẾ ĐỘ TÌM KIẾM BẠN MUỐN:
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

    # Nạp danh sách từ khóa gốc
    raw_keywords = load_keywords()
    print(f"\n[✓] Đã nạp thành công kho {len(raw_keywords)} từ khóa tìm kiếm tự nhiên.")

    session_results = []
    overall_start = datetime.now()

    for p_idx, current_profile in enumerate(selected_profiles):
        p_name = current_profile.get("name", f"Profile {current_profile.get('id', p_idx+1)}")
        if len(selected_profiles) > 1:
            print("\n" + "#" * 66)
            print(f"### [TIẾN TRÌNH] BẮT ĐẦU TÀI KHOẢN {p_idx + 1}/{len(selected_profiles)}: {p_name}")
            print("#" * 66)

        res = run_profile_session(current_profile, selected_mode, config, keywords_pool=raw_keywords)
        session_results.append(res)

        # Nghỉ giữa các profile nếu chạy nhiều profile
        if p_idx < len(selected_profiles) - 1:
            inter_profile_pause = random.uniform(10, 18)
            print(f"\n{'='*66}")
            print(f"⏳ Đã xong {p_name}. Tạm dừng an toàn {inter_profile_pause:.1f}s trước khi chuyển sang tài khoản tiếp theo...")
            print(f"{'='*66}\n")
            time.sleep(inter_profile_pause)

    # ==========================
    # TỔNG KẾT TOÀN BỘ PHIÊN
    # ==========================
    overall_duration = datetime.now() - overall_start
    total_mins, total_secs = divmod(int(overall_duration.total_seconds()), 60)
    total_searches_done = sum(r["searches"] for r in session_results)

    print("\n" + "=" * 66)
    print("🎉 TẤT CẢ CÁC PHIÊN TÌM KIẾM ĐÃ HOÀN TẤT!")
    print(f"   - Chế độ tìm kiếm                  : {selected_mode.upper()}")
    print(f"   - Số tài khoản đã chạy             : {len(session_results)}")
    for r in session_results:
        print(f"     • {r['profile_name']}: {r['searches']} lượt search (~{r['searches'] * 3} điểm)")
    print(f"   - Tổng số lượt tìm kiếm hoàn thành : {total_searches_done}")
    print(f"   - Tổng thời gian chạy              : {total_mins} phút {total_secs} giây")
    print(f"   - Tổng điểm Rewards ước tính       : ~{total_searches_done * 3} điểm")
    print("=" * 66)
    print("Bạn có thể mở Microsoft Edge để kiểm tra số điểm Rewards được cộng!")
    if not args.non_interactive and sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
        try:
            input("\nNhấn phím ENTER để kết thúc chương trình...")
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Người dùng đã dừng chương trình bằng Ctrl+C.")
        try:
            cfg = load_config()
            for p in cfg.get("profiles", []):
                p_dir = get_profile_abs_path(p)
                kill_zombie_edge_processes(p_dir)
        except Exception:
            pass
        sys.exit(0)
