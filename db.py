# -*- coding: utf-8 -*-
"""
db.py - Backward Compatibility Shim
Chuyen tiep toan bo loi goi den module src.core.db da mo-dun hoa.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.core.db import *  # noqa: F401, F403
from src.core.db import __all__

if __name__ == "__main__":
    init_db()  # noqa: F405
    print(f"[*] SQLite Database da san sang tai: {DB_PATH}")  # noqa: F405
