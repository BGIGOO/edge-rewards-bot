# ⚡ Microsoft Rewards Auto Bot - Anti-Ban Multi-Account Dashboard (4+ Accs)

Hệ thống bot tự động hóa tìm kiếm trên **Microsoft Edge** thông minh, an toàn, hỗ trợ cày trọn vẹn điểm **Microsoft Rewards** hàng ngày cho **nhiều tài khoản cùng lúc (4+ tài khoản)** trên cả 2 nền tảng **Desktop (PC)** và **Mobile (Điện thoại giả lập)**.

Tích hợp giao diện quản lý **Web UI Dashboard** hiện đại theo phong cách **Playful Geometric**, theo dõi Live Terminal trực tiếp và cơ chế **Anti-Ban / Human Mimicking** chuẩn mực nhằm phòng tránh phát hiện, cooldown hoặc khóa tài khoản.

---

## 🌟 Tính Năng Nổi Bật

- 🛡️ **Mô phỏng hành vi người dùng thật 100% (Human Mimicking)**:
  - **Gõ phím từng ký tự (Human Typing)**: Tốc độ gõ phím ngẫu nhiên (40ms – 100ms/ký tự) kèm nhịp dừng tự nhiên như người gõ thật.
  - **Cuộn trang đọc nội dung (Human Browsing)**: Tự động cuộn trang mượt mà lên xuống để xem bài viết sau khi tìm kiếm.
  - **Tương tác ngẫu nhiên (Natural CTR)**: Tự động rê chuột và click ngẫu nhiên vào các kết quả tìm kiếm để đọc trang.
  - **Xóa dấu vết tự động hóa**: Xóa cờ `navigator.webdriver`, ẩn cờ automation của Chromium.
- ⏱️ **Cơ chế chống giới hạn tìm kiếm (15-Minute Cooldown Safe)**:
  - Tự động chia nhỏ đợt tìm kiếm (mỗi đợt 3-4 lần tìm kiếm), sau đó tạm nghỉ an toàn trước khi tiếp tục, giúp vượt qua cơ chế giới hạn điểm của Microsoft.
- 📱 **Hỗ trợ trọn vẹn 2 nền tảng PC & Mobile**:
  - **PC (Desktop)**: Tự động hoàn thành toàn bộ lượt tìm kiếm trên máy tính (mặc định 30+ lượt).
  - **Mobile (Điện thoại)**: Tự động chuyển đổi User-Agent và viewport chuẩn màn hình di động (Pixel 7 / iPhone) để nhận tối đa điểm thưởng Mobile.
- 👥 **Hệ thống Quản lý Đa Tài khoản (Multi-Account 4+ Profiles)**:
  - Quản lý tách biệt từng tài khoản trong các thư mục Profile độc lập (`edge_profile`, `edge_profile_2`, `edge_profile_3`, `edge_profile_4`...).
  - Tuyệt đối **không bị xung đột cookie, không bị ghi đè phiên đăng nhập hay văng session**.
  - Đăng nhập 1 lần duy nhất cho mỗi tài khoản, lưu phiên vĩnh viễn trên máy.
  - Hỗ trợ thêm không giới hạn số lượng tài khoản (Acc 5, Acc 6...) trực tiếp từ Web UI.
- 🎨 **Web UI Dashboard Trực Quan & Hiện Đại**:
  - Giao diện Dashboard thiết kế theo hệ chuẩn **Playful Geometric** (Warm Cream `#FFFDF5`, Deep Navy `#1E293B`, nút bấm Pop Shadows).
  - Thao tác **1-Click** để chạy toàn bộ 4 tài khoản nối tiếp nhau (tự động nghỉ an toàn giữa các tài khoản).
  - Màn hình **Live Terminal** cập nhật trực tiếp tiến trình, từ khóa đang gõ, điểm số kiếm được theo thời gian thực.
  - Nút **Dừng khẩn cấp (Emergency Stop)** ngắt tiến trình an toàn ngay lập tức.
  - Quản lý cấu hình (`config.json`) và kho từ khóa (`keywords.txt`) trực quan dạng modal.

---

## 📂 Cấu Trúc Thư Mục Tinh Gọn

Dự án được tối ưu tối giản, tinh gọn và rõ ràng:

