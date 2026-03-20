"""
Tests for VoiceClone system control modules.

Tests cover file_manager security boundaries, path validation,
read/list operations, and app launcher safety checks.

Run: python3 tests/test_system.py
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.system.file_manager import FileManager
from src.system.app_launcher import AppLauncher

passed = 0
failed = 0


def assert_test(name: str, condition: bool) -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}")


# ─── FileManager Tests ───────────────────────────────────

print("\n📁 FileManager — Security:")

fm = FileManager()

# Blocked paths
result = fm.list_directory("/System")
assert_test("Block /System access", not result["success"])

result = fm.list_directory("/usr")
assert_test("Block /usr access", not result["success"])

result = fm.read_file("/etc/passwd")
assert_test("Block /etc/passwd read", not result["success"])

# Path traversal
result = fm.list_directory("~/../../etc")
assert_test("Block path traversal (../..)", not result["success"])

# ─── FileManager — Read Operations ───────────────────────

print("\n📁 FileManager — Read Operations:")

# List home directory
result = fm.list_directory("~")
assert_test("List home directory", result["success"])
assert_test("Home has items", result["count"] > 0)

# File info
result = fm.get_file_info("~")
assert_test("Get file info for ~", result["success"])
assert_test("Home is directory", result["type"] == "directory")

# ─── FileManager — Write Operations ─────────────────────

print("\n📁 FileManager — Write Operations:")

# Create temp dir for testing
test_dir = tempfile.mkdtemp(prefix="voiceclone_test_")

try:
    # Create folder
    test_folder = os.path.join(test_dir, "test_folder", "nested")
    result = fm.create_folder(test_folder)
    assert_test("Create nested folder", result["success"])
    assert_test("Folder exists", os.path.isdir(test_folder))

    # Write file
    test_file = os.path.join(test_dir, "test.txt")
    result = fm.write_file(test_file, "Hello VoiceClone!")
    assert_test("Write file", result["success"])
    assert_test("File exists", os.path.isfile(test_file))

    # Read file
    result = fm.read_file(test_file)
    assert_test("Read file", result["success"])
    assert_test("Content matches", result["content"] == "Hello VoiceClone!")
    assert_test("Not truncated", not result["truncated"])

    # Read with truncation
    result = fm.read_file(test_file, max_chars=5)
    assert_test("Read truncated", result["truncated"])
    assert_test("Truncated content", result["content"] == "Hello")

    # Copy file
    copy_dest = os.path.join(test_dir, "copy.txt")
    result = fm.copy_file(test_file, copy_dest)
    assert_test("Copy file", result["success"])
    assert_test("Copy exists", os.path.isfile(copy_dest))

    # Search files
    result = fm.search_files("test.txt", test_dir)
    assert_test("Search files", result["success"])
    assert_test("Found test.txt", result["count"] >= 1)

    # Move file
    move_dest = os.path.join(test_dir, "moved.txt")
    result = fm.move_file(copy_dest, move_dest)
    assert_test("Move file", result["success"])
    assert_test("Moved file exists", os.path.isfile(move_dest))
    assert_test("Original gone", not os.path.isfile(copy_dest))

    # List directory
    result = fm.list_directory(test_dir)
    assert_test("List test dir", result["success"])
    assert_test("Has items", result["count"] >= 2)

    # Read nonexistent file
    result = fm.read_file(os.path.join(test_dir, "nonexistent.txt"))
    assert_test("Read nonexistent fails", not result["success"])

finally:
    shutil.rmtree(test_dir, ignore_errors=True)

# ─── AppLauncher Tests ───────────────────────────────────

print("\n🚀 AppLauncher — Safety:")

launcher = AppLauncher()

# Safe apps
assert_test("Safari is safe", launcher.is_safe_app("Safari"))
assert_test("Calculator is safe", launcher.is_safe_app("Calculator"))
assert_test("Chrome is safe", launcher.is_safe_app("Chrome"))

# Blocked apps
result = launcher.open_app("sudo")
assert_test("Block sudo", not result["success"])

result = launcher.open_app("rm")
assert_test("Block rm", not result["success"])

result = launcher.open_app("mkfs")
assert_test("Block mkfs", not result["success"])

# List running apps (just verify it doesn't crash)
result = launcher.list_running_apps()
assert_test("List running apps doesn't crash", "success" in result)

# ─── Summary ─────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 50)

if failed:
    sys.exit(1)
