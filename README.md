<div align="center">

<pre align="center">
 █████╗  ██████╗ ██╗   ██╗██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗
██╔══██╗██╔════╝ ╚██╗ ██╔╝██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║
███████║██║  ███╗ ╚████╔╝ ██║ █╗ ██║███████║   ██║   ██║     ███████║
██╔══██║██║   ██║  ╚██╔╝  ██║███╗██║██╔══██║   ██║   ██║     ██╔══██║
██║  ██║╚██████╔╝   ██║   ╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
</pre>

<p align="center">
  <strong>Autonomous Git, Pull Request and CI Watchdog Daemon for Google Antigravity CLI</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square" alt="Python 3.10+" /></a>
  <a href="#features"><img src="https://img.shields.io/badge/Dependencies-Zero%20(Stdlib)-success?style=flat-square" alt="Zero Dependencies" /></a>
  <a href="#features"><img src="https://img.shields.io/badge/Protocol-Stream--JSON%20(NDJSON)-orange?style=flat-square" alt="Stream-JSON" /></a>
  <a href="#unified-bot-integration-with-agytele"><img src="https://img.shields.io/badge/AgyTele-Co--Bot%20Ready-emerald?style=flat-square" alt="Co-Bot Ready" /></a>
</p>

</div>

---

## Overview

AgyWatch is an autonomous Git and CI watchdog daemon written in pure Python (`asyncio`) for the Google Antigravity CLI (`agy`). It monitors repositories in the background, triggers automated code reviews for new pull requests, diagnoses failed test suites and CI runs, and sends alerts via Telegram.

---

## Features

- **Zero External Dependencies**: Built entirely with Python 3.10+ standard libraries (`asyncio`, `urllib.request`, `json`, `socket`, `dataclasses`, `pathlib`). No `pip install` required.
- **Automated PR Review**: Fetches git diffs via `gh`, invokes `agy --output-format stream-json`, and returns structured reviews with `APPROVE`, `REQUEST_CHANGES`, or `COMMENT` verdicts.
- **CI and Test Diagnostics**: Detects failed `pytest` or GitHub Actions runs, extracts error tracebacks, and prompts the agent to perform root-cause analysis and generate code patches.
- **Local Model Auto-Sync**: Automatically detects the active AI model from local Antigravity settings (`~/.gemini/antigravity-cli/settings.json`) without hardcoded model strings.
- **Co-Bot Ready**: Can run standalone or mount directly into an existing [AgyTele](https://github.com/huuan26/AgyTele) instance using a single Telegram bot token.

---

## Architecture

```text
  [ Local Git Repos / GitHub Remote (gh) ]
                     │
         (Polls PRs, CI, Test Suite)
                     ▼
        ┌─────────────────────────┐
        │    AgyWatch Daemon      │ ◄── Port 9879 Lock (Standalone)
        └────────────┬────────────┘
                     │
          (Headless stream-json)
                     ▼
        ┌─────────────────────────┐
        │  Antigravity CLI (agy)  │ ──► Code Review & Self-Healing
        └────────────┬────────────┘
                     │
          (Actionable Review / Patch)
                     ▼
        ┌─────────────────────────┐
        │  Unified Telegram Bot   │ ◄── [Review] [Approve] [Doctor]
        └─────────────────────────┘
```

---

## Unified Bot Integration with AgyTele

To run AgyWatch and AgyTele together on the same Telegram bot without polling conflicts (HTTP 409):

Add three lines to `Anti-Tele-An/main.py`:

```python
import sys
sys.path.append("C:/Users/ADMIN/Documents/AgyWatch")
from src.integration import attach_to_agy_tele

# After initializing the router:
router = BotRouter(tg, state, bridge)
attach_to_agy_tele(tele_router=router, tele_tg=tg)
```

---

## Commands

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/watch` | `/watch [status\|check]` | Show daemon status or trigger an immediate repository scan |
| `/prs` | `/prs [repo_name]` | List open pull requests with quick action buttons |
| `/review` | `/review <PR_NUMBER> [repo]` | Run an in-depth Antigravity code review for a PR |
| `/doctor` | `/doctor [local_path]` | Run local test suite (`pytest`) or inspect failed CI run logs |

---

## Quick Start (Standalone)

### 1. Configuration

Create or update `config.json`:

```json
{
  "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
  "allowed_user_ids": [6876958198],
  "poll_interval_seconds": 60,
  "default_model": "auto",
  "auto_review_new_prs": false,
  "auto_notify_telegram": true,
  "repos": [
    {
      "name": "huuan26/polars-anta",
      "local_path": "C:/Users/ADMIN/Documents/polars-anta",
      "watch_prs": true,
      "watch_ci": true,
      "watch_local_tests": true,
      "test_command": "python -m pytest"
    }
  ]
}
```

### 2. Run

On Windows, double-click `run.bat` or run:

```bash
# Optional interactive wizard:
python setup.py

# Start daemon:
python main.py
```

### 3. Run Unit Tests

```bash
python -m unittest discover -s tests -v
```

---

<div align="center">

**AgyWatch &bull; Autonomous Git &amp; CI Watchdog for Google Antigravity**  
Maintained by [huuan26](https://github.com/huuan26)

</div>
