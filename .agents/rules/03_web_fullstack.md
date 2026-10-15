---
trigger: always_on
---

# 03. Quy tắc Thiết kế Backend API (`web_server.py`) & Frontend (`web/`)

## 1. Nguyên tắc tại Backend (`web_server.py`)
- **Không chạy tác vụ nặng làm nghẽn (Block) luồng chính của Web Server:** Các tác vụ chạy Bot Edge hoặc chạy điểm danh Android tốn nhiều thời gian bắt buộc phải được đẩy vào Background Thread/Task hoặc Worker riêng. API chỉ trả về trạng thái `"started"` ngay lập tức cho giao diện.
- **Chuẩn hóa định dạng trả về (JSON Response):** Mọi API endpoint trong `web_server.py` phải trả về định dạng JSON thống nhất:
  `{"status": "success" | "error", "data": ..., "message": "..."}`
- Nếu cần hiển thị ảnh chụp màn hình từ `data/screenshots/` lên giao diện Web, hãy tạo một route/static mount riêng trong `web_server.py` trỏ tới `data/screenshots/` thay vì lưu thẳng ảnh vào thư mục `web/`.

## 2. Nguyên tắc tại Frontend (`web/index.html`, `web/app.js`, `web/style.css`)
- **Tách biệt trách nhiệm trong `app.js`:**
  - Gom tất cả các hàm gọi `fetch()` vào một đối tượng `ApiService` ở đầu file.
  - Mọi lệnh gọi `fetch()` phải có `try...catch` để bắt lỗi mạng và hiển thị thông báo rõ ràng lên giao diện, không để lỗi im lặng trong Console.
  - Khi người dùng bấm nút chạy Bot (Edge hoặc Android), phải khóa nút bấm (disable button) và hiển thị trạng thái đang chạy (loading) để tránh người dùng bấm đúp nhiều lần gây tạo trùng lặp nhiều tiến trình Bot.