# -*- coding: utf-8 -*-
"""
====================================================================
           AI KEYWORDS GENERATOR FOR MICROSOFT REWARDS
   Tự động sinh 50 từ khóa tìm kiếm Bing mới hoàn toàn (3 - 6 từ)
   Đan xen 50% tiếng Anh & 50% tiếng Việt - Tự nhiên như người thật
   Hỗ trợ Google Gemini API + Semantic NLP Combinatorial Engine
====================================================================
"""

import os
import sys
import json
import random
import re
import urllib.request
import urllib.error

# Console Windows UTF-8
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_PATH = os.path.join(SCRIPT_DIR, "keywords.txt")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")


def count_words(text):
    """Đếm số từ trong cụm từ"""
    return len(text.strip().split())


def clean_keyword(line):
    """Làm sạch chuỗi từ khóa"""
    if not line:
        return ""
    cleaned = re.sub(r"^[\d\.\-\*\•\>\s]+", "", line).strip()
    cleaned = cleaned.strip("\"'[]`").strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_valid_keyword(kw, min_words=3, max_words=6):
    """Kiểm tra từ khóa đạt chuẩn từ 3 đến 6 từ"""
    if not kw:
        return False
    wcount = count_words(kw)
    if not (min_words <= wcount <= max_words):
        return False
    if "http" in kw or ".com" in kw or len(kw) > 65:
        return False
    return True


def get_gemini_api_key():
    """Lấy Gemini API Key từ config.json hoặc biến môi trường"""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                api_key = cfg.get("ai_settings", {}).get("gemini_api_key", "")
        except Exception:
            pass
    return api_key.strip()


def call_gemini_api(api_key, count=50, timeout=15):
    """Gọi Google Gemini API để sinh từ khóa theo yêu cầu"""
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


