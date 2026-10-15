# -*- coding: utf-8 -*-
"""
src/core/db_connection.py
=========================
Quan ly ket noi SQLite, thiet lap WAL mode, timeout=30.0 va khoi tao schema ban dau.
Tuan thu rule 01_architecture (< 250 dong) va rule 02_automation_bots.
"""

import os
import json
import sqlite3
from src.core.paths import DB_PATH, CONFIG_PATH, resolve_profile_path


def get_db_connection() -> sqlite3.Connection:
    """Tao ket noi SQLite voi Row factory dict, timeout=30.0 va WAL mode."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db() -> None:
    """Khoi tao cau truc cac bang SQLite va nap du lieu ban dau tu config.json."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Bang profiles: Quan ly danh sach tai khoan
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
            desktop_points TEXT DEFAULT '0/90',
            mobile_points TEXT DEFAULT '0/60',
            offers_points INTEGER DEFAULT 0,
            last_run TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Dam bao migration cac cot moi neu bang da ton tai
    migrations = [
        ("desktop_points", "TEXT", "'0/90'"),
        ("mobile_points", "TEXT", "'0/60'"),
        ("offers_points", "INTEGER", "0"),
        ("app_checkin_status", "TEXT", "'pending'"),
        ("app_checkin_time", "TEXT", "''")
    ]
    for col, c_type, def_v in migrations:
        try:
            cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col} {c_type} DEFAULT {def_v}")
        except Exception:
            pass

    # Bang run_history: Lich su cac phien chay bot
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

    # Bang android_checkin_logs: Lich su diem danh App Bing Android
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS android_checkin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT,
            status TEXT,
            message TEXT,
            frame_before TEXT,
            frame_after TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Nap du lieu ban dau tu config.json neu bang profiles dang trong
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
                    raw_path = p.get("path", f"./edge_profile_{p_id}" if p_id != 1 else "./edge_profile")
                    path = str(resolve_profile_path(raw_path))
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
            print(f"[!] Loi khi nap du lieu ban dau vao SQLite: {e}")

    conn.close()


def sync_db_to_config() -> None:
    """Dong bo danh sach profiles tu SQLite sang config.json de bot doc doc lap."""
    try:
        from src.core.db_queries import get_all_profiles
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
        print(f"[!] Loi dong bo DB sang config.json: {e}")
