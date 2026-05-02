"""Central configuration for file extension categories used across all tools."""

# ---------------------------------------------------------------------------
# CATEGORIES
# Each key is the folder/category name. Each value is the list of extensions
# that belong to it. Extensions must be lowercase with a leading dot.
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, list[str]] = {

    "Documents": [
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".rst",
        ".tex", ".wpd", ".wps", ".pages", ".numbers", ".key",
        ".xls", ".xlsx", ".ods", ".csv", ".tsv",
        ".ppt", ".pptx", ".odp",
    ],

    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
        ".webp", ".svg", ".ico", ".heic", ".heif", ".raw", ".cr2",
        ".nef", ".arw", ".dng", ".psd", ".ai", ".eps", ".xcf",
    ],

    "Videos": [
        ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm",
        ".m4v", ".mpg", ".mpeg", ".3gp", ".3g2", ".ogv", ".ts",
        ".vob", ".rm", ".rmvb", ".divx",
    ],

    "Audio": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma",
        ".aiff", ".aif", ".opus", ".mid", ".midi", ".amr", ".ape",
        ".ra", ".au",
    ],

    "Archives": [
        ".zip", ".tar", ".gz", ".bz2", ".xz", ".rar", ".7z",
        ".tgz", ".tbz2", ".lz", ".lzma", ".zst", ".cab", ".iso",
        ".dmg", ".pkg", ".deb", ".rpm",
    ],

    "Code": [
        # Python
        ".py", ".pyw", ".pyx", ".pxd",
        # JavaScript / TypeScript
        ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
        # Web
        ".html", ".htm", ".css", ".scss", ".sass", ".less",
        # Backend languages
        ".java", ".kt", ".kts", ".scala", ".groovy",
        ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp",
        ".cs", ".fs", ".vb",
        ".go", ".rs", ".swift", ".m", ".mm",
        ".rb", ".php", ".pl", ".pm", ".lua",
        ".r", ".rmd", ".jl",
        # Shell
        ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
        # Config / markup used in code
        ".json", ".jsonl", ".yaml", ".yml", ".toml", ".xml",
        ".ini", ".cfg", ".conf", ".env",
        # Query / notebooks
        ".sql", ".graphql", ".ipynb",
        # Misc
        ".dart", ".ex", ".exs", ".clj", ".cljs", ".hs", ".elm",
    ],

    "Data": [
        ".csv", ".tsv", ".parquet", ".avro", ".orc",
        ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb",
        ".jsonl", ".ndjson", ".arrow", ".feather", ".hdf5", ".h5",
        ".pkl", ".pickle", ".npy", ".npz", ".mat",
        ".xml", ".rdf", ".geojson", ".shp",
    ],

    "Fonts": [
        ".ttf", ".otf", ".woff", ".woff2", ".eot", ".fon", ".fnt",
    ],

    "Ebooks": [
        ".epub", ".mobi", ".azw", ".azw3", ".djvu", ".fb2", ".lit",
    ],

    "Executables": [
        ".exe", ".msi", ".app", ".apk", ".ipa",
        ".bin", ".run", ".out", ".appimage",
    ],

    "System": [
        ".dll", ".so", ".dylib", ".sys", ".drv",
        ".log", ".bak", ".tmp", ".cache", ".lock",
        ".pid", ".sock",
    ],

    "3D_Models": [
        ".obj", ".fbx", ".stl", ".dae", ".3ds", ".blend",
        ".gltf", ".glb", ".ply", ".step", ".stp", ".iges",
    ],

    "Subtitles": [
        ".srt", ".vtt", ".ass", ".ssa", ".sub", ".sbv",
    ],

    "Torrents": [
        ".torrent", ".magnet",
    ],

    "Certificates": [
        ".pem", ".crt", ".cer", ".key", ".p12", ".pfx",
        ".csr", ".der", ".jks",
    ],

}

# ---------------------------------------------------------------------------
# Derived flat lookup: extension -> category name
# Built automatically from CATEGORIES so there is a single source of truth.
# If an extension appears in multiple categories the last one wins — avoid
# duplicates in CATEGORIES above.
# ---------------------------------------------------------------------------

EXTENSION_TO_CATEGORY: dict[str, str] = {
    ext: category
    for category, extensions in CATEGORIES.items()
    for ext in extensions
}

# ---------------------------------------------------------------------------
# Default folder name for files whose extension is not in any category.
# ---------------------------------------------------------------------------

DEFAULT_CATEGORY = "Others"
