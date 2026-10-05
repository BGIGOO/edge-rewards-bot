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
    open_browser_for_login,
    check_profile_points
)
import db
db.init_db()


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


def get_edge_account_email(profile_dict):
    """Tự động phát hiện email tài khoản Microsoft/Edge đã đăng nhập trong thư mục profile"""
    try:
        pdir = get_profile_abs_path(profile_dict)
        pdir_name = profile_dict.get("profile_directory", "Default")

        # 1. Kiểm tra trong chính thư mục bot profile (Local State)
        ls_path = os.path.join(pdir, "Local State")
        if os.path.exists(ls_path):
            try:
                with open(ls_path, "r", encoding="utf-8", errors="ignore") as f:
                    ls = json.load(f)
                    info_cache = ls.get("profile", {}).get("info_cache", {})
                    if pdir_name in info_cache:
                        u = info_cache[pdir_name].get("user_name")
                        if u and "@" in u:
                            return u
            except Exception:
                pass

        # 2. Kiểm tra Preferences trong pdir_name hoặc thư mục Default của bot profile
        for sub in [pdir_name, "Default"]:
            pref_path = os.path.join(pdir, sub, "Preferences")
            if os.path.exists(pref_path):
                try:
                    with open(pref_path, "r", encoding="utf-8", errors="ignore") as f:
                        d = json.load(f)
                        for a in d.get("account_info", []):
                            em = a.get("email")
                            if em and "@" in em:
                                return em
                except Exception:
                    pass
    except Exception:
        pass
    return None


async def get_profiles(request):
    """Lấy danh sách các profile và trạng thái từ SQLite, tự động nhận diện email đã đăng nhập"""
    profiles = db.get_all_profiles()
    result = []

    for p in profiles:
        p_dir = get_profile_abs_path(p)
        dir_exists = os.path.exists(p_dir)
        email = get_edge_account_email(p)

        name = p.get("name", "")
        # Nếu phát hiện email hợp lệ đã đăng nhập mà profile chưa có email hoặc đang là unlogged
        if email:
            if not p.get("email") or p.get("status") == "unlogged" or name.startswith("Chưa đăng nhập"):
                p["email"] = email
                p["name"] = email
                p["status"] = "ready"
                db.update_profile_db(p["id"], name=email, email=email, status="ready")
        else:
            # Nếu chưa có email và tên không phải là email
            if not p.get("email") and "@" not in name:
                if p.get("status") != "unlogged":
                    p["status"] = "unlogged"
                    db.update_profile_db(p["id"], status="unlogged")

        result.append({
            "id": str(p.get("id")),
            "name": p.get("name"),
            "email": p.get("email") or "",
            "path": p.get("path", ""),
            "profile_directory": p.get("profile_directory", "Default"),
            "status": p.get("status", "ready"),
            "total_points": p.get("total_points", 0) or 0,
            "today_points": p.get("today_points", 0) or 0,
            "desktop_points": p.get("desktop_points") or "0/90",
            "mobile_points": p.get("mobile_points") or "0/60",
            "offers_points": p.get("offers_points", 0) or 0,
            "last_run": p.get("last_run", ""),
            "exists": dir_exists
        })

    return JSONResponse(result)


async def add_profile(request):
    """Thêm tài khoản profile mới vào SQLite và đồng bộ config"""
    data = await request.json()
    name = data.get("name")
    custom_path = data.get("path")
    prof_dir = data.get("profile_directory", "Default")

    new_p = db.add_profile_db(name=name, custom_path=custom_path, profile_directory=prof_dir)
    task_mgr.add_log(f"➕ [CẤU HÌNH] Đã thêm tài khoản mới vào Database: {new_p['name']} ({new_p['path']})", "info")
    return JSONResponse({"status": "success", "profile": new_p})


async def update_profile(request):
    """Cập nhật thông tin profile trong SQLite"""
    p_id = request.path_params.get("id")
    data = await request.json()
    updated = db.update_profile_db(p_id, name=data.get("name"), custom_path=data.get("path"))
    if updated:
        return JSONResponse({"status": "success", "profile": updated})
    return JSONResponse({"status": "not_found"}, status_code=404)


async def delete_profile(request):
    """Xóa profile khỏi SQLite"""
    p_id = request.path_params.get("id")
    success = db.delete_profile_db(p_id)
    if not success:
        return JSONResponse({"status": "not_found"}, status_code=404)

    task_mgr.add_log(f"🗑️ [CẤU HÌNH] Đã xóa Profile ID #{p_id} khỏi Database.", "warn")
    return JSONResponse({"status": "success"})