```
auto_microsoft/
├── config.json              # File cấu hình (danh sách profiles, số lượt search, độ trễ, cooldown...)
├── keywords.txt             # Kho từ khóa tìm kiếm tự nhiên phong phú (Việt + Anh)
├── requirements.txt         # Danh sách thư viện Python cần thiết
├── edge_rewards_bot.py      # Mã nguồn bot cốt lõi (tìm kiếm, cuộn trang, giả lập thao tác)
├── web_server.py            # Backend máy chủ quản lý Web Dashboard (Starlette / Uvicorn)
├── start_web_ui.bat         # 🚀 [Khuyên dùng] Khởi động Giao diện Web 1-click
├── run_bot.bat              # 💻 Khởi động chạy nhanh qua Bảng đen Terminal / CMD
├── verify_anti_detection.py # Tool kiểm toán đánh giá các tiêu chuẩn an toàn Anti-Ban
├── web/                     # Giao diện người dùng Web Dashboard
│   ├── index.html           # Cấu trúc giao diện
│   ├── style.css            # Thiết kế thẩm mỹ Playful Geometric
│   └── app.js               # Logic điều khiển, WebSocket Live Log, API
└── .gitignore               # Bảo vệ bảo mật (loại trừ toàn bộ cookie, profile cá nhân)
```

---

## 🚀 Hướng Dẫn Cài Đặt (Dành Cho Người Mới Bắt Đầu)

### Bước 1: Cài đặt Python (Nếu máy tính chưa có)
1. Tải Python phiên bản 3.10 trở lên tại trang chủ: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. **Cực kỳ quan trọng**: Khi bắt đầu chạy file cài đặt, hãy **tích chọn ô `Add Python to PATH`** (hoặc `Add python.exe to PATH`) ở màn hình đầu tiên trước khi bấm **Install Now**.

### Bước 2: Tải dự án về máy
- Bạn có thể clone repo bằng Git:
  ```bash
  git clone https://github.com/BGIGOO/edge-rewards-bot.git
  cd edge-rewards-bot
  ```
- Hoặc bấm vào nút xanh **Code** trên GitHub -> chọn **Download ZIP**, sau đó giải nén ra thư mục bất kỳ trên máy tính.

> 💡 **Tin vui:** Bạn **không cần phải gõ lệnh cài đặt thư viện thủ công**. Cả hai file `start_web_ui.bat` và `run_bot.bat` đều đã được tích hợp sẵn cơ chế **tự động kiểm tra và cài đặt toàn bộ thư viện cần thiết** trong lần khởi chạy đầu tiên!

---

## 🎮 Hướng Dẫn Sử Dụng

Bạn có thể lựa chọn 1 trong 2 cách sử dụng dưới đây tùy theo sở thích:

### Cách 1: Sử Dụng Giao Diện Web UI (Khuyên Dùng - Trực Quan, Đơn Giản Nhất)

#### 1. Khởi động Web Dashboard:
- Nhấp đúp chuột vào file **`start_web_ui.bat`**.
- Hệ thống sẽ tự động khởi động server và mở trình duyệt quản lý tại địa chỉ: **`http://127.0.0.1:5000`**.

#### 2. Đăng nhập lần đầu cho các tài khoản (Chỉ cần làm 1 lần duy nhất):
- Trên giao diện Web, bạn sẽ nhìn thấy 4 Card đại diện cho 4 Profile tài khoản:
  - `Profile 1 (Chính)`
  - `Profile 2 (Phụ 1)`
  - `Profile 3 (Tài khoản 3)`
  - `Profile 4 (Tài khoản 4)`
- Bấm nút **`🔑 Đăng Nhập Edge`** tại Card của từng tài khoản:
  - Cửa sổ trình duyệt Edge sẽ mở ra trang Microsoft Rewards.
  - Bạn đăng nhập tài khoản Microsoft tương ứng của Profile đó.
  - Đăng nhập thành công xong, bạn chỉ cần **đóng cửa sổ Edge lại**.
  - Phiên đăng nhập sẽ được lưu vĩnh viễn trong thư mục Profile riêng (`edge_profile`, `edge_profile_2`...), các lần sau bot tự động nhận diện mà không bao giờ hỏi lại!

#### 3. Cày điểm hàng ngày (Thao tác 1-Click):
- Bấm nút lớn màu xanh: **`🚀 CHẠY TẤT CẢ 4 ACC (FULL PC + MOB)`**.
- Bot sẽ tự động thực hiện quy trình hoàn hảo:
  - Chạy toàn bộ PC + Mobile cho Acc 1 ➡️ Tự động dừng nghỉ an toàn (30–60s) ➡️ Chạy Acc 2 ➡️ Nghỉ ➡️ Chạy Acc 3 ➡️ Nghỉ ➡️ Chạy Acc 4.
