from __future__ import annotations

import asyncio
import json
import shutil
from typing import Any, Callable, Coroutine


def find_agy_binary() -> str:
    """Tìm đường dẫn thực thi của Antigravity CLI (`agy`)."""
    found = shutil.which("agy") or shutil.which("agy.exe")
    return found or "agy"


class AgyRunner:
    """
    Trình điều phối subprocess thực thi Google Antigravity CLI (`agy`)
    ở chế độ không đầu (Headless) qua giao thức stream-json (NDJSON).
    """

    def __init__(self, default_model: str = "gemini-4-argon-high") -> None:
        self.default_model = default_model
        self.agy_bin = find_agy_binary()

    async def execute_task(
        self,
        prompt: str,
        workspace: str,
        model: str | None = None,
        timeout: float = 300.0,
        on_progress: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    ) -> tuple[int, str]:
        """
        Thực thi một tác vụ phân tích/review/doctor qua Antigravity CLI.
        - `prompt`: Yêu cầu chi tiết gửi cho agent.
        - `workspace`: Thư mục làm việc của dự án.
        - `on_progress`: Callback bất đồng bộ nhận thông báo tiến độ từng bước.
        Trả về: (returncode, final_response_text)
        """
        chosen_model = model or self.default_model
        args = [
            self.agy_bin,
            "--output-format",
            "stream-json",
            "--model",
            chosen_model,
            prompt,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=workspace,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as ex:
            return -1, f"Lỗi khởi chạy tiến trình Antigravity CLI: {ex}"

        final_chunks: list[str] = []

        async def _read_stdout() -> None:
            if not proc.stdout:
                return
            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    p_type = payload.get("type", "")

                    if p_type == "content":
                        chunk = payload.get("content", "")
                        if chunk:
                            final_chunks.append(chunk)

                    elif p_type == "tool_call":
                        tool_name = payload.get("name", "Tool")
                        summary = payload.get("summary", "")
                        msg = f"⚙️ Đang chạy: <b>{tool_name}</b> {summary}".strip()
                        if on_progress:
                            await on_progress(msg)

                    elif p_type == "result":
                        res_text = payload.get("result", "")
                        if res_text and not final_chunks:
                            final_chunks.append(res_text)

                except json.JSONDecodeError:
                    # Dòng text thuần từ output CLI
                    if not line.startswith("{"):
                        final_chunks.append(line)

        try:
            await asyncio.wait_for(_read_stdout(), timeout=timeout)
            await proc.wait()
            returncode = proc.returncode or 0
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return -1, f"Tác vụ bị quá thời gian giới hạn ({int(timeout)}s)."
        except Exception as ex:
            return -1, f"Lỗi trong quá trình thực thi: {ex}"

        result_text = "".join(final_chunks).strip()
        return returncode, result_text
