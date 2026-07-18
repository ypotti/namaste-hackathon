"""
browser.py — Headless browser screenshot utility for the reviewer agent.

Renders a generated HTML string in a headless Chromium browser via Playwright,
waits for the p5.js canvas to finish its first draw pass, then captures a
full-page screenshot.

Public API
----------
capture_screenshot(html: str, cfg: WorkflowConfig, attempt: int) -> tuple[bytes, Path | None]
    Returns the raw PNG bytes and, when cfg.screenshot_save is True, the Path
    where the file was written.  Returns (bytes, None) when save is disabled.

The caller is responsible for handling ImportError when playwright is not
installed (screenshot_enabled should be False in that case).
"""

from __future__ import annotations

import base64
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import WorkflowConfig

# Viewport wide enough to show the full 900px canvas plus page padding.
_VIEWPORT_WIDTH = 1100
_VIEWPORT_HEIGHT = 900

# How long (ms) to wait after networkidle before taking the screenshot.
# p5.js runs setup() synchronously once the script executes, but giving it
# an extra settling period avoids capturing a blank first frame on slow CDN.
_SETTLE_MS = 1500


def capture_screenshot(
    html: str,
    cfg: WorkflowConfig,
    attempt: int,
) -> tuple[bytes, Path | None]:
    """
    Render *html* in a headless browser and return a PNG screenshot.

    Parameters
    ----------
    html:
        The full HTML document string to render.
    cfg:
        Active WorkflowConfig — used for screenshot_dir and screenshot_save.
    attempt:
        Current review attempt number, embedded in the output filename so
        screenshots from different retry passes don't overwrite each other.

    Returns
    -------
    (png_bytes, saved_path)
        png_bytes  — raw PNG image data, ready to base64-encode for the LLM.
        saved_path — Path where the file was written, or None if screenshot_save
                     is False.

    Raises
    ------
    ImportError
        If playwright is not installed.  Callers should guard with a try/except
        and set cfg.screenshot_enabled = False at startup if the import fails.
    RuntimeError
        If the browser fails to launch or the page times out.
    """
    # Deferred import so the rest of the package stays importable even when
    # playwright is not installed.
    from playwright.sync_api import sync_playwright  # type: ignore[import]

    # Write the HTML to a temporary file so the browser can load it via a
    # file:// URL.  This ensures that any relative paths inside the document
    # (none expected, but defensive) resolve correctly.
    with tempfile.NamedTemporaryFile(
        suffix=".html", mode="w", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(html)
        tmp_path = Path(tmp.name)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": _VIEWPORT_WIDTH, "height": _VIEWPORT_HEIGHT}
            )

            # Navigate and wait until no outstanding network requests remain
            # (p5.js loaded from CDN) or 15 s timeout.
            page.goto(tmp_path.as_uri(), wait_until="networkidle", timeout=15_000)

            # Extra settle time for p5.js to run setup() and draw() at least once.
            page.wait_for_timeout(_SETTLE_MS)

            png_bytes: bytes = page.screenshot(full_page=True)
            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    saved_path: Path | None = None
    if cfg.screenshot_save:
        cfg.screenshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        # Sanitise thread_id so it's safe as a filename component
        thread_slug = "".join(
            c if c.isalnum() or c in "-_" else "_"
            for c in (cfg.thread_id or "default")
        )[:40]
        filename = (
            f"review_attempt_{attempt}"
            f"_{thread_slug}"
            f"_{cfg.session_run_id}"
            f"_{timestamp}.png"
        )
        saved_path = cfg.screenshot_dir / filename
        saved_path.write_bytes(png_bytes)

    return png_bytes, saved_path


def png_to_data_url(png_bytes: bytes) -> str:
    """Encode raw PNG bytes as a base64 data URL for the OpenAI vision API."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"
