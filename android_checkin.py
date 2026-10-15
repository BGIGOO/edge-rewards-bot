# -*- coding: utf-8 -*-
"""
android_checkin.py - Backward Compatibility Shim
Chuyển tiếp toàn bộ lời gọi đến module src.bots.android đã mô-đun hóa.
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.bots.android import *  # noqa: F401, F403
from src.bots.android import __all__

if __name__ == "__main__":
    from src.bots.android.checkin_flow import main
    main()
