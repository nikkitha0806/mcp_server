"""Google Drive API wrapper — auth + core file operations."""

import io
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Read-only scope for listing/downloading; add Drive scope for write operations.
SCOPES = ["https://www.googleapis.com/auth/drive"]

_CREDENTIALS_FILE = Path(__file__).parent.parent / "credentials" / "credentials.json"
_TOKEN_FILE = Path(__file__).parent.parent / "credentials" / "token.json"

# Maps Google Drive MIME types to readable labels
MIME_LABELS = {
    "application/vnd.google-apps.folder": "Folder",
    "application/vnd.google-apps.document": "Google Doc",
    "application/vnd.google-apps.spreadsheet": "Google Sheet",
    "application/vnd.google-apps.presentation": "Google Slides",
    "application/vnd.google-apps.form": "Google Form",
    "application/pdf": "PDF",
}

# Export formats for Google Workspace files
EXPORT_FORMATS = {
    "application/vnd.google-apps.document": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
    ),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
}


def _get_service():
    """Authenticate and return a Drive API service client."""
    if not _CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {_CREDENTIALS_FILE}.\n"
            "Download it from Google Cloud Console → APIs & Services → Credentials."
        )

    creds = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        _TOKEN_FILE.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds)


def _file_dict(f: dict) -> dict:
    """Normalise a Drive API file resource into a clean dict."""
    mime = f.get("mimeType", "")
    return {
        "id": f.get("id"),
        "name": f.get("name"),
        "type": MIME_LABELS.get(mime, mime.split("/")[-1]),
        "mime_type": mime,
        "size_bytes": int(f.get("size", 0)) if "size" in f else None,
        "modified": f.get("modifiedTime"),
        "created": f.get("createdTime"),
        "parents": f.get("parents", []),
        "web_link": f.get("webViewLink"),
    }


# ---------------------------------------------------------------------------
# Public functions (called by MCP tools)
# ---------------------------------------------------------------------------

def list_files(folder_id: str = "root", max_results: int = 50) -> dict:
    """
    List files and folders inside a Drive folder.

    Args:
        folder_id: Drive folder ID (default 'root' = My Drive top level).
        max_results: Maximum number of items to return.

    Returns:
        dict with 'folder_id', 'total', and 'files'.
    """
    service = _get_service()
    query = f"'{folder_id}' in parents and trashed = false"
    fields = "files(id,name,mimeType,size,modifiedTime,createdTime,parents,webViewLink)"

    response = service.files().list(
        q=query,
        pageSize=max_results,
        fields=f"nextPageToken, {fields}",
        orderBy="folder,name",
    ).execute()

    files = [_file_dict(f) for f in response.get("files", [])]
    return {"folder_id": folder_id, "total": len(files), "files": files}


def search_files(query: str, max_results: int = 20) -> dict:
    """
    Search files across all of Drive by name or full-text query.

    Args:
        query: Search term. Examples: 'budget', 'name contains "report"',
               'mimeType = "application/pdf"'
        max_results: Maximum number of results.

    Returns:
        dict with 'query', 'total', and 'files'.
    """
    service = _get_service()
    # If the caller passes a plain string, wrap it as a name search
    if not any(op in query for op in ["contains", "=", "!=", "<", ">"]):
        drive_query = f"name contains '{query}' and trashed = false"
    else:
        drive_query = f"({query}) and trashed = false"

    fields = "files(id,name,mimeType,size,modifiedTime,createdTime,parents,webViewLink)"
    response = service.files().list(
        q=drive_query,
        pageSize=max_results,
        fields=f"nextPageToken, {fields}",
    ).execute()

    files = [_file_dict(f) for f in response.get("files", [])]
    return {"query": query, "total": len(files), "files": files}


def get_file_info(file_id: str) -> dict:
    """
    Get full metadata for a specific file or folder by its Drive ID.

    Args:
        file_id: Google Drive file/folder ID.

    Returns:
        dict with file metadata.
    """
    service = _get_service()
    fields = "id,name,mimeType,size,modifiedTime,createdTime,parents,webViewLink,description,starred,shared"
    f = service.files().get(fileId=file_id, fields=fields).execute()
    result = _file_dict(f)
    result["description"] = f.get("description")
    result["starred"] = f.get("starred", False)
    result["shared"] = f.get("shared", False)
    return result


