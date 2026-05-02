"""File moving tools — move single files, bulk moves, and pattern-based moves."""

import shutil
from pathlib import Path


def move_file(src: str, dest: str, overwrite: bool = False) -> dict:
    """
    Move a single file to a destination path or directory.

    Args:
        src: Source file path.
        dest: Destination file path or directory.
        overwrite: If True, overwrite an existing file at the destination.

    Returns:
        dict with 'src', 'dest', and 'status'.
    """
    source = Path(src)
    destination = Path(dest)

    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    if not source.is_file():
        raise ValueError(f"Source is not a file: {src}")

    if destination.is_dir():
        destination = destination / source.name

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Destination already exists: {destination}. Use overwrite=True to replace."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))

    return {"src": str(source), "dest": str(destination), "status": "moved"}


def move_files_bulk(file_paths: list[str], dest_dir: str, overwrite: bool = False) -> dict:
    """
    Move multiple files into a destination directory.

    Args:
        file_paths: List of source file paths.
        dest_dir: Target directory (created if it doesn't exist).
        overwrite: If True, overwrite existing files at the destination.

    Returns:
        dict with 'total', 'moved', 'skipped', and per-file 'results'.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    results = []
    moved = 0
    skipped = 0

    for fp in file_paths:
        source = Path(fp)
        target = dest / source.name

        if not source.exists():
            results.append({"src": fp, "status": "error", "reason": "source not found"})
            skipped += 1
            continue

        if target.exists() and not overwrite:
            results.append({"src": fp, "status": "skipped", "reason": "destination exists"})
            skipped += 1
            continue

        shutil.move(str(source), str(target))
        results.append({"src": fp, "dest": str(target), "status": "moved"})
        moved += 1

    return {
        "dest_dir": str(dest),
        "total": len(file_paths),
        "moved": moved,
        "skipped": skipped,
        "results": results,
    }


def move_files_matching(source_dir: str, pattern: str, dest_dir: str, overwrite: bool = False) -> dict:
    """
    Move all files matching a glob pattern from source_dir to dest_dir.

    Args:
        source_dir: Directory to search for matching files.
        pattern: Glob pattern, e.g. '*.csv' or '**/*.log'.
        dest_dir: Target directory (created if it doesn't exist).
        overwrite: If True, overwrite existing files at the destination.

    Returns:
        dict with 'pattern', 'total', 'moved', 'skipped', and 'results'.
    """
    root = Path(source_dir)
    if not root.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    matching = [p for p in root.glob(pattern) if p.is_file()]
    file_paths = [str(p) for p in matching]

    result = move_files_bulk(file_paths, dest_dir, overwrite=overwrite)
    result["pattern"] = pattern
    result["source_dir"] = str(root)

    return result
