# -*- coding: utf-8 -*-
"""
Web Server Dashboard - Hệ thống Quản lý Đa Tài khoản Microsoft Rewards
Backend API & WebSocket server sử dụng Starlette & Uvicorn
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from collections import deque
from datetime import datetime

# Đảm bảo console Windows hỗ trợ tiếng Việt
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(SCRIPT_DIR, "web")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
KEYWORDS_PATH = os.path.join(SCRIPT_DIR, "keywords.txt")

# Import các hàm tiện ích từ bot
sys.path.insert(0, SCRIPT_DIR)
from edge_rewards_bot import (
    load_config,
    get_profile_abs_path,
    kill_zombie_edge_processes,
    open_browser_for_login
)


class BotTaskManager:
    def __init__(self):
        self.is_running = False
        self.current_process = None
        self.current_task_info = None
        self.stop_requested = False
        self.log_history = deque(maxlen=600)
        self.active_websockets = set()
        self.task_runner_future = None

    def add_log(self, text: str, log_type: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {
            "time": timestamp,
            "text": text,
            "type": log_type
        }
        self.log_history.append(entry)
        asyncio.create_task(self.broadcast_log(entry))

    async def broadcast_log(self, entry: dict):
        if not self.active_websockets:
            return
        dead_ws = set()
        payload = json.dumps(entry, ensure_ascii=False)
        for ws in self.active_websockets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_ws.add(ws)
        for ws in dead_ws:
            self.active_websockets.discard(ws)

    async def run_bot_sequence(self, profiles_to_run: list, mode: str):
        self.is_running = True
        self.stop_requested = False
        total_accs = len(profiles_to_run)
        
        self.add_log(f"🚀 [HỆ THỐNG] Bắt đầu phiên chạy cho {total_accs} tài khoản. Chế độ: {mode.upper()}", "start")
        
        for idx, profile in enumerate(profiles_to_run):
            if self.stop_requested:
                self.add_log("🛑 [HỆ THỐNG] Nhận lệnh dừng khẩn cấp. Kết thúc chuỗi tác vụ!", "warn")
                break

            p_id = profile.get("id", str(idx + 1))
            p_name = profile.get("name", f"Profile {p_id}")
            p_dir = get_profile_abs_path(profile)

            self.current_task_info = {
                "profile_id": p_id,
                "profile_name": p_name,
                "current_index": idx + 1,
                "total_profiles": total_accs,
                "mode": mode,
                "status": "running"
            }

            self.add_log(f"\n=======================================================", "info")
            self.add_log(f"▶️ [BƯỚC {idx + 1}/{total_accs}] BẮT ĐẦU: {p_name}", "start")
            self.add_log(f"=======================================================", "info")

            cmd = [
                sys.executable,
                "-u",
                os.path.join(SCRIPT_DIR, "edge_rewards_bot.py"),
                "--profile", p_id,
                "--mode", mode,
                "--non-interactive"
            ]

            try:
                self.current_process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=SCRIPT_DIR
                )

                while True:
                    line = await self.current_process.stdout.readline()
                    if not line:
                        break
                    decoded_line = line.decode("utf-8", errors="replace").rstrip()
                    if decoded_line:
                        # Phân loại màu log
                        ltype = "info"
                        if "[!]" in decoded_line or "Lỗi" in decoded_line or "Error" in decoded_line:
                            ltype = "error"
                        elif "[✓]" in decoded_line or "thành công" in decoded_line or "HOÀN TẤT" in decoded_line:
                            ltype = "success"
                        elif "⏳" in decoded_line or "[*]" in decoded_line or "Tạm nghỉ" in decoded_line:
                            ltype = "warn"
                        elif "🖥️" in decoded_line or "📱" in decoded_line or "👆" in decoded_line:
                            ltype = "action"
                        
                        self.add_log(decoded_line, ltype)

                await self.current_process.wait()
                exit_code = self.current_process.returncode

                if self.stop_requested:
                    self.add_log(f"🛑 Đã hủy tiến trình {p_name}.", "warn")
                    break

                if exit_code == 0:
                    self.add_log(f"✅ [HOÀN TẤT] {p_name} đã hoàn thành lượt tìm kiếm!", "success")
                else:
                    self.add_log(f"⚠️ {p_name} kết thúc với mã {exit_code}.", "warn")

            except Exception as e:
                self.add_log(f"❌ [LỖI TIẾN TRÌNH] {p_name}: {e}", "error")
            finally:
                self.current_process = None
                kill_zombie_edge_processes(p_dir)

            # Nghỉ an toàn giữa 2 profile nếu còn profile tiếp theo
            if idx < total_accs - 1 and not self.stop_requested:
                cooldown_secs = 15
                self.add_log(f"⏳ Tạm dừng an toàn {cooldown_secs}s trước khi chuyển sang tài khoản tiếp theo...", "warn")
                for c in range(cooldown_secs, 0, -1):
                    if self.stop_requested:
                        break
                    await asyncio.sleep(1)

        self.is_running = False
        self.current_task_info = None
        self.add_log("🎉 [HỆ THỐNG] Toàn bộ tác vụ đã kết thúc. Sẵn sàng cho phiên tiếp theo!\n", "success")

    def stop_bot(self):
        self.stop_requested = True
        if self.current_process:
            try:
                self.current_process.terminate()
            except Exception:
                pass
        self.is_running = False
        self.current_task_info = None
        self.add_log("🛑 [HỆ THỐNG] Đã yêu cầu dừng toàn bộ tác vụ!", "error")
        # Quét và dọn dẹp các tiến trình Edge của bot
        try:
            cfg = load_config()
            for p in cfg.get("profiles", []):
                p_dir = get_profile_abs_path(p)
                kill_zombie_edge_processes(p_dir)
        except Exception:
            pass


task_mgr = BotTaskManager()


# ====================================================================
# API CONTROLLERS
# ====================================================================

async def get_status(request):
    """Lấy trạng thái hoạt động hiện tại"""
    return JSONResponse({
        "is_running": task_mgr.is_running,
        "current_task": task_mgr.current_task_info,
        "logs_count": len(task_mgr.log_history)
    })


async def get_profiles(request):
    """Lấy danh sách các profile và trạng thái"""
    cfg = load_config()
    profiles = cfg.get("profiles", [])
    result = []
    for p in profiles:
        p_dir = get_profile_abs_path(p)
        dir_exists = os.path.exists(p_dir)
        result.append({
            "id": p.get("id"),
            "name": p.get("name", f"Profile {p.get('id')}"),
            "path": p.get("path", ""),
            "profile_directory": p.get("profile_directory", "Default"),
            "exists": dir_exists
        })
    return JSONResponse(result)


async def add_profile(request):
    """Thêm tài khoản profile mới"""
    data = await request.json()
    cfg = load_config()
    profiles = cfg.get("profiles", [])
    
    # Tự động tạo ID mới
    existing_ids = [int(p.get("id")) for p in profiles if str(p.get("id", "")).isdigit()]
    next_id = str(max(existing_ids) + 1) if existing_ids else "1"
    
    name = data.get("name") or f"Profile {next_id} (Tài khoản {next_id})"
    custom_path = data.get("path")
    if not custom_path:
        custom_path = f"./edge_profile_{next_id}" if next_id != "1" else "./edge_profile"

    new_p = {
        "id": next_id,
        "name": name,
        "path": custom_path,
        "profile_directory": "Default"
    }
    profiles.append(new_p)
    cfg["profiles"] = profiles

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    task_mgr.add_log(f"➕ [CẤU HÌNH] Đã thêm tài khoản mới: {name} ({custom_path})", "info")
    return JSONResponse({"status": "success", "profile": new_p})


async def update_profile(request):
    """Cập nhật thông tin profile"""
    p_id = request.path_params.get("id")
    data = await request.json()
    cfg = load_config()
    profiles = cfg.get("profiles", [])
    
    updated = False
    for p in profiles:
        if str(p.get("id")) == str(p_id):
            if "name" in data and data["name"]:
                p["name"] = data["name"]
            if "path" in data and data["path"]:
                p["path"] = data["path"]
            updated = True
            break

    if updated:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return JSONResponse({"status": "success"})
    return JSONResponse({"status": "not_found"}, status_code=404)


async def delete_profile(request):
    """Xóa profile khỏi danh sách"""
    p_id = request.path_params.get("id")
    cfg = load_config()
    profiles = cfg.get("profiles", [])
    
    new_profiles = [p for p in profiles if str(p.get("id")) != str(p_id)]
    if len(new_profiles) == len(profiles):
        return JSONResponse({"status": "not_found"}, status_code=404)

    cfg["profiles"] = new_profiles
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    task_mgr.add_log(f"🗑️ [CẤU HÌNH] Đã xóa Profile ID {p_id} khỏi danh sách.", "warn")
    return JSONResponse({"status": "success"})


async def unlock_profile(request):
    """Mở khóa và dọn dẹp tiến trình zombie cho profile"""
    p_id = request.path_params.get("id")
    cfg = load_config()
    matched = [p for p in cfg.get("profiles", []) if str(p.get("id")) == str(p_id)]
    if matched:
        p_dir = get_profile_abs_path(matched[0])
        kill_zombie_edge_processes(p_dir)
        task_mgr.add_log(f"🧹 [DỌN DẸP] Đã giải phóng lock file & đóng tiến trình treo cho {matched[0].get('name')}.", "success")
        return JSONResponse({"status": "success"})
    return JSONResponse({"status": "not_found"}, status_code=404)


async def login_profile(request):
    """Mở trình duyệt Edge với GUI để người dùng đăng nhập tài khoản / kiểm tra điểm"""
    p_id = request.path_params.get("id")
    cfg = load_config()
    matched = [p for p in cfg.get("profiles", []) if str(p.get("id")) == str(p_id)]
    if not matched:
        return JSONResponse({"status": "not_found"}, status_code=404)

    target_profile = matched[0]
    task_mgr.add_log(f"🔑 [ĐĂNG NHẬP] Đang mở trình duyệt Edge cho {target_profile.get('name')}...", "start")

    # Mở Edge độc lập trong tiến trình nền không chặn
    proc = open_browser_for_login(target_profile, config=cfg)
    if proc:
        task_mgr.add_log(f"👉 [ĐĂNG NHẬP] Cửa sổ Edge đã mở. Hãy đăng nhập tài khoản và đóng cửa sổ khi xong.", "info")
        return JSONResponse({"status": "success", "message": "Edge opened"})
    else:
        task_mgr.add_log("❌ [LỖI] Không thể khởi động Microsoft Edge.", "error")
        return JSONResponse({"status": "error"}, status_code=500)


async def run_task(request):
    """Kích hoạt chạy bot"""
    if task_mgr.is_running:
        return JSONResponse({"status": "error", "message": "Bot đang bận chạy một tác vụ khác!"}, status_code=400)

    data = await request.json()
    profile_choice = data.get("profile", "all")
    mode = data.get("mode", "all")

    cfg = load_config()
    profiles = cfg.get("profiles", [])
    if not profiles:
        return JSONResponse({"status": "error", "message": "Chưa có tài khoản nào được cấu hình!"}, status_code=400)

    if profile_choice == "all":
        profiles_to_run = profiles
    else:
        matched = [p for p in profiles if str(p.get("id")) == str(profile_choice)]
        if not matched:
            return JSONResponse({"status": "error", "message": f"Không tìm thấy Profile {profile_choice}"}, status_code=404)
        profiles_to_run = matched

    # Khởi động background sequence
    asyncio.create_task(task_mgr.run_bot_sequence(profiles_to_run, mode))
    return JSONResponse({"status": "started", "count": len(profiles_to_run), "mode": mode})


async def stop_task(request):
    """Dừng bot khẩn cấp"""
    task_mgr.stop_bot()
    return JSONResponse({"status": "stopped"})


async def get_config_endpoint(request):
    """Lấy cấu hình tìm kiếm và browser"""
    cfg = load_config()
    return JSONResponse({
        "search_settings": cfg.get("search_settings", {}),
        "browser_settings": cfg.get("browser_settings", {})
    })


async def save_config_endpoint(request):
    """Lưu cấu hình tìm kiếm và browser"""
    data = await request.json()
    cfg = load_config()
    if "search_settings" in data:
        cfg["search_settings"].update(data["search_settings"])
    if "browser_settings" in data:
        cfg["browser_settings"].update(data["browser_settings"])

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    task_mgr.add_log("💾 [CẤU HÌNH] Đã cập nhật cài đặt tìm kiếm.", "info")
    return JSONResponse({"status": "success"})


async def get_keywords_endpoint(request):
    """Lấy danh sách từ khóa"""
    content = ""
    lines_count = 0
    if os.path.exists(KEYWORDS_PATH):
        with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        lines_count = len([l for l in content.splitlines() if l.strip() and not l.strip().startswith("#")])
    return JSONResponse({"content": content, "count": lines_count})


async def save_keywords_endpoint(request):
    """Lưu danh sách từ khóa"""
    data = await request.json()
    content = data.get("content", "")
    with open(KEYWORDS_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    lines_count = len([l for l in content.splitlines() if l.strip() and not l.strip().startswith("#")])
    task_mgr.add_log(f"💾 [TỪ KHÓA] Đã cập nhật kho từ khóa ({lines_count} từ khóa hợp lệ).", "info")
    return JSONResponse({"status": "success", "count": lines_count})


async def get_logs_endpoint(request):
    """Lấy lịch sử log gần nhất"""
    return JSONResponse(list(task_mgr.log_history))


async def clear_logs_endpoint(request):
    """Xóa màn hình log"""
    task_mgr.log_history.clear()
    return JSONResponse({"status": "cleared"})


async def websocket_logs(websocket: WebSocket):
    """WebSocket stream log trực tiếp"""
    await websocket.accept()
    task_mgr.active_websockets.add(websocket)
    try:
        # Gửi toàn bộ log gần nhất cho client mới kết nối
        for entry in list(task_mgr.log_history):
            await websocket.send_text(json.dumps(entry, ensure_ascii=False))
        while True:
            # Giữ kết nối mở
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        task_mgr.active_websockets.discard(websocket)


async def serve_index(request):
    """Phục vụ file index.html chính"""
    index_file = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"error": "Web UI index.html not found"}, status_code=404)


# Thiết lập các routes
routes = [
    Route("/", serve_index),
    Route("/api/status", get_status, methods=["GET"]),
    Route("/api/profiles", get_profiles, methods=["GET"]),
    Route("/api/profiles", add_profile, methods=["POST"]),
    Route("/api/profiles/{id}", update_profile, methods=["PUT"]),
    Route("/api/profiles/{id}", delete_profile, methods=["DELETE"]),
    Route("/api/profiles/{id}/unlock", unlock_profile, methods=["POST"]),
    Route("/api/profiles/{id}/login", login_profile, methods=["POST"]),
    Route("/api/run", run_task, methods=["POST"]),
    Route("/api/stop", stop_task, methods=["POST"]),
    Route("/api/config", get_config_endpoint, methods=["GET", "POST"]),
    Route("/api/keywords", get_keywords_endpoint, methods=["GET", "POST"]),
    Route("/api/logs", get_logs_endpoint, methods=["GET"]),
    Route("/api/logs/clear", clear_logs_endpoint, methods=["POST"]),
    WebSocketRoute("/ws/logs", websocket_logs),
]

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

# Mount thư mục tĩnh nếu tồn tại
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def main():
    port = 5000
    print("=" * 65)
    print("🚀 MICROSOFT REWARDS AUTO BOT - WEB UI SERVER")
    print(f"👉 Đang chạy tại địa chỉ: http://127.0.0.1:{port}")
    print("=" * 65)
    
    # Tự động mở trình duyệt sau 1.5 giây
    def open_browser():
        time.sleep(1.2)
        try:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception:
            pass
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
