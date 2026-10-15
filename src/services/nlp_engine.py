# -*- coding: utf-8 -*-
"""
src/services/nlp_engine.py
==========================
Semantic NLP Combinatorial Engine & Validation Helpers.
Sinh từ khóa tự nhiên chuẩn 3-6 từ cân bằng Anh-Việt.
Tuân thủ rule 01_architecture (< 250 dòng).
"""

import random
import re
from typing import List, Set, Optional


def count_words(text: str) -> int:
    """Đếm số từ trong cụm từ."""
    return len(text.strip().split())


def clean_keyword(line: str) -> str:
    """Làm sạch chuỗi từ khóa."""
    if not line:
        return ""
    cleaned = re.sub(r"^[\d\.\-\*\•\>\s]+", "", line).strip()
    cleaned = cleaned.strip("\"'[]`").strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_valid_keyword(kw: str, min_words: int = 3, max_words: int = 6) -> bool:
    """Kiểm tra từ khóa đạt chuẩn từ min_words đến max_words từ."""
    if not kw:
        return False
    wcount = count_words(kw)
    if not (min_words <= wcount <= max_words):
        return False
    if "http" in kw or ".com" in kw or len(kw) > 65:
        return False
    return True


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
        "làm sườn xào", "nấu phở bò", "làm bánh mì bơ", "rán nem giòn", "làm gà chiên",
        "nấu canh chua", "kho thịt trứng", "nấu bò sốt vang", "pha trà sữa", "pha cà phê muối",
        "làm bánh flan", "nấu chè hạt sen", "làm nước ép cần", "chế biến cá hồi", "nấu lẩu thái",
        "làm salad ức gà", "pha trà đào sả", "nấu bún bò huế", "làm bánh bông lan", "nấu cháo sườn",
        "luộc gà da giòn", "làm kim chi cải", "nướng thịt xiên", "nấu súp cua nấm",
        "du lịch đà lạt", "khám phá phú quốc", "đi phượt sapa", "phượt hà giang", "đi vịnh hạ long",
        "du lịch côn đảo", "khám phá phú quý", "thăm phố cổ hội an", "du lịch biển quy nhơn",
        "đi bà nà hills", "thưởng thức ẩm thực huế", "du lịch đảo cát bà", "ngắm lúa mù cang chải",
        "khám phá hang sơn đoòng", "du lịch miền tây sông nước", "phượt đèo mã pí lèng",
        "tối ưu windows 11", "tiết kiệm pin laptop", "tăng tốc mạng wifi", "chọn mua bàn phím",
        "chọn tai nghe bluetooth", "mua chuột không dây", "lắp ráp máy tính", "chọn mua iphone 16",
        "chọn card màn hình", "mua màn hình đồ họa", "dọn dẹp bộ nhớ máy", "bảo vệ pin điện thoại",
        "sửa lỗi máy tính chậm", "chọn mua macbook m3", "khôi phục dữ liệu ổ", "cài đặt lại win",
        "tập yoga buổi sáng", "giảm mỡ bụng nhanh", "chạy bộ mỗi ngày", "ngủ ngon sâu giấc",
        "uống nước đúng cách", "tập gym tăng cơ", "ăn kiêng eat clean", "thiền định giảm stress",
        "giảm đau vai gáy", "tăng sức đề kháng", "chăm sóc da mặt", "uống trà xanh mỗi sáng",
        "thải độc gan tự nhiên", "cải thiện trí nhớ", "tập plank đúng tư thế", "giãn cơ sau chạy",
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
        "learn python fast", "start web development", "build custom pc", "clean mechanical keyboard",
        "speed up windows", "fix slow laptop", "choose wireless mouse", "extend battery life",
        "troubleshoot wifi connection", "learn machine learning", "backup data safely", "setup dual monitor",
        "pick budget monitor", "learn prompt engineering", "secure home network", "learn git basics",
        "start morning yoga", "burn belly fat", "build strong core", "improve sleep quality",
        "drink warm water", "walk daily steps", "meditate ten minutes", "eat healthy meals",
        "stretch after workout", "gain lean muscle", "reduce daily stress", "stay well hydrated",
        "maintain healthy posture", "boost immune system", "do daily cardio",
        "bake garlic bread", "cook pasta carbonara", "make fluffy pancakes", "bake chocolate cookies",
        "brew cold coffee", "cook chicken soup", "make matcha latte", "grill beef burger",
        "make fruit smoothie", "roast vegetables nicely", "prepare healthy breakfast", "cook fried rice",
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
    def generate_single_vn(cls) -> str:
        """Sinh 1 câu tiếng Việt chuẩn xác từ 3 đến 6 từ."""
        action = random.choice(cls.VN_ACTIONS)
        topic = random.choice(cls.VN_TOPICS)
        base_words = count_words(action) + count_words(topic)

        max_suffix_words = max(0, 6 - base_words)
        min_suffix_words = max(0, 3 - base_words)
        possible_lens = [l for l in cls.VN_SUFFIX_OPTIONS.keys() if min_suffix_words <= l <= max_suffix_words]
        chosen_len = random.choice(possible_lens) if possible_lens else 0

        suffix = random.choice(cls.VN_SUFFIX_OPTIONS.get(chosen_len, [""]))
        query = f"{action} {topic} {suffix}".strip()
        return clean_keyword(query)

    @classmethod
    def generate_single_en(cls) -> str:
        """Sinh 1 câu tiếng Anh chuẩn xác từ 3 đến 6 từ."""
        action = random.choice(cls.EN_ACTIONS)
        topic = random.choice(cls.EN_TOPICS)
        base_words = count_words(action) + count_words(topic)

        max_suffix_words = max(0, 6 - base_words)
        min_suffix_words = max(0, 3 - base_words)
        possible_lens = [l for l in cls.EN_SUFFIX_OPTIONS.keys() if min_suffix_words <= l <= max_suffix_words]
        chosen_len = random.choice(possible_lens) if possible_lens else 0

        suffix = random.choice(cls.EN_SUFFIX_OPTIONS.get(chosen_len, [""]))
        query = f"{action} {topic} {suffix}".strip()
        return clean_keyword(query)

    @classmethod
    def generate_batch(cls, count: int = 50, seen: Optional[Set[str]] = None) -> List[str]:
        """Sinh batch N từ khóa cân bằng 50% Anh - 50% Việt, đúng chuẩn 3-6 từ."""
        seen = seen or set()
        results = []
        target_each = count // 2

        # 1. Sinh tiếng Việt
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

        # 2. Sinh tiếng Anh
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

        for v, e in zip(vn_collected, en_collected):
            results.append(v)
            results.append(e)

        results.extend(vn_collected[len(results)//2:])
        results.extend(en_collected[len(results)//2:])

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
