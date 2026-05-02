"""MCP server exposing file management tools: scan, move, organize, categorize."""

import sys
import os

# Allow imports from the project root when running directly
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP

from tools.categorize import categorize_by_date, categorize_by_size, categorize_by_type
from tools.move import move_file, move_files_bulk, move_files_matching
from tools.organize import organize_by_date, organize_by_extension
from tools.scan import find_duplicates, find_files, get_file_info, scan_directory

mcp = FastMCP(
    name="file-manager",
    instructions=(
        "A file management assistant. Use these tools to scan directories, "
        "categorize files by type/size/date, organize them into folders, "
        "move files, and find duplicates."
    ),
)

# ---------------------------------------------------------------------------
# SCAN tools
# ---------------------------------------------------------------------------

@mcp.tool()
def scan_dir(path: str, recursive: bool = False) -> dict:
    """
    List all files in a directory with their name, size, extension, and
    last-modified timestamp.

    Args:
        path: Absolute path to the directory to scan.
        recursive: Set to true to include files in subdirectories.
    """
    return scan_directory(path, recursive=recursive)


@mcp.tool()
def file_info(file_path: str) -> dict:
    """
    Get detailed metadata for a single file: name, path, size, extension,
    created/modified timestamps, and whether it is hidden.

    Args:
        file_path: Absolute path to the file.
    """
    return get_file_info(file_path)


@mcp.tool()
def search_files(directory: str, pattern: str) -> dict:
    """
    Find files matching a glob pattern inside a directory.
    Examples of pattern: '*.pdf', '**/*.log', 'report_*.csv'

    Args:
        directory: Root directory to search in.
        pattern: Glob pattern to match file names.
    """
    return find_files(directory, pattern)


@mcp.tool()
def detect_duplicates(directory: str) -> dict:
    """
    Find duplicate files in a directory by comparing SHA-256 content hashes.
    Returns groups of files that are identical.

    Args:
        directory: Directory to scan for duplicates.
    """
    return find_duplicates(directory)


# ---------------------------------------------------------------------------
# CATEGORIZE tools
# ---------------------------------------------------------------------------

@mcp.tool()
def categorize_by_file_type(directory: str) -> dict:
    """
    Group all files in a directory into categories based on their type:
    Documents, Images, Videos, Audio, Code, Data, Archives, etc.

    Args:
        directory: Absolute path to the directory to categorize.
    """
    return categorize_by_type(directory)


@mcp.tool()
def categorize_by_file_size(directory: str) -> dict:
    """
    Group files into size buckets:
      Tiny (<10 KB), Small (10 KB–1 MB), Medium (1–100 MB),
      Large (100 MB–1 GB), Huge (>1 GB).

    Args:
        directory: Absolute path to the directory to categorize.
    """
    return categorize_by_size(directory)


@mcp.tool()
def categorize_by_modified_date(directory: str) -> dict:
    """
    Group files by the month they were last modified (YYYY-MM buckets).
    Useful for finding old or recently changed files.

    Args:
        directory: Absolute path to the directory to categorize.
    """
    return categorize_by_date(directory)


# ---------------------------------------------------------------------------
# ORGANIZE tools
# ---------------------------------------------------------------------------

@mcp.tool()
def organize_files_by_type(
    source_dir: str,
    dest_dir: str | None = None,
    dry_run: bool = True,
) -> dict:
    """
    Move files from source_dir into category subfolders (Images/, Documents/,
    Code/, etc.) based on their extension.

    Set dry_run=false to actually move files (default is a safe preview).

    Args:
        source_dir: Directory whose files will be organized.
        dest_dir: Where to create category subfolders. Defaults to source_dir.
        dry_run: If true, preview the changes without moving anything.
    """
    return organize_by_extension(source_dir, dest_dir=dest_dir, dry_run=dry_run)


@mcp.tool()
def organize_files_by_date(
    source_dir: str,
    dest_dir: str | None = None,
    dry_run: bool = True,
) -> dict:
    """
    Move files from source_dir into date subfolders structured as YYYY/MM/
    based on each file's last-modified date.

    Set dry_run=false to actually move files (default is a safe preview).

    Args:
        source_dir: Directory whose files will be organized.
        dest_dir: Where to create date subfolders. Defaults to source_dir.
        dry_run: If true, preview the changes without moving anything.
    """
    return organize_by_date(source_dir, dest_dir=dest_dir, dry_run=dry_run)


# ---------------------------------------------------------------------------
# MOVE tools
# ---------------------------------------------------------------------------

@mcp.tool()
def move_single_file(src: str, dest: str, overwrite: bool = False) -> dict:
    """
    Move a single file to a new location or directory.

    Args:
        src: Absolute path to the source file.
        dest: Destination file path or directory path.
        overwrite: If true, replace an existing file at the destination.
    """
    return move_file(src, dest, overwrite=overwrite)


@mcp.tool()
def move_multiple_files(file_paths: list[str], dest_dir: str, overwrite: bool = False) -> dict:
    """
    Move a list of files into a destination directory in one operation.

    Args:
        file_paths: List of absolute paths to the files to move.
        dest_dir: Destination directory (created if it does not exist).
        overwrite: If true, replace existing files at the destination.
    """
    return move_files_bulk(file_paths, dest_dir, overwrite=overwrite)


@mcp.tool()
def move_files_by_pattern(
    source_dir: str,
    pattern: str,
    dest_dir: str,
    overwrite: bool = False,
) -> dict:
    """
    Move all files matching a glob pattern from source_dir to dest_dir.
    Example patterns: '*.pdf', '**/*.jpg', 'invoice_*.csv'

    Args:
        source_dir: Directory to search for matching files.
        pattern: Glob pattern to match file names.
        dest_dir: Destination directory (created if it does not exist).
        overwrite: If true, replace existing files at the destination.
    """
    return move_files_matching(source_dir, pattern, dest_dir, overwrite=overwrite)


if __name__ == "__main__":
    mcp.run(transport="stdio")