- Theo dõi toàn bộ quá trình tại màn hình **Live Terminal** bên phải: hiển thị trực tiếp từng từ khóa đang tìm kiếm, số điểm thưởng tăng lên và thông báo hoàn thành.
- Nếu muốn ngắt giữa chừng: Bấm nút đỏ **`🛑 DỪNG KHẨN CẤP`**.

#### 4. Các tính năng mở rộng trên Web UI:
- **Chạy riêng lẻ từng phần**: Trên mỗi Card tài khoản đều có nút riêng để chạy `PC`, `Mobile`, hoặc `Full` cho riêng tài khoản đó.
- **Thêm tài khoản mới**: Bấm nút **`+ Thêm Tài Khoản`** trên thanh công cụ để mở rộng thêm Acc 5, Acc 6...
- **Cấu hình bot**: Bấm nút **`⚙️ Cấu Hình`** để điều chỉnh số lượt tìm kiếm, thời gian nghỉ (delay), bật/tắt chế độ chạy ngầm (Headless), cơ chế Cooldown.
- **Kho từ khóa**: Bấm nút **`📝 Từ Khóa`** để xem hoặc bổ sung thêm từ khóa tìm kiếm theo ý thích.

---

### Cách 2: Sử Dụng Bảng Đen Terminal (`run_bot.bat`)

Nếu bạn thích sự gọn nhẹ của màn hình dòng lệnh truyền thống:
1. Nhấp đúp chuột vào file **`run_bot.bat`**.
2. Chọn tài khoản muốn chạy:
   - `[1]`: Profile 1 (Chính)
   - `[2]`: Profile 2 (Phụ 1)
   - `[3]`: Profile 3 (Tài khoản 3)
   - `[4]`: Profile 4 (Tài khoản 4)
   - `[5]`: Chạy lần lượt cả 4 Profile
3. Chọn chế độ tìm kiếm:
   - `[1]`: Chỉ tìm kiếm Desktop / PC
   - `[2]`: Chỉ tìm kiếm Mobile
   - `[3]`: Chạy cả hai (Desktop rồi tới Mobile)

---

### Cách 3: Chạy Bằng Lệnh Dành Cho Developer / Task Scheduler

Dành cho ai muốn tích hợp vào Windows Task Scheduler để tự động chạy ngầm theo giờ cố định hàng ngày:

```powershell
# Chạy tương tác (menu hỏi chọn Profile và Mode)
python edge_rewards_bot.py

# Chạy cụ thể Profile 1 với chế độ Desktop
python edge_rewards_bot.py --profile 1 --mode desktop

# Chạy Profile 2 với cả hai chế độ PC + Mobile
python edge_rewards_bot.py --profile 2 --mode all

# Chạy tự động lần lượt toàn bộ các profile có trong cấu hình
python edge_rewards_bot.py --profile all --mode all
```

---

## ⚙️ Giải Thích Các Thông Số Trong `config.json`

File `config.json` cho phép bạn tinh chỉnh mọi hành vi của bot:

| Thông số | Mặc định | Ý nghĩa & Khuyến nghị |
| :--- | :---: | :--- |
| `pc_searches` | `31` | Số lượt tìm kiếm trên máy tính (30 lượt ăn 90-150 điểm + 1 lượt dự phòng). |
| `mobile_searches` | `21` | Số lượt tìm kiếm trên di động (20 lượt ăn 60-100 điểm + 1 lượt dự phòng). |
| `min_delay_seconds` | `12` | Thời gian dừng nghỉ tối thiểu giữa các lần tìm kiếm (giây). |
| `max_delay_seconds` | `22` | Thời gian dừng nghỉ tối đa giữa các lần tìm kiếm (giây). |
| `enable_cooldown_batches` | `true` | Bật chế độ chia nhỏ đợt tìm kiếm để vượt qua chính sách 15-minute search cooldown của Microsoft. |
| `batch_size` | `4` | Số lượt tìm kiếm trong mỗi đợt nhỏ trước khi tạm nghỉ dài. |
| `batch_cooldown_minutes` | `3` | Thời gian nghỉ giải lao giữa các đợt nhỏ (phút). |
| `enable_smooth_scrolling` | `true` | Mô phỏng hành vi người dùng cuộn chuột xem nội dung bài viết. |
| `enable_mouse_movement` | `true` | Rê chuột ngẫu nhiên trong trang kết quả tìm kiếm. |
| `random_click_chance` | `0.25` | Tỷ lệ 25% ngẫu nhiên nhấp vào xem 1 trang tin trong kết quả tìm kiếm (tăng độ tin cậy của tài khoản). |
| `human_typing_speed_min` | `0.04` | Tốc độ gõ phím nhanh nhất (0.04 giây/ký tự). |
| `human_typing_speed_max` | `0.10` | Tốc độ gõ phím tự nhiên (0.10 giây/ký tự). |
| `headless` | `false` | `false`: Hiện cửa sổ trình duyệt để theo dõi trực quan; `true`: Chạy ẩn hoàn toàn dưới nền. |
| `mobile_device_name` | `"Pixel 7"` | Thiết bị giả lập khi tìm kiếm trên Mobile. |

