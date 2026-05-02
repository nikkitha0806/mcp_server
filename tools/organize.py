"""File organizing tools — sort files into subdirectories by extension or date."""

import shutil
from datetime import datetime
from pathlib import Path

from tools.config import DEFAULT_CATEGORY, EXTENSION_TO_CATEGORY


def organize_by_extension(source_dir: str, dest_dir: str | None = None, dry_run: bool = False) -> dict:
    """
    Move files into subdirectories named after their category (Images, Documents, etc.).

    Files with unrecognized extensions go into an 'Others' folder.

    Args:
        source_dir: Directory containing the files to organize.
        dest_dir: Where to create category subdirs. Defaults to source_dir.
        dry_run: If True, simulate the operation without moving files.

    Returns:
        dict with 'total', 'moved', 'dry_run', and per-category 'summary'.
    """
    root = Path(source_dir)
    if not root.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    target_root = Path(dest_dir) if dest_dir else root
    summary: dict[str, list[str]] = {}
    moved = 0

    for entry in root.iterdir():
        if not entry.is_file():
            continue

        category = EXTENSION_TO_CATEGORY.get(entry.suffix.lower(), DEFAULT_CATEGORY)
        category_dir = target_root / category

        summary.setdefault(category, []).append(entry.name)

        if not dry_run:
            category_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(entry), str(category_dir / entry.name))
        moved += 1

    return {
        "source_dir": str(root),
        "dest_dir": str(target_root),
        "dry_run": dry_run,
        "total": moved,
        "moved": 0 if dry_run else moved,
        "summary": {cat: {"count": len(files), "files": files} for cat, files in summary.items()},
    }


def organize_by_date(source_dir: str, dest_dir: str | None = None, dry_run: bool = False) -> dict:
    """
    Move files into subdirectories structured as YYYY/MM based on last-modified date.

    Args:
        source_dir: Directory containing the files to organize.
        dest_dir: Where to create date subdirs. Defaults to source_dir.
        dry_run: If True, simulate the operation without moving files.

    Returns:
        dict with 'total', 'moved', 'dry_run', and per-month 'summary'.
    """
    root = Path(source_dir)
    if not root.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    target_root = Path(dest_dir) if dest_dir else root
    summary: dict[str, list[str]] = {}
    moved = 0

    for entry in root.iterdir():
        if not entry.is_file():
            continue

        mtime = datetime.fromtimestamp(entry.stat().st_mtime)
        folder_key = mtime.strftime("%Y/%m")
        date_dir = target_root / mtime.strftime("%Y") / mtime.strftime("%m")

        summary.setdefault(folder_key, []).append(entry.name)

        if not dry_run:
            date_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(entry), str(date_dir / entry.name))
        moved += 1

    return {
        "source_dir": str(root),
        "dest_dir": str(target_root),
        "dry_run": dry_run,
        "total": moved,
        "moved": 0 if dry_run else moved,
        "summary": {month: {"count": len(files), "files": files} for month, files in summary.items()},
    }
