from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
EXAMPLE_PATH = Path(__file__).resolve().parent / "config.example.json"
TELE_CONFIG_PATH = Path("C:/Users/ADMIN/Documents/Anti-Tele-An/config.json")


def check_prerequisites() -> None:
    print("\n🔍 Đang kiểm tra môi trường hệ thống...")
    has_git = shutil.which("git") is not None
    has_gh = shutil.which("gh") is not None
    has_agy = shutil.which("agy") is not None or shutil.which("agy.exe") is not None

    print(f"  • Git CLI : {'✅ Đã cài đặt' if has_git else '❌ Chưa tìm thấy git trong PATH'}")
    print(f"  • GitHub CLI (gh) : {'✅ Đã cài đặt' if has_gh else '⚠️ Chưa cài đặt gh (Cần để lấy PR/CI)'}")
    print(f"  • Antigravity CLI (agy) : {'✅ Đã cài đặt' if has_agy else '⚠️ Chưa tìm thấy agy trong PATH'}")


def interactive_setup() -> None:
    print("=" * 65)
    print("🛠️  AGYWATCH - THIẾT LẬP CẤU HÌNH NHANH")
    print("=" * 65)

    check_prerequisites()

    existing: dict = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    elif TELE_CONFIG_PATH.exists():
        try:
            with open(TELE_CONFIG_PATH, "r", encoding="utf-8") as f:
                tele_cfg = json.load(f)
                existing["bot_token"] = tele_cfg.get("bot_token", "")
                existing["allowed_user_ids"] = tele_cfg.get("allowed_user_ids", [])
                existing["default_model"] = tele_cfg.get("default_model", "gemini-4-argon-high")
        except Exception:
            pass

    default_token = existing.get("bot_token", "")
    default_users = ",".join(str(x) for x in existing.get("allowed_user_ids", [])) or "6876958198"

    print("\n--- 1. CẤU HÌNH TELEGRAM BOT ---")
    token = input(f"Telegram Bot Token [{default_token[:15]}...]: ").strip() or default_token
    users_raw = input(f"Telegram User ID hợp lệ [{default_users}]: ").strip() or default_users
    allowed_ids = [int(x.strip()) for x in users_raw.split(",") if x.strip().isdigit()]

    print("\n--- 2. CẤU HÌNH REPOSITORY GIÁM SÁT ---")
    default_repo = "huuan26/polars-anta"
    repo_name = input(f"Tên GitHub Repository theo dõi [{default_repo}]: ").strip() or default_repo
    default_local = "C:/Users/ADMIN/Documents/polars-anta"
    local_path = input(f"Đường dẫn local của repo [{default_local}]: ").strip() or default_local

    config_data = {
        "bot_token": token,
        "allowed_user_ids": allowed_ids,
        "poll_interval_seconds": 60,
        "default_model": existing.get("default_model", "gemini-4-argon-high"),
        "auto_review_new_prs": False,
        "auto_notify_telegram": True,
        "repos": [
            {
                "name": repo_name,
                "local_path": local_path,
                "watch_prs": True,
                "watch_ci": True,
                "watch_local_tests": True,
                "test_command": "python -m pytest",
            }
        ],
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    print("\n✅ Đã lưu cấu hình thành công vào config.json!")
    print("Bạn có thể chạy `python main.py` hoặc nhấp đúp vào `run.bat` để bắt đầu!\n")


if __name__ == "__main__":
    interactive_setup()
