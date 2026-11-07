from __future__ import annotations

import asyncio
import json
import shutil
from typing import Any


class GitInspector:
    """
    Bộ giao tiếp bất đồng bộ với Git và GitHub CLI (gh).
    Không phụ thuộc thư viện bên ngoài, chạy thuần qua tiến trình CLI.
    """

    def __init__(self) -> None:
        self.has_gh = shutil.which("gh") is not None
        self.has_git = shutil.which("git") is not None

    async def _run_command(
        self,
        args: list[str],
        cwd: str | None = None,
        timeout: float = 45.0,
    ) -> tuple[int, str, str]:
        """Thực thi câu lệnh bất đồng bộ với timeout an toàn."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
            return proc.returncode or 0, stdout, stderr
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return -1, "", "Command timed out"
        except Exception as ex:
            return -1, "", str(ex)

    async def list_open_prs(self, repo_name: str) -> list[dict[str, Any]]:
        """Lấy danh sách các Pull Request đang mở từ GitHub repo."""
        if not self.has_gh:
            return []
        fields = "number,title,author,headRefName,baseRefName,createdAt,updatedAt,url"
        code, out, _ = await self._run_command(
            ["gh", "pr", "list", "-R", repo_name, "--state", "open", "--json", fields]
        )
        if code == 0 and out:
            try:
                data = json.loads(out)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        return []

    async def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """Lấy toàn bộ git diff của một Pull Request."""
        if not self.has_gh:
            return ""
        code, out, _ = await self._run_command(
            ["gh", "pr", "diff", str(pr_number), "-R", repo_name]
        )
        return out if code == 0 else ""

    async def get_pr_details(self, repo_name: str, pr_number: int) -> dict[str, Any]:
        """Lấy thông tin chi tiết của một PR."""
        if not self.has_gh:
            return {}
        fields = "number,title,body,author,headRefName,baseRefName,files,url,mergeable"
        code, out, _ = await self._run_command(
            ["gh", "pr", "view", str(pr_number), "-R", repo_name, "--json", fields]
        )
        if code == 0 and out:
            try:
                return json.loads(out)
            except json.JSONDecodeError:
                pass
        return {}

    async def list_ci_runs(
        self, repo_name: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Lấy danh sách kết quả CI gần nhất của repository."""
        if not self.has_gh:
            return []
        fields = "databaseId,name,status,conclusion,headBranch,url,createdAt"
        code, out, _ = await self._run_command(
            ["gh", "run", "list", "-R", repo_name, "--limit", str(limit), "--json", fields]
        )
        if code == 0 and out:
            try:
                data = json.loads(out)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        return []

    async def get_failed_ci_logs(self, repo_name: str, run_id: int) -> str:
        """Lấy log lỗi của một CI run bị thất bại."""
        if not self.has_gh:
            return ""
        code, out, _ = await self._run_command(
            ["gh", "run", "view", str(run_id), "-R", repo_name, "--log-failed"]
        )
        return out if code == 0 else ""

    async def submit_pr_review(
        self, repo_name: str, pr_number: int, decision: str, body: str
    ) -> bool:
        """
        Gửi review trực tiếp lên GitHub PR.
        decision: 'approve' | 'comment' | 'request-changes'
        """
        if not self.has_gh:
            return False
        flag = f"--{decision}" if decision in ("approve", "comment", "request-changes") else "--comment"
        code, _, _ = await self._run_command(
            ["gh", "pr", "review", str(pr_number), "-R", repo_name, flag, "-b", body]
        )
        return code == 0

    async def comment_on_pr(self, repo_name: str, pr_number: int, body: str) -> bool:
        """Gửi comment lên PR hoặc Issue."""
        if not self.has_gh:
            return False
        code, _, _ = await self._run_command(
            ["gh", "pr", "comment", str(pr_number), "-R", repo_name, "--body", body]
        )
        return code == 0

    async def run_local_tests(
        self, local_path: str, test_command: str = "python -m pytest"
    ) -> tuple[int, str, str]:
        """Chạy kiểm thử cục bộ trong thư mục repository."""
        args = test_command.split()
        return await self._run_command(args, cwd=local_path, timeout=120.0)