> 💡 **Kinh nghiệm cày điểm an toàn**:
> - Nếu tài khoản của bạn bị Microsoft áp dụng cơ chế giới hạn điểm (*chỉ tính điểm 3-4 lần tìm kiếm mỗi 15 phút*), hãy giữ `"enable_cooldown_batches": true`. Bot sẽ tự tìm kiếm 4 lượt rồi nghỉ ngơi, sau đó tự tìm kiếm tiếp cho đến khi hoàn thành đủ chỉ tiêu mà bạn không cần phải canh chừng.

---

## 🔒 Cơ Chế Độc Lập Profile & Bảo Mật Tuyệt Đối

1. **Phân tách Profile độc lập**:
   - `Profile 1` ➡️ Lưu tại `./edge_profile`
   - `Profile 2` ➡️ Lưu tại `./edge_profile_2`
   - `Profile 3` ➡️ Lưu tại `./edge_profile_3`
   - `Profile 4` ➡️ Lưu tại `./edge_profile_4`
   - Mỗi tài khoản có môi trường Edge độc lập hoàn toàn, không chung đụng LocalStorage, Cookie hay Cache.
2. **An toàn bảo mật (Privacy First)**:
   - Toàn bộ dữ liệu tài khoản, mật khẩu (nếu lưu trên Edge) và cookie đăng nhập được lưu trữ **cục bộ 100% trên máy tính của bạn**.
   - File `.gitignore` của repo đã được cấu hình chặt chẽ để loại trừ toàn bộ thư mục `edge_profile*`, file logs và session. Khi bạn push code lên GitHub cá nhân hay fork về, **không bao giờ có nguy cơ lộ thông tin cá nhân**.

---

## 🕵️‍♂️ Kiểm Toán Tiêu Chuẩn Anti-Ban

Dự án có sẵn script kiểm toán độc lập để đánh giá mức độ an toàn trước khi vận hành:

```powershell
python verify_anti_detection.py
```

Hệ thống sẽ tự động quét codebase, đối chiếu các cờ bảo vệ, tốc độ typing, giả lập viewport và chấm điểm an toàn (Safety Score 5/5) cho bạn.

---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### 1. Lỗi: `'python' is not recognized as an internal or external command`?
👉 Do bạn chưa tích chọn **"Add Python to PATH"** lúc cài đặt Python. Hãy tải lại bộ cài Python, chọn **Modify** hoặc cài lại và nhớ đánh dấu vào ô `Add Python to PATH`.

### 2. Trình duyệt Edge báo driver không khớp hoặc tự động cập nhật?
👉 Thư viện `webdriver-manager` tích hợp sẵn trong bot sẽ tự động tải về và khớp phiên bản Microsoft Edge WebDriver chuẩn xác nhất với phiên bản Edge hiện có trên máy tính của bạn. Bạn không cần tải driver thủ công.

### 3. Làm sao để chạy ngầm không hiện cửa sổ trình duyệt cho đỡ rối mắt?
👉 Trên giao diện Web UI, bấm nút **`⚙️ Cấu Hình`** ➡️ Tích chọn **`Chạy ngầm (Headless Mode)`** ➡️ Bấm **Lưu cấu hình**. Trình duyệt sẽ chạy ẩn hoàn toàn dưới nền mà vẫn cày đủ điểm!

### 4. Muốn thêm tài khoản thứ 5, thứ 6 thì làm thế nào?
👉 Trên Web UI: Bấm nút **`+ Thêm Tài Khoản`**, đặt tên cho Profile mới và bấm **Thêm**. Hệ thống sẽ tự động tạo thư mục Profile mới và hiển thị Card điều khiển cho bạn.

---

## 📄 License & Miễn Trừ Trách Nhiệm

Dự án được phân phối theo giấy phép mã nguồn mở MIT. Dự án được xây dựng cho mục đích học tập, nghiên cứu tự động hóa trình duyệt và quản lý tài nguyên cá nhân. Vui lòng tuân thủ điều khoản dịch vụ của nhà cung cấp.
