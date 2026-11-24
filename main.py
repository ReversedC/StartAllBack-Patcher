"""
StartAllBack maintenance CLI.

This version removes the Tkinter GUI and provides safe backup/restore
operations. It does not modify licensing data or patch executable code.
Run with: py SAB_cli.py
"""

import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

DLL_NAME = "StartAllBackX64.dll"


def log(message):
    print(message, flush=True)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def relaunch_as_admin():
    """Relaunch this script through UAC, preserving its command-line arguments."""
    executable = sys.executable
    parameters = subprocess.list2cmdline([str(Path(__file__).resolve()), *sys.argv[1:]])

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, parameters, str(Path(__file__).resolve().parent), 1
        )
    except Exception as exc:
        log(f"[ERROR] Could not request administrator privileges: {exc}")
        return False

    if result <= 32:
        log(f"[ERROR] Windows could not start the elevated process (code {result}).")
        return False
    return True


def find_dll():
    candidates = []

    for env_name in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env_name)
        if base:
            candidates.append(Path(base) / "StartAllBack" / DLL_NAME)

    # Also check the folder containing this script.
    candidates.append(Path(__file__).resolve().parent / DLL_NAME)

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    return None


def backup_dll(dll_path):
    backup_path = Path(str(dll_path) + ".bak")

    if backup_path.exists():
        log(f"[INFO] Backup already exists: {backup_path}")
        log("[INFO] It was left untouched to avoid overwriting your original backup.")
        return False

    try:
        shutil.copy2(dll_path, backup_path)
        log(f"[OK] Backup created: {backup_path}")
        return True
    except (PermissionError, OSError) as exc:
        log(f"[ERROR] Could not create backup: {exc}")
        return False


def restore_dll(dll_path):
    backup_path = Path(str(dll_path) + ".bak")

    if not backup_path.is_file():
        log(f"[ERROR] Backup not found: {backup_path}")
        return False

    try:
        shutil.copy2(backup_path, dll_path)
        log(f"[OK] Original DLL restored from: {backup_path}")
        return True
    except (PermissionError, OSError) as exc:
        log(f"[ERROR] Could not restore DLL: {exc}")
        return False


def main():
    print("StartAllBack Maintenance CLI")
    print("=" * 32)

    if not is_admin():
        log("[INFO] Administrator privileges are required for DLL maintenance.")
        log("[INFO] Requesting UAC elevation...")
        if relaunch_as_admin():
            return 0
        log("[ERROR] Please open Command Prompt as Administrator and run this script again.")
        return 1

    log("[OK] Running with administrator privileges.")

    dll_path = find_dll()
    if dll_path is None:
        log(f"[ERROR] {DLL_NAME} was not found in the usual installation folders.")
        log("Check that StartAllBack is installed, or place this script in its installation folder.")
        input("\nPress Enter to exit...")
        return 1

    log(f"[OK] DLL found: {dll_path}")

    while True:
        print("\nChoose an operation:")
        print("  1. Create a backup of the current DLL")
        print("  2. Restore the DLL from the .bak backup")
        print("  3. Exit")

        choice = input("\nSelection [1-3]: ").strip()

        if choice == "1":
            backup_dll(dll_path)
        elif choice == "2":
            confirm = input("Restore the DLL from its backup? [y/N]: ").strip().lower()
            if confirm == "y":
                restore_dll(dll_path)
            else:
                log("[INFO] Restore cancelled.")
        elif choice == "3":
            log("Exiting.")
            return 0
        else:
            log("[WARN] Invalid selection. Enter 1, 2, or 3.")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)
