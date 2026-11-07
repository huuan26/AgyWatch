from __future__ import annotations

import socket
import unittest

from src.config import RepoTarget, WatchConfig, load_watch_config
from src.git_inspector import GitInspector
from src.reviewer import PRReviewer
from src.telegram_api import escape_html
from src.watch_router import WatchRouter


class TestAgyWatchCore(unittest.TestCase):
    def test_escape_html(self) -> None:
        raw = "<div>Hello & 'world' > 10 < 20</div>"
        escaped = escape_html(raw)
        self.assertNotIn("<div", escaped)
        self.assertIn("&lt;div", escaped)
        self.assertIn("&amp;", escaped)
        self.assertIn("&gt;", escaped)

    def test_repo_target_serialization(self) -> None:
        target = RepoTarget(
            name="huuan26/polars-anta",
            local_path="C:/test/path",
            watch_prs=True,
            watch_ci=True,
        )
        data = target.to_dict()
        self.assertEqual(data["name"], "huuan26/polars-anta")
        self.assertTrue(data["watch_prs"])

        restored = RepoTarget.from_dict(data)
        self.assertEqual(restored.name, target.name)
        self.assertEqual(restored.local_path, target.local_path)

    def test_watch_config(self) -> None:
        cfg = WatchConfig(
            bot_token="test_token",
            allowed_user_ids=[123456],
            poll_interval_seconds=30,
            repos=[RepoTarget(name="huuan26/polars-anta")],
        )
        self.assertEqual(cfg.bot_token, "test_token")
        self.assertEqual(cfg.poll_interval_seconds, 30)
        self.assertEqual(len(cfg.repos), 1)

    def test_review_prompt_builder(self) -> None:
        inspector = GitInspector()
        reviewer = PRReviewer(inspector=inspector, runner=None)  # type: ignore

        meta = {
            "title": "feat: add TRIX indicator",
            "author": {"login": "test_user"},
            "body": "Fixes #20",
        }
        diff = "+ def trix():\n+     pass\n"

        prompt = reviewer.build_review_prompt(meta, diff)
        self.assertIn("feat: add TRIX indicator", prompt)
        self.assertIn("@test_user", prompt)
        self.assertIn("DECISION: APPROVE", prompt)
        self.assertIn("+ def trix():", prompt)

    def test_single_instance_socket_lock(self) -> None:
        test_port = 9888
        sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock1.bind(("127.0.0.1", test_port))
        sock1.listen(1)

        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with self.assertRaises(OSError):
            sock2.bind(("127.0.0.1", test_port))

        sock1.close()
        sock2.close()


if __name__ == "__main__":
    unittest.main()
