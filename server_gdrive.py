"""MCP server exposing Google Drive file operations."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP

from tools.gdrive import (
    create_folder,
    delete_file,
    download_file,
    get_file_info,
    list_files,
    list_folders,
    move_file,
    search_files,
    upload_file,
)

mcp = FastMCP(
    name="google-drive",
    instructions=(
        "Access and manage Google Drive files. "
        "Use gdrive_list to browse folders, gdrive_search to find files, "
        "gdrive_download to save files locally, gdrive_upload to push local files, "
        "and gdrive_organize to move files between folders."
    ),
)

# ---------------------------------------------------------------------------
# Browse
# ---------------------------------------------------------------------------

@mcp.tool()
def gdrive_list(folder_id: str = "root", max_results: int = 50) -> dict:
    """
    List files and folders inside a Google Drive folder.

    Args:
        folder_id: Drive folder ID. Use 'root' for My Drive top level.
                   Get an ID from a previous gdrive_list or gdrive_search call.
        max_results: Maximum number of items to return (default 50).
    """
    return list_files(folder_id=folder_id, max_results=max_results)


@mcp.tool()
def gdrive_list_folders(parent_id: str = "root") -> dict:
    """
    List only the subfolders inside a Google Drive folder.

    Args:
        parent_id: Parent folder ID. Use 'root' for My Drive top level.
    """
    return list_folders(parent_id=parent_id)


@mcp.tool()
def gdrive_search(query: str, max_results: int = 20) -> dict:
    """
    Search for files across all of Google Drive by name or content.

    Simple usage  — pass a plain keyword:  'budget report'
    Advanced usage — pass a Drive query:   'mimeType = "application/pdf"'
    Other examples:
      'name contains "invoice"'
      'modifiedTime > "2024-01-01"'

    Args:
        query: Search keyword or Drive query expression.
        max_results: Maximum number of results to return.
    """
    return search_files(query=query, max_results=max_results)


@mcp.tool()
def gdrive_file_info(file_id: str) -> dict:
    """
    Get detailed metadata for a specific file or folder using its Drive ID.

    Args:
        file_id: The Google Drive file or folder ID.
    """
    return get_file_info(file_id=file_id)


# ---------------------------------------------------------------------------
# Download / Upload
# ---------------------------------------------------------------------------

@mcp.tool()
def gdrive_download(file_id: str, dest_path: str) -> dict:
    """
    Download a file from Google Drive to a local path.

    Google Docs/Sheets/Slides are automatically exported to .docx/.xlsx/.pptx.

    Args:
        file_id: Google Drive file ID.
        dest_path: Local file path or local directory to save the file into.
    """
    return download_file(file_id=file_id, dest_path=dest_path)


@mcp.tool()
def gdrive_upload(local_path: str, folder_id: str = "root") -> dict:
    """
    Upload a local file to Google Drive.

    Args:
        local_path: Absolute path to the local file to upload.
        folder_id: Drive folder ID to upload into (default: My Drive root).
    """
    return upload_file(local_path=local_path, folder_id=folder_id)


# ---------------------------------------------------------------------------
# Organise
# ---------------------------------------------------------------------------

@mcp.tool()
def gdrive_create_folder(name: str, parent_id: str = "root") -> dict:
    """
    Create a new folder in Google Drive.

    Args:
        name: Name for the new folder.
        parent_id: Parent folder ID (default: My Drive root).
    """
    return create_folder(name=name, parent_id=parent_id)


@mcp.tool()
def gdrive_move(file_id: str, new_folder_id: str) -> dict:
    """
    Move a file or folder to a different Google Drive folder.

    Args:
        file_id: Drive ID of the file or folder to move.
        new_folder_id: Drive ID of the destination folder.
    """
    return move_file(file_id=file_id, new_folder_id=new_folder_id)


@mcp.tool()
def gdrive_delete(file_id: str, permanent: bool = False) -> dict:
    """
    Delete a file from Google Drive.

    By default the file is moved to Trash (recoverable).
    Set permanent=true to delete it forever.

    Args:
        file_id: Google Drive file ID to delete.
        permanent: If true, permanently delete instead of trashing.
    """
    return delete_file(file_id=file_id, permanent=permanent)


if __name__ == "__main__":
    mcp.run(transport="stdio")
