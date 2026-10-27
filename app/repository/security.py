from pathlib import Path
class SecurityError(Exception):
    pass


SENSITIVE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    ".env.test", "id_rsa", "id_ed25519", "credentials.json",
    "id_dsa", "id_ecdsa", "id_ed25519_sk", "id_ecdsa_sk",
    ".netrc", ".npmrc", ".pypirc", "secrets.json", "token.json",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore"}
SENSITIVE_DIRECTORIES = {".ssh", ".aws", ".secrets"}


def is_sensitive_path(path: Path) -> bool:
    """Identify common credential files and private-key directories."""
    parts = {part.casefold() for part in path.parts}
    name = path.name.casefold()
    return (
        bool(parts & SENSITIVE_DIRECTORIES)
        or name in SENSITIVE_NAMES
        or name.startswith(".env.")
        or path.suffix.casefold() in SENSITIVE_SUFFIXES
    )


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

    if is_sensitive_path(candidate):
        raise SecurityError("Access denied: the requested path may contain credentials.")

    return candidate
