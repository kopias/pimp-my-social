"""Which Chromium the pipeline drives.

Locally that's the installed Google Chrome, so nothing needs downloading. A server sets
PMS_CHROME_CHANNEL= (empty) to use Playwright's own Chromium instead.
"""

import os

CHANNEL = os.environ.get("PMS_CHROME_CHANNEL", "chrome") or None
