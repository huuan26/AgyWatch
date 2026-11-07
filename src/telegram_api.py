from __future__ import annotations

import asyncio
import json
import re
import urllib.error
import urllib.request
from typing import Any


def escape_html(text: str) -> str:
    """Escape ký tự đặc biệt cho định dạng Telegram HTML."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class TelegramClient:
    """Async HTTP Client giao tiếp thuần Python với Telegram Bot API (Zero External Deps)."""

    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def _sync_post(
        self, method: str, payload: dict[str, Any], http_timeout: float
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{method}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=http_timeout) as resp:
                raw_body = resp.read().decode("utf-8")
                return json.loads(raw_body)
        except urllib.error.HTTPError as err:
            try:
                err_body = err.read().decode("utf-8")
                return json.loads(err_body)
            except Exception:
                return {"ok": False, "error_code": err.code, "description": str(err)}
        except Exception as exc:
            return {"ok": False, "description": str(exc)}

    async def call_api(
        self,
        method: str,
        payload: dict[str, Any] | None = None,
        http_timeout: float = 15.0,
    ) -> dict[str, Any]:
        """Gọi API bất đồng bộ không chặn event loop."""
        return await asyncio.to_thread(self._sync_post, method, payload or {}, http_timeout)

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Gửi tin nhắn Telegram dạng HTML, tự động cắt ngắn nếu vượt quá 4096 ký tự."""
        if len(text) > 4000:
            text = text[:3990] + "\n\n<i>...(nội dung đã được rút gọn)...</i>"

        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        res = await self.call_api("sendMessage", payload)
        if not res.get("ok"):
            # Fallback sang text thuần nếu có thẻ HTML lỗi
            plain = re.sub(r"<[^>]+>", "", text)
            payload["text"] = plain
            payload.pop("parse_mode", None)
            res = await self.call_api("sendMessage", payload)
        return res

    async def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Cập nhật nội dung một tin nhắn đang hiển thị."""
        if len(text) > 4000:
            text = text[:3990] + "..."

        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        res = await self.call_api("editMessageText", payload)
        if not res.get("ok"):
            plain = re.sub(r"<[^>]+>", "", text)
            payload["text"] = plain
            payload.pop("parse_mode", None)
            res = await self.call_api("editMessageText", payload)
        return res

    async def answer_callback_query(
        self, callback_query_id: str, text: str | None = None
    ) -> dict[str, Any]:
        """Phản hồi sự kiện bấm nút Inline Keyboard."""
        payload: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        return await self.call_api("answerCallbackQuery", payload)

    async def get_updates(self, offset: int = 0, timeout: int = 20) -> dict[str, Any]:
        """Polling các update mới từ Telegram."""
        return await self.call_api(
            "getUpdates",
            {"offset": offset, "timeout": timeout},
            http_timeout=float(timeout + 5),
        )

    async def delete_webhook(self) -> dict[str, Any]:
        return await self.call_api("deleteWebhook", {"drop_pending_updates": False})

    async def set_my_commands(self, commands: list[dict[str, str]]) -> dict[str, Any]:
        return await self.call_api("setMyCommands", {"commands": commands})
