<div align="center">

<pre align="center">
 █████╗  ██████╗ ██╗   ██╗██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗
██╔══██╗██╔════╝ ╚██╗ ██╔╝██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║
███████║██║  ███╗ ╚████╔╝ ██║ █╗ ██║███████║   ██║   ██║     ███████║
██╔══██║██║   ██║  ╚██╔╝  ██║███╗██║██╔══██║   ██║   ██║     ██╔══██║
██║  ██║╚██████╔╝   ██║   ╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
</pre>

<p align="center">
  <strong>Autonomous Git, Pull Request and CI Watchdog Daemon for Google Antigravity CLI (agy)</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square" alt="Python 3.10+" /></a>
  <a href="#key-features"><img src="https://img.shields.io/badge/Dependencies-Zero%20(Stdlib)-success?style=flat-square" alt="Zero Dependencies" /></a>
  <a href="#system-architecture"><img src="https://img.shields.io/badge/Protocol-Stream--JSON%20(NDJSON)-orange?style=flat-square" alt="Stream-JSON" /></a>
  <a href="#key-features"><img src="https://img.shields.io/badge/Security-Port%209879%20Lock-blueviolet?style=flat-square" alt="Socket Lock" /></a>
  <a href="#unified-bot-integration-with-agytele"><img src="https://img.shields.io/badge/AgyTele-Co--Bot%20Ready-emerald?style=flat-square" alt="Co-Bot Ready" /></a>
  <a href="#quick-start"><img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Platform Support" /></a>
</p>

<p align="center">
  <a href="#overview">Overview</a> &bull;
  <a href="#key-features">Key Features</a> &bull;
  <a href="#system-architecture">Architecture</a> &bull;
  <a href="#unified-bot-integration-with-agytele">Unified Bot Integration</a> &bull;
  <a href="#command-reference">Commands</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#project-structure">Project Structure</a> &bull;
  <a href="#verification-and-testing">Testing</a>
</p>

</div>

---

## Overview

AgyWatch là hệ thống daemon giám sát tự động (Watchdog) được phát triển bằng Python chuẩn (`asyncio`), đóng vai trò như một trợ lý kỹ thuật trực tuyến liên tục cho các kho mã nguồn Git của bạn.

Hệ thống hoạt động ngầm và theo dõi trạng thái repository theo chu kỳ:
1. **Phát hiện Pull Request mới**: Quét git diff, kích hoạt Google Antigravity CLI (`agy`) phân tích cấu trúc mã nguồn, tính toán học, chuẩn vector hóa và độ phủ kiểm thử; sau đó trả về bản đánh giá kèm khuyến nghị `APPROVE`, `REQUEST_CHANGES` hoặc `COMMENT`.
2. **Chẩn đoán kiểm thử và CI (Self-Healing Doctor)**: Khi phát hiện `pytest` hoặc GitHub Actions CI thất bại, hệ thống tự động trích xuất traceback lỗi, gửi đến Antigravity để phân tích nguyên nhân gốc rễ (Root Cause Analysis) và đề xuất bản vá tương ứng.
3. **Điều khiển và thông báo hai chiều qua Telegram**: Chuyển tiếp trạng thái đến Telegram kèm các nút thao tác trực tiếp: `[Review PR]`, `[Approve trên GitHub]`, `[Chẩn đoán lỗi]`.
4. **Tự động đồng bộ Model**: Tự động nhận diện model AI mà máy tính đang sử dụng trong Antigravity CLI (`~/.gemini/antigravity-cli/settings.json`) thay vì cố định một model cụ thể.

---

## Key Features