def download_file(file_id: str, dest_path: str) -> dict:
    """
    Download a Drive file to a local path.
    Google Workspace files (Docs/Sheets/Slides) are exported to Office format.

    Args:
        file_id: Google Drive file ID.
        dest_path: Local file path or directory to save the file.

    Returns:
        dict with 'file_id', 'saved_to', and 'size_bytes'.
    """
    service = _get_service()
    meta = service.files().get(fileId=file_id, fields="name,mimeType").execute()
    name = meta["name"]
    mime = meta["mimeType"]

    dest = Path(dest_path)
    if dest.is_dir():
        dest = dest / name

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Google Workspace files must be exported
    if mime in EXPORT_FORMATS:
        export_mime, ext = EXPORT_FORMATS[mime]
        if not dest.suffix:
            dest = dest.with_suffix(ext)
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        request = service.files().get_media(fileId=file_id)

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    dest.write_bytes(buffer.getvalue())
    return {"file_id": file_id, "name": name, "saved_to": str(dest), "size_bytes": dest.stat().st_size}


def upload_file(local_path: str, folder_id: str = "root") -> dict:
    """
    Upload a local file to a Drive folder.

    Args:
        local_path: Absolute path to the local file.
        folder_id: Drive folder ID to upload into (default: root).

    Returns:
        dict with the new file's Drive metadata.
    """
    service = _get_service()
    source = Path(local_path)
    if not source.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    import mimetypes
    mime_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"

    file_metadata = {"name": source.name, "parents": [folder_id]}
    media = MediaFileUpload(str(source), mimetype=mime_type, resumable=True)

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name,mimeType,size,modifiedTime,webViewLink,parents",
    ).execute()

    return _file_dict(uploaded)


def create_folder(name: str, parent_id: str = "root") -> dict:
    """
    Create a new folder in Drive.

    Args:
        name: Folder name.
        parent_id: Parent folder ID (default: root).

    Returns:
        dict with the new folder's metadata.
    """
    service = _get_service()
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(
        body=metadata,
        fields="id,name,mimeType,modifiedTime,createdTime,parents,webViewLink",
    ).execute()
    return _file_dict(folder)


def move_file(file_id: str, new_folder_id: str) -> dict:
    """
    Move a file to a different folder.

    Args:
        file_id: Drive file ID to move.
        new_folder_id: Destination folder ID.

    Returns:
        dict with updated file metadata.
    """
    service = _get_service()
    # Retrieve current parents so we can remove them
    f = service.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(f.get("parents", []))

    updated = service.files().update(
        fileId=file_id,
        addParents=new_folder_id,
        removeParents=previous_parents,
        fields="id,name,mimeType,size,modifiedTime,parents,webViewLink",
    ).execute()
    return _file_dict(updated)


def delete_file(file_id: str, permanent: bool = False) -> dict:
    """
    Delete a file (moves to Trash by default).

    Args:
        file_id: Drive file ID to delete.
        permanent: If True, permanently delete instead of trashing.

    Returns:
        dict with 'file_id' and 'status'.
    """
    service = _get_service()
    if permanent:
        service.files().delete(fileId=file_id).execute()
        status = "permanently_deleted"
    else:
        service.files().update(fileId=file_id, body={"trashed": True}).execute()
        status = "moved_to_trash"
    return {"file_id": file_id, "status": status}


def list_folders(parent_id: str = "root") -> dict:
    """
    List only folders inside a Drive folder.

    Args:
        parent_id: Parent folder ID (default: root).

    Returns:
        dict with 'parent_id', 'total', and 'folders'.
    """
    service = _get_service()
    query = (
        f"'{parent_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    response = service.files().list(
        q=query,
        pageSize=100,
        fields="files(id,name,mimeType,modifiedTime,createdTime,parents,webViewLink)",
        orderBy="name",
    ).execute()

    folders = [_file_dict(f) for f in response.get("files", [])]
    return {"parent_id": parent_id, "total": len(folders), "folders": folders}
