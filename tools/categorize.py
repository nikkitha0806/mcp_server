"""File categorization tools — group files by type, size, or date."""

from datetime import datetime
from pathlib import Path

from tools.config import DEFAULT_CATEGORY, EXTENSION_TO_CATEGORY


def categorize_by_type(directory: str) -> dict:
    """
    Group files in a directory by their media/content type category.

    Args:
        directory: Directory to scan.

    Returns:
        dict with 'total' and 'categories', each containing file entries.
    """
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    categories: dict[str, list[dict]] = {}

    for entry in sorted(root.rglob("*")):
        if not entry.is_file():
            continue

        category = EXTENSION_TO_CATEGORY.get(entry.suffix.lower(), DEFAULT_CATEGORY)
        stat = entry.stat()
        categories.setdefault(category, []).append({
            "name": entry.name,
            "path": str(entry),
            "size_bytes": stat.st_size,
            "extension": entry.suffix.lower(),
        })

    return {
        "directory": str(root),
        "total": sum(len(v) for v in categories.values()),
        "categories": {
            cat: {"count": len(files), "files": files}
            for cat, files in sorted(categories.items())
        },
    }


def categorize_by_size(directory: str) -> dict:
    """
    Group files into size buckets: Tiny, Small, Medium, Large, Huge.

    Buckets:
        Tiny   < 10 KB
        Small  10 KB – 1 MB
        Medium 1 MB – 100 MB
        Large  100 MB – 1 GB
        Huge   > 1 GB

    Args:
        directory: Directory to scan.

    Returns:
        dict with 'total' and 'buckets', each containing file entries.
    """
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    BUCKETS = [
        ("Tiny",   0,              10 * 1024),
        ("Small",  10 * 1024,      1 * 1024 ** 2),
        ("Medium", 1 * 1024 ** 2,  100 * 1024 ** 2),
        ("Large",  100 * 1024 ** 2, 1 * 1024 ** 3),
        ("Huge",   1 * 1024 ** 3,  float("inf")),
    ]

    buckets: dict[str, list[dict]] = {name: [] for name, _, _ in BUCKETS}

    for entry in sorted(root.rglob("*")):
        if not entry.is_file():
            continue

        size = entry.stat().st_size
        bucket_name = next(
            name for name, low, high in BUCKETS if low <= size < high
        )
        buckets[bucket_name].append({
            "name": entry.name,
            "path": str(entry),
            "size_bytes": size,
        })

    return {
        "directory": str(root),
        "total": sum(len(v) for v in buckets.values()),
        "buckets": {
            name: {"count": len(files), "files": files}
            for name, files in buckets.items()
        },
    }


def categorize_by_date(directory: str) -> dict:
    """
    Group files by their last-modified month (YYYY-MM).

    Args:
        directory: Directory to scan.

    Returns:
        dict with 'total' and 'months', sorted chronologically.
    """
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    months: dict[str, list[dict]] = {}

    for entry in sorted(root.rglob("*")):
        if not entry.is_file():
            continue

        stat = entry.stat()
        month_key = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m")
        months.setdefault(month_key, []).append({
            "name": entry.name,
            "path": str(entry),
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })

    return {
        "directory": str(root),
        "total": sum(len(v) for v in months.values()),
        "months": {
            month: {"count": len(files), "files": files}
            for month, files in sorted(months.items())
        },
    }
