# -*- coding: utf-8 -*-
"""
src/bots/android
================
Android Bing App Auto Check-in Bot package.
"""

from src.bots.android.adb_client import (
    ADBClient,
    find_adb_path,
    load_default_pin,
    ping_host,
    get_adb_device_state,
    DEFAULT_DEVICE,
    REWARDS_BTN
)
from src.bots.android.screen_analyzer import (
    capture_screenshot,
    find_today_circle,
    check_daily_streak_status
)
from src.bots.android.checkin_flow import (
    AndroidBingCheckinBot,
    run_checkin_flow,
    main
)

__all__ = [
    "ADBClient",
    "find_adb_path",
    "load_default_pin",
    "ping_host",
    "get_adb_device_state",
    "DEFAULT_DEVICE",
    "REWARDS_BTN",
    "capture_screenshot",
    "find_today_circle",
    "check_daily_streak_status",
    "AndroidBingCheckinBot",
    "run_checkin_flow",
    "main"
]
