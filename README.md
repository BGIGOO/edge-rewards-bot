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

3. **Hỗ trợ đa Profile / Đa tài khoản**:
   - Quản lý độc lập các tài khoản (ví dụ Profile 1 và Profile 2), mỗi tài khoản có phiên làm việc riêng biệt (`./edge_profile` và `./edge_profile_2`), không lo bị xung đột cookie hay đăng xuất.
   - Hỗ trợ chọn chạy riêng từng tài khoản hoặc tự động chạy tuần tự cả 2 tài khoản trong 1 lần bấm!

4. **Kho từ khóa phong phú**:
   - Hơn 150 từ khóa tìm kiếm thực tế (tiếng Việt và tiếng Anh) thuộc các chủ đề: thời sự, công nghệ, nấu ăn, du lịch, đời sống...
   - Tự động xáo trộn ngẫu nhiên mỗi lần chạy, không bao giờ trùng lặp.

---

## 📂 Cấu trúc thư mục

```
auto_microsoft/
├── config.json              # File cấu hình (danh sách profiles, số lượt search, delay, cooldown...)
├── keywords.txt             # Danh sách các từ khóa tìm kiếm thực tế
├── edge_rewards_bot.py      # File mã nguồn Python chính (hỗ trợ --profile và --mode)
├── run_bot.bat              # Menu chọn tài khoản và chế độ nhanh
├── run_pc.bat               # Chạy nhanh chế độ PC với lựa chọn profile
├── run_mobile.bat           # Chạy nhanh chế độ Mobile với lựa chọn profile
└── README.md                # Hướng dẫn chi tiết
```

---

## 🚀 Cách sử dụng

### Cách 1: Chạy nhanh bằng 1 cú click (Khuyên dùng)
- Click đúp chuột vào file **`run_bot.bat`**.
- Chọn tài khoản muốn chạy:
  - `[1]`: Profile 1 (Tài khoản 1)
  - `[2]`: Profile 2 (Tài khoản 2)
  - `[3]`: Chạy lần lượt cả 2 Profile
- Chọn chế độ tìm kiếm:
  - `[1]`: Desktop (PC)
  - `[2]`: Mobile
  - `[3]`: Cả hai (Desktop rồi Mobile)

### Cách 2: Chạy bằng dòng lệnh Terminal
```powershell
# Chạy tương tác (menu hỏi chọn Profile và Mode)
python edge_rewards_bot.py

# Chạy cụ thể Profile 1 với chế độ Desktop
python edge_rewards_bot.py --profile 1 --mode desktop

# Chạy Profile 2 với cả hai chế độ
python edge_rewards_bot.py --profile 2 --mode all

# Chạy tự động lần lượt cả 2 tài khoản
python edge_rewards_bot.py --profile all --mode all
```

---

## ⚙️ Tùy chỉnh thông số trong `config.json`

Bạn có thể mở file `config.json` bằng bất kỳ trình soạn thảo nào để chỉnh thông số:

```json
{
  "search_settings": {
    "pc_searches": 31,                 // Số lượt tìm kiếm PC
    "mobile_searches": 21,             // Số lượt tìm kiếm Mobile
    "min_delay_seconds": 12,           // Độ trễ tối thiểu giữa các lượt tìm kiếm (giây)
    "max_delay_seconds": 22,           // Độ trễ tối đa giữa các lượt tìm kiếm (giây)
    "enable_cooldown_batches": true,   // Bật/tắt chế độ ngắt quãng an toàn
    "batch_size": 4,                   // Cứ mỗi 4 lượt tìm kiếm...
    "batch_cooldown_minutes": 5,       // ...thì nghỉ 5-15 phút (nếu tài khoản bị cooldown)
    "enable_smooth_scrolling": true,   // Bật cuộn trang mô phỏng đọc bài
    "enable_mouse_movement": true,     // Bật rê chuột ngẫu nhiên
    "random_click_chance": 0.25,       // Tỷ lệ click vào đọc kết quả tự nhiên (CTR)
    "human_typing_speed_min": 0.04,    // Tốc độ gõ phím nhỏ nhất (giây/phím)
    "human_typing_speed_max": 0.10     // Tốc độ gõ phím lớn nhất (giây/phím)
  },
  "browser_settings": {
    "profile_directory_path": "./edge_profile",
    "headless": false,                 // Hiện cửa sổ duyệt web để theo dõi trực quan
    "mobile_device_name": "Pixel 7"    // Thiết bị giả lập khi search Mobile
  },
  "profiles": [
    {
      "id": "1",
      "name": "Tài khoản 1 (Chính)",
      "path": "./edge_profile"
    },
    {
      "id": "2",
      "name": "Tài khoản 2 (Phụ)",
      "path": "./edge_profile_2"
    }
  ]
}
```

> **Mẹo An Toàn**:
> - Nếu tài khoản của bạn bị Microsoft áp dụng cơ chế *15-minute search cooldown* (chỉ tính điểm 3-4 lần search mỗi 15 phút), bạn hãy đổi `"enable_cooldown_batches": true` trong `config.json`. Bot sẽ tự động search 4 lượt rồi ngủ 15 phút, sau đó tự search tiếp cho tới khi hoàn tất.
