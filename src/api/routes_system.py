# -*- coding: utf-8 -*-
"""
src/api/routes_system.py
========================
Cac endpoint he thong: trang thai, config, logs, WebSocket stream, static index.html va metadata.
Tuan thu rule 01_architecture (< 250 dong) va rule 03_web_fullstack.
"""

import os
import json
import time
from starlette.responses import JSONResponse, FileResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from src.core.paths import WEB_DIR, CONFIG_PATH
from src.core import db
from src.bots.edge.runner import load_config
from src.api.task_manager import task_mgr


async def get_status(request):
    """Lay trang thai tong the he thong."""
    return JSONResponse({
        "status": "success",
        "is_running": task_mgr.is_running,
        "pc_is_running": task_mgr.pc_is_running,
        "android_is_running": task_mgr.android_is_running,
        "current_task": task_mgr.pc_task_info,
        "android_task": task_mgr.android_task_info,
        "logs_count": len(task_mgr.log_history)
    })


async def get_history_endpoint(request):
    """Lay lich su cac phien chay bot."""
    history = db.get_recent_history()
    return JSONResponse(history)


async def get_config_endpoint(request):
    """Lay cau hinh tim kiem, browser va android."""
    cfg = load_config()
    return JSONResponse({
        "status": "success",
        "search_settings": cfg.get("search_settings", {}),
        "browser_settings": cfg.get("browser_settings", {}),
        "android_settings": cfg.get("android_settings", {})
    })


async def save_config_endpoint(request):
    """Luu cau hinh tim kiem, browser va android."""
    try:
        data = await request.json()
        cfg = load_config()
        if "search_settings" in data:
            cfg["search_settings"].update(data["search_settings"])
        if "browser_settings" in data:
            cfg["browser_settings"].update(data["browser_settings"])
        if "android_settings" in data:
            if "android_settings" not in cfg:
                cfg["android_settings"] = {}
            cfg["android_settings"].update(data["android_settings"])

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

        task_mgr.add_log("💾 [CẤU HÌNH] Đã cập nhật cài đặt hệ thống.", "info")
        return JSONResponse({"status": "success", "message": "Đã lưu cấu hình thành công"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def get_logs_endpoint(request):
    """Lay lich su log gan nhat."""
    return JSONResponse(list(task_mgr.log_history))


async def clear_logs_endpoint(request):
    """Xoa man hinh log."""
    task_mgr.log_history.clear()
    return JSONResponse({"status": "success", "message": "Đã xóa buffer log"})


async def websocket_logs(websocket: WebSocket):
    """WebSocket stream log truc tiep."""
    await websocket.accept()
    task_mgr.active_websockets.add(websocket)
    try:
        for entry in list(task_mgr.log_history):
            await websocket.send_text(json.dumps(entry, ensure_ascii=False))
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        task_mgr.active_websockets.discard(websocket)


async def serve_index(request):
    """Phuc vu file index.html chinh cua Frontend."""
    index_file = os.path.join(str(WEB_DIR), "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"status": "error", "message": "index.html not found"}, status_code=404)


cached_ip_info = {"ip": "1.52.0.121", "last_check": 0}


async def get_metadata_endpoint(request):
    """Lay thong tin IP, Headers va metadata moi truong chay."""
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
        "status": "success",
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
