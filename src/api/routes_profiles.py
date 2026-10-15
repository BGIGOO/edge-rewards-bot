# -*- coding: utf-8 -*-
"""
src/api/routes_profiles.py
==========================
Cac endpoint quan ly danh sach tai khoan (profiles), dang nhap, mo khoa, kiem tra diem.
Tuan thu rule 01_architecture (< 250 dong) va rule 03_web_fullstack.
"""

import os
import json
import asyncio
from starlette.responses import JSONResponse

from src.core import db
from src.bots.edge.runner import load_config
from src.bots.edge.points_parser import check_profile_points
from src.bots.edge.browser import (
    get_profile_abs_path,
    kill_zombie_edge_processes,
    open_browser_for_login
)
from src.api.task_manager import task_mgr


def get_edge_account_email(profile_dict: dict) -> str:
    """Tu dong phat hien email da dang nhap trong thu muc profile Edge."""
    try:
        pdir = get_profile_abs_path(profile_dict)
        pdir_name = profile_dict.get("profile_directory", "Default")

        ls_path = os.path.join(pdir, "Local State")
        if os.path.exists(ls_path):
            try:
                with open(ls_path, "r", encoding="utf-8", errors="ignore") as f:
                    ls = json.load(f)
                    info = ls.get("profile", {}).get("info_cache", {}).get(pdir_name, {})
                    u = info.get("user_name")
                    if u and "@" in u:
                        return u
            except Exception:
                pass

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
    return ""


async def get_profiles(request):
    """Lay danh sach cac profile va tu dong cap nhat email neu phat hien dang nhap moi."""
    profiles = db.get_all_profiles()
    result = []

    for p in profiles:
        p_dir = get_profile_abs_path(p)
        dir_exists = os.path.exists(p_dir)
        email = get_edge_account_email(p)
        name = p.get("name", "")

        if email:
            if not p.get("email") or p.get("status") == "unlogged" or name.startswith("Chưa đăng nhập"):
                p["email"] = email
                p["name"] = email
                p["status"] = "ready"
                db.update_profile_db(p["id"], name=email, email=email, status="ready")
        else:
            if not p.get("email") and "@" not in name and p.get("status") != "unlogged":
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
    try:
        body = await request.json()
    except Exception:
        body = {}
    name = body.get("name", "").strip() or None
    c_path = body.get("path", "").strip() or None
    p_dir = body.get("profile_directory", "").strip() or None
    created = db.add_profile_db(name, c_path, p_dir)
    return JSONResponse({"status": "success", "profile": created, "message": "Thêm tài khoản thành công"})


async def update_profile(request):
    p_id = request.path_params.get("id")
    try:
        body = await request.json()
    except Exception:
        body = {}
    updated = db.update_profile_db(
        p_id, name=body.get("name"), email=body.get("email"),
        custom_path=body.get("path"), status=body.get("status")
    )
    return JSONResponse({"status": "success", "profile": updated, "message": "Cập nhật tài khoản thành công"})


async def delete_profile(request):
    p_id = request.path_params.get("id")
    ok = db.delete_profile_db(p_id)
    return JSONResponse({"status": "success" if ok else "error", "message": "Xóa thành công" if ok else "Không tìm thấy profile"})


async def unlock_profile(request):
    p_id = request.path_params.get("id")
    target = db.get_profile_by_id(p_id)
    if not target:
        matched = [p for p in load_config().get("profiles", []) if str(p.get("id")) == str(p_id)]
        target = matched[0] if matched else None

    if target:
        p_dir = get_profile_abs_path(target)
        kill_zombie_edge_processes(p_dir)
        task_mgr.add_log(f"🧹 Đã mở khóa & giải phóng tiến trình treo cho {target.get('name')}.", "success")
        return JSONResponse({"status": "success", "message": "Đã mở khóa profile thành công"})
    return JSONResponse({"status": "error", "message": "Không tìm thấy profile"}, status_code=404)


async def login_profile(request):
    p_id = request.path_params.get("id")
    target = db.get_profile_by_id(p_id)
    if not target:
        matched = [p for p in load_config().get("profiles", []) if str(p.get("id")) == str(p_id)]
        target = matched[0] if matched else None
    if not target:
        return JSONResponse({"status": "error", "message": "Không tìm thấy profile"}, status_code=404)

    task_mgr.add_log(f"🔑 Đang mở Edge cho {target.get('name')} để đăng nhập...", "start")
    proc = open_browser_for_login(target)
    if proc:
        task_mgr.add_log("👉 Hãy đăng nhập và đóng cửa sổ Edge khi hoàn tất.", "info")
        return JSONResponse({"status": "success", "message": "Trình duyệt Edge đã mở"})
    task_mgr.add_log("❌ Không thể khởi động Microsoft Edge.", "error")
    return JSONResponse({"status": "error", "message": "Không thể mở Edge"}, status_code=500)


async def check_profile_endpoint(request):
    p_id = request.path_params.get("id")
    target = db.get_profile_by_id(p_id)
    if not target:
        matched = [p for p in load_config().get("profiles", []) if str(p.get("id")) == str(p_id)]
        target = matched[0] if matched else None
    if not target:
        return JSONResponse({"status": "error", "message": "Không tìm thấy hồ sơ tài khoản"}, status_code=404)

    if task_mgr.pc_is_running and task_mgr.pc_task_info and str(task_mgr.pc_task_info.get("profile_id")) == str(p_id):
        return JSONResponse({
            "status": "error", "message": f"Tài khoản {target.get('name')} đang chạy bot. Hãy đợi hoàn tất!"
        }, status_code=400)

    p_name = target.get("name", f"Profile {p_id}")
    task_mgr.add_log(f"🔍 Kiểm tra điểm thực tế cho {p_name}...", "start")
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, check_profile_points, target)

    if res.get("success"):
        d = res.get("data", {})
        task_mgr.add_log(f"⭐ {p_name}: Khả dụng: {d.get('total_points', 0):,} pts | Hôm nay +{d.get('today_points', 0)} pts", "success")
        return JSONResponse({"status": "success", "profile": res.get("profile"), "data": d, "message": "Kiểm tra điểm thành công"})
    err = res.get("message", "Không thể kiểm tra điểm")
    task_mgr.add_log(f"❌ {p_name}: {err}", "error")
    return JSONResponse({"status": "error", "message": err}, status_code=400)


async def stop_profile_task(request):
    p_id = request.path_params.get("id")
    cfg = load_config()
    matched = [p for p in cfg.get("profiles", []) if str(p.get("id")) == str(p_id)]
    p_name = matched[0].get("name", f"Profile {p_id}") if matched else f"Profile {p_id}"
    stopped = False

    if task_mgr.pc_is_running and task_mgr.pc_task_info and str(task_mgr.pc_task_info.get("profile_id")) == str(p_id):
        task_mgr.stop_pc_bot()
        task_mgr.add_log(f"🛑 Đã dừng tìm kiếm cho {p_name}!", "warn")
        stopped = True
    elif matched:
        kill_zombie_edge_processes(get_profile_abs_path(matched[0]))
        task_mgr.add_log(f"🛑 Đã đóng tiến trình Edge của {p_name}.", "warn")
        stopped = True

    return JSONResponse({"status": "success", "stopped": stopped, "profile_id": p_id, "message": f"Đã dừng profile {p_id}"})
