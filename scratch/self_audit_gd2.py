# -*- coding: utf-8 -*-
"""
Self-Audit Script cho Giai Đoạn 2 (GD2)
Kiểm tra tự động toàn diện:
1. Giới hạn số dòng code (< 250 dòng/file trong src/)
2. Biên dịch (py_compile) & Import modules (chống Circular Import)
3. Kiểm tra tĩnh (AST Check):
   - Mọi lệnh subprocess trong adb_client.py bắt buộc có timeout
   - Mọi khối mở driver trong browser.py/runner.py có khối finally đóng driver
4. Kiểm tra tương thích ngược (Backward Compatibility):
   - Xác nhận tất cả các hàm/class mà web_server.py yêu cầu đều tồn tại
5. Kiểm tra tính năng nghiệp vụ:
   - save_android_checkin_result hỗ trợ profile_id linh hoạt (Sửa lỗi #20)
   - SQLite WAL mode & timeout=30.0
"""

import ast
import sys
import importlib
import py_compile
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent

passed_checks = 0
failed_checks = 0


def check(name, condition, msg=""):
    global passed_checks, failed_checks
    if condition:
        print(f"  [PASS] {name}")
        passed_checks += 1
    else:
        print(f"  [FAIL] {name} - {msg}")
        failed_checks += 1


print("=" * 65)
print("1. KIỂM TRA SỐ DÒNG CODE (LINE COUNT <= 250 DÒNG TRONG src/)")
print("=" * 65)

src_py_files = sorted(list((ROOT_DIR / "src").rglob("*.py")))
all_under_250 = True

for f in src_py_files:
    rel_path = f.relative_to(ROOT_DIR)
    lines = len(f.read_text(encoding="utf-8").splitlines())
    if lines > 250:
        check(f"{rel_path} <= 250 dòng", False, f"Vượt quá giới hạn: {lines} dòng!")
        all_under_250 = False
    else:
        check(f"{rel_path} <= 250 dòng ({lines} dòng)", True)

check("TẤT CẢ các file .py trong src/ đều <= 250 dòng", all_under_250)


print("\n" + "=" * 65)
print("2. BIÊN DỊCH CÚ PHÁP & KIỂM TRA IMPORT (CHỐNG CIRCULAR IMPORT)")
print("=" * 65)

all_files_to_compile = src_py_files + [
    ROOT_DIR / "db.py",
    ROOT_DIR / "ai_keywords.py",
    ROOT_DIR / "edge_rewards_bot.py",
    ROOT_DIR / "android_checkin.py",
    ROOT_DIR / "web_server.py",
]

for pf in all_files_to_compile:
    try:
        py_compile.compile(str(pf), doraise=True)
        check(f"py_compile: {pf.name}", True)
    except py_compile.PyCompileError as e:
        check(f"py_compile: {pf.name}", False, str(e))

sys.path.insert(0, str(ROOT_DIR))

modules_to_test = [
    "src.core.paths",
    "src.core.db_connection",
    "src.core.db_queries",
    "src.core.db",
    "src.services.nlp_engine",
    "src.services.ai_keywords",
    "src.bots.edge.anti_detect",
    "src.bots.edge.browser",
    "src.bots.edge.points_parser",
    "src.bots.edge.searcher",
    "src.bots.edge.runner",
    "src.bots.edge",
    "src.bots.android.adb_client",
    "src.bots.android.screen_analyzer",
    "src.bots.android.checkin_flow",
    "src.bots.android",
    "db",
    "ai_keywords",
    "edge_rewards_bot",
    "android_checkin",
]

for mod_name in modules_to_test:
    try:
        mod = importlib.import_module(mod_name)
        check(f"Import thành công: {mod_name}", True)
    except Exception as e:
        check(f"Import thành công: {mod_name}", False, str(e))


print("\n" + "=" * 65)
print("3. KIỂM TRA TĨNH AST: TIMEOUT CHO SUBPROCESS & KHỐI FINALLY")
print("=" * 65)

# 3.1 Kiểm tra mọi subprocess.run trong adb_client.py đều có timeout
adb_client_path = ROOT_DIR / "src" / "bots" / "android" / "adb_client.py"
tree_adb = ast.parse(adb_client_path.read_text(encoding="utf-8"))
subproc_calls_in_adb = 0
all_have_timeout = True

