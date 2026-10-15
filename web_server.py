# -*- coding: utf-8 -*-
"""
web_server.py - Web Server Launcher Shim
Chuyển tiếp toàn bộ yêu cầu đến module src.api.server đã mô-đun hóa.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.api.server import app, main

if __name__ == "__main__":
    main()
