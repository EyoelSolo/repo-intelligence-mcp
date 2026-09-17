from dataclasses import dataclass
from pathlib import Path

from app.config import Config
from app.repository.detector import detect_language


@dataclass
class FileInfo:
    path: str
    absolute_path: str
    language: str | None
    size: int
    lines: int