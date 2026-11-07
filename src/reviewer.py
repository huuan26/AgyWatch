from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from .agy_runner import AgyRunner
from .git_inspector import GitInspector


@dataclass
class ReviewResult:
    """Kết quả phân tích Pull Request từ AI Agent."""

    repo_name: str
    pr_number: int
    title: str
    author: str
    decision: str  # "APPROVE", "REQUEST_CHANGES", "COMMENT"
    summary: str
    review_markdown: str


class PRReviewer:
    """Hệ thống đánh giá Pull Request chuyên sâu bằng Antigravity CLI."""

    def __init__(self, inspector: GitInspector, runner: AgyRunner) -> None:
        self.inspector = inspector
        self.runner = runner

    def build_review_prompt(self, pr_meta: dict[str, Any], diff: str) -> str:
        """Tạo prompt chuẩn mực cho Antigravity đánh giá toàn diện mã nguồn."""
        title = pr_meta.get("title", "")
        author = pr_meta.get("author", {}).get("login", "unknown")
        body = pr_meta.get("body", "")

        # Giới hạn diff tránh tràn context nếu PR quá lớn
        diff_snippet = diff[:28000] if len(diff) > 28000 else diff
        truncated_note = "\n\n*(Diff was truncated to 28,000 chars)*" if len(diff) > 28000 else ""

        prompt = f"""You are an elite Senior Code Reviewer for a high-performance quantitative & systems codebase.
Review the following Pull Request with high precision:

**PR Title**: {title}
**Author**: @{author}
**PR Description**:
{body}

**Git Diff**:
```diff
{diff_snippet}{truncated_note}
```

### Review Guidelines:
1. **Architectural & Vectorization Fit**: Check if expressions are fully vectorized (pure expressions, no Python for-loops, safe .over("symbol") multi-asset behavior).
2. **Mathematical & Algorithmic Parity**: Verify formula edge-cases (division by zero, null/NaN handling, standard deviation / moments sample vs population).
3. **API & Namespace Completeness**: Verify namespace exposure, `__all__` exports, type annotations, and docstrings.
4. **Test Suite Quality**: Verify comprehensive unit tests, golden reference parity, edge tests.
5. **Final Recommendation**:
   At the very end of your review, conclude with an explicit line:
   `DECISION: APPROVE` or `DECISION: REQUEST_CHANGES` or `DECISION: COMMENT`
   followed by a 1-sentence executive verdict.

Provide a clear, concise, structured GitHub Markdown review.
"""
        return prompt

    async def review_pr(
        self,
        repo_name: str,
        pr_number: int,
        workspace: str = "",
        on_progress: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    ) -> ReviewResult:
        """Thực hiện quy trình review PR tự động."""
        if on_progress:
            await on_progress(f"🔍 Đang tải thông tin và diff của PR #{pr_number} ({repo_name})...")

        meta = await self.inspector.get_pr_details(repo_name, pr_number)
        diff = await self.inspector.get_pr_diff(repo_name, pr_number)

        if not diff:
            return ReviewResult(
                repo_name=repo_name,
                pr_number=pr_number,
                title=meta.get("title", f"PR #{pr_number}"),
                author=meta.get("author", {}).get("login", ""),
                decision="COMMENT",
                summary="Không tìm thấy diff của PR.",
                review_markdown="Không có dữ liệu git diff để phân tích.",
            )

        prompt = self.build_review_prompt(meta, diff)

        if on_progress:
            await on_progress("🧠 Antigravity Agent đang phân tích kiến trúc và thuật toán...")

        work_dir = workspace or "."
        code, output = await self.runner.execute_task(
            prompt=prompt,
            workspace=work_dir,
            timeout=240.0,
            on_progress=on_progress,
        )

        decision = "COMMENT"
        if "DECISION: APPROVE" in output.upper():
            decision = "APPROVE"
        elif "DECISION: REQUEST_CHANGES" in output.upper():
            decision = "REQUEST_CHANGES"

        # Trích xuất dòng tóm tắt
        summary = "Đã hoàn thành đánh giá mã nguồn."
        match = re.search(r"DECISION:[^\n]+\n([^\n]+)", output)
        if match:
            summary = match.group(1).strip()

        return ReviewResult(
            repo_name=repo_name,
            pr_number=pr_number,
            title=meta.get("title", f"PR #{pr_number}"),
            author=meta.get("author", {}).get("login", ""),
            decision=decision,
            summary=summary,
            review_markdown=output,
        )
