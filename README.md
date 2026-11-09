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


</div>

---

## Purpose

AgyWatch is a lightweight, zero-dependency background daemon designed to automate Git repository maintenance for Google Antigravity CLI users.

It continuously monitors your repositories to:
- Review incoming pull requests with automated code analysis and structured verdicts (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`).
- Diagnose broken tests (`pytest`) and failed GitHub Actions CI runs with root-cause analysis and proposed patches.
- Deliver real-time status alerts and interactive review actions directly to Telegram.
- Automatically track whichever AI model is currently active on your local machine.

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
