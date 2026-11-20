# Publishing & Scheduling to YouTube and Instagram

ClipForge integrates with **Zernio** to schedule approved 9:16 clips directly to connected YouTube and Instagram accounts.

---

## Environment Configuration

Configure your credentials in `.env` or in your shell:

```bash
# Direct Zernio credentials:
ZERNIO_API_KEY="your_zernio_api_key"
ZERNIO_YOUTUBE_ACCOUNT_ID="your_youtube_account_id"
ZERNIO_INSTAGRAM_ACCOUNT_ID="your_instagram_account_id"

# Generic aliases also supported by publish.py:
PUBLISH_API_KEY="your_zernio_api_key"
PUBLISH_YOUTUBE_ACCOUNT_ID="your_youtube_account_id"
PUBLISH_INSTAGRAM_ACCOUNT_ID="your_instagram_account_id"
```

---

## Difference Between `publish.py` and `zernio_publish.py`

* **`zernio_publish.py`**: The primary publishing engine that handles presigned video upload, metadata assembly, idempotency keys, and post creation via the Zernio REST API. It expects `ZERNIO_*` environment variables.
* **`publish.py`**: A lightweight compatibility wrapper around `zernio_publish.py` that maps generic `PUBLISH_*` environment variables to `ZERNIO_*`. Both invoke the same underlying publisher.

---

## Publishing Commands

### 1. Dry Run Preview (No network publish)
Before posting, preview the target accounts and scheduled times:
```bash
# Windows PowerShell
python zernio_publish.py "output\clip-ID" --scheduled-for "FUTURE_ISO_TIME"

# macOS / Linux / Bash
python3 zernio_publish.py output/clip-ID --scheduled-for "FUTURE_ISO_TIME"
```

### 2. Schedule a Post
Review the generated `output/clip-ID.json` file and set `"approved": true`, then schedule with `--publish`:
```bash
# Windows PowerShell
python zernio_publish.py "output\clip-ID" --scheduled-for "FUTURE_ISO_TIME" --publish

# macOS / Linux / Bash
python3 zernio_publish.py output/clip-ID --scheduled-for "FUTURE_ISO_TIME" --publish
```

*Time format:* ISO-8601 with timezone offset (e.g., `2026-11-25T12:00:00+05:30`).

### 3. Immediate Publish
To post immediately without waiting for a schedule:
```bash
python zernio_publish.py "output\clip-ID" --now --publish
```

---

## Unattended Automated Publishing

For hands-off publishing without per-clip approval:
1. Ensure you have standing rights/permissions for your source channels.
2. Set `CLIPFORGE_UNATTENDED_POSTS=1` (or legacy `GTA_UNATTENDED_POSTS=1`) in your environment.
3. Pass `--unattended` with a future `--scheduled-for` time:
```bash
python zernio_publish.py "output\clip-ID" --unattended --scheduled-for "FUTURE_ISO_TIME" --publish
```

> **Warning:** `--unattended --now` is disallowed for safety; unattended posts must always be scheduled in the future so you can review or cancel them if needed.
