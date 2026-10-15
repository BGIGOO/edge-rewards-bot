# -*- coding: utf-8 -*-
"""
src/api/routes_edge.py
======================
Cac endpoint dieu khien bot PC Edge, quan ly keywords va sinh tu khoa AI.
Tuan thu rule 01_architecture (< 250 dong) va rule 03_web_fullstack.
"""

import os
import asyncio
from starlette.responses import JSONResponse

from src.core.paths import KEYWORDS_PATH
from src.bots.edge.runner import load_config
from src.services.ai_keywords import generate_new_keywords, append_keywords_to_file
from src.api.task_manager import task_mgr


async def run_task(request):
    """Kich hoat chay bot tim kiem PC."""
    if task_mgr.pc_is_running:
        return JSONResponse({"status": "error", "message": "Bot PC đang bận chạy một tác vụ khác!"}, status_code=400)

    try:
        data = await request.json()
    except Exception:
        data = {}

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
                "message": "Không có tài khoản nào đã đăng nhập! Vui lòng bấm 'Đăng nhập' trước."
            }, status_code=400)
    else:
        matched = [p for p in profiles if str(p.get("id")) == str(profile_choice)]
        if not matched:
            return JSONResponse({"status": "error", "message": f"Không tìm thấy Profile {profile_choice}"}, status_code=404)
        target = matched[0]
        if target.get("status") == "unlogged" or not ("@" in str(target.get("name", "")) or target.get("email")):
            return JSONResponse({
                "status": "error",
                "message": f"Tài khoản #{profile_choice} ({target.get('name')}) chưa đăng nhập! Hãy đăng nhập trước."
            }, status_code=400)
        profiles_to_run = matched

    asyncio.create_task(task_mgr.run_bot_sequence(profiles_to_run, mode))
    return JSONResponse({"status": "success", "mode": mode, "count": len(profiles_to_run), "message": "Đã bắt đầu tìm kiếm PC"})


async def stop_task(request):
    """Dung bot khancap tat ca tac vu."""
    task_mgr.stop_bot()
    return JSONResponse({"status": "success", "message": "Đã dừng các tiến trình bot"})


async def get_keywords_endpoint(request):
    """Lay danh sach tu khoa."""
    content = ""
    lines_count = 0
    if os.path.exists(KEYWORDS_PATH):
        with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        lines_count = len([l for l in content.splitlines() if l.strip() and not l.strip().startswith("#")])
    return JSONResponse({"status": "success", "content": content, "count": lines_count})


async def save_keywords_endpoint(request):
    """Luu danh sach tu khoa vao file."""
    try:
        data = await request.json()
        content = data.get("content", "")
        os.makedirs(os.path.dirname(os.path.abspath(KEYWORDS_PATH)), exist_ok=True)
        with open(KEYWORDS_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        lines_count = len([l for l in content.splitlines() if l.strip() and not l.strip().startswith("#")])
        task_mgr.add_log(f"💾 [TỪ KHÓA] Đã cập nhật {lines_count} từ khóa hợp lệ.", "info")
        return JSONResponse({"status": "success", "count": lines_count, "message": f"Đã lưu thành công kho {lines_count} từ khóa"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def generate_ai_keywords_endpoint(request):
    """Goi AI sinh 50 tu khoa moi (chay async executor tranh block luong)."""
    try:
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass

        count = max(10, min(int(body.get("count", 50)), 100))
        current_content = body.get("current_content")
        existing_set = set()

        if current_content is not None:
            for line in current_content.splitlines():
                c = line.strip().lower()
                if c and not c.startswith("#"):
                    existing_set.add(c)
        elif os.path.exists(KEYWORDS_PATH):
            with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    c = line.strip().lower()
                    if c and not c.startswith("#"):
                        existing_set.add(c)

        # Chay sinh tu khoa trong thread rieng khong lam nghen web server
        loop = asyncio.get_event_loop()
        new_kws = await loop.run_in_executor(None, generate_new_keywords, count, existing_set)

        if current_content is not None:
            clean = current_content.strip()
            updated_content = (clean + "\n" + "\n".join(new_kws) + "\n") if clean else ("\n".join(new_kws) + "\n")
            os.makedirs(os.path.dirname(os.path.abspath(KEYWORDS_PATH)), exist_ok=True)
            with open(KEYWORDS_PATH, "w", encoding="utf-8") as f:
                f.write(updated_content)
        else:
            append_keywords_to_file(new_kws)
            updated_content = ""
            if os.path.exists(KEYWORDS_PATH):
                with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
                    updated_content = f.read()

        total = len([l for l in updated_content.splitlines() if l.strip() and not l.strip().startswith("#")])
        task_mgr.add_log(f"✨ [AI KEYWORDS] Đã sinh {len(new_kws)} từ khóa mới (Tổng: {total}).", "success")
        return JSONResponse({
            "status": "success",
            "count": len(new_kws),
            "new_keywords": new_kws,
            "updated_content": updated_content,
            "total_count": total,
            "message": f"Đã sinh {len(new_kws)} từ khóa mới thành công"
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