async def unlock_profile(request):
    """Mở khóa và dọn dẹp tiến trình zombie cho profile"""
    p_id = request.path_params.get("id")
    target = db.get_profile_by_id(p_id)
    if not target:
        cfg = load_config()
        matched = [p for p in cfg.get("profiles", []) if str(p.get("id")) == str(p_id)]
        if matched:
            target = matched[0]
    if target:
        p_dir = get_profile_abs_path(target)
        kill_zombie_edge_processes(p_dir)
        task_mgr.add_log(f"🧹 [DỌN DẸP] Đã giải phóng lock file & đóng tiến trình treo cho {target.get('name')}.", "success")
        return JSONResponse({"status": "success"})
    return JSONResponse({"status": "not_found"}, status_code=404)


async def login_profile(request):
    """Mở trình duyệt Edge với GUI để người dùng đăng nhập tài khoản / kiểm tra điểm"""
    p_id = request.path_params.get("id")
    target_profile = db.get_profile_by_id(p_id)
    if not target_profile:
        cfg = load_config()
        matched = [p for p in cfg.get("profiles", []) if str(p.get("id")) == str(p_id)]
        if matched:
            target_profile = matched[0]
    if not target_profile:
        return JSONResponse({"status": "not_found"}, status_code=404)

    task_mgr.add_log(f"🔑 [ĐĂNG NHẬP] Đang mở trình duyệt Edge cho {target_profile.get('name')}...", "start")

    # Mở Edge độc lập trong tiến trình nền không chặn
    proc = open_browser_for_login(target_profile)
    if proc:
        task_mgr.add_log(f"👉 [ĐĂNG NHẬP] Cửa sổ Edge đã mở. Hãy đăng nhập tài khoản và đóng cửa sổ khi xong.", "info")
        return JSONResponse({"status": "success", "message": "Edge opened"})
    else:
        task_mgr.add_log("❌ [LỖI] Không thể khởi động Microsoft Edge.", "error")
        return JSONResponse({"status": "error"}, status_code=500)


async def check_profile_endpoint(request):
    """Kiểm tra điểm thực tế trên Bing Rewards cho DUY NHẤT 1 tài khoản chỉ định (An toàn, chống ban)"""
    p_id = request.path_params.get("id")
    target_profile = db.get_profile_by_id(p_id)
    if not target_profile:
        cfg = load_config()
        matched = [p for p in cfg.get("profiles", []) if str(p.get("id")) == str(p_id)]
        if matched:
            target_profile = matched[0]

    if not target_profile:
        return JSONResponse({"status": "error", "message": "Không tìm thấy hồ sơ tài khoản"}, status_code=404)

    # Nếu tài khoản này đang chạy tìm kiếm
    if task_mgr.is_running and task_mgr.current_task_info and str(task_mgr.current_task_info.get("profile_id")) == str(p_id):
        return JSONResponse({
            "status": "error", 
            "message": f"Tài khoản {target_profile.get('name')} đang trong phiên chạy bot. Vui lòng đợi bot chạy xong trước khi check điểm!"
        }, status_code=400)

    p_name = target_profile.get("name", f"Profile {p_id}")
    task_mgr.add_log(f"🔍 [CHECK ĐIỂM] Đang kết nối kiểm tra điểm thực tế cho {p_name}...", "start")

    loop = asyncio.get_event_loop()
    # Chạy trong executor để không làm nghẽn event loop của web server
    res = await loop.run_in_executor(None, check_profile_points, target_profile)

    if res.get("success"):
        d = res.get("data", {})
        today_p = d.get('today_points', 0)
        pc_p = d.get('desktop_points', '0/90')
        mob_p = d.get('mobile_points', '0/60')
        tot_p = d.get('total_points', 0)
        task_mgr.add_log(
            f"⭐ [ĐIỂM REWARDS] {p_name}: Hôm nay +{today_p} pts | PC: {pc_p} | Mobile: {mob_p} | Tổng tích lũy: {tot_p} pts",
            "success"
        )
        return JSONResponse({
            "status": "success",
            "profile": res.get("profile"),
            "data": d
        })
    else:
        err_msg = res.get("message", "Không thể kiểm tra điểm")
        task_mgr.add_log(f"❌ [CHECK ĐIỂM THẤT BẠI] {p_name}: {err_msg}", "error")
        return JSONResponse({
            "status": "error",
            "message": err_msg
        }, status_code=400)



