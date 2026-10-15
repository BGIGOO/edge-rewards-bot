# -*- coding: utf-8 -*-
"""
src/core/db_queries.py
======================
Cac truy van CRUD cho profiles, run_history va android_checkin_logs.
Tuan thu rule 01_architecture (< 250 dong).
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from src.core.paths import PROFILES_DIR, resolve_profile_path
from src.core.db_connection import get_db_connection, sync_db_to_config


def get_all_profiles() -> List[Dict[str, Any]]:
    """Lay danh sach tat ca cac profiles."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_profile_by_id(profile_id: int) -> Optional[Dict[str, Any]]:
    """Lay thong tin 1 profile theo ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (int(profile_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_profile_db(name: Optional[str] = None,
                   custom_path: Optional[str] = None,
                   profile_directory: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Them tai khoan moi vao SQLite, tu dong tao duong dan trong data/profiles/."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(id) FROM profiles")
    max_id = cursor.fetchone()[0]
    next_id = (max_id + 1) if max_id is not None else 1

    if not name:
        name = f"Chưa đăng nhập (Profile {next_id})"

    if not custom_path:
        folder = "edge_profile" if next_id == 1 else f"edge_profile_{next_id}"
        custom_path = str(PROFILES_DIR / folder)
    else:
        custom_path = str(resolve_profile_path(custom_path))

    if not profile_directory:
        profile_directory = "Default"

    email = name if "@" in name else ""
    status = "ready" if email else "unlogged"

    cursor.execute("""
        INSERT INTO profiles (id, name, email, path, profile_directory, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (next_id, name, email, custom_path, profile_directory, status))
    conn.commit()
    conn.close()

    sync_db_to_config()
    return get_profile_by_id(next_id)


def update_profile_db(profile_id: int,
                      name: Optional[str] = None,
                      email: Optional[str] = None,
                      custom_path: Optional[str] = None,
                      status: Optional[str] = None,
                      total_points: Optional[int] = None,
                      today_points: Optional[int] = None,
                      desktop_points: Optional[str] = None,
                      mobile_points: Optional[str] = None,
                      offers_points: Optional[int] = None,
                      last_run: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Cap nhat thong tin profile trong SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()

    updates = []
    params: List[Any] = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
        if "@" in name and email is None:
            updates.append("email = ?")
            params.append(name)
            if status is None:
                updates.append("status = ?")
                params.append("ready")

    if email is not None:
        updates.append("email = ?")
        params.append(email)
        if email and status is None:
            updates.append("status = ?")
            params.append("ready")

    if custom_path is not None:
        updates.append("path = ?")
        params.append(str(resolve_profile_path(custom_path)))

    if status is not None:
        updates.append("status = ?")
        params.append(status)

    if total_points is not None:
        updates.append("total_points = ?")
        params.append(total_points)

    if today_points is not None:
        updates.append("today_points = ?")
        params.append(today_points)

    if desktop_points is not None:
        updates.append("desktop_points = ?")
        params.append(desktop_points)

    if mobile_points is not None:
        updates.append("mobile_points = ?")
        params.append(mobile_points)

    if offers_points is not None:
        updates.append("offers_points = ?")
        params.append(offers_points)

    if last_run is not None:
        updates.append("last_run = ?")
        params.append(last_run)

    if updates:
        params.append(int(profile_id))
        sql = f"UPDATE profiles SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, params)
        conn.commit()

    conn.close()
    sync_db_to_config()
    return get_profile_by_id(profile_id)


def delete_profile_db(profile_id: int) -> bool:
    """Xoa profile khoi SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profiles WHERE id = ?", (int(profile_id),))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected > 0:
        sync_db_to_config()
        return True
    return False


def log_run_history(profile_id: int,
                    profile_name: str,
                    mode: str,
                    searches_count: int = 0,
                    points_earned: int = 0,
                    status: str = "completed",
                    started_at: Optional[str] = None,
                    finished_at: Optional[str] = None,
                    summary: str = "") -> None:
    """Ghi lai lich su chay bot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO run_history 
        (profile_id, profile_name, mode, searches_count, points_earned, status, started_at, finished_at, log_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (profile_id, profile_name, mode, searches_count, points_earned, status, started_at, finished_at, summary))
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Lay danh sach lich su chay gan day."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM run_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_android_checkin_result(status: str,
                                message: str = "",
                                frame_before: str = "",
                                frame_after: str = "",
                                device: str = "100.71.117.39:5555",
                                profile_id: Optional[int] = None) -> None:
    """
    Luu ket qua diem danh Android vao SQLite.
    Sua loi #20: Nhan profile_id tuy chon (neu None se cap nhat cac profile 'ready'/'running').
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO android_checkin_logs 
        (device, status, message, frame_before, frame_after)
        VALUES (?, ?, ?, ?, ?)
    """, (device, status, message, frame_before, frame_after))

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    if profile_id is not None:
        cursor.execute("""
            UPDATE profiles 
            SET app_checkin_status = ?, app_checkin_time = ?
            WHERE id = ?
        """, (status, now_str, int(profile_id)))
    else:
        cursor.execute("""
            UPDATE profiles 
            SET app_checkin_status = ?, app_checkin_time = ?
            WHERE status IN ('ready', 'running')
        """, (status, now_str))

    conn.commit()
    conn.close()


def get_latest_android_checkin() -> Dict[str, Any]:
    """Lay ket qua diem danh Android gan nhat."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM android_checkin_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "status": "pending",
        "message": "Chưa có lượt điểm danh nào hôm nay.",
        "frame_before": "",
        "frame_after": "",
        "created_at": ""
    }