# ====================================================================
# SEMANTIC NLP COMBINATORIAL ENGINE (HƠN 100.000 TỔ HỢP TỰ NHIÊN)
# ====================================================================
class SemanticNLPEngine:
    """
    Tổ hợp thông minh bảo đảm 100% câu sinh ra có độ dài chuẩn 3-6 từ.
    Đan xen cân bằng 50% tiếng Việt & 50% tiếng Anh.
    """

    # --- TIẾNG VIỆT ---
    VN_ACTIONS = [
        "cách", "hướng dẫn", "mẹo", "bí quyết", "kinh nghiệm", "công thức",
        "review", "đánh giá", "lợi ích của", "bài tập", "lộ trình", "tìm hiểu",
        "so sánh", "nguyên nhân", "thời tiết tại", "giá vé tham quan", "top các loại"
    ]

    VN_TOPICS = [
        # Nấu ăn & Ẩm thực (2-3 từ)
        "làm sườn xào", "nấu phở bò", "làm bánh mì bơ", "rán nem giòn", "làm gà chiên",
        "nấu canh chua", "kho thịt trứng", "nấu bò sốt vang", "pha trà sữa", "pha cà phê muối",
        "làm bánh flan", "nấu chè hạt sen", "làm nước ép cần", "chế biến cá hồi", "nấu lẩu thái",
        "làm salad ức gà", "pha trà đào sả", "nấu bún bò huế", "làm bánh bông lan", "nấu cháo sườn",
        "luộc gà da giòn", "làm kim chi cải", "nướng thịt xiên", "nấu súp cua nấm",
        # Du lịch & Trải nghiệm (2-3 từ)
        "du lịch đà lạt", "khám phá phú quốc", "đi phượt sapa", "phượt hà giang", "đi vịnh hạ long",
        "du lịch côn đảo", "khám phá phú quý", "thăm phố cổ hội an", "du lịch biển quy nhơn",
        "đi bà nà hills", "thưởng thức ẩm thực huế", "du lịch đảo cát bà", "ngắm lúa mù cang chải",
        "khám phá hang sơn đoòng", "du lịch miền tây sông nước", "phượt đèo mã pí lèng",
        # Công nghệ & Thiết bị (2-3 từ)
        "tối ưu windows 11", "tiết kiệm pin laptop", "tăng tốc mạng wifi", "chọn mua bàn phím",
        "chọn tai nghe bluetooth", "mua chuột không dây", "lắp ráp máy tính", "chọn mua iphone 16",
        "chọn card màn hình", "mua màn hình đồ họa", "dọn dẹp bộ nhớ máy", "bảo vệ pin điện thoại",
        "sửa lỗi máy tính chậm", "chọn mua macbook m3", "khôi phục dữ liệu ổ", "cài đặt lại win",
        # Sức khỏe, Thể thao & Đời sống (2-3 từ)
        "tập yoga buổi sáng", "giảm mỡ bụng nhanh", "chạy bộ mỗi ngày", "ngủ ngon sâu giấc",
        "uống nước đúng cách", "tập gym tăng cơ", "ăn kiêng eat clean", "thiền định giảm stress",
        "giảm đau vai gáy", "tăng sức đề kháng", "chăm sóc da mặt", "uống trà xanh mỗi sáng",
        "thải độc gan tự nhiên", "cải thiện trí nhớ", "tập plank đúng tư thế", "giãn cơ sau chạy",
        # Học tập & Kỹ năng sống (2-3 từ)
        "học lập trình python", "học tiếng anh giao tiếp", "thiết kế canva cơ bản", "chỉnh sửa video capcut",
        "thuyết trình trước đám đông", "quản lý tài chính cá nhân", "lập kế hoạch làm việc",
        "đọc sách hiệu quả", "học kỹ năng giao tiếp", "rèn luyện sự tập trung", "ghi nhớ từ vựng nhanh"
    ]

    VN_SUFFIX_OPTIONS = {
        0: [""],
        1: ["ngon", "nhanh", "dễ", "tốt", "chuẩn", "rẻ"],
        2: ["tại nhà", "hiệu quả", "đơn giản", "chuẩn vị", "tiết kiệm", "mới nhất", "cực ngon", "nhanh nhất", "mỗi ngày"],
        3: ["cho người mới", "trong năm 2026", "cực kỳ đơn giản", "an toàn tại nhà", "ít tốn kém"]
    }

    # --- TIẾNG ANH ---
    EN_ACTIONS = [
        "how to", "best way to", "easy guide to", "tips for", "simple steps to",
        "benefits of", "why choose", "guide to", "ideas for", "top secrets to",
        "quick guide to", "reviews of", "how to easily", "best habits for"
    ]

    EN_TOPICS = [
        # Coding & Tech (2-3 words)
        "learn python fast", "start web development", "build custom pc", "clean mechanical keyboard",
        "speed up windows", "fix slow laptop", "choose wireless mouse", "extend battery life",
        "troubleshoot wifi connection", "learn machine learning", "backup data safely", "setup dual monitor",
        "pick budget monitor", "learn prompt engineering", "secure home network", "learn git basics",
        # Health & Fitness (2-3 words)
        "start morning yoga", "burn belly fat", "build strong core", "improve sleep quality",
        "drink warm water", "walk daily steps", "meditate ten minutes", "eat healthy meals",
        "stretch after workout", "gain lean muscle", "reduce daily stress", "stay well hydrated",
        "maintain healthy posture", "boost immune system", "do daily cardio",
        # Cooking & Food (2-3 words)
        "bake garlic bread", "cook pasta carbonara", "make fluffy pancakes", "bake chocolate cookies",
        "brew cold coffee", "cook chicken soup", "make matcha latte", "grill beef burger",
        "make fruit smoothie", "roast vegetables nicely", "prepare healthy breakfast", "cook fried rice",
        # Travel & Lifestyle (2-3 words)
        "travel on budget", "pack light luggage", "find cheap flights", "explore Southeast Asia",
        "visit Tokyo spots", "plan camping trip", "save monthly money", "organize clean desk",
        "read books regularly", "wake up early", "overcome daily procrastination", "learn public speaking"
    ]

    EN_SUFFIX_OPTIONS = {
        0: [""],
        1: ["fast", "easily", "daily", "safely", "better", "today"],
        2: ["at home", "in 2026", "step by step", "on budget", "every day", "for beginners", "without stress"],
        3: ["for complete beginners", "with simple ingredients", "in just ten minutes", "for busy professionals"]
    }

    @classmethod
    def generate_single_vn(cls):
        """Sinh 1 câu tiếng Việt chuẩn xác từ 3 đến 6 từ"""
        action = random.choice(cls.VN_ACTIONS)
        topic = random.choice(cls.VN_TOPICS)
        base_words = count_words(action) + count_words(topic)

        # Quyết định số từ của suffix để tổng câu nằm trong khoảng 3 - 6 từ
        max_suffix_words = max(0, 6 - base_words)
        min_suffix_words = max(0, 3 - base_words)

        possible_lens = [l for l in cls.VN_SUFFIX_OPTIONS.keys() if min_suffix_words <= l <= max_suffix_words]
        if not possible_lens:
            chosen_len = 0
        else:
            chosen_len = random.choice(possible_lens)

        suffix = random.choice(cls.VN_SUFFIX_OPTIONS.get(chosen_len, [""]))
        query = f"{action} {topic} {suffix}".strip()
        return clean_keyword(query)

    @classmethod
    def generate_single_en(cls):
        """Sinh 1 câu tiếng Anh chuẩn xác từ 3 đến 6 từ"""
        action = random.choice(cls.EN_ACTIONS)
        topic = random.choice(cls.EN_TOPICS)
        base_words = count_words(action) + count_words(topic)

        max_suffix_words = max(0, 6 - base_words)
        min_suffix_words = max(0, 3 - base_words)

        possible_lens = [l for l in cls.EN_SUFFIX_OPTIONS.keys() if min_suffix_words <= l <= max_suffix_words]
        if not possible_lens:
            chosen_len = 0
        else:
            chosen_len = random.choice(possible_lens)

        suffix = random.choice(cls.EN_SUFFIX_OPTIONS.get(chosen_len, [""]))
        query = f"{action} {topic} {suffix}".strip()
        return clean_keyword(query)

    @classmethod
    def generate_batch(cls, count=50, seen=None):
        """Sinh batch N từ khóa cân bằng 50% Anh - 50% Việt, đúng chuẩn 3-6 từ, không trùng"""
        seen = seen or set()
        results = []
        target_each = count // 2

        # 1. Sinh nhóm tiếng Việt
        attempts = 0
        vn_collected = []
        while len(vn_collected) < target_each and attempts < 1000:
            attempts += 1
            kw = cls.generate_single_vn()
            if is_valid_keyword(kw, min_words=3, max_words=6):
                kw_low = kw.lower()
                if kw_low not in seen:
                    seen.add(kw_low)
                    vn_collected.append(kw)

        # 2. Sinh nhóm tiếng Anh
        attempts = 0
        en_collected = []
        needed_en = count - len(vn_collected)
        while len(en_collected) < needed_en and attempts < 1000:
            attempts += 1
            kw = cls.generate_single_en()
            if is_valid_keyword(kw, min_words=3, max_words=6):
                kw_low = kw.lower()
                if kw_low not in seen:
                    seen.add(kw_low)
                    en_collected.append(kw)

        # Đan xen 1 Việt - 1 Anh
        for v, e in zip(vn_collected, en_collected):
            results.append(v)
            results.append(e)

        # Nếu còn dư lẻ
        rem_vn = vn_collected[len(results)//2:]
        rem_en = en_collected[len(results)//2:]
        results.extend(rem_vn)
        results.extend(rem_en)

        # Nếu vẫn thiếu do trùng lặp, sinh bổ sung linh hoạt
        while len(results) < count:
            is_vn = (len(results) % 2 == 0)
            kw = cls.generate_single_vn() if is_vn else cls.generate_single_en()
            if is_valid_keyword(kw, 3, 6):
                kw_low = kw.lower()
                if kw_low not in seen:
                    seen.add(kw_low)
                    results.append(kw)

        random.shuffle(results)
        return results[:count]


def generate_new_keywords(count=50, existing_set=None):
    """
    Hàm sinh từ khóa chính thức:
    - Đảm bảo trả về đúng CHÍNH XÁC `count` (50) từ khóa mới hoàn toàn.
    - Đảm bảo 100% từ khóa có độ dài từ 3 đến 6 từ.
    - Đan xen 50% tiếng Anh & 50% tiếng Việt.
    - Ưu tiên gọi AI (Gemini API) nếu có cấu hình key; tự động fallback sang Semantic NLP Engine.
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
    collected = []

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
            print(f"[!] Gemini API không khả dụng ({e}), sử dụng Semantic NLP Combinatorial Engine...", flush=True)

    # 2. Sinh bằng Semantic NLP Engine cho đủ chính xác `count` từ khóa
    if len(collected) < count:
        needed = count - len(collected)
        synthesized = SemanticNLPEngine.generate_batch(count=needed, seen=seen)
        collected.extend(synthesized)

    random.shuffle(collected)
    return collected[:count]


def append_keywords_to_file(new_keywords):
    """Lưu thêm các từ khóa mới vào cuối keywords.txt"""
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
