from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from .agy_runner import AgyRunner
from .git_inspector import GitInspector


@dataclass
class DiagnosisResult:
    """Kết quả chẩn đoán và khắc phục lỗi tự động."""

    target: str
    status: str  # "HEALTHY" | "FAILED" | "FIXED"
    error_summary: str
    analysis: str
    suggested_patch: str


class DoctorEngine:
    """Bác sĩ tự động (Self-Healing Doctor) phát hiện và sửa lỗi kiểm thử / CI."""

    def __init__(self, inspector: GitInspector, runner: AgyRunner) -> None:
        self.inspector = inspector
        self.runner = runner

    async def check_local_health(
        self,
        local_path: str,
        test_command: str = "python -m pytest",
        on_progress: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    ) -> DiagnosisResult:
        """Chạy kiểm thử local và triệu hồi Antigravity phân tích nếu có lỗi."""
        if on_progress:
            await on_progress(f"🧪 Đang chạy kiểm thử: <code>{test_command}</code>...")

        code, stdout, stderr = await self.inspector.run_local_tests(
            local_path=local_path, test_command=test_command
        )

        if code == 0:
            return DiagnosisResult(
                target=local_path,
                status="HEALTHY",
                error_summary="Tất cả bài kiểm thử đều vượt qua (100% Passed).",
                analysis="Codebase khỏe mạnh, không phát hiện lỗi hồi quy.",
                suggested_patch="",
            )

        # Có lỗi kiểm thử -> gom log
        raw_error = f"{stdout}\n{stderr}"
        snippet = raw_error[-8000:] if len(raw_error) > 8000 else raw_error

        if on_progress:
            await on_progress("🩺 Phát hiện test fail! Antigravity đang chẩn đoán nguyên nhân...")

        prompt = f"""You are an elite Software Engineer and Debugging Expert.
The test suite failed with the following output:

```text
{snippet}
```

Please perform a Root Cause Analysis (RCA):
1. **Root Cause**: Pinpoint exactly which file, function, and assertion/line caused the failure.
2. **Analysis**: Explain why the error occurred.
3. **Proposed Fix / Patch**: Provide the exact code diff or fix needed to resolve this failure.
"""

        _, analysis = await self.runner.execute_task(
            prompt=prompt,
            workspace=local_path,
            timeout=240.0,
            on_progress=on_progress,
        )

        return DiagnosisResult(
            target=local_path,
            status="FAILED",
            error_summary="Phát hiện bài kiểm thử bị lỗi!",
            analysis=analysis,
            suggested_patch="",
        )

    async def check_ci_health(
        self,
        repo_name: str,
        workspace: str,
        on_progress: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    ) -> list[DiagnosisResult]:
        """Kiểm tra các CI Run gần nhất trên GitHub."""
        runs = await self.inspector.list_ci_runs(repo_name, limit=3)
        results: list[DiagnosisResult] = []

        for r in runs:
            conclusion = r.get("conclusion")
            run_id = r.get("databaseId")
            run_name = r.get("name", "CI")
            if conclusion == "failure" and run_id:
                if on_progress:
                    await on_progress(f"🚨 Phát hiện CI Run #{run_id} ({run_name}) bị FAIL! Đang trích xuất log...")
                logs = await self.inspector.get_failed_ci_logs(repo_name, run_id)
                prompt = f"""Analyze the failed GitHub Actions CI run #{run_id} ({run_name}):

Logs:
```text
{logs[-8000:]}
```

Identify the root cause of the CI failure and suggest the required fix.
"""
                _, analysis = await self.runner.execute_task(
                    prompt=prompt,
                    workspace=workspace or ".",
                    timeout=200.0,
                    on_progress=on_progress,
                )
                results.append(
                    DiagnosisResult(
                        target=f"{repo_name} (Run #{run_id})",
                        status="FAILED",
                        error_summary=f"CI '{run_name}' thất bại trên GitHub Actions.",
                        analysis=analysis,
                        suggested_patch="",
                    )
                )

        return results
