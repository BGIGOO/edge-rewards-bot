# -*- coding: utf-8 -*-
"""
scratch/self_audit_gd3.py
=========================
Bộ kiểm tra tự động chốt hạ Giai đoạn 3 và toàn bộ hệ thống:
1. Quét giới hạn 250 dòng/file đối với 100% file Python và JavaScript.
2. Kiểm tra biên dịch cú pháp và import toàn bộ các module.
3. Kiểm tra tích hợp Web Server (Integration Test bằng Starlette TestClient).
4. Kiểm tra Mount tĩnh (/static, /screenshots) và Route contract.
"""

import os
import sys
import py_compile
from pathlib import Path

# Configure utf-8 for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add workspace root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

passed_tests = 0
failed_tests = 0


def record_result(name: str, passed: bool, msg: str = ""):
    global passed_tests, failed_tests
    if passed:
        passed_tests += 1
        print(f"  [PASS] {name}")
    else:
        failed_tests += 1
        print(f"  [FAIL] {name}: {msg}")


def test_line_limits():
    print("\n--- 1. KIỂM TRA GIỚI HẠN DÒNG (< 250 DÒNG/FILE) ---")
    
    # 1.1 Root Python Shims
    root_shims = ["db.py", "ai_keywords.py", "edge_rewards_bot.py", "android_checkin.py", "web_server.py"]
    for shim in root_shims:
        p = ROOT_DIR / shim
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                lines = len(f.readlines())
            record_result(f"Root Shim {shim} <= 250 lines", lines <= 250, f"Có {lines} dòng (> 250)")
        else:
            record_result(f"Root Shim {shim} exists", False, "File không tồn tại")

    # 1.2 Python files in src/
    for root, dirs, files in os.walk(str(ROOT_DIR / "src")):
        for f in files:
            if f.endswith(".py"):
                file_path = Path(root) / f
                rel_path = file_path.relative_to(ROOT_DIR)
                with open(file_path, "r", encoding="utf-8") as fp:
                    lines = len(fp.readlines())
                record_result(f"Python src/{rel_path} <= 250 lines", lines <= 250, f"Có {lines} dòng (> 250)")

    # 1.3 JavaScript files in web/
    for root, dirs, files in os.walk(str(ROOT_DIR / "web")):
        for f in files:
            if f.endswith(".js"):
                file_path = Path(root) / f
                rel_path = file_path.relative_to(ROOT_DIR)
                with open(file_path, "r", encoding="utf-8") as fp:
                    lines = len(fp.readlines())
                record_result(f"JavaScript web/{rel_path} <= 250 lines", lines <= 250, f"Có {lines} dòng (> 250)")


def test_syntax_and_imports():
    print("\n--- 2. KIỂM TRA BIÊN DỊCH & IMPORTS ---")
    
    # 2.1 Compile all .py files
    py_files = []
    for shim in ["db.py", "ai_keywords.py", "edge_rewards_bot.py", "android_checkin.py", "web_server.py"]:
        py_files.append(ROOT_DIR / shim)
    for root, dirs, files in os.walk(str(ROOT_DIR / "src")):
        for f in files:
            if f.endswith(".py"):
                py_files.append(Path(root) / f)

    for pf in py_files:
        rel = pf.relative_to(ROOT_DIR)
        try:
            py_compile.compile(str(pf), doraise=True)
            record_result(f"Compile {rel}", True)
        except py_compile.PyCompileError as e:
            record_result(f"Compile {rel}", False, str(e))

    # 2.2 Import key modules
    try:
        from src.api.server import app, routes
        record_result("Import src.api.server (app, routes)", True)
    except Exception as e:
        record_result("Import src.api.server (app, routes)", False, str(e))

    try:
        from src.api.task_manager import task_mgr
        record_result("Import src.api.task_manager (task_mgr)", True)
    except Exception as e:
        record_result("Import src.api.task_manager (task_mgr)", False, str(e))

    try:
        import web_server
        record_result("Import web_server root shim", hasattr(web_server, "app"))
    except Exception as e:
        record_result("Import web_server root shim", False, str(e))


