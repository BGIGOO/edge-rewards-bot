# -*- coding: utf-8 -*-
"""
src/bots/edge/browser.py
========================
Quản lý khởi tạo Edge WebDriver, profile data, dọn dẹp zombie processes.
Bảo đảm đóng trình duyệt 100% với try...finally / Context Manager (rule 02).
Tuân thủ rule 01_architecture (< 250 dòng).
"""

import os
import time
import shutil
import subprocess
from contextlib import contextmanager
from typing import Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from src.core.paths import resolve_profile_path


def get_profile_abs_path(target: Any = None, base_dir: Any = None) -> str:
    """Lấy đường dẫn tuyệt đối an toàn đến thư mục profile Edge."""
    p_path = "./edge_profile"
    if isinstance(target, str):
        p_path = target
    elif isinstance(target, dict):
        p_path = (target.get("path")
                  or target.get("profile_path")
                  or target.get("browser_settings", {}).get("profile_directory_path", "./edge_profile"))

    p_path = os.path.expandvars(p_path)
    resolved = str(resolve_profile_path(p_path))
    os.makedirs(resolved, exist_ok=True)
    return resolved


def sync_profile_from_system(profile: Any) -> None:
    """Đồng bộ cookie/session từ Edge gốc nếu là profile 1-3."""
    if not isinstance(profile, dict):
        return
    p_id = str(profile.get("id", ""))
    if p_id not in ["1", "2", "3"] and not profile.get("sync_from_system"):
        return

    prof_dir_name = profile.get("profile_directory")
    if not prof_dir_name:
        return

    user_data = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
    src_profile = os.path.join(user_data, prof_dir_name)
    if not os.path.exists(src_profile):
        return

    target_dir = get_profile_abs_path(profile)
    dst_profile = os.path.join(target_dir, prof_dir_name)
    os.makedirs(os.path.join(dst_profile, "Network"), exist_ok=True)

    # Đồng bộ Local State & session files
    local_state_src = os.path.join(user_data, "Local State")
    local_state_dst = os.path.join(target_dir, "Local State")
    c_dst = os.path.join(dst_profile, "Network", "Cookies")
    if os.path.exists(local_state_src) and (not os.path.exists(local_state_dst) or not os.path.exists(c_dst)):
        try:
            shutil.copy2(local_state_src, local_state_dst)
        except Exception:
            pass

    for fname in ["Preferences", "Secure Preferences", "Web Data", "Login Data"]:
        fsrc, fdst = os.path.join(src_profile, fname), os.path.join(dst_profile, fname)
        if os.path.exists(fsrc) and not os.path.exists(fdst):
            try:
                shutil.copy2(fsrc, fdst)
            except Exception:
                pass

    for cname in ["Cookies", "Cookies-journal", "Network Persistent State"]:
        c_src, c_dest = os.path.join(src_profile, "Network", cname), os.path.join(dst_profile, "Network", cname)
        if os.path.exists(c_src) and not os.path.exists(c_dest):
            try:
                shutil.copy2(c_src, c_dest)
            except Exception:
                pass


def kill_zombie_edge_processes(profile_dir: Optional[str] = None) -> None:
    """Đóng các tiến trình msedge.exe / msedgedriver.exe cũ đang khóa profile_dir."""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name = 'msedgedriver.exe'\" | Stop-Process -Force -ErrorAction SilentlyContinue"],
            capture_output=True, timeout=5
        )
        if profile_dir:
            norm_win = os.path.abspath(profile_dir).replace("/", "\\")
            norm_fwd = os.path.abspath(profile_dir).replace("\\", "/")
            folder = os.path.basename(os.path.normpath(profile_dir))
            ps = (
                f"$p = Get-CimInstance Win32_Process -Filter \"Name = 'msedge.exe'\" | "
                f"Where-Object {{ $_.CommandLine -like '*{folder}*' -or $_.CommandLine -like '*{norm_win}*' -or $_.CommandLine -like '*{norm_fwd}*' }}; "
                f"foreach ($x in $p) {{ Stop-Process -Id $x.ProcessId -Force -ErrorAction SilentlyContinue }}"
            )
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], capture_output=True, timeout=8)
            port_f = os.path.join(norm_win, "DevToolsActivePort")
            if os.path.exists(port_f):
                try:
                    os.remove(port_f)
                except Exception:
                    pass
            time.sleep(1)
    except Exception:
        pass


