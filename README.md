# 🌟 Tool Tự Động Tìm Kiếm Microsoft Edge Kiếm Điểm Rewards (Anti-Ban & Human Mimicking)

Tool Python tự động hóa tìm kiếm trên **Microsoft Edge** để cày trọn vẹn điểm **Microsoft Rewards** hàng ngày cho cả **Desktop (PC)** và **Mobile (Điện thoại)**, được thiết kế mô phỏng hoàn hảo hành vi người dùng thật nhằm phòng tránh bị phát hiện, cooldown hoặc khóa tài khoản.

---

## 🎯 Các tính năng nổi bật

1. **Thao tác mô phỏng người thật 100% (Anti-Ban / Cooldown Safe)**:
   - **Gõ phím từng ký tự (Human Typing)**: Không dán từ khóa đồng loạt, mà gõ từng phím với độ trễ ngẫu nhiên (80ms - 200ms) kèm nhịp nghỉ ngẫu nhiên.
   - **Cuộn trang tự nhiên (Human Browsing)**: Sau khi tìm kiếm, bot tự động cuộn trang mượt mà lên xuống như người dùng đang đọc kết quả.
   - **Thời gian dừng nghỉ ngẫu nhiên (Dwell Time)**: Giãn cách 10s - 20s giữa các lần tìm kiếm (có thể tùy chỉnh).
   - **Xóa dấu vết bot**: Tắt cờ Automation của trình duyệt và xóa cờ `navigator.webdriver`.

2. **Tìm kiếm cả 2 nền tảng để tối đa hóa điểm**:
   - **Chế độ PC (Desktop)**: Thực hiện các lượt tìm kiếm máy tính thông thường.
   - **Chế độ Mobile (Giả lập iPhone)**: Tự động đổi User-Agent và kích thước màn hình sang iPhone/Android để nhận trọn điểm tìm kiếm di động.

3. **Sử dụng trực tiếp Profile Edge thật**:
   - Sử dụng đúng Profile hiện tại của bạn (`User Data/Default`), không cần nhập lại mật khẩu hay mã OTP.
   - Có cơ chế cảnh báo hoặc tự đóng Edge đang chạy để tránh lỗi khóa dữ liệu (file lock).

4. **Kho từ khóa phong phú**:
   - Hơn 150 từ khóa tìm kiếm thực tế (tiếng Việt và tiếng Anh) thuộc các chủ đề: thời sự, công nghệ, nấu ăn, du lịch, đời sống...
   - Tự động xáo trộn ngẫu nhiên mỗi lần chạy, không bao giờ trùng lặp.

---

## 📂 Cấu trúc thư mục

```
auto_microsoft/
├── config.json              # File cấu hình (số lượt search, delay, cooldown...)
├── keywords.txt             # Danh sách các từ khóa tìm kiếm thực tế
├── edge_rewards_bot.py      # File mã nguồn Python chính
├── run_bot.bat              # File click đúp chạy nhanh trên Windows
└── README.md                # Hướng dẫn chi tiết
```

---

## 🚀 Cách sử dụng

### Cách 1: Chạy nhanh bằng 1 cú click (Khuyên dùng)
- Click đúp chuột vào file **`run_bot.bat`**.
- Nếu Microsoft Edge đang mở, tool sẽ hỏi bạn có muốn đóng Edge không (`y/n`). Nhấn **`y`** (hoặc Enter) để tool đóng Edge và bắt đầu chạy.

### Cách 2: Chạy bằng dòng lệnh Terminal
```powershell
# Chuyển vào thư mục tool
cd d:\Hoc_Tap\file_vs_code\DoAn_TTTN\auto_microsoft

# Chạy script
python edge_rewards_bot.py
```

---

## ⚙️ Tùy chỉnh thông số trong `config.json`

Bạn có thể mở file `config.json` bằng bất kỳ trình soạn thảo nào để chỉnh thông số:

```json
{
  "search_settings": {
    "pc_searches": 32,                 // Số lượt tìm kiếm PC (Level 2 thường cần 30 lượt = 90 điểm)
    "mobile_searches": 22,             // Số lượt tìm kiếm Mobile (Level 2 thường cần 20 lượt = 60 điểm)
    "min_delay_seconds": 10,           // Độ trễ tối thiểu giữa các lượt tìm kiếm (giây)
    "max_delay_seconds": 20,           // Độ trễ tối đa giữa các lượt tìm kiếm (giây)
    "enable_cooldown_batches": false,  // Bật/tắt chế độ ngắt quãng an toàn (mặc định tắt)
    "batch_size": 4,                   // Cứ mỗi 4 lượt tìm kiếm...
    "batch_cooldown_minutes": 15,      // ...thì nghỉ 15 phút (nếu tài khoản của bạn bị giới hạn cooldown)
    "enable_smooth_scrolling": true,   // Bật cuộn trang mô phỏng đọc bài
    "human_typing_speed_min": 0.08,    // Tốc độ gõ phím nhỏ nhất (giây/phím)
    "human_typing_speed_max": 0.20     // Tốc độ gõ phím lớn nhất (giây/phím)
  },
  "browser_settings": {
    "use_system_edge_profile": true,   // Dùng Profile Edge của máy (không cần login lại)
    "user_data_path": "auto",          // Tự động nhận diện đường dẫn Profile
    "profile_directory": "Default",    // Tên profile (Default là tài khoản chính)
    "headless": false,                 // Hiện cửa sổ duyệt web để theo dõi trực quan
    "mobile_device_name": "iPhone 12 Pro" // Thiết bị giả lập khi search Mobile
  }
}
```

> **Mẹo An Toàn**:
> - Nếu tài khoản của bạn bị Microsoft áp dụng cơ chế *15-minute search cooldown* (chỉ tính điểm 3-4 lần search mỗi 15 phút), bạn hãy đổi `"enable_cooldown_batches": true` trong `config.json`. Bot sẽ tự động search 4 lượt rồi ngủ 15 phút, sau đó tự search tiếp cho tới khi hoàn tất.
