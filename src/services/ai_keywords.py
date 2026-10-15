# -*- coding: utf-8 -*-
"""
src/services/ai_keywords.py
===========================
AI Keywords Generator (Google Gemini API + NLP Fallback).
Tuân thủ rule 01_architecture (< 250 dòng).
"""

import os
import json
import random
import urllib.request
import urllib.error
from typing import List, Set, Optional

from src.core.paths import KEYWORDS_PATH, CONFIG_PATH
from src.services.nlp_engine import (
    count_words,
    clean_keyword,
    is_valid_keyword,
    SemanticNLPEngine
)


def get_gemini_api_key() -> str:
    """Lấy Gemini API Key từ config.json hoặc biến môi trường."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                api_key = cfg.get("ai_settings", {}).get("gemini_api_key", "")
        except Exception:
            pass
    return api_key.strip()


def call_gemini_api(api_key: str, count: int = 50, timeout: int = 15) -> List[str]:
    """Gọi Google Gemini API để sinh từ khóa theo yêu cầu."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = (
        f"Generate exactly {count + 15} natural Bing search queries.\n"
        f"Requirements:\n"
        f"1. Exactly half in Vietnamese and half in English.\n"
        f"2. Every search query MUST have strictly between 3 and 6 words.\n"
        f"3. Topics: technology, cooking, fitness, travel, news, lifestyle, science, entertainment.\n"
        f"4. Output format: ONLY a valid JSON array of strings. Example: [\"cách làm sữa chua dẻo\", \"best budget gaming laptop 2026\"]."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        text_content = res_data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text_content)


def generate_new_keywords(count: int = 50, existing_set: Optional[Set[str]] = None) -> List[str]:
    """
    Sinh từ khóa chuẩn 3-6 từ, 50% Anh - 50% Việt.
    Ưu tiên Gemini API nếu có key, tự động fallback sang SemanticNLPEngine.
    """
    if existing_set is None:
        existing_set = set()
        if os.path.exists(KEYWORDS_PATH):
            with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    c = clean_keyword(line)
                    if c:
                        existing_set.add(c.lower())

    seen = set(existing_set)
    collected: List[str] = []

    # 1. Thử gọi Google Gemini API nếu có key
    api_key = get_gemini_api_key()
    if api_key:
        try:
            print(f"[*] Đang gọi Google Gemini AI sinh {count} từ khóa mới...", flush=True)
            ai_list = call_gemini_api(api_key, count=count)
            for item in ai_list:
                kw = clean_keyword(item)
                if is_valid_keyword(kw, min_words=3, max_words=6):
                    kw_lower = kw.lower()
                    if kw_lower not in seen:
                        seen.add(kw_lower)
                        collected.append(kw)
                        if len(collected) >= count:
                            break
            print(f"[✓] Gemini AI đã sinh thành công {len(collected)} từ khóa!", flush=True)
        except Exception as e:
            print(f"[!] Gemini API không khả dụng ({e}), chuyển sang NLP Engine...", flush=True)

    # 2. Bổ sung bằng Semantic NLP Engine cho đủ count
    if len(collected) < count:
        needed = count - len(collected)
        synthesized = SemanticNLPEngine.generate_batch(count=needed, seen=seen)
        collected.extend(synthesized)

    random.shuffle(collected)
    return collected[:count]


def append_keywords_to_file(new_keywords: List[str]) -> int:
    """Lưu thêm các từ khóa mới vào cuối keywords.txt."""
    if not new_keywords:
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(KEYWORDS_PATH)), exist_ok=True)
    with open(KEYWORDS_PATH, "a", encoding="utf-8") as f:
        for kw in new_keywords:
            f.write(f"\n{kw}")
    return len(new_keywords)


def main():
    print("=" * 65)
    print("✨ TEST AI KEYWORDS GENERATOR (50 TỪ KHÓA MỚI, 3-6 TỪ, ANH & VIỆT)")
    print("=" * 65)
    kws = generate_new_keywords(50)
    print(f"✅ ĐÃ SINH RA CHÍNH XÁC {len(kws)} TỪ KHÓA MỚI HOÀN TOÀN:\n")
    for idx, kw in enumerate(kws, 1):
        words = count_words(kw)
        print(f" {idx:2d}. [{words} từ] {kw}")


if __name__ == "__main__":
    main()
