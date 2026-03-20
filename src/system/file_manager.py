"""
VoiceClone — File Manager

OS-level file operations exposed as LLM tools.
Implements security boundaries: safe actions (read/list) don't need confirmation,
destructive actions (delete/move) require user confirmation.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Security Constants ───────────────────────────────────

# Directories that are ALWAYS blocked
BLOCKED_PATHS = {
    "/System",
    "/usr",
    "/bin",
    "/sbin",
    "/etc",
    "/private/etc",
    "/Library",
}

# Temp dirs that ARE allowed (resolve through /private on macOS)
ALLOWED_PREFIXES = {
    "/tmp",
    "/var/folders",     # macOS temp dirs
    "/private/tmp",
    "/private/var/folders",
}

# Patterns that are blocked in filenames
BLOCKED_PATTERNS = {".."}

# Max file size to read (5 MB)
MAX_READ_SIZE = 5 * 1024 * 1024

# Max items to return in directory listing
MAX_LIST_ITEMS = 200


@dataclass
class FileInfo:
    """Information about a file or directory."""
    name: str
    path: str
    type: str  # "file" | "directory" | "symlink"
    size: int = 0
    modified: float = 0
    extension: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "type": self.type,
            "size": self.size,
            "modified": self.modified,
            "extension": self.extension,
        }


class FileManager:
    """
    Secure file operations for VoiceClone.

    All paths are validated against security boundaries before execution.
    The home directory is the default safe zone.
    """

    def __init__(self, home_dir: Optional[str] = None) -> None:
        self.home_dir = Path(home_dir or Path.home()).resolve()

    # ─── Security ─────────────────────────────────────────

    def _validate_path(self, path: str) -> Path:
        """
        Validate and resolve a path, ensuring it's safe to access.

        Args:
            path: User-provided path string.

        Returns:
            Resolved Path object.

        Raises:
            PermissionError: If the path is in a blocked zone.
            ValueError: If the path contains blocked patterns.
        """
        # Expand ~ and resolve
        resolved = Path(path).expanduser().resolve()

        # Check for blocked patterns
        for pattern in BLOCKED_PATTERNS:
            if pattern in str(path):
                raise ValueError(f"Path contains blocked pattern: '{pattern}'")

        # Check if path is in an explicitly allowed prefix (e.g. temp dirs)
        resolved_str = str(resolved)
        in_allowed = any(resolved_str.startswith(p) for p in ALLOWED_PREFIXES)

        # Check against blocked directories (skip if in allowed prefix)
        if not in_allowed:
            for blocked in BLOCKED_PATHS:
                if resolved_str.startswith(blocked):
                    raise PermissionError(
                        f"Access to '{blocked}' is not allowed for security."
                    )

        return resolved

    def _is_in_home(self, path: Path) -> bool:
        """Check if a path is within the user's home directory."""
        try:
            path.resolve().relative_to(self.home_dir)
            return True
        except ValueError:
            return False

    # ─── Read Operations (No confirmation needed) ─────────

    def list_directory(
        self,
        path: str = "~",
        pattern: str = "*",
        show_hidden: bool = False,
    ) -> dict[str, Any]:
        """
        List files and directories.

        Args:
            path: Directory to list (default: home).
            pattern: Glob pattern to filter results.
            show_hidden: Whether to include hidden files.

        Returns:
            Dict with items list and metadata.
        """
        try:
            dir_path = self._validate_path(path)

            if not dir_path.is_dir():
                return {"error": f"'{path}' is not a directory", "success": False}

            items: list[dict[str, Any]] = []
            for entry in sorted(dir_path.glob(pattern))[:MAX_LIST_ITEMS]:
                if not show_hidden and entry.name.startswith("."):
                    continue
                try:
                    stat = entry.stat()
                    items.append(FileInfo(
                        name=entry.name,
                        path=str(entry),
                        type="directory" if entry.is_dir() else "file",
                        size=stat.st_size if entry.is_file() else 0,
                        modified=stat.st_mtime,
                        extension=entry.suffix,
                    ).to_dict())
                except (PermissionError, OSError):
                    continue

            return {
                "success": True,
                "path": str(dir_path),
                "count": len(items),
                "items": items,
            }

        except (PermissionError, ValueError) as e:
            return {"error": str(e), "success": False}

    def read_file(
        self,
        path: str,
        max_chars: int = 5000,
    ) -> dict[str, Any]:
        """
        Read a text file.

        Args:
            path: File path.
            max_chars: Maximum characters to return.

        Returns:
            Dict with file content.
        """
        try:
            file_path = self._validate_path(path)

            if not file_path.is_file():
                return {"error": f"'{path}' is not a file", "success": False}

            if file_path.stat().st_size > MAX_READ_SIZE:
                return {
                    "error": f"File is too large ({file_path.stat().st_size} bytes). Max: {MAX_READ_SIZE}",
                    "success": False,
                }

            content = file_path.read_text(encoding="utf-8", errors="replace")
            truncated = len(content) > max_chars

            return {
                "success": True,
                "path": str(file_path),
                "content": content[:max_chars],
                "truncated": truncated,
                "size": len(content),
            }

        except (PermissionError, ValueError) as e:
            return {"error": str(e), "success": False}
        except UnicodeDecodeError:
            return {"error": "File is not a text file", "success": False}

    def search_files(
        self,
        query: str,
        path: str = "~",
        max_results: int = 20,
    ) -> dict[str, Any]:
        """
        Search for files by name.

        Args:
            query: Search query (case-insensitive substring match).
            path: Directory to search in.
            max_results: Maximum number of results.

        Returns:
            Dict with matching files.
        """
        try:
            search_path = self._validate_path(path)
            query_lower = query.lower()
            results: list[dict[str, Any]] = []

            for root, dirs, files in os.walk(search_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for name in files:
                    if query_lower in name.lower():
                        full_path = os.path.join(root, name)
                        try:
                            stat = os.stat(full_path)
                            results.append({
                                "name": name,
                                "path": full_path,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                            })
                        except OSError:
                            continue

                        if len(results) >= max_results:
                            return {
                                "success": True,
                                "query": query,
                                "results": results,
                                "count": len(results),
                                "truncated": True,
                            }

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
                "truncated": False,
            }

        except (PermissionError, ValueError) as e:
            return {"error": str(e), "success": False}

    def get_file_info(self, path: str) -> dict[str, Any]:
        """Get metadata about a file or directory."""
        try:
            file_path = self._validate_path(path)
            if not file_path.exists():
                return {"error": f"'{path}' does not exist", "success": False}

            stat = file_path.stat()
            return {
                "success": True,
                "name": file_path.name,
                "path": str(file_path),
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": file_path.suffix,
                "readable": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK),
            }

        except (PermissionError, ValueError) as e:
            return {"error": str(e), "success": False}

    # ─── Write Operations (Confirmation: none or single) ──

    def create_folder(self, path: str) -> dict[str, Any]:
        """
        Create a folder (including parent directories).

        Confirmation level: NONE
        """
        try:
            folder_path = self._validate_path(path)
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info("Created folder: %s", folder_path)
            return {"success": True, "path": str(folder_path)}
        except (PermissionError, ValueError, OSError) as e:
            return {"error": str(e), "success": False}

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        """
        Write content to a text file.

        Confirmation level: SINGLE (overwrites existing files)
        """
        try:
            file_path = self._validate_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            logger.info("Wrote file: %s (%d bytes)", file_path, len(content))
            return {
                "success": True,
                "path": str(file_path),
                "size": len(content),
            }
        except (PermissionError, ValueError, OSError) as e:
            return {"error": str(e), "success": False}

    def copy_file(self, source: str, destination: str) -> dict[str, Any]:
        """
        Copy a file or directory.

        Confirmation level: NONE
        """
        try:
            src = self._validate_path(source)
            dst = self._validate_path(destination)

            if not src.exists():
                return {"error": f"Source '{source}' does not exist", "success": False}

            if src.is_dir():
                shutil.copytree(str(src), str(dst))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))

            logger.info("Copied: %s → %s", src, dst)
            return {"success": True, "from": str(src), "to": str(dst)}

        except (PermissionError, ValueError, OSError) as e:
            return {"error": str(e), "success": False}

    # ─── Destructive Operations (Confirmation: single/double) ──

    def move_file(self, source: str, destination: str) -> dict[str, Any]:
        """
        Move a file or directory.

        Confirmation level: SINGLE
        """
        try:
            src = self._validate_path(source)
            dst = self._validate_path(destination)

            if not src.exists():
                return {"error": f"Source '{source}' does not exist", "success": False}

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

            logger.info("Moved: %s → %s", src, dst)
            return {"success": True, "from": str(src), "to": str(dst)}

        except (PermissionError, ValueError, OSError) as e:
            return {"error": str(e), "success": False}

    def delete_file(self, path: str) -> dict[str, Any]:
        """
        Delete a file or directory (moves to trash on macOS, permanent on Linux).

        Confirmation level: DOUBLE
        """
        try:
            target = self._validate_path(path)

            if not target.exists():
                return {"error": f"'{path}' does not exist", "success": False}

            # Try to use trash (macOS)
            moved_to_trash = False
            try:
                import subprocess
                if os.uname().sysname == "Darwin":
                    # macOS: move to Trash via osascript
                    subprocess.run(
                        ["osascript", "-e",
                         f'tell application "Finder" to delete POSIX file "{target}"'],
                        check=True,
                        capture_output=True,
                    )
                    moved_to_trash = True
            except Exception:
                pass

            if not moved_to_trash:
                if target.is_dir():
                    shutil.rmtree(str(target))
                else:
                    target.unlink()

            logger.info("Deleted: %s (trash=%s)", target, moved_to_trash)
            return {
                "success": True,
                "path": str(target),
                "moved_to_trash": moved_to_trash,
            }

        except (PermissionError, ValueError, OSError) as e:
            return {"error": str(e), "success": False}
