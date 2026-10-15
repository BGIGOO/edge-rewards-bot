# -*- coding: utf-8 -*-
"""
src/core/paths.py
=================
Quan ly tap trung TAT CA duong dan trong du an auto_microsoft.

Quy tac:
- TUYET DOI khong hardcode duong dan o bat ky file nao khac.
- Moi file chi import tu module nay.
- Su dung pathlib.Path de dam bao tuong thich da nen tang.
"""

from pathlib import Path

# -- Goc du an ---------------------------------------------------------------
# src/core/paths.py -> parent -> src/core -> parent -> src -> parent -> root
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent

# -- Thu muc du lieu runtime (KHONG bao gio commit len git) ------------------
DATA_DIR: Path = ROOT_DIR / "data"
PROFILES_DIR: Path = DATA_DIR / "profiles"
SCREENSHOTS_DIR: Path = DATA_DIR / "screenshots"

# -- File du lieu runtime ----------------------------------------------------
DB_PATH: Path = DATA_DIR / "rewards_bot.db"
KEYWORDS_PATH: Path = DATA_DIR / "keywords.txt"

# -- File cau hinh (van o goc du an, duoc version control) -------------------
CONFIG_PATH: Path = ROOT_DIR / "config.json"

# -- Thu muc ma nguon --------------------------------------------------------
SRC_DIR: Path = ROOT_DIR / "src"
WEB_DIR: Path = ROOT_DIR / "web"


def ensure_dirs() -> None:
    """Dam bao tat ca thu muc data ton tai. Goi khi khoi dong ung dung."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def get_profile_dir(profile_id_or_name: str) -> Path:
    """
    Tra ve duong dan thu muc profile theo ID.
    Vi du: get_profile_dir("1") -> data/profiles/edge_profile
             get_profile_dir("2") -> data/profiles/edge_profile_2
    """
    pid = str(profile_id_or_name).strip()
    folder = "edge_profile" if pid == "1" else f"edge_profile_{pid}"
    return PROFILES_DIR / folder


def resolve_profile_path(path_str: str) -> Path:
    """
    Chuyen doi duong dan profile tu config (co the la tuong doi hoac tuyet doi)
    sang duong dan tuyet doi dua tren ROOT_DIR.

    Vi du:
        "./edge_profile"        -> data/profiles/edge_profile
        "./edge_profile_2"      -> data/profiles/edge_profile_2
        "D:/abs/path"           -> D:/abs/path (giu nguyen neu la absolute)
    """
    p = Path(path_str.strip())

    if p.is_absolute():
        return p

    # Chuan hoa relative path: loai bo "./" o dau
    path_norm = path_str.lstrip("./").lstrip("\\")

    # Neu path bat dau bang "edge_profile" -> gom ve PROFILES_DIR
    if path_norm.startswith("edge_profile"):
        return PROFILES_DIR / path_norm

    # Neu path da co "data/" -> resolve tu ROOT_DIR
    if path_norm.startswith("data"):
        return ROOT_DIR / path_norm

    # Fallback: resolve tu ROOT_DIR
    return (ROOT_DIR / p).resolve()


# Khoi tao thu muc khi import module
ensure_dirs()
