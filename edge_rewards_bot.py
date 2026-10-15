# -*- coding: utf-8 -*-
"""
edge_rewards_bot.py - Backward Compatibility Shim
Chuyển tiếp toàn bộ lời gọi đến module src.bots.edge đã mô-đun hóa.
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
from src.bots.edge import *  # noqa: F401, F403
from src.bots.edge import __all__

if __name__ == "__main__":
    from src.bots.edge.runner import main
    main()
