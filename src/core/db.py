# -*- coding: utf-8 -*-
"""
src/core/db.py
==============
Facade module re-export toan bo chuc nang database tu db_connection va db_queries.
Tuan thu rule 01_architecture (< 250 dong).
"""

from src.core.paths import DB_PATH, CONFIG_PATH, PROFILES_DIR, resolve_profile_path
from src.core.db_connection import (
    get_db_connection,
    init_db,
    sync_db_to_config
)
from src.core.db_queries import (
    get_all_profiles,
    get_profile_by_id,
    add_profile_db,
    update_profile_db,
    delete_profile_db,
    log_run_history,
    get_recent_history,
    save_android_checkin_result,
    get_latest_android_checkin
)

__all__ = [
    "DB_PATH",
    "CONFIG_PATH",
    "PROFILES_DIR",
    "resolve_profile_path",
    "get_db_connection",
    "init_db",
    "sync_db_to_config",
    "get_all_profiles",
    "get_profile_by_id",
    "add_profile_db",
    "update_profile_db",
    "delete_profile_db",
    "log_run_history",
    "get_recent_history",
    "save_android_checkin_result",
    "get_latest_android_checkin"
]

# Tu dong khoi tao DB va schema khi import
try:
    init_db()
except Exception as _e:
    pass
