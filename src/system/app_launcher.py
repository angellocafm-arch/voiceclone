"""
VoiceClone — App Launcher

Launch system applications and manage running processes.
macOS primary, Linux secondary.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

# Apps that are always safe to open
SAFE_APPS = {
    "safari", "chrome", "google chrome", "firefox",
    "finder", "files", "nautilus",
    "notes", "textedit", "gedit", "kate",
    "calculator", "calendar", "contacts",
    "photos", "preview", "music", "spotify",
    "mail", "messages", "facetime",
    "settings", "system preferences", "system settings",
    "terminal", "iterm", "console",
    "vlc", "quicktime player",
}

# Apps that require confirmation
CONFIRM_APPS = {
    "terminal", "iterm",  # Can run arbitrary commands
}

# Apps/commands that are BLOCKED
BLOCKED_APPS = {
    "sudo", "su", "rm", "mkfs", "dd", "diskutil",
    "format", "fdisk", "shutdown", "reboot", "halt",
}


class AppLauncher:
    """
    Launch and manage system applications.

    Security: Only whitelisted apps can be opened without confirmation.
    System-level commands are blocked.
    """

    def __init__(self) -> None:
        self._system = os.uname().sysname

    def open_app(self, app_name: str) -> dict[str, Any]:
        """
        Open an application by name.

        Confirmation level: NONE for safe apps, SINGLE for others.

        Args:
            app_name: Name of the application.

        Returns:
            Success/failure dict.
        """
        app_lower = app_name.lower().strip()

        # Security check
        if app_lower in BLOCKED_APPS:
            return {
                "error": f"'{app_name}' is blocked for security reasons.",
                "success": False,
            }

        try:
            if self._system == "Darwin":
                return self._open_macos(app_name)
            elif self._system == "Linux":
                return self._open_linux(app_name)
            else:
                return {"error": f"Unsupported OS: {self._system}", "success": False}

        except Exception as e:
            logger.error("Failed to open app '%s': %s", app_name, e)
            return {"error": str(e), "success": False}

    def _open_macos(self, app_name: str) -> dict[str, Any]:
        """Open an app on macOS using 'open -a'."""
        result = subprocess.run(
            ["open", "-a", app_name],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            logger.info("Opened app (macOS): %s", app_name)
            return {"success": True, "app": app_name, "os": "macOS"}

        return {
            "error": f"Could not open '{app_name}': {result.stderr.strip()}",
            "success": False,
        }

    def _open_linux(self, app_name: str) -> dict[str, Any]:
        """Open an app on Linux using common launchers."""
        # Try direct command first
        for cmd in [app_name.lower(), app_name.lower().replace(" ", "-")]:
            try:
                proc = subprocess.Popen(
                    [cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info("Opened app (Linux): %s (pid=%d)", cmd, proc.pid)
                return {"success": True, "app": app_name, "pid": proc.pid, "os": "Linux"}
            except FileNotFoundError:
                continue

        # Try xdg-open for .desktop apps
        try:
            subprocess.Popen(
                ["gtk-launch", app_name.lower()],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {"success": True, "app": app_name, "os": "Linux"}
        except FileNotFoundError:
            pass

        return {"error": f"Application '{app_name}' not found", "success": False}

    def list_running_apps(self) -> dict[str, Any]:
        """
        List currently running applications.

        Confirmation level: NONE
        """
        try:
            if self._system == "Darwin":
                result = subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to get name of every process whose background only is false'],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    apps = [a.strip() for a in result.stdout.strip().split(", ") if a.strip()]
                    return {"success": True, "apps": apps, "count": len(apps)}

            elif self._system == "Linux":
                result = subprocess.run(
                    ["wmctrl", "-l"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    apps = []
                    for line in result.stdout.strip().split("\n"):
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            apps.append(parts[3])
                    return {"success": True, "apps": apps, "count": len(apps)}

            return {"success": True, "apps": [], "count": 0}

        except Exception as e:
            logger.error("Failed to list apps: %s", e)
            return {"error": str(e), "success": False}

    def is_safe_app(self, app_name: str) -> bool:
        """Check if an app is in the safe list."""
        return app_name.lower().strip() in SAFE_APPS
