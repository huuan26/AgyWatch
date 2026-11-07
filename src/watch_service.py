from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .agy_runner import AgyRunner
from .config import WatchConfig
from .doctor import DoctorEngine
from .git_inspector import GitInspector
from .reviewer import PRReviewer
from .telegram_api import TelegramClient, escape_html

STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "state.json"


class WatchService:
    """
    Dịch vụ giám sát trung tâm của AgyWatch.
    Chạy nền, phát hiện Pull Requests, CI fails, và điều phối Antigravity CLI.
    """

    def __init__(
        self,
        config: WatchConfig,
        tg: TelegramClient | None = None,
        inspector: GitInspector | None = None,
        runner: AgyRunner | None = None,
    ) -> None:
        self.config = config
        self.tg = tg or (TelegramClient(config.bot_token) if config.bot_token else None)
        self.inspector = inspector or GitInspector()
        self.runner = runner or AgyRunner(default_model=config.default_model)
        self.reviewer = PRReviewer(self.inspector, self.runner)
        self.doctor = DoctorEngine(self.inspector, self.runner)

        self._running = False
        self._seen_prs: set[str] = set()
        self._seen_ci: set[str] = set()
        self._load_state()

    def _load_state(self) -> None:
        """Tải trạng thái các PR / CI đã ghi nhận trước đó từ disk."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._seen_prs = set(data.get("seen_prs", []))
                    self._seen_ci = set(data.get("seen_ci", []))
            except Exception:
                pass

    def _save_state(self) -> None:
        """Lưu lại trạng thái vào data/state.json."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "seen_prs": list(self._seen_prs),
                        "seen_ci": list(self._seen_ci),
                        "updated_at": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception:
            pass

    async def broadcast_telegram(
        self, text: str, reply_markup: dict[str, Any] | None = None
    ) -> None:
        """Gửi thông báo tới tất cả người dùng trong allowed_user_ids."""
        if not self.tg or not self.config.allowed_user_ids:
            return
        for uid in self.config.allowed_user_ids:
            await self.tg.send_message(uid, text, reply_markup=reply_markup)

    async def start(self) -> None:
        """Khởi động vòng lặp giám sát định kỳ."""
        self._running = True
        print(f"👁️  AgyWatch Service đã kích hoạt! Chu kỳ quét: {self.config.poll_interval_seconds}s")
        print(f"📦 Repositories được giám sát: {[r.name for r in self.config.repos]}")

        while self._running:
            try:
                await self.poll_cycle()
            except Exception as e:
                print(f"⚠️ Lỗi trong chu kỳ quét AgyWatch: {e}")
            await asyncio.sleep(self.config.poll_interval_seconds)

    def stop(self) -> None:
        """Dừng vòng lặp giám sát."""
        self._running = False
        print("🛑 AgyWatch Service đã dừng.")

    async def poll_cycle(self) -> None:
        """Một chu kỳ kiểm tra toàn bộ repositories đã đăng ký."""
        for repo in self.config.repos:
            # 1. Quét Pull Requests mới
            if repo.watch_prs:
                prs = await self.inspector.list_open_prs(repo.name)
                for pr in prs:
                    pr_num = pr.get("number")
                    if not pr_num:
                        continue
                    key = f"{repo.name}#{pr_num}"
                    if key not in self._seen_prs:
                        self._seen_prs.add(key)
                        self._save_state()
                        await self._handle_new_pr(repo.name, pr)

            # 2. Quét CI Runs bị thất bại
            if repo.watch_ci:
                runs = await self.inspector.list_ci_runs(repo.name, limit=3)
                for r in runs:
                    if r.get("conclusion") == "failure":
                        run_id = str(r.get("databaseId", ""))
                        key = f"{repo.name}#ci#{run_id}"
                        if key not in self._seen_ci:
                            self._seen_ci.add(key)
                            self._save_state()
                            await self._handle_failed_ci(repo.name, r)

    async def _handle_new_pr(self, repo_name: str, pr: dict[str, Any]) -> None:
        """Xử lý khi phát hiện Pull Request mới."""
        pr_num = pr.get("number")
        title = pr.get("title", "")
        author = pr.get("author", {}).get("login", "unknown")
        url = pr.get("url", "")

        print(f"🔔 Phát hiện PR mới: {repo_name} #{pr_num} bởi @{author}: {title}")

        msg = (
            f"🔔 <b>Pull Request Mới Phát Hiện!</b>\n\n"
            f"• <b>Repo:</b> <code>{escape_html(repo_name)}</code>\n"
            f"• <b>PR:</b> <a href=\"{url}\">#{pr_num}</a> - {escape_html(title)}\n"
            f"• <b>Tác giả:</b> @{escape_html(author)}\n"
        )

        buttons = {
            "inline_keyboard": [
                [
                    {
                        "text": "🔍 Review với Antigravity",
                        "callback_data": f"watch:review:{repo_name}:{pr_num}",
                    }
                ],
                [
                    {
                        "text": "✅ Phê duyệt (Approve)",
                        "callback_data": f"watch:approve:{repo_name}:{pr_num}",
                    },
                    {
                        "text": "❌ Đóng / Bỏ qua",
                        "callback_data": f"watch:ignore:{repo_name}:{pr_num}",
                    },
                ],
            ]
        }

        await self.broadcast_telegram(msg, reply_markup=buttons)

        if self.config.auto_review_new_prs:
            await self.execute_review_flow(repo_name, int(pr_num))

    async def _handle_failed_ci(self, repo_name: str, run: dict[str, Any]) -> None:
        """Xử lý khi phát hiện CI Actions thất bại."""
        run_id = run.get("databaseId", "")
        run_name = run.get("name", "CI Workflow")
        branch = run.get("headBranch", "unknown")
        url = run.get("url", "")

        msg = (
            f"🚨 <b>Cảnh báo: GitHub Actions CI Thất Bại!</b>\n\n"
            f"• <b>Repo:</b> <code>{escape_html(repo_name)}</code>\n"
            f"• <b>Workflow:</b> {escape_html(run_name)} (<a href=\"{url}\">Run #{run_id}</a>)\n"
            f"• <b>Nhánh:</b> <code>{escape_html(branch)}</code>\n"
        )

        buttons = {
            "inline_keyboard": [
                [
                    {
                        "text": "🩺 Bác sĩ chẩn đoán & Sửa lỗi",
                        "callback_data": f"watch:ci_doctor:{repo_name}:{run_id}",
                    },
                    {
                        "text": "Bỏ qua",
                        "callback_data": f"watch:ignore:{repo_name}:{run_id}",
                    },
                ]
            ]
        }

        await self.broadcast_telegram(msg, reply_markup=buttons)

    async def execute_review_flow(
        self, repo_name: str, pr_number: int, chat_id: int | None = None
    ) -> str:
        """Kích hoạt Antigravity CLI phân tích PR và gửi báo cáo kết quả."""
        target_repo = next((r for r in self.config.repos if r.name == repo_name), None)
        local_path = target_repo.local_path if target_repo else ""

        progress_msg_id: int | None = None

        async def _on_progress(msg: str) -> None:
            nonlocal progress_msg_id
            if self.tg and chat_id:
                if progress_msg_id is None:
                    res = await self.tg.send_message(chat_id, f"⏳ {msg}")
                    if res.get("ok"):
                        progress_msg_id = res["result"]["message_id"]
                else:
                    await self.tg.edit_message_text(chat_id, progress_msg_id, f"⏳ {msg}")

        result = await self.reviewer.review_pr(
            repo_name=repo_name,
            pr_number=pr_number,
            workspace=local_path,
            on_progress=_on_progress if chat_id else None,
        )

        badge = (
            "✅ <b>KHUYẾN NGHỊ: APPROVE</b>"
            if result.decision == "APPROVE"
            else "⚠️ <b>KHUYẾN NGHỊ: CẦN CHỈNH SỬA / COMMENT</b>"
        )

        report = (
            f"📋 <b>Báo Cáo Review PR #{pr_number} ({escape_html(repo_name)})</b>\n\n"
            f"• <b>Tiêu đề:</b> {escape_html(result.title)}\n"
            f"• <b>Tác giả:</b> @{escape_html(result.author)}\n"
            f"• <b>Đánh giá:</b> {badge}\n"
            f"• <b>Tóm tắt:</b> {escape_html(result.summary)}\n\n"
            f"<b>Chi tiết phân tích:</b>\n"
            f"<pre>{escape_html(result.review_markdown[:2500])}</pre>"
        )

        buttons = {
            "inline_keyboard": [
                [
                    {
                        "text": "🚀 Gửi Approve lên GitHub ngay",
                        "callback_data": f"watch:post_approve:{repo_name}:{pr_number}",
                    },
                    {
                        "text": "💬 Gửi Review Comment",
                        "callback_data": f"watch:post_comment:{repo_name}:{pr_number}",
                    },
                ]
            ]
        }

        if self.tg and chat_id:
            await self.tg.send_message(chat_id, report, reply_markup=buttons)
        else:
            await self.broadcast_telegram(report, reply_markup=buttons)

        return report
