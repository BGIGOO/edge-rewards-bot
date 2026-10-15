# -*- coding: utf-8 -*-
"""
src/api/server.py
=================
Khoi tao Starlette App, dang ky routes, mount static directories va khoi chay Uvicorn.
Tuan thu rule 01_architecture (< 250 dong) va rule 03_web_fullstack.
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
import uvicorn

from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from src.core.paths import WEB_DIR, SCREENSHOTS_DIR
from src.api.routes_profiles import (
    get_profiles, add_profile, update_profile, delete_profile,
    unlock_profile, login_profile, check_profile_endpoint, stop_profile_task
)
from src.api.routes_edge import (
    run_task, stop_task, get_keywords_endpoint,
    save_keywords_endpoint, generate_ai_keywords_endpoint
)
from src.api.routes_android import (
    run_android_endpoint, stop_android_endpoint, get_android_status_endpoint,
    open_android_app_endpoint, close_android_app_endpoint, reconnect_android_endpoint,
    turn_on_android_screen_endpoint, turn_off_android_screen_endpoint, toggle_android_screen_endpoint
)
from src.api.routes_system import (
    get_status, get_history_endpoint, get_config_endpoint, save_config_endpoint,
    get_logs_endpoint, clear_logs_endpoint, websocket_logs, serve_index, get_metadata_endpoint
)

routes = [
    Route("/", serve_index),
    Route("/api/status", get_status, methods=["GET"]),
    Route("/api/profiles", get_profiles, methods=["GET"]),
    Route("/api/profiles", add_profile, methods=["POST"]),
    Route("/api/profiles/{id}", update_profile, methods=["PUT"]),
    Route("/api/profiles/{id}", delete_profile, methods=["DELETE"]),
    Route("/api/profiles/{id}/unlock", unlock_profile, methods=["POST"]),
    Route("/api/profiles/{id}/login", login_profile, methods=["POST"]),
    Route("/api/profiles/{id}/check", check_profile_endpoint, methods=["POST"]),
    Route("/api/profiles/{id}/stop", stop_profile_task, methods=["POST"]),
    Route("/api/run", run_task, methods=["POST"]),
    Route("/api/stop", stop_task, methods=["POST"]),
    Route("/api/config", get_config_endpoint, methods=["GET"]),
    Route("/api/config", save_config_endpoint, methods=["POST"]),
    Route("/api/keywords", get_keywords_endpoint, methods=["GET"]),
    Route("/api/keywords", save_keywords_endpoint, methods=["POST"]),
    Route("/api/keywords/generate-ai", generate_ai_keywords_endpoint, methods=["POST"]),
    Route("/api/logs", get_logs_endpoint, methods=["GET"]),
    Route("/api/logs/clear", clear_logs_endpoint, methods=["POST"]),
    Route("/api/history", get_history_endpoint, methods=["GET"]),
    Route("/api/android/checkin", run_android_endpoint, methods=["POST"]),
    Route("/api/android/stop", stop_android_endpoint, methods=["POST"]),
    Route("/api/android/status", get_android_status_endpoint, methods=["GET"]),
    Route("/api/android/app/open", open_android_app_endpoint, methods=["POST"]),
    Route("/api/android/app/close", close_android_app_endpoint, methods=["POST"]),
    Route("/api/android/screen/on", turn_on_android_screen_endpoint, methods=["POST"]),
    Route("/api/android/screen/off", turn_off_android_screen_endpoint, methods=["POST"]),
    Route("/api/android/screen/toggle", toggle_android_screen_endpoint, methods=["POST"]),
    Route("/api/android/connect", reconnect_android_endpoint, methods=["POST"]),
    Route("/api/metadata", get_metadata_endpoint, methods=["GET"]),
    WebSocketRoute("/ws/logs", websocket_logs),
]

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")


def free_port(port: int = 5000) -> None:
    """Tu dong giai phong port neu co tien trinh cu chiem giu."""
    try:
        curr_pid = os.getpid()
        ps_cmd = (
            f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
            f"Where-Object {{ $_.OwningProcess -ne {curr_pid} }} | "
            f"ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=5)
        time.sleep(0.3)
    except Exception:
        pass


def main():
    port = 5000
    free_port(port)
    print("=" * 65)
    print("🚀 MICROSOFT REWARDS AUTO BOT - WEB UI SERVER")
    print(f"👉 Đang chạy tại địa chỉ: http://127.0.0.1:{port}")
    print("=" * 65)

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except (KeyboardInterrupt, SystemExit):
        print("\n[*] Đã nhận lệnh dừng Web Server.")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Lỗi Uvicorn: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
