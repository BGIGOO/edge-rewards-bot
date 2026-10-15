---
trigger: always_on
---

# 02. Quy tắc Tối ưu hóa Bot (Edge & Android) và Database

## 1. Tối ưu hóa Trình duyệt Edge (`edge_rewards_bot.py` -> `src/bots/edge/`)
- **Tách biệt Khởi tạo và Kịch bản:** Tách phần cấu hình trình duyệt/anti-detect vào `browser.py` và phần kịch bản tìm kiếm/nhận điểm vào `searcher.py`.
- **Chống rò rỉ bộ nhớ (Memory Leak):** Quá trình khởi tạo và chạy trình duyệt Edge bắt buộc phải nằm trong cấu trúc `try...finally` hoặc Context Manager (`with`) để đảm bảo tiến trình trình duyệt luôn được đóng (`driver.quit()` / `context.close()`) ngay cả khi xảy ra lỗi giữa chừng.
- **Hạn chế `time.sleep` cứng khi chờ tải trang:** Sử dụng cơ chế chờ thông minh (Explicit Wait) khi đợi phần tử xuất hiện trên DOM. Chỉ sử dụng `sleep` ngẫu nhiên (random delay) khi mô phỏng tốc độ gõ phím và thời gian nghỉ giữa 2 lần tìm kiếm của người thật.

## 2. Tối ưu hóa Android ADB (`android_checkin.py` -> `src/bots/android/`)
- **Tách biệt tầng giao tiếp ADB:** Mọi lệnh gọi `subprocess` tới `adb` (tap, swipe, screencap, pull) phải được gom vào file `adb_client.py`. File `checkin.py` chỉ gọi lại các hàm này.
- **Bắt buộc có Timeout:** Mọi lệnh `subprocess.run()` gọi ADB bắt buộc phải có tham số `timeout=15` (hoặc phù hợp) và bắt ngoại lệ `subprocess.TimeoutExpired`. Tuyệt đối không để một lệnh ADB bị treo làm đơ toàn bộ luồng của Web Server.
- **Lưu ảnh đúng chỗ:** Mọi ảnh chụp màn hình kiểm tra trạng thái trước/sau điểm danh phải lưu vào `data/screenshots/`.

## 3. Tối ưu hóa SQLite (`db.py` -> `src/core/db.py`)
- Vì cả `web_server.py` và các luồng chạy Bot đều đọc/ghi vào `rewards_bot.db` cùng lúc, khi khởi tạo kết nối SQLite bắt buộc phải:
  1. Thiết lập `timeout=30.0` trong `sqlite3.connect()`.
  2. Kích hoạt chế độ WAL bằng lệnh `PRAGMA journal_mode=WAL;` để cho phép đọc và ghi đồng thời mà không bị lỗi `sqlite3.OperationalError: database is locked`.