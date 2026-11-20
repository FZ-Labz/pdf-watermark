"""
updater.py - Installs and updates the Windows app with Velopack.

People install the app once with PDF-Watermark-Setup.exe (no admin rights,
lives in %LOCALAPPDATA%\\PDFWatermark). After that, the app asks GitHub
Releases for a newer version when it opens. "Update now" downloads only what
changed since the installed version, then Velopack swaps it in and restarts
the app. Settings live in %APPDATA% and are never touched.

The release workflow builds the update files with `vpk pack` and publishes
them with `vpk upload github`; see .github/workflows/release.yml.

Set PDF_WATERMARK_UPDATE_URL to a folder or URL to test against a local feed
instead of GitHub.
"""

from __future__ import annotations

import logging
import os
import sys

log = logging.getLogger("pdf-watermark")

REPO_URL = "https://github.com/FZ-Labz/pdf-watermark"
PAGE = f"{REPO_URL}/releases/latest"


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
    """A newer release, if there is one. Never raises; None when not installed or offline."""
    try:
        manager = _manager()
        info = manager.check_for_updates()
    except Exception:  # noqa: BLE001 - not installed by Velopack, offline, rate-limited...
        log.info("update check skipped", exc_info=True)
        return None
    if not info:
        return None
    return {"version": info.TargetFullRelease.Version, "page": PAGE, "_info": info, "_manager": manager}


def install(update: dict) -> None:
    """Download the update and restart into it. Raises on failure, changing nothing."""
    manager, info = update["_manager"], update["_info"]
    manager.download_updates(info)
    # Velopack's Update.exe waits for this process to exit, swaps the new
    # version in and starts it again.
    manager.wait_exit_then_apply_updates(info, silent=True, restart=True)