<table>
  <thead>
    <tr>
      <th width="50%">Tính năng</th>
      <th width="50%">Cơ chế Kỹ thuật</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <strong>Zero External Dependencies</strong><br />
        Hoạt động ngay trên môi trường Python tiêu chuẩn mà không cần cài đặt thêm thư viện bên ngoài.
      </td>
      <td>
        Sử dụng độc quyền các module tiêu chuẩn của Python 3.10+: <code>asyncio</code>, <code>urllib.request</code>, <code>json</code>, <code>socket</code>, <code>dataclasses</code>, <code>pathlib</code>. Không cần bước <code>pip install</code>.
      </td>
    </tr>
    <tr>
      <td>
        <strong>Đánh giá Pull Request tự động</strong><br />
        Phân tích chuyên sâu thuật toán và kiến trúc mã nguồn.
      </td>
      <td>
        Thu thập thông tin và git diff thông qua <code>gh pr diff</code>, khởi chạy <code>agy --output-format stream-json</code> với prompt thẩm định chuyên biệt, phát hiện sớm các vi phạm cấu trúc hoặc lỗi xử lý biên.
      </td>
    </tr>
    <tr>
      <td>
        <strong>Chẩn đoán và khắc phục lỗi tự động</strong><br />
        Kiểm tra sức khỏe bộ test và workflow CI.
      </td>
      <td>
        Theo dõi <code>gh run list</code> và test runner cục bộ. Tự động thu thập log thất bại, kích hoạt agent phân tích nguyên nhân và đưa ra gợi ý sửa đổi.
      </td>
    </tr>
    <tr>
      <td>
        <strong>Tích hợp dùng chung bot với AgyTele</strong><br />
        Hợp nhất vào cùng một Bot Telegram duy nhất.
      </td>
      <td>
        Cung cấp hàm <code>attach_to_agy_tele()</code> cho phép nhúng router và vòng lặp daemon trực tiếp vào phiên làm việc của AgyTele, tránh hiện tượng xung đột polling (HTTP 409 Conflict).
      </td>
    </tr>
    <tr>
      <td>
        <strong>Khóa Socket đơn tiến trình (Port 9879)</strong><br />
        Ngăn chặn việc khởi chạy trùng lặp ở chế độ độc lập.
      </td>
      <td>
        Ràng buộc cổng nội bộ <code>127.0.0.1:9879</code> khi khởi động phiên độc lập, đảm bảo an toàn tài nguyên hệ thống.
      </td>
    </tr>
  </tbody>
</table>

---

## System Architecture

```text
               ┌──────────────────────────────────────────────┐
               │    Local Git Repos / GitHub Remote (gh)      │
               └──────────────────────┬───────────────────────┘
                                      │
                         (Polls PRs, CI, Test Suite)
                                      ▼
               ┌──────────────────────────────────────────────┐
               │              AgyWatch Service                │
               │   - GitInspector & Event Deduplication       │
               │   - Port 9879 Socket Lock (Standalone)       │
               └──────────────┬────────────────┬──────────────┘
                              │                │
            (Headless stream-json)    (Interactive Dispatch)
                              ▼                ▼
       ┌────────────────────────────┐    ┌───────────────────────────────────┐
       │   Antigravity CLI (agy)    │    │      Unified Telegram Router      │
       │   - PR Code Reviewer       │    │   - Real-time Alert Messages      │
       │   - Self-Healing Doctor    │    │   - Inline Action Buttons         │
       └────────────────────────────┘    │   - [Review] [Approve] [Doctor]   │
                                         └───────────────────────────────────┘
```

---

## Unified Bot Integration with AgyTele

Nếu bạn đang sử dụng **AgyTele** (`Anti-Tele-An`), hệ thống hỗ trợ tích hợp trực tiếp để dùng chung một Bot Telegram duy nhất mà không cần tạo thêm bot mới.

### Cách tích hợp vào `Anti-Tele-An/main.py`:

Mở file `C:\Users\ADMIN\Documents\Anti-Tele-An\main.py`, thêm import và dòng gắn dịch vụ sau khi khởi tạo `router`:

```python
# Thêm import ở đầu file:
import sys
sys.path.append("C:/Users/ADMIN/Documents/AgyWatch")
from src.integration import attach_to_agy_tele

# Trong hàm run_bot(), ngay sau dòng khởi tạo router:
router = BotRouter(tg, state, bridge)

# Thêm dòng này để kích hoạt AgyWatch chạy song song:
attach_to_agy_tele(tele_router=router, tele_tg=tg)
```

