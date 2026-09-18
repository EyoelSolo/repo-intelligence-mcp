from pathlib import Path
class SecurityError(Exception):
    pass

def safe_path(repository_root: Path, requested_path: str) -> Path:


    root = repository_root.resolve()

    requested = Path(requested_path)

    if requested.is_absolute():
        candidate = requested.resolve()
    else:
        candidate = (root / requested).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        raise SecurityError(
            f"Access denied: path is outside repository: {requested_path}"
        )

    return candidate