from __future__ import annotations

import shutil
import subprocess

def is_available() -> bool:
    """Check if the notify-send command is available on the system."""
    return shutil.which("notify-send") is not None

def send_desktop_notification(title: str, message: str) -> None:
    """Send a desktop notification using notify-send."""
    if not is_available():
        return
    
    subprocess.run(["notify-send", title, message], check=False)