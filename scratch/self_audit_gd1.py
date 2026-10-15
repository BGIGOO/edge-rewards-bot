# -*- coding: utf-8 -*-
"""
Self-Audit Script cho Giai Đoạn 1 (GD1)
Kiểm tra tính toàn vẹn của:
1. Cấu trúc thư mục chuẩn & Dọn dẹp dữ liệu cũ
2. Biên dịch mã nguồn Python (py_compile)
3. Module import & Path resolution (paths.py)
4. Cơ sở dữ liệu SQLite (data/rewards_bot.db), WAL mode, đường dẫn profiles
5. Cấu hình config.json
6. Frontend & Static routing
"""

import os
import sys
import json
import sqlite3
import py_compile
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent

passed_checks = 0
failed_checks = 0
warnings = 0

def check(name, condition, msg=""):
    global passed_checks, failed_checks
    if condition:
        print(f"  [PASS] {name}")
        passed_checks += 1
    else:
        print(f"  [FAIL] {name} - {msg}")
        failed_checks += 1

def warn(name, msg):
    global warnings
    print(f"  [WARN] {name} - {msg}")
    warnings += 1


print("=" * 60)
print("1. KIỂM TRA CẤU TRÚC THƯ MỤC VÀ DỌN DẸP DỮ LIỆU CŨ")
print("=" * 60)

check("src/__init__.py tồn tại", (ROOT_DIR / "src" / "__init__.py").exists())
check("src/core/__init__.py tồn tại", (ROOT_DIR / "src" / "core" / "__init__.py").exists())
check("src/core/paths.py tồn tại", (ROOT_DIR / "src" / "core" / "paths.py").exists())
check("data/ tồn tại", (ROOT_DIR / "data").is_dir())
check("data/profiles/ tồn tại", (ROOT_DIR / "data" / "profiles").is_dir())
check("data/screenshots/ tồn tại", (ROOT_DIR / "data" / "screenshots").is_dir())
check("data/rewards_bot.db tồn tại", (ROOT_DIR / "data" / "rewards_bot.db").is_file())
check("data/keywords.txt tồn tại", (ROOT_DIR / "data" / "keywords.txt").is_file())

# Kiểm tra dữ liệu cũ không còn ở root
check("Root KHÔNG còn rewards_bot.db", not (ROOT_DIR / "rewards_bot.db").exists())
check("Root KHÔNG còn keywords.txt", not (ROOT_DIR / "keywords.txt").exists())
check("Root KHÔNG còn test_device_screen.png", not (ROOT_DIR / "test_device_screen.png").exists())
check("web/ KHÔNG còn android_checkin_before.png", not (ROOT_DIR / "web" / "android_checkin_before.png").exists())
check("web/ KHÔNG còn android_checkin_after.png", not (ROOT_DIR / "web" / "android_checkin_after.png").exists())

# Kiểm tra profile folders ở root
root_profiles = [p.name for p in ROOT_DIR.glob("edge_profile*") if p.is_dir()]
check("Root KHÔNG còn thư mục edge_profile*", len(root_profiles) == 0, f"Tìm thấy: {root_profiles}")

# Kiểm tra screenshots có trong data/screenshots
ss_files = list((ROOT_DIR / "data" / "screenshots").glob("*.png"))
check("data/screenshots có chứa ảnh chụp", len(ss_files) > 0, f"Số lượng ảnh: {len(ss_files)}")


print("\n" + "=" * 60)
print("2. BIÊN DỊCH CÚ PHÁP CÁC FILE PYTHON (py_compile)")
print("=" * 60)

py_files = [
    ROOT_DIR / "src" / "core" / "paths.py",
    ROOT_DIR / "db.py",
    ROOT_DIR / "ai_keywords.py",
    ROOT_DIR / "edge_rewards_bot.py",
    ROOT_DIR / "android_checkin.py",
    ROOT_DIR / "web_server.py",
]

for pf in py_files:
    try:
        py_compile.compile(str(pf), doraise=True)
        check(f"Biên dịch {pf.name}", True)
    except py_compile.PyCompileError as e:
        check(f"Biên dịch {pf.name}", False, str(e))


print("\n" + "=" * 60)
print("3. KIỂM TRA MODULE PATHS.PY & RESOLVE_PROFILE_PATH")
print("=" * 60)

sys.path.insert(0, str(ROOT_DIR))
try:
    from src.core.paths import (
        ROOT_DIR as R_DIR,
        DATA_DIR,
        PROFILES_DIR,
        SCREENSHOTS_DIR,
        DB_PATH,
        KEYWORDS_PATH,
        CONFIG_PATH,
        resolve_profile_path,
        get_profile_dir
    )
    check("Import src.core.paths thành công", True)

    p1 = resolve_profile_path("./edge_profile")
    check("resolve_profile_path('./edge_profile') -> data/profiles/edge_profile",
          p1 == PROFILES_DIR / "edge_profile", f"Nhận được: {p1}")

    p2 = resolve_profile_path("edge_profile_2")
    check("resolve_profile_path('edge_profile_2') -> data/profiles/edge_profile_2",
          p2 == PROFILES_DIR / "edge_profile_2", f"Nhận được: {p2}")

    p_abs = resolve_profile_path(str(PROFILES_DIR / "edge_profile_3"))
    check("resolve_profile_path(đường dẫn tuyệt đối) giữ nguyên",
          p_abs == PROFILES_DIR / "edge_profile_3", f"Nhận được: {p_abs}")

