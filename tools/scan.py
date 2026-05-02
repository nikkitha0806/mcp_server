"""File scanning tools — list, inspect, search, and find duplicates."""

import hashlib
import os
from datetime import datetime
from pathlib import Path


def scan_directory(path: str, recursive: bool = False) -> dict:
    """
    List all files in a directory with basic metadata.

    Args:
        path: Directory path to scan.
        recursive: If True, scan subdirectories as well.

    Returns:
        dict with 'path', 'total_files', 'total_size_bytes', and 'files' list.
    """
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    glob_pattern = "**/*" if recursive else "*"
    files = []
    total_size = 0

    for entry in sorted(root.glob(glob_pattern)):
        if entry.is_file():
            stat = entry.stat()
            size = stat.st_size
            total_size += size
            files.append({
                "name": entry.name,
                "path": str(entry),
                "size_bytes": size,
                "extension": entry.suffix.lower(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

    return {
        "path": str(root),
        "recursive": recursive,
        "total_files": len(files),
        "total_size_bytes": total_size,
        "files": files,
    }


def get_file_info(file_path: str) -> dict:
    """
    Return detailed metadata for a single file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        dict with name, path, size, timestamps, extension, and mime hint.
    """
    fp = Path(file_path)
    if not fp.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not fp.is_file():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    stat = fp.stat()
    return {
        "name": fp.name,
        "path": str(fp.resolve()),
        "extension": fp.suffix.lower(),
        "size_bytes": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_hidden": fp.name.startswith("."),
    }


def find_files(directory: str, pattern: str) -> dict:
    """
    Find files matching a glob pattern inside a directory.

    Args:
        directory: Root directory to search in.
        pattern: Glob pattern, e.g. '*.pdf' or '**/*.log'.

    Returns:
        dict with 'pattern', 'total_found', and 'matches' list.
    """
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    matches = [
        {"name": p.name, "path": str(p), "size_bytes": p.stat().st_size}
        for p in sorted(root.glob(pattern))
        if p.is_file()
    ]

    return {
        "directory": str(root),
        "pattern": pattern,
        "total_found": len(matches),
        "matches": matches,
    }


def find_duplicates(directory: str) -> dict:
    """
    Find duplicate files in a directory by comparing SHA-256 hashes.

    Args:
        directory: Directory to scan for duplicates.

    Returns:
        dict with 'total_duplicates' and 'groups' (files sharing the same hash).
    """
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    hash_map: dict[str, list[str]] = {}

    for entry in root.rglob("*"):
        if entry.is_file():
            file_hash = _sha256(entry)
            hash_map.setdefault(file_hash, []).append(str(entry))

    groups = [
        {"hash": h, "count": len(paths), "files": paths}
        for h, paths in hash_map.items()
        if len(paths) > 1
    ]

    return {
        "directory": str(root),
        "total_duplicates": sum(g["count"] - 1 for g in groups),
        "groups": groups,
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
