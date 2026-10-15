# -*- coding: utf-8 -*-
"""
src/services
============
Services module for auto_microsoft (AI keywords generation, NLP engine).
"""

from src.services.nlp_engine import (
    count_words,
    clean_keyword,
    is_valid_keyword,
    SemanticNLPEngine
)
from src.services.ai_keywords import (
    generate_new_keywords,
    append_keywords_to_file
)

__all__ = [
    "count_words",
    "clean_keyword",
    "is_valid_keyword",
    "SemanticNLPEngine",
    "generate_new_keywords",
    "append_keywords_to_file"
]
