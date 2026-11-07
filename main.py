from __future__ import annotations

import asyncio
import socket
import sys
from datetime import datetime

from src.config import load_watch_config
from src.telegram_api import TelegramClient, escape_html
from src.watch_router import WatchRouter
from src.watch_service import WatchService

SINGLE_INSTANCE_PORT = 9879


def acquire_single_instance_lock(port: int = SINGLE_INSTANCE_PORT) -> socket.socket:
    """Đảm bảo chỉ có duy nhất 1 tiến trình AgyWatch chạy trên máy tại một thời điểm."""
    lock_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_sock.bind(("127.0.0.1", port))
        lock_sock.listen(1)
        return lock_sock
    except OSError:
        print("=" * 65)
        print(f"❌ LỖI: Cổng nội bộ {port} đang được sử dụng!")
        print("Một tiến trình AgyWatch khác đang chạy trên máy tính này.")
        print("Vui lòng đóng cửa sổ Terminal cũ trước khi mở phiên mới.")
        print("=" * 65)
        sys.exit(1)


async def run_standalone_watch() -> None:
    """Khởi chạy AgyWatch ở chế độ Độc Lập (Standalone Daemon + Telegram Bot)."""
    config = load_watch_config()
    _lock = acquire_single_instance_lock()

    if not config.bot_token:
        print("❌ LỖI: Chưa cấu hình bot_token trong config.json.")
        sys.exit(1)

    tg = TelegramClient(config.bot_token)
    service = WatchService(config=config, tg=tg)
    router = WatchRouter(service=service, tg=tg)

    print("=" * 65)
    print("👁️  AGYWATCH (Autonomous Git & CI Watchdog for Antigravity)")
    print(f"📦 Repositories   : {[r.name for r in config.repos]}")
    print(f"⏱️  Poll Interval  : {config.poll_interval_seconds}s")
    print(f"🤖 Default Model  : {config.default_model}")
    print(f"🛡️  Allowed Users  : {sorted(config.allowed_user_ids)}")
    print("=" * 65)

    # 1. Đăng ký menu lệnh Telegram
    await tg.delete_webhook()
    await tg.set_my_commands(
        [
            {"command": "watch", "description": "Xem trạng thái giám sát hoặc quét ngay (/watch check)"},
            {"command": "prs", "description": "Xem danh sách các Pull Request đang mở"},
            {"command": "review", "description": "Yêu cầu Antigravity review PR: /review <PR_NUM>"},
            {"command": "doctor", "description": "Chạy chẩn đoán lỗi test local hoặc CI"},
        ]
    )
    print("✅ Đã đăng ký Menu lệnh AgyWatch với Telegram.")

    # 2. Bỏ qua các tin nhắn cũ lúc offline
    offset = 0
    resp_init = await tg.get_updates(offset=-1, timeout=1)
    if resp_init.get("ok"):
        res = resp_init.get("result") or []
        if res:
            offset = int(res[-1]["update_id"]) + 1

    # 3. Thông báo sẵn sàng
    now_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    for admin_id in config.allowed_user_ids:
        await tg.send_message(
            admin_id,
            f"👁️ <b>AgyWatch Daemon Đã Khởi Động!</b> (<code>{now_str}</code>)\n"
            f"• <b>Giám sát:</b> <code>{escape_html(', '.join(r.name for r in config.repos))}</code>\n"
            f"• <b>Chu kỳ:</b> <code>{config.poll_interval_seconds}s</code>\n"
            f"<i>Hệ thống tự động phát hiện PR mới, theo dõi CI failures và hỗ trợ review tức thì. Gõ /watch để kiểm tra.</i>",
        )

    # 4. Chạy background task polling cho WatchService
    watch_task = asyncio.create_task(service.start())

    print("💬 Đang lắng nghe lệnh từ Telegram và theo dõi Repositories... (Ctrl + C để dừng)\n")

    try:
        while True:
            resp = await tg.get_updates(offset=offset, timeout=20)
            if not resp.get("ok"):
                await asyncio.sleep(2.0)
                continue

            for update in resp.get("result") or []:
                offset = int(update["update_id"]) + 1

                # A. Xử lý tin nhắn văn bản
                msg = update.get("message")
                if msg:
                    from_user = msg.get("from", {})
                    user_id = from_user.get("id")
                    chat_id = msg.get("chat", {}).get("id")
                    text = msg.get("text", "")

                    if config.allowed_user_ids and user_id not in config.allowed_user_ids:
                        continue

                    if chat_id and text:
                        await router.handle_message(chat_id, text)

                # B. Xử lý nút bấm Inline Keyboard
                callback = update.get("callback_query")
                if callback:
                    cb_user_id = callback.get("from", {}).get("id")
                    if config.allowed_user_ids and cb_user_id not in config.allowed_user_ids:
                        continue
                    await router.handle_callback_query(callback)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n🛑 Nhận tín hiệu dừng tiến trình...")
    finally:
        service.stop()
        watch_task.cancel()
        _lock.close()
        print("✅ AgyWatch đã dừng an toàn.")


def main() -> None:
    try:
        asyncio.run(run_standalone_watch())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