except Exception as e:
    check("Import src.core.paths", False, str(e))


print("\n" + "=" * 60)
print("4. KIỂM TRA CƠ SỞ DỮ LIỆU SQLITE & BẢNG PROFILES")
print("=" * 60)

try:
    import db
    conn = db.get_db_connection()
    cur = conn.cursor()

    # Kiểm tra journal_mode WAL
    cur.execute("PRAGMA journal_mode;")
    jmode = cur.fetchone()[0]
    check(f"SQLite journal_mode là WAL (nhận được: {jmode})", jmode.lower() == "wal")

    # Kiểm tra các bảng
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    check("Bảng profiles tồn tại", "profiles" in tables)
    check("Bảng run_history tồn tại", "run_history" in tables)

    # Kiểm tra dữ liệu profiles
    cur.execute("SELECT id, name, email, path FROM profiles;")
    rows = cur.fetchall()
    check(f"Bảng profiles có dữ liệu ({len(rows)} bản ghi)", len(rows) > 0)

    all_paths_in_data = True
    for r in rows:
        pid, name, email, path_val = r[0], r[1], r[2], r[3]
        in_data = "data\\profiles" in path_val or "data/profiles" in path_val
        exists_on_disk = os.path.exists(path_val)
        print(f"    Profile ID {pid} ({name}):")
        print(f"      Path: {path_val}")
        print(f"      Trỏ vào data/profiles: {in_data} | Thư mục thực tế tồn tại: {exists_on_disk}")
        if not in_data or not exists_on_disk:
            all_paths_in_data = False

    check("Tất cả đường dẫn profile trong SQLite trỏ vào data/profiles/ và thư mục tồn tại", all_paths_in_data)
    conn.close()
except Exception as e:
    check("Kết nối và kiểm tra SQLite", False, str(e))


print("\n" + "=" * 60)
print("5. KIỂM TRA CẤU HÌNH CONFIG.JSON")
print("=" * 60)

try:
    with open(ROOT_DIR / "config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    cfg_profiles = cfg.get("profiles", [])
    check(f"config.json chứa profiles ({len(cfg_profiles)} profiles)", len(cfg_profiles) > 0)

    cfg_all_in_data = True
    for p in cfg_profiles:
        pval = p.get("path", "")
        in_data = "data\\profiles" in pval or "data/profiles" in pval
        if not in_data:
            cfg_all_in_data = False
    check("Tất cả profiles trong config.json trỏ vào data/profiles/", cfg_all_in_data)

    def_prof = cfg.get("browser_settings", {}).get("profile_directory_path", "")
    check("browser_settings.profile_directory_path trỏ vào data/profiles",
          "data" in def_prof and "profiles" in def_prof, f"Nhận được: {def_prof}")

except Exception as e:
    check("Kiểm tra config.json", False, str(e))


print("\n" + "=" * 60)
print("6. KIỂM TRA FRONTEND VÀ STATIC MOUNT ROUTING")
print("=" * 60)

with open(ROOT_DIR / "web" / "index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

check("index.html KHÔNG chứa /static/android_checkin",
      "/static/android_checkin" not in html_content)
check("index.html sử dụng /screenshots/android_checkin",
      "/screenshots/android_checkin" in html_content)

with open(ROOT_DIR / "web" / "app.js", "r", encoding="utf-8") as f:
    js_content = f.read()

check("app.js KHÔNG chứa /static/android_checkin",
      "/static/android_checkin" not in js_content)
check("app.js sử dụng /screenshots/android_checkin",
      "/screenshots/android_checkin" in js_content)

with open(ROOT_DIR / "web_server.py", "r", encoding="utf-8") as f:
    ws_content = f.read()

check("web_server.py mount /screenshots trỏ vào SCREENSHOTS_DIR",
      'app.mount("/screenshots"' in ws_content)


print("\n" + "=" * 60)
print(f"KẾT QUẢ SELF-AUDIT: {passed_checks} PASSED | {failed_checks} FAILED | {warnings} WARNINGS")
print("=" * 60)

if failed_checks == 0:
    print(">>> GIAI ĐOẠN 1 HOÀN TOÀN ĐẠT CHUẨN VÀ SẴN SÀNG! <<<")
else:
    print(">>> CẦN SỬA CÁC MỤC THẤT BẠI TRƯỚC KHI BƯỚC SANG GIAI ĐOẠN 2! <<<")