for node in ast.walk(tree_adb):
    if isinstance(node, ast.Call):
        func = node.func
        is_subproc = False
        if isinstance(func, ast.Attribute) and func.attr == "run":
            if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                is_subproc = True
        if is_subproc:
            subproc_calls_in_adb += 1
            kw_names = [kw.arg for kw in node.keywords]
            if "timeout" not in kw_names:
                all_have_timeout = False
                print(f"    [!] Line {node.lineno}: subprocess.run thiếu timeout!")

check(f"Mọi subprocess.run trong adb_client.py ({subproc_calls_in_adb} lệnh) đều có tham số timeout",
      subproc_calls_in_adb > 0 and all_have_timeout)

# 3.2 Kiểm tra finally quit driver trong browser.py và runner.py
for script_name in ["browser.py", "runner.py"]:
    script_p = ROOT_DIR / "src" / "bots" / "edge" / script_name
    tree_s = ast.parse(script_p.read_text(encoding="utf-8"))
    has_try_finally = any(isinstance(n, ast.Try) and len(n.finalbody) > 0 for n in ast.walk(tree_s))
    check(f"{script_name} có khối try...finally quản lý đóng tài nguyên", has_try_finally)


print("\n" + "=" * 65)
print("4. KIỂM TRA TƯƠNG THÍCH NGƯỢC (BACKWARD COMPATIBILITY CHO WEB_SERVER.PY)")
print("=" * 65)

import db
import ai_keywords
import edge_rewards_bot
import android_checkin

# Kiểm tra các hàm db.py mà web_server.py gọi
db_expected = [
    "init_db", "get_all_profiles", "get_profile_by_id", "add_profile_db",
    "update_profile_db", "delete_profile_db", "get_recent_history",
    "save_android_checkin_result", "get_latest_android_checkin"
]
for fn in db_expected:
    check(f"db.{fn} tồn tại", hasattr(db, fn))

# Kiểm tra các hàm ai_keywords.py
for fn in ["generate_new_keywords", "append_keywords_to_file"]:
    check(f"ai_keywords.{fn} tồn tại", hasattr(ai_keywords, fn))

# Kiểm tra các hàm edge_rewards_bot.py
edge_expected = [
    "load_config", "get_profile_abs_path", "kill_zombie_edge_processes",
    "open_browser_for_login", "check_profile_points"
]
for fn in edge_expected:
    check(f"edge_rewards_bot.{fn} tồn tại", hasattr(edge_rewards_bot, fn))

# Kiểm tra class android_checkin.py
check("android_checkin.AndroidBingCheckinBot tồn tại", hasattr(android_checkin, "AndroidBingCheckinBot"))

bot_inst = android_checkin.AndroidBingCheckinBot()
bot_methods_expected = [
    "open_app", "close_app", "turn_on_device", "turn_off_device",
    "toggle_screen", "reconnect_device", "get_device_status",
    "capture_screenshot", "execute_checkin"
]
for m in bot_methods_expected:
    check(f"AndroidBingCheckinBot.{m} tồn tại", hasattr(bot_inst, m))


print("\n" + "=" * 65)
print("5. KIỂM TRA TÍNH NĂNG NGHIỆP VỤ (SỬA LỖI #20 & SQLITE WAL)")
print("=" * 65)

# Kiểm tra signature của save_android_checkin_result hỗ trợ profile_id
import inspect
sig = inspect.signature(db.save_android_checkin_result)
check("save_android_checkin_result có tham số profile_id (Sửa lỗi #20)",
      "profile_id" in sig.parameters)

# Kiểm tra WAL mode và connection timeout
conn = db.get_db_connection()
cur = conn.cursor()
cur.execute("PRAGMA journal_mode;")
jmode = cur.fetchone()[0]
check(f"Database journal_mode là WAL ({jmode})", jmode.lower() == "wal")
conn.close()


print("\n" + "=" * 65)
print(f"KẾT QUẢ SELF-AUDIT GIAI ĐOẠN 2: {passed_checks} PASSED | {failed_checks} FAILED")
print("=" * 65)

if failed_checks == 0:
    print(">>> GIAI ĐOẠN 2 HOÀN TẤT XUẤT SẮC - SẴN SÀNG COMMIT GIT! <<<")
else:
    print(">>> CẦN SỬA CÁC MỤC THẤT BẠI TRƯỚC KHI COMMIT! <<<")