def test_integration_endpoints():
    print("\n--- 3. KIỂM TRA TÍCH HỢP WEB SERVER (TESTCLIENT) ---")
    try:
        from starlette.testclient import TestClient
        from src.api.server import app
        client = TestClient(app)

        # GET / (index.html)
        r = client.get("/")
        record_result("GET / (index.html)", r.status_code == 200 and "Microsoft Rewards Auto" in r.text)

        # Verify scripts loaded in index.html
        expected_scripts = [
            "/static/js/state.js",
            "/static/js/api.js",
            "/static/js/terminal.js",
            "/static/js/profiles.js",
            "/static/js/android.js",
            "/static/js/settings.js",
            "/static/app.js"
        ]
        all_scripts_found = all(s in r.text for s in expected_scripts)
        record_result("HTML contains all 7 modular script tags", all_scripts_found)

        # GET /api/status
        r = client.get("/api/status")
        d = r.json()
        status_ok = r.status_code == 200 and d.get("status") == "success" and "is_running" in d and "pc_is_running" in d and "android_is_running" in d
        record_result("GET /api/status (unified schema + backwards compatibility)", status_ok)

        # GET /api/profiles
        r = client.get("/api/profiles")
        d = r.json()
        record_result("GET /api/profiles", r.status_code == 200 and isinstance(d, list))

        # GET /api/config
        r = client.get("/api/config")
        d = r.json()
        config_ok = r.status_code == 200 and d.get("status") == "success" and "search_settings" in d and "android_settings" in d
        record_result("GET /api/config", config_ok)

        # GET /api/keywords
        r = client.get("/api/keywords")
        d = r.json()
        record_result("GET /api/keywords", r.status_code == 200 and d.get("status") == "success" and "count" in d)

        # GET /api/history
        r = client.get("/api/history")
        d = r.json()
        record_result("GET /api/history", r.status_code == 200 and isinstance(d, list))

        # GET /api/metadata
        r = client.get("/api/metadata")
        d = r.json()
        record_result("GET /api/metadata", r.status_code == 200 and d.get("status") == "success" and "pc_user_agent" in d)

        # GET Static assets
        r = client.get("/static/style.css")
        record_result("GET /static/style.css", r.status_code == 200)

        r = client.get("/static/js/api.js")
        record_result("GET /static/js/api.js", r.status_code == 200 and "ApiService" in r.text)

        r = client.get("/static/js/state.js")
        record_result("GET /static/js/state.js", r.status_code == 200 and "appState" in r.text)

        r = client.get("/static/app.js")
        record_result("GET /static/app.js", r.status_code == 200 and "loadStatus" in r.text)

        # GET Screenshots static mount
        r = client.get("/screenshots/android_checkin_before.png")
        record_result("GET /screenshots/android_checkin_before.png", r.status_code == 200)

    except Exception as e:
        record_result("Web Server Integration Tests", False, str(e))


def main():
    print("=" * 65)
    print("🧪 TỰ KIỂM TRA TOÀN DIỆN GIAI ĐOẠN 3 (SELF-AUDIT GD3)")
    print("=" * 65)

    test_line_limits()
    test_syntax_and_imports()
    test_integration_endpoints()

    print("\n" + "=" * 65)
    print(f"KẾT QUẢ TỰ KIỂM TRA: {passed_tests} PASS / {failed_tests} FAIL")
    print("=" * 65)

    if failed_tests > 0:
        print(f"\n❌ Có {failed_tests} kiểm tra THẤT BẠI. Cần sửa lỗi ngay!")
        sys.exit(1)
    else:
        print("\n🎉 100% KIỂM TRA ĐẠT TIÊU CHUẨN! HỆ THỐNG GIAI ĐOẠN 3 HOÀN HẢO!")
        sys.exit(0)


if __name__ == "__main__":
    main()
