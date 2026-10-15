# -*- coding: utf-8 -*-
"""
src/api/routes_android.py
=========================
Cac endpoint dieu khien thiet bi Android qua ADB: diem danh, bat/tat man hinh, mo/dong app.
Tuan thu rule 01_architecture (< 250 dong) va rule 03_web_fullstack.
"""

import asyncio
from starlette.responses import JSONResponse

from src.core import db
from src.bots.edge.runner import load_config
from src.bots.android.checkin_flow import AndroidBingCheckinBot
from src.api.task_manager import task_mgr


async def run_android_endpoint(request):
    if task_mgr.android_is_running:
        return JSONResponse({"status": "error", "message": "Tiến trình điểm danh Android đang chạy rồi!"}, status_code=400)
    asyncio.create_task(task_mgr.run_android_checkin())
    return JSONResponse({"status": "success", "message": "Đã bắt đầu tiến trình điểm danh Android song song!"})


async def stop_android_endpoint(request):
    task_mgr.stop_android_bot()
    return JSONResponse({"status": "success", "message": "Đã yêu cầu dừng điểm danh Android!"})


async def get_android_status_endpoint(request):
    latest = db.get_latest_android_checkin()
    cfg = load_config()
    android_cfg = cfg.get("android_settings", {})
    dev = android_cfg.get("device_address", "100.71.117.39:5555")
    pkg = android_cfg.get("package_name", "com.microsoft.bing")

    loop = asyncio.get_event_loop()
    def _check():
        bot = AndroidBingCheckinBot(device=dev, package=pkg)
        return bot.get_device_status()

    try:
        dev_status = await asyncio.wait_for(loop.run_in_executor(None, _check), timeout=6.0)
    except Exception as e:
        dev_status = {
            "ping_ok": False, "ping_ms": None, "adb_state": "timeout",
            "is_connected": False, "app_status": "unreachable", "app_running": False,
            "screen_awake": None, "screen_unlocked": None, "message": f"Timeout hoặc lỗi: {e}"
        }

    return JSONResponse({
        "status": "success", "config": android_cfg, "latest": latest,
        "device_status": dev_status, "is_running": task_mgr.android_is_running
    })


async def open_android_app_endpoint(request):
    if task_mgr.android_is_running:
        return JSONResponse({"status": "error", "message": "Điểm danh đang chạy, vui lòng chờ..."}, status_code=400)
    cfg = load_config()
    android_cfg = cfg.get("android_settings", {})
    dev, pkg, pin = android_cfg.get("device_address", "100.71.117.39:5555"), android_cfg.get("package_name", "com.microsoft.bing"), android_cfg.get("pin", "")

    loop = asyncio.get_event_loop()
    try:
        task_mgr.add_log(f"📱 Đang mở App Bing trên {dev}...", "action")
        res = await asyncio.wait_for(loop.run_in_executor(None, lambda: AndroidBingCheckinBot(device=dev, pin=pin, package=pkg).open_app()), timeout=15.0)
        status = "success" if res.get("success") else "error"
        return JSONResponse({"status": status, **res}, status_code=200 if status == "success" else 400)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def close_android_app_endpoint(request):
    if task_mgr.android_is_running:
        return JSONResponse({"status": "error", "message": "Điểm danh đang chạy, vui lòng chờ..."}, status_code=400)
    cfg = load_config()
    android_cfg = cfg.get("android_settings", {})
    dev, pkg = android_cfg.get("device_address", "100.71.117.39:5555"), android_cfg.get("package_name", "com.microsoft.bing")

    loop = asyncio.get_event_loop()
    try:
        task_mgr.add_log(f"📱 Đang tắt App Bing trên {dev}...", "action")
        res = await asyncio.wait_for(loop.run_in_executor(None, lambda: AndroidBingCheckinBot(device=dev, package=pkg).close_app()), timeout=15.0)
        status = "success" if res.get("success") else "error"
        return JSONResponse({"status": status, **res}, status_code=200 if status == "success" else 400)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def reconnect_android_endpoint(request):
    cfg = load_config()
    dev = cfg.get("android_settings", {}).get("device_address", "100.71.117.39:5555")
    loop = asyncio.get_event_loop()
    try:
        task_mgr.add_log(f"📱 Đang kết nối lại tới {dev}...", "action")
        ok = await asyncio.wait_for(loop.run_in_executor(None, lambda: AndroidBingCheckinBot(device=dev).reconnect_device()), timeout=15.0)
        msg = f"Đã kết nối thành công tới {dev}" if ok else f"Không thể kết nối tới {dev}"
        return JSONResponse({"status": "success" if ok else "error", "success": ok, "message": msg}, status_code=200 if ok else 400)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def turn_on_android_screen_endpoint(request):
    if task_mgr.android_is_running:
        return JSONResponse({"status": "error", "message": "Điểm danh đang chạy, vui lòng chờ..."}, status_code=400)
    cfg = load_config()
    android_cfg = cfg.get("android_settings", {})
    dev, pin = android_cfg.get("device_address", "100.71.117.39:5555"), android_cfg.get("pin", "")

    loop = asyncio.get_event_loop()
    try:
        res = await asyncio.wait_for(loop.run_in_executor(None, lambda: AndroidBingCheckinBot(device=dev, pin=pin).turn_on_device()), timeout=25.0)
        return JSONResponse({"status": "success" if res.get("success") else "error", **res})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def turn_off_android_screen_endpoint(request):
    if task_mgr.android_is_running:
        return JSONResponse({"status": "error", "message": "Điểm danh đang chạy, vui lòng chờ..."}, status_code=400)
    cfg = load_config()
    dev = cfg.get("android_settings", {}).get("device_address", "100.71.117.39:5555")

    loop = asyncio.get_event_loop()
    try:
        res = await asyncio.wait_for(loop.run_in_executor(None, lambda: AndroidBingCheckinBot(device=dev).turn_off_device()), timeout=15.0)
        return JSONResponse({"status": "success" if res.get("success") else "error", **res})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def toggle_android_screen_endpoint(request):
    if task_mgr.android_is_running:
        return JSONResponse({"status": "error", "message": "Điểm danh đang chạy, vui lòng chờ..."}, status_code=400)
    cfg = load_config()
    android_cfg = cfg.get("android_settings", {})
    dev, pin = android_cfg.get("device_address", "100.71.117.39:5555"), android_cfg.get("pin", "")

    loop = asyncio.get_event_loop()
    try:
        res = await asyncio.wait_for(loop.run_in_executor(None, lambda: AndroidBingCheckinBot(device=dev, pin=pin).toggle_screen()), timeout=25.0)
        return JSONResponse({"status": "success" if res.get("success") else "error", **res})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