**Ưu điểm:**
- Bot Telegram duy nhất vừa xử lý các tác vụ phát triển của AgyTele vừa tự động giám sát PR/CI của AgyWatch.
- Tránh xung đột kết nối Telegram Long-polling.

---

## Command Reference

| Lệnh | Cú pháp | Chức năng | Giao diện |
| :--- | :--- | :--- | :--- |
| `/watch` | `/watch [status\|check]` | Kiểm tra trạng thái daemon, danh sách repository hoặc yêu cầu quét ngay lập tức (`/watch check`) | Tin nhắn văn bản |
| `/prs` | `/prs [repo_name]` | Hiển thị danh sách các Pull Request đang mở kèm nút bấm xem xét nhanh | Inline Keyboard |
| `/review` | `/review <PR_NUMBER> [repo]` | Kích hoạt Antigravity CLI phân tích mã nguồn PR và gửi báo cáo chi tiết | Inline Keyboard |
| `/doctor` | `/doctor [local_path]` | Chạy bộ kiểm thử cục bộ (`pytest`) hoặc chẩn đoán log lỗi từ GitHub Actions CI | Tin nhắn văn bản |

---

## Quick Start (Standalone Mode)

Khi sử dụng AgyWatch ở chế độ daemon độc lập:

### 1. Khởi chạy bằng kịch bản Windows:
Nhấp đúp chuột vào file `run.bat`.

### 2. Khởi chạy bằng dòng lệnh:
```bash
# Cấu hình tham số qua giao diện tương tác
python setup.py

# Khởi động tiến trình giám sát
python main.py
```

### 3. Cấu hình mẫu (`config.json`):
```json
{
  "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
  "allowed_user_ids": [6876958198],
  "poll_interval_seconds": 60,
  "default_model": "auto",
  "auto_review_new_prs": false,
  "auto_notify_telegram": true,
  "repos": [
    {
      "name": "huuan26/polars-anta",
      "local_path": "C:/Users/ADMIN/Documents/polars-anta",
      "watch_prs": true,
      "watch_ci": true,
      "watch_local_tests": true,
      "test_command": "python -m pytest"
    }
  ]
}
```

*Lưu ý: Khi `default_model` được đặt là `"auto"`, hệ thống sẽ tự động sử dụng model mà máy tính đang kích hoạt trong Antigravity CLI.*

---

## Project Structure

```text
AgyWatch/
├── data/
│   └── state.json             # Lưu trữ định danh PR và CI đã xử lý
├── src/
│   ├── __init__.py            # Export giao diện công khai
│   ├── agy_runner.py          # Quản lý tiến trình stream-json của Antigravity CLI
│   ├── config.py              # Đọc cấu hình và phát hiện model local
│   ├── doctor.py              # Engine chẩn đoán kiểm thử và workflow CI
│   ├── git_inspector.py       # Wrapper tương tác Git và GitHub CLI (gh)
│   ├── integration.py         # Hàm kết nối tích hợp vào AgyTele
│   ├── reviewer.py            # Tạo prompt đánh giá PR và phân loại kết luận
│   ├── telegram_api.py        # Client HTTP Telegram thuần Python
│   ├── watch_router.py        # Bộ định tuyến lệnh và callback cho Telegram
│   └── watch_service.py       # Vòng lặp giám sát bất đồng bộ trung tâm
├── tests/
│   └── test_core.py           # Bộ kiểm thử đơn vị
├── config.example.json        # File cấu hình tham chiếu mẫu
├── config.json                # File cấu hình hoạt động cục bộ (được bỏ qua bởi git)
├── main.py                    # Điểm khởi chạy chế độ độc lập (Socket lock 9879)
├── run.bat                    # Kịch bản khởi chạy trên Windows
├── setup.py                   # Trình cài đặt cấu hình tương tác
└── README.md                  # Tài liệu hướng dẫn sử dụng
```

---

## Verification and Testing

Thực thi bộ kiểm thử đơn vị bằng test runner nguyên bản của Python:

```bash
python -m unittest discover -s tests -v
```

---

<div align="center">

**AgyWatch &bull; Autonomous Git &amp; CI Watchdog for Google Antigravity**  
Maintained by [huuan26](https://github.com/huuan26)

</div>
