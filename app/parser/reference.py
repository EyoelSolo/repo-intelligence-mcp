
from dataclasses import dataclass


@dataclass
class Reference:
    name: str
    file: str
    line: int
    kind: str
    text: str
