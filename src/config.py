from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
AGY_TELE_CONFIG_PATH = Path("C:/Users/ADMIN/Documents/Anti-Tele-An/config.json")
SETTINGS_PATH = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"


def get_active_local_model() -> str:
    """Đọc model mà máy tính đang dùng hiện tại trong Antigravity CLI."""
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            model = data.get("model")
            if model and str(model).strip():
                return str(model).strip()
        except Exception:
            pass
    return "auto"


@dataclass
class RepoTarget:
    """Đặc tả thông tin một repository được giám sát bởi AgyWatch."""

    name: str  # Ví dụ: "huuan26/polars-anta"
    local_path: str = ""  # Đường dẫn local nếu có, ví dụ: "C:/Users/ADMIN/Documents/polars-anta"
    watch_prs: bool = True
    watch_ci: bool = True
    watch_local_tests: bool = False
    test_command: str = "python -m pytest"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RepoTarget:
        return cls(
            name=str(data.get("name", "")).strip(),
            local_path=str(data.get("local_path", "")).strip(),
            watch_prs=bool(data.get("watch_prs", True)),
            watch_ci=bool(data.get("watch_ci", True)),
            watch_local_tests=bool(data.get("watch_local_tests", False)),
            test_command=str(data.get("test_command", "python -m pytest")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "local_path": self.local_path,
            "watch_prs": self.watch_prs,
            "watch_ci": self.watch_ci,
            "watch_local_tests": self.watch_local_tests,
            "test_command": self.test_command,
        }


@dataclass
class WatchConfig:
    """Cấu hình vận hành trung tâm cho AgyWatch."""

    bot_token: str = ""
    allowed_user_ids: list[int] = field(default_factory=list)
    poll_interval_seconds: int = 60
    default_model: str = "gemini-4-argon-high"
    auto_review_new_prs: bool = False  # True: tự động review; False: báo tin nhắn kèm nút bấm [Review ngay]
    auto_notify_telegram: bool = True
    repos: list[RepoTarget] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatchConfig:
        repos_raw = data.get("repos", [])
        repos = [RepoTarget.from_dict(r) for r in repos_raw if isinstance(r, dict)]

        raw_ids = data.get("allowed_user_ids", [])
        allowed_ids = [int(uid) for uid in raw_ids if str(uid).strip().isdigit()]

        raw_model = str(data.get("default_model", "auto")).strip()
        if not raw_model or raw_model.lower() in ("auto", "local", "current"):
            default_model = get_active_local_model()
        else:
            default_model = raw_model

        return cls(
            bot_token=str(data.get("bot_token", "")).strip(),
            allowed_user_ids=allowed_ids,
            poll_interval_seconds=int(data.get("poll_interval_seconds", 60)),
            default_model=default_model,
            auto_review_new_prs=bool(data.get("auto_review_new_prs", False)),
            auto_notify_telegram=bool(data.get("auto_notify_telegram", True)),
            repos=repos,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bot_token": self.bot_token,
            "allowed_user_ids": self.allowed_user_ids,
            "poll_interval_seconds": self.poll_interval_seconds,
            "default_model": self.default_model,
            "auto_review_new_prs": self.auto_review_new_prs,
            "auto_notify_telegram": self.auto_notify_telegram,
            "repos": [r.to_dict() for r in self.repos],
        }


def load_watch_config(config_path: Path | str | None = None) -> WatchConfig:
    """
    Nạp cấu hình từ:
    1. config_path chỉ định.
    2. Biến môi trường AGY_WATCH_CONFIG.
    3. C:/Users/ADMIN/Documents/AgyWatch/config.json.
    4. Kế thừa token và allowed_user_ids từ Anti-Tele-An nếu có sẵn.
    """
    target_path: Path
    if config_path:
        target_path = Path(config_path)
    elif os.environ.get("AGY_WATCH_CONFIG"):
        target_path = Path(os.environ["AGY_WATCH_CONFIG"])
    else:
        target_path = DEFAULT_CONFIG_PATH

    data: dict[str, Any] = {}
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Không thể đọc file cấu hình tại {target_path}: {e}")

    # Fallback tự động mượn bot_token & allowed_user_ids từ Anti-Tele-An nếu chưa có
    if not data.get("bot_token") and AGY_TELE_CONFIG_PATH.exists():
        try:
            with open(AGY_TELE_CONFIG_PATH, "r", encoding="utf-8") as f:
                tele_data = json.load(f)
                if not data.get("bot_token"):
                    data["bot_token"] = tele_data.get("bot_token", "")
                if not data.get("allowed_user_ids"):
                    data["allowed_user_ids"] = tele_data.get("allowed_user_ids", [])
                if not data.get("default_model"):
                    data["default_model"] = tele_data.get("default_model", "gemini-4-argon-high")
        except Exception:
            pass

    # Thiết lập mặc định 1 repo mẫu nếu danh sách trống
    if not data.get("repos"):
        data["repos"] = [
            {
                "name": "huuan26/polars-anta",
                "local_path": "C:/Users/ADMIN/Documents/polars-anta",
                "watch_prs": True,
                "watch_ci": True,
                "watch_local_tests": True,
                "test_command": "python -m pytest",
            }
        ]

    return WatchConfig.from_dict(data)
