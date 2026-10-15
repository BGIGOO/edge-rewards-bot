# -*- coding: utf-8 -*-
"""
src/bots/android/screen_analyzer.py
==================================
Chup anh man hinh qua ADB va phan tich thi giac may tinh (Computer Vision).
Nhan dien the diem danh, trang thai da diem danh (dau check) va toa do nut bam.
Tuan thu rule 01_architecture (< 250 dong).
"""

import os
import subprocess
from typing import Optional, Tuple, Any

import numpy as np
from PIL import Image

from src.core.paths import SCREENSHOTS_DIR
from src.bots.android.adb_client import log


def capture_screenshot(adb_client: Any, save_path: Optional[str] = None) -> Optional[Image.Image]:
    """Chup anh man hinh qua ADB va luu vao SCREENSHOTS_DIR hoac save_path."""
    remote_tmp = "/data/local/tmp/checkin_snap.png"
    local_target = save_path or str(SCREENSHOTS_DIR / "checkin_snap.png")
    os.makedirs(os.path.dirname(os.path.abspath(local_target)), exist_ok=True)

    try:
        adb_client._adb_shell("screencap", "-p", remote_tmp, timeout=15)
        cmd = [adb_client.adb, "-s", adb_client.device, "pull", remote_tmp, local_target]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if r.returncode == 0 and os.path.exists(local_target) and os.path.getsize(local_target) > 5000:
            return Image.open(local_target).convert("RGB")
        else:
            log(f"Lỗi pull ảnh: {r.stderr}", "warn")
    except Exception as e:
        log(f"Lỗi chụp ảnh qua ADB ({e})", "warn")
    return None


def find_today_circle(img: Image.Image) -> Optional[Tuple[int, int]]:
    """Tim vong tron ngay hom nay (vien cam) trong the diem danh legacy."""
    w, h = img.size
    arr = np.asarray(img)
    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)

    orange = (r > 190) & (g > 95) & (g < 205) & (b < 130)
    y0, y1 = int(h * 0.15), int(h * 0.70)
    band = orange[y0:y1, :]
    colsum = band.sum(axis=0)

    if colsum.max() == 0:
        return None

    thresh = colsum.max() * 0.22
    groups = []
    in_g = False
    start = 0

    for x, v in enumerate(colsum):
        if v > thresh and not in_g:
            in_g = True
            start = x
        elif v <= thresh and in_g:
            in_g = False
            groups.append((start, x))
    if in_g:
        groups.append((start, len(colsum)))

    groups = [(a, z) for a, z in groups if z - a > 10]
    groups.sort()

    for a, z in groups:
        cx = (a + z) // 2
        col = band[:, a:z]
        rowsum = col.sum(axis=1)
        cy = y0 + int(np.argmax(rowsum))

        x0, x1 = max(cx - 10, 0), min(cx + 11, w)
        yy0, yy1 = max(cy - 10, 0), min(cy + 11, h)
        patch = arr[yy0:yy1, x0:x1].astype(int)
        white_ratio = ((patch[:, :, 0] > 215) & (patch[:, :, 1] > 215) & (patch[:, :, 2] > 215)).mean()

        if white_ratio < 0.02:
            return cx, cy

    return None


def check_daily_streak_status(img: Image.Image) -> Tuple[bool, Tuple[int, int]]:
    """
    Kiem tra the 'Chuoi lien tiep' tren App Bing:
    Phat hien dau checkmark xanh la (✓) tai vi tri huy hieu.
    Tra ve (already_done, (tap_x, tap_y)).
    """
    w, h = img.size
    arr = np.asarray(img)

    x0, x1 = int(w * 0.61), int(w * 0.73)
    y0, y1 = int(h * 0.31), int(h * 0.50)

    patch = arr[y0:y1, x0:x1].astype(int)
    r, g, b = patch[:, :, 0], patch[:, :, 1], patch[:, :, 2]
    green_mask = (g > 120) & (g > r + 50) & (g > b + 30)
    green_pixels = int(green_mask.sum())

    card_tap_x = int(w * 0.50)
    card_tap_y = int(h * 0.417)

    if green_pixels > 50:
        log(f"Phát hiện dấu check xanh lá ({green_pixels} px) -> Đã điểm danh!", "success")
        return True, (card_tap_x, card_tap_y)

    log(f"Hàng 'Đăng ký vào' chưa có dấu check xanh lá ({green_pixels} px) -> Chưa điểm danh.", "info")
    return False, (card_tap_x, card_tap_y)
