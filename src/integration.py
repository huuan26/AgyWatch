from __future__ import annotations

import asyncio
from typing import Any

from .config import WatchConfig, load_watch_config
from .telegram_api import TelegramClient
from .watch_router import WatchRouter
from .watch_service import WatchService


def attach_to_agy_tele(
    tele_router: Any,
    tele_tg: Any,
    watch_config: WatchConfig | None = None,
) -> WatchService:
    """
    Tích hợp AgyWatch vào AgyTele (Anti-Tele-An) để DÙNG CHUNG 1 BOT DUY NHẤT.

    Cách sử dụng trong `Anti-Tele-An/main.py`:
    ---------------------------------------------------------
    from src.integration import attach_to_agy_tele  # hoặc import từ C:/.../AgyWatch

    # Ngay sau khi khởi tạo router và tg:
    watch_service = attach_to_agy_tele(router, tg)
    ---------------------------------------------------------

    Khi kích hoạt:
    1. Cả hai hệ thống cùng chia sẻ 1 kết nối Telegram (không bị lỗi 409 Conflict polling).
    2. Tự động thêm các lệnh `/watch`, `/prs`, `/review`, `/doctor` vào menu bot.
    3. Tự động khởi chạy vòng lặp daemon giám sát ngầm.
    """
    config = watch_config or load_watch_config()

    # Tái sử dụng client Telegram đã có của AgyTele
    tg_client = tele_tg if isinstance(tele_tg, TelegramClient) else TelegramClient(config.bot_token)
    service = WatchService(config=config, tg=tg_client)
    watch_router = WatchRouter(service=service, tg=tg_client)

    # 1. Bọc method handle_message của router gốc
    orig_handle_message = tele_router.handle_message

    async def _combined_handle_message(chat_id: int, text: str) -> None:
        handled = await watch_router.handle_message(chat_id, text)
        if not handled:
            await orig_handle_message(chat_id, text)

    tele_router.handle_message = _combined_handle_message

    # 2. Bọc method handle_callback_query của router gốc (nếu có)
    if hasattr(tele_router, "handle_callback_query"):
        orig_handle_callback = tele_router.handle_callback_query

        async def _combined_handle_callback(query: dict[str, Any]) -> None:
            handled = await watch_router.handle_callback_query(query)
            if not handled:
                await orig_handle_callback(query)

        tele_router.handle_callback_query = _combined_handle_callback

    # 3. Chạy background task polling cho WatchService
    asyncio.create_task(service.start())

    print("🔗 [Integration] Đã gắn AgyWatch vào AgyTele thành công (Dùng chung 1 Bot Telegram).")
    return service