def open_browser_for_login(target_profile: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
    """Mở Edge gốc cho người dùng đăng nhập tài khoản Microsoft."""
    p_dir = get_profile_abs_path(target_profile)
    kill_zombie_edge_processes(p_dir)

    email = target_profile.get("email") or ""
    name = target_profile.get("name") or ""
    status = target_profile.get("status") or ""
    has_email = bool(status != "unlogged" and ("@" in email or ("@" in name and not name.startswith("Chưa đăng nhập"))))
    target_url = "https://rewards.bing.com" if has_email else "https://login.live.com/login.srf?prompt=select_account"

    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ]
    msedge_exe = next((p for p in edge_paths if os.path.exists(p)), "msedge")
    cmd = [
        msedge_exe, f"--user-data-dir={p_dir}", "--no-first-run", "--no-default-browser-check",
        "--disable-features=msImplicitSignin,msEdgeSingleSignOn,WebAccountManager", target_url
    ]
    if isinstance(target_profile, dict) and target_profile.get("profile_directory"):
        cmd.append(f"--profile-directory={target_profile['profile_directory']}")

    try:
        return subprocess.Popen(cmd)
    except Exception as e:
        print(f"[!] Không thể mở Microsoft Edge: {e}")
        return None


def create_edge_driver(is_mobile: bool = False, config: Optional[Dict[str, Any]] = None, profile_target: Any = None):
    """Khởi tạo Edge WebDriver với anti-detect flags và mobile emulation."""
    options = EdgeOptions()
    browser_cfg = config.get("browser_settings", {}) if config else {}
    target_prof = profile_target if profile_target is not None else config
    profile_dir = get_profile_abs_path(target_prof)

    kill_zombie_edge_processes(profile_dir)
    sync_profile_from_system(target_prof)

    args = [
        f"--user-data-dir={profile_dir}",
        "--disable-features=msImplicitSignin,msEdgeSingleSignOn,WebAccountManager",
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox", "--disable-dev-shm-usage", "--disable-notifications",
        "--disable-infobars", "--no-first-run", "--no-default-browser-check",
        "--lang=vi-VN,vi,en-US,en"
    ]
    for arg in args:
        options.add_argument(arg)

    if isinstance(target_prof, dict) and target_prof.get("profile_directory"):
        options.add_argument(f"--profile-directory={target_prof['profile_directory']}")

    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)

    if browser_cfg.get("headless", False):
        options.add_argument("--headless=new")

    if is_mobile:
        device_name = browser_cfg.get("mobile_device_name", "Pixel 7")
        options.add_experimental_option("mobileEmulation", {"deviceName": device_name})
    else:
        options.add_argument("--start-maximized")

    driver = None
    for attempt in range(2):
        try:
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            break
        except Exception:
            try:
                driver = webdriver.Edge(options=options)
                break
            except Exception as e_direct:
                if attempt == 0:
                    kill_zombie_edge_processes(profile_dir)
                    time.sleep(1.5)
                else:
                    raise e_direct

    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                if (!window.chrome) { window.chrome = {}; }
                window.chrome.runtime = {};
                Object.defineProperty(navigator, 'languages', { get: () => ['vi-VN', 'vi', 'en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                """
            }
        )
    except Exception:
        pass

    if is_mobile:
        driver.set_window_size(412, 915)

    return driver


@contextmanager
def managed_browser(is_mobile: bool = False, config: Optional[Dict[str, Any]] = None, profile_target: Any = None):
    """Context manager bảo đảm đóng Edge WebDriver 100% trong khối finally."""
    driver = create_edge_driver(is_mobile=is_mobile, config=config, profile_target=profile_target)
    profile_dir = get_profile_abs_path(profile_target or config)
    try:
        yield driver
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        time.sleep(0.5)
        kill_zombie_edge_processes(profile_dir)
