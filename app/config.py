from dataclasses import dataclass
from pathlib import path


@dataclass
class Config: 
    repository_root: path
