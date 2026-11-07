from __future__ import annotations

from typing import Any

from .telegram_api import TelegramClient, escape_html
from .watch_service import WatchService


class WatchRouter:
    """
    Bộ định tuyến lệnh Telegram dành riêng cho AgyWatch.
    Được thiết kế theo cấu trúc mô-đun để có thể:
    1. Chạy độc lập trong AgyWatch.
    2. Gắn trực tiếp vào BotRouter của Anti-Tele-An (AgyTele) để dùng CHUNG 1 BOT duy nhất.
    """

    def __init__(self, service: WatchService, tg: TelegramClient) -> None:
        self.service = service
        self.tg = tg

    async def handle_message(self, chat_id: int, text: str) -> bool:
        """
        Xử lý tin nhắn văn bản.
        Trả về True nếu lệnh thuộc về AgyWatch, False nếu không phải để chuyển tiếp cho AgyTele.
        """
        text = text.strip()
        if not text:
            return False

        # 1. /watch [status | check | on | off]
        if text.startswith("/watch"):
            args = text.split()
            subcmd = args[1].lower() if len(args) > 1 else "status"
            await self._cmd_watch(chat_id, subcmd)
            return True

        # 2. /prs [repo_name]
        if text.startswith("/prs"):
            parts = text.split(maxsplit=1)
            target_repo = parts[1].strip() if len(parts) > 1 else ""
            await self._cmd_prs(chat_id, target_repo)
            return True

        # 3. /review <pr_number> [repo_name]
        if text.startswith("/review"):
            parts = text.split()
            if len(parts) < 2:
                await self.tg.send_message(
                    chat_id,
                    "ℹ️ <b>Cú pháp:</b> <code>/review &lt;PR_NUMBER&gt; [repo_name]</code>\n"
                    "<i>Ví dụ: /review 33 hoặc /review 33 huuan26/polars-anta</i>",
                )
                return True
            pr_num = int(parts[1]) if parts[1].isdigit() else 0
            repo_name = (
                parts[2]
                if len(parts) > 2
                else (self.service.config.repos[0].name if self.service.config.repos else "")
            )
            if pr_num > 0 and repo_name:
                await self.tg.send_message(
                    chat_id,
                    f"🚀 <b>Đã tiếp nhận yêu cầu review PR #{pr_num} trên {escape_html(repo_name)}!</b>\n"
                    "Đang triệu hồi Antigravity CLI phân tích mã nguồn...",
                )
                await self.service.execute_review_flow(repo_name, pr_num, chat_id=chat_id)
            return True

        # 4. /doctor [local_path | repo_name]
        if text.startswith("/doctor"):
            parts = text.split(maxsplit=1)
            target = parts[1].strip() if len(parts) > 1 else ""
            await self._cmd_doctor(chat_id, target)
            return True

        return False

    async def handle_callback_query(self, query: dict[str, Any]) -> bool:
        """
        Xử lý sự kiện bấm nút Inline Keyboard.
        Trả về True nếu callback bắt đầu bằng 'watch:', False nếu là của AgyTele.
        """
        data = query.get("data", "")
        if not data.startswith("watch:"):
            return False

        qid = query.get("id", "")
        msg = query.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        msg_id = msg.get("message_id")

        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""

        await self.tg.answer_callback_query(qid, "Đã ghi nhận yêu cầu...")

        # A. Kích hoạt Review PR từ nút bấm
        if action == "review" and len(parts) >= 4:
            repo_name = parts[2]
            pr_num = int(parts[3])
            await self.tg.send_message(
                chat_id,
                f"🧠 <b>Bắt đầu Review PR #{pr_num} ({escape_html(repo_name)})...</b>",
            )
            await self.service.execute_review_flow(repo_name, pr_num, chat_id=chat_id)
            return True

        # B. Xác nhận Approve PR trực tiếp lên GitHub
        if action == "post_approve" and len(parts) >= 4:
            repo_name = parts[2]
            pr_num = int(parts[3])
            ok = await self.service.inspector.submit_pr_review(
                repo_name, pr_num, "approve", "Approved via Antigravity AgyWatch review verification. 🚀"
            )
            if ok:
                await self.tg.send_message(
                    chat_id,
                    f"✅ <b>Đã gửi APPROVE thành công lên PR #{pr_num} ({escape_html(repo_name)})!</b>",
                )
            else:
                await self.tg.send_message(
                    chat_id, f"❌ Không thể gửi review lên GitHub cho PR #{pr_num}."
                )
            return True

        # C. Bác sĩ chẩn đoán CI thất bại
        if action == "ci_doctor" and len(parts) >= 4:
            repo_name = parts[2]
            run_id = int(parts[3])
            await self.tg.send_message(
                chat_id,
                f"🩺 <b>Antigravity đang phân tích log thất bại của CI Run #{run_id}...</b>",
            )
            logs = await self.service.inspector.get_failed_ci_logs(repo_name, run_id)
            prompt = f"Analyze this failed CI log and provide root cause + exact fix:\n\n```text\n{logs[-8000:]}\n```"
            _, analysis = await self.service.runner.execute_task(
                prompt=prompt,
                workspace=".",
                timeout=200.0,
            )
            report = (
                f"🩺 <b>Kết quả Chẩn đoán CI Run #{run_id} ({escape_html(repo_name)})</b>:\n\n"
                f"<pre>{escape_html(analysis[:3500])}</pre>"
            )
            await self.tg.send_message(chat_id, report)
            return True

        # D. Bỏ qua / Đóng nút
        if action == "ignore":
            if chat_id and msg_id:
                await self.tg.edit_message_text(
                    chat_id, msg_id, "<i>(Đã bỏ qua thông báo này)</i>"
                )
            return True

        return True

    async def _cmd_watch(self, chat_id: int, subcmd: str) -> None:
        """Xử lý lệnh /watch."""
        if subcmd == "check":
            await self.tg.send_message(chat_id, "🔄 Đang quét ngay lập tức toàn bộ repositories...")
            await self.service.poll_cycle()
            await self.tg.send_message(chat_id, "✅ Đã hoàn thành chu kỳ quét.")
            return

        repos_text = "\n".join(
            [f"• <code>{escape_html(r.name)}</code> (PRs: {'Bật' if r.watch_prs else 'Tắt'}, CI: {'Bật' if r.watch_ci else 'Tắt'})" for r in self.service.config.repos]
        )
        msg = (
            f"👁️ <b>Trạng Thái AgyWatch Daemon</b>\n\n"
            f"• <b>Trạng thái:</b> {'🟢 Đang hoạt động' if self.service._running else '🟡 Sẵn sàng'}\n"
            f"• <b>Chu kỳ quét:</b> {self.service.config.poll_interval_seconds}s\n"
            f"• <b>Tự động Review:</b> {'Bật' if self.service.config.auto_review_new_prs else 'Tắt (Chờ bấm nút)'}\n\n"
            f"<b>Danh sách Repositories theo dõi:</b>\n{repos_text}\n\n"
            f"<i>Gõ /watch check để quét ngay, /prs để xem PRs đang mở, /doctor để khám lỗi test.</i>"
        )
        await self.tg.send_message(chat_id, msg)

    async def _cmd_prs(self, chat_id: int, target_repo: str) -> None:
        """Xử lý lệnh /prs."""
        repo_name = target_repo or (self.service.config.repos[0].name if self.service.config.repos else "")
        if not repo_name:
            await self.tg.send_message(chat_id, "⚠️ Chưa cấu hình repository nào trong danh sách theo dõi.")
            return

        prs = await self.service.inspector.list_open_prs(repo_name)
        if not prs:
            await self.tg.send_message(
                chat_id, f"🎉 Hiện không có Pull Request nào đang mở trên <code>{escape_html(repo_name)}</code>."
            )
            return

        msg_lines = [f"📂 <b>Các Pull Request Đang Mở ({escape_html(repo_name)}):</b>\n"]
        buttons: list[list[dict[str, str]]] = []

        for pr in prs[:5]:
            p_num = pr.get("number")
            p_title = pr.get("title", "")
            p_author = pr.get("author", {}).get("login", "")
            msg_lines.append(f"• <b>#{p_num}</b>: {escape_html(p_title)} (@{escape_html(p_author)})")
            buttons.append(
                [
                    {
                        "text": f"🔍 Review PR #{p_num}",
                        "callback_data": f"watch:review:{repo_name}:{p_num}",
                    }
                ]
            )

        await self.tg.send_message(
            chat_id, "\n".join(msg_lines), reply_markup={"inline_keyboard": buttons}
        )

    async def _cmd_doctor(self, chat_id: int, target: str) -> None:
        """Xử lý lệnh /doctor."""
        # Ưu tiên local path từ repo config nếu có
        repo = next(
            (r for r in self.service.config.repos if r.name == target or r.local_path == target),
            self.service.config.repos[0] if self.service.config.repos else None,
        )

        if not repo or not repo.local_path:
            await self.tg.send_message(
                chat_id, "⚠️ Không tìm thấy đường dẫn local repo để chạy kiểm thử."
            )
            return

        await self.tg.send_message(
            chat_id,
            f"🧪 <b>AgyWatch Doctor đang khám sức khỏe repo:</b> <code>{escape_html(repo.local_path)}</code>...",
        )
        diag = await self.service.doctor.check_local_health(
            repo.local_path, test_command=repo.test_command
        )

        if diag.status == "HEALTHY":
            await self.tg.send_message(
                chat_id,
                f"✅ <b>BÁO CÁO KHỎE MẠNH (HEALTHY):</b>\n{escape_html(diag.error_summary)}",
            )
        else:
            msg = (
                f"🩺 <b>BÁO CÁO CHẨN ĐOÁN LỖI TEST:</b>\n\n"
                f"<pre>{escape_html(diag.analysis[:3500])}</pre>"
            )
            await self.tg.send_message(chat_id, msg)
