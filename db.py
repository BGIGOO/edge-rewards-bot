# -*- coding: utf-8 -*-
"""
Database Management Module - SQLite
Quản lý hồ sơ tài khoản (profiles), trạng thái đăng nhập, điểm số và lịch sử chạy bot.
"""

import os
import json
import sqlite3
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "rewards_bot.db")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")


def get_db_connection():
    """Tạo kết nối SQLite với Row factory dạng dictionary"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Khởi tạo cấu trúc bảng SQLite và nạp dữ liệu ban đầu từ config.json nếu DB mới"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Bảng profiles: Quản lý danh sách tài khoản
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT DEFAULT '',
            path TEXT NOT NULL,
            profile_directory TEXT DEFAULT 'Default',
            status TEXT DEFAULT 'unlogged',
            total_points INTEGER DEFAULT 0,
            today_points INTEGER DEFAULT 0,
            last_run TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bảng run_history: Lịch sử các phiên chạy
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS run_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            profile_name TEXT,
            mode TEXT,
            searches_count INTEGER DEFAULT 0,
            points_earned INTEGER DEFAULT 0,
            status TEXT,
            started_at TEXT,
            finished_at TEXT,
            log_summary TEXT
        )
    """)
    conn.commit()

    # Kiểm tra nếu bảng profiles trống, tự động import từ config.json
    cursor.execute("SELECT COUNT(*) FROM profiles")
    count = cursor.fetchone()[0]
    if count == 0 and os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                profiles = cfg.get("profiles", [])
                for p in profiles:
                    p_id = int(p.get("id", 1)) if str(p.get("id", "")).isdigit() else 1
                    name = p.get("name", f"Profile {p_id}")
                    path = p.get("path", f"./edge_profile_{p_id}" if p_id != 1 else "./edge_profile")
                    prof_dir = p.get("profile_directory", "Default")
                    email = name if "@" in name else ""
                    status = "ready" if email else "unlogged"

                    cursor.execute("""
                        INSERT OR REPLACE INTO profiles 
                        (id, name, email, path, profile_directory, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (p_id, name, email, path, prof_dir, status))
            conn.commit()
        except Exception as e:
            print(f"[!] Lỗi khi nạp dữ liệu ban đầu vào SQLite: {e}")

    conn.close()


def sync_db_to_config():
    """Đồng bộ danh sách profiles từ SQLite sang config.json để bot đọc độc lập"""
    try:
        profiles = get_all_profiles()
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        else:
            cfg = {}

        cfg["profiles"] = [
            {
                "id": str(p["id"]),
                "name": p["name"],
                "email": p.get("email", ""),
                "path": p["path"],
                "profile_directory": p["profile_directory"],
                "status": p.get("status", "ready")
            }
            for p in profiles
        ]

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Lỗi đồng bộ DB sang config.json: {e}")


def get_all_profiles():
    """Lấy danh sách tất cả các profiles"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_profile_by_id(profile_id):
    """Lấy thông tin 1 profile theo ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (int(profile_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_profile_db(name=None, custom_path=None, profile_directory=None):
    """Thêm tài khoản mới vào SQLite"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tự động tính next_id
    cursor.execute("SELECT MAX(id) FROM profiles")
    max_id = cursor.fetchone()[0]
    next_id = (max_id + 1) if max_id is not None else 1

    if not name:
        name = f"Chưa đăng nhập (Profile {next_id})"

    if not custom_path:
        custom_path = f"./edge_profile_{next_id}" if next_id != 1 else "./edge_profile"

    # Profile mới độc lập luôn dùng thư mục 'Default' bên trong folder riêng của nó
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


def update_profile_db(profile_id, name=None, email=None, custom_path=None, status=None, total_points=None, today_points=None, last_run=None):
    """Cập nhật thông tin profile trong SQLite"""
    conn = get_db_connection()
    cursor = conn.cursor()

    updates = []
    params = []

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
        params.append(custom_path)

    if status is not None:
        updates.append("status = ?")
        params.append(status)

    if total_points is not None:
        updates.append("total_points = ?")
        params.append(total_points)

    if today_points is not None:
        updates.append("today_points = ?")
        params.append(today_points)

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


def delete_profile_db(profile_id):
    """Xóa profile khỏi SQLite"""
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


def log_run_history(profile_id, profile_name, mode, searches_count=0, points_earned=0, status="completed", started_at=None, finished_at=None, summary=""):
    """Ghi lại lịch sử chạy bot"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO run_history 
        (profile_id, profile_name, mode, searches_count, points_earned, status, started_at, finished_at, log_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (profile_id, profile_name, mode, searches_count, points_earned, status, started_at, finished_at, summary))
    conn.commit()
    conn.close()


def get_recent_history(limit=20):
    """Lấy danh sách lịch sử chạy gần đây"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM run_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