async def get_history_endpoint(request):
    """Lấy danh sách lịch sử chạy từ SQLite"""
    return JSONResponse(db.get_recent_history(30))


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
        profiles_to_run = [
            p for p in profiles 
            if p.get("status") != "unlogged" and ("@" in str(p.get("name", "")) or p.get("email"))
        ]
        if not profiles_to_run:
            return JSONResponse({
                "status": "error", 
                "message": "Không có tài khoản nào đã đăng nhập! Vui lòng bấm 'Đăng nhập' cho ít nhất 1 tài khoản trước khi chạy."
            }, status_code=400)
    else:
        matched = [p for p in profiles if str(p.get("id")) == str(profile_choice)]
        if not matched:
            return JSONResponse({"status": "error", "message": f"Không tìm thấy Profile {profile_choice}"}, status_code=404)
        target = matched[0]
        if target.get("status") == "unlogged" or not ("@" in str(target.get("name", "")) or target.get("email")):
            return JSONResponse({
                "status": "error",
                "message": f"Tài khoản #{profile_choice} ({target.get('name')}) chưa đăng nhập! Vui lòng bấm 'Đăng nhập' trên bảng điều khiển trước."
            }, status_code=400)
        profiles_to_run = matched

    # Khởi động background sequence
    asyncio.create_task(task_mgr.run_bot_sequence(profiles_to_run, mode))
    return JSONResponse({"status": "started", "count": len(profiles_to_run), "mode": mode})


async def stop_task(request):
    """Dừng bot khẩn cấp"""
    task_mgr.stop_bot()
    return JSONResponse({"status": "stopped"})


async def stop_profile_task(request):
    """Dừng tìm kiếm cho profile cụ thể"""
    p_id = request.path_params.get("id")
    cfg = load_config()
    matched = [p for p in cfg.get("profiles", []) if str(p.get("id")) == str(p_id)]
    p_name = matched[0].get("name", f"Profile {p_id}") if matched else f"Profile {p_id}"
    
    stopped = False
    if task_mgr.is_running and task_mgr.current_task_info and str(task_mgr.current_task_info.get("profile_id")) == str(p_id):
        task_mgr.stop_bot()
        task_mgr.add_log(f"🛑 [DỪNG PROFILE] Đã dừng tìm kiếm cho {p_name}!", "warn")
        stopped = True
    else:
        # Nếu profile này đang mở trình duyệt hoặc có tiến trình Edge treo
        if matched:
            p_dir = get_profile_abs_path(matched[0])
            kill_zombie_edge_processes(p_dir)
            task_mgr.add_log(f"🛑 [DỪNG PROFILE] Đã đóng tiến trình Edge của {p_name}.", "warn")
            stopped = True

    return JSONResponse({"status": "success", "stopped": stopped, "profile_id": p_id})


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


cached_ip_info = {"ip": "1.52.0.121", "last_check": 0}

async def get_metadata_endpoint(request):
    """Lấy thông tin IP, Headers và Metadata môi trường chạy"""
    now = time.time()
    if now - cached_ip_info.get("last_check", 0) > 300:
        try:
            import urllib.request
            req = urllib.request.Request("https://api.ipify.org?format=json", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                if data.get("ip"):
                    cached_ip_info["ip"] = data["ip"]
                    cached_ip_info["last_check"] = now
        except Exception:
            pass

    cfg = load_config()
    search_cfg = cfg.get("search_settings", {})
    return JSONResponse({
        "ip": cached_ip_info.get("ip", "1.52.0.121"),
        "location": "Vietnam (VN)",
        "proxy": "Direct (None)",
        "pc_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "mobile_user_agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 EdgA/131.0.0.0",
        "delay": f"{search_cfg.get('min_delay_seconds', 12)}s - {search_cfg.get('max_delay_seconds', 22)}s",
        "client_hints": {
            "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
    })


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
    Route("/api/profiles/{id}/check", check_profile_endpoint, methods=["POST"]),
    Route("/api/profiles/{id}/stop", stop_profile_task, methods=["POST"]),
    Route("/api/run", run_task, methods=["POST"]),
    Route("/api/stop", stop_task, methods=["POST"]),
    Route("/api/config", get_config_endpoint, methods=["GET", "POST"]),
    Route("/api/keywords", get_keywords_endpoint, methods=["GET", "POST"]),
    Route("/api/logs", get_logs_endpoint, methods=["GET"]),
    Route("/api/logs/clear", clear_logs_endpoint, methods=["POST"]),
    Route("/api/history", get_history_endpoint, methods=["GET"]),
    Route("/api/metadata", get_metadata_endpoint, methods=["GET"]),
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
