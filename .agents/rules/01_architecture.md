---
trigger: always_on
---

# 01. Quy tắc Kiến trúc Hệ thống & Quản lý Đường dẫn (Architecture & Paths)

## 1. Nguyên tắc làm việc của AI (Vibe Coding Workflow)
- **Không sửa code mù quáng:** Trước khi tái cấu trúc (refactor) hoặc thêm tính năng lớn, bắt buộc liệt kê danh sách các file sẽ bị ảnh hưởng và giải thích lý do trước khi viết code.
- **Giới hạn độ dài file:** Không để bất kỳ file `.py` hoặc `.js` nào vượt quá 250 dòng. Nếu vượt quá, phải chủ động tách thành các module nhỏ hơn theo đúng chức năng.
- **Bảo toàn tính năng:** Khi tách file hoặc di chuyển thư mục, phải kiểm tra kỹ các lệnh `import` để đảm bảo không làm gãy luồng chạy hiện tại của hệ thống.

## 2. Cấu trúc thư mục chuẩn của dự án `auto_microsoft`
Mọi file tạo mới hoặc tái cấu trúc phải tuân thủ nghiêm ngặt cấu trúc phân tầng sau:
- `config/`: Chứa `config.json`.
- `data/`: Chứa TOÀN BỘ dữ liệu phát sinh khi chạy (Runtime Data). Tuyệt đối không lưu dữ liệu chạy ở thư mục gốc hoặc trong thư mục `web/`.
  - `data/profiles/`: Chứa các thư mục `edge_profile`, `edge_profile_2`, v.v.
  - `data/screenshots/`: Chứa toàn bộ ảnh chụp màn hình debug (`android_checkin_before.png`, `android_checkin_after.png`, `test_device_screen.png`).
  - `data/rewards_bot.db`: File cơ sở dữ liệu SQLite.
  - `data/keywords.txt`: File danh sách từ khóa.
- `src/`: Chứa toàn bộ mã nguồn Python đã được mô-đun hóa:
  - `src/core/`: `paths.py` (quản lý đường dẫn), `db.py` (SQLite), `logger.py`.
  - `src/services/`: `ai_keywords.py`.
  - `src/bots/edge/`: Logic điều khiển trình duyệt Edge.
  - `src/bots/android/`: Logic điều khiển ADB và điểm danh Android.
  - `src/api/`: `web_server.py` (Backend API).
- `web/`: Chỉ chứa các file tĩnh của Frontend (`index.html`, `style.css`, `app.js`).

## 3. Quản lý đường dẫn (Path Management)
- **Cấm dùng chuỗi đường dẫn tương đối cứng (Hardcoded Relative Paths):** Tuyệt đối không viết kiểu `"web/android_checkin_before.png"` hay `"edge_profile_2"`.
- Bắt buộc sử dụng `pathlib.Path` tính từ gốc dự án (`ROOT_DIR = Path(__file__).resolve().parent...`) được định nghĩa tập trung tại `src/core/paths.py`.