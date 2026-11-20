"""
updater.py - Installs and updates the Windows app with Velopack.

People install the app once with PDF-Watermark-Setup.exe (no admin rights,
lives in %LOCALAPPDATA%\\PDFWatermark). After that, the app looks for a newer
release when it opens and every CHECK_EVERY seconds while it stays open, and
shows a card offering it. "Update now" downloads only what changed since the
installed version, then Velopack swaps it in and restarts the app. Settings
live in %APPDATA% and are never touched.

The release workflow builds the update files with `vpk pack` and publishes
them with `vpk upload github`; see .github/workflows/release.yml.

Checking often has to stay cheap: GitHub's API allows only 60 calls an hour
per internet connection, shared by every PC in an office. So each check first
reads the small releases.win.json from the latest release's downloads, which
is not counted against that limit, and asks Velopack (which does use the API)
only once that file shows a newer version.

Set PDF_WATERMARK_UPDATE_URL to a folder or URL to test against a local feed
instead of GitHub.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import urllib.request
from pathlib import Path

log = logging.getLogger("pdf-watermark")

REPO_URL = "https://github.com/FZ-Labz/pdf-watermark"
PAGE = f"{REPO_URL}/releases/latest"
FEED = f"{REPO_URL}/releases/latest/download/releases.win.json"
CHECK_EVERY = 120   # seconds between checks while the app is open

_found: dict | None = None   # the last update Velopack confirmed, reused while it is still the newest


def current_version() -> str:
    """This build's version: the VERSION file, which the release build stamps and bundles."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    try:
        return (base / "VERSION").read_text(encoding="utf-8").strip() or "0.0.0"
    except OSError:
        return "0.0.0"


def version_key(version: str) -> tuple[int, int, int]:
    """
    (major, minor, patch) for comparing. Anything after the numbers, such as
    "-test.1", is ignored, as Velopack itself does.
    """
    m = re.match(r"\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", version or "")
    return tuple(int(p or 0) for p in m.groups()) if m else (0, 0, 0)


def newest_in_feed(feed: dict) -> str | None:
    """The highest full-package version listed in a releases.win.json."""
    versions = [a.get("Version", "") for a in feed.get("Assets", []) if a.get("Type", "Full") == "Full"]
    return max(versions, key=version_key, default=None)


def latest_version(timeout: float = 10) -> str | None:
    """The newest published version, from the latest release's feed file. None if it can't be read."""
    request = urllib.request.Request(FEED, headers={"User-Agent": "PDF-Watermark-updater"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https URL
        return newest_in_feed(json.loads(response.read().decode("utf-8")))


def startup() -> None:
    """
    Velopack's install/update/uninstall hooks. Must run first thing: when the
    installer calls the app with one of its hook arguments, this does the work
    and exits the process.
    """
    if not getattr(sys, "frozen", False):
        return
    try:
        import velopack

        velopack.App().run()
    except Exception:  # noqa: BLE001 - never stop the app from opening
        logging.getLogger("pdf-watermark").warning("velopack startup failed", exc_info=True)


def _manager():
    import velopack

    source = os.environ.get("PDF_WATERMARK_UPDATE_URL") or velopack.GithubSource(REPO_URL)
    return velopack.UpdateManager(source)


def check() -> dict | None:
    """A newer release, if there is one. Never raises; None when up to date, not installed or offline."""
    global _found
    try:
        if not os.environ.get("PDF_WATERMARK_UPDATE_URL"):
            latest = latest_version()
            if not latest or version_key(latest) <= version_key(current_version()):
                return None
            if _found and _found["version"] == latest:
                return _found
        manager = _manager()
        info = manager.check_for_updates()
    except Exception:  # noqa: BLE001 - not installed by Velopack, offline, rate-limited...
        log.info("update check skipped", exc_info=True)
        return None
    if not info:
        return None
    _found = {"version": info.TargetFullRelease.Version, "page": PAGE, "_info": info, "_manager": manager}
    return _found


def install(update: dict) -> None:
    """Download the update and restart into it. Raises on failure, changing nothing."""
    manager, info = update["_manager"], update["_info"]
    manager.download_updates(info)
    # Velopack's Update.exe waits for this process to exit, swaps the new
    # version in and starts it again.
    manager.wait_exit_then_apply_updates(info, silent=True, restart=True)
