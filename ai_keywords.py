# -*- coding: utf-8 -*-
"""
ai_keywords.py - Backward Compatibility Shim
Chuyển tiếp toàn bộ lời gọi đến module src.services.ai_keywords đã mô-đun hóa.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.services.ai_keywords import *  # noqa: F401, F403
from src.services.nlp_engine import SemanticNLPEngine, count_words, clean_keyword, is_valid_keyword  # noqa: F401

if __name__ == "__main__":
    from src.services.ai_keywords import main
    main()
