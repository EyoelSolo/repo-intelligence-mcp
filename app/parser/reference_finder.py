
from dataclasses import dataclass


@dataclass
class Reference:
    name: str
    file: str
    line: int
    kind: str
    text: str

class ReferenceFinder:
    IDENTIFIER_TYPES = {
        "identifier",
        "property_identifier",
        "type_identifier",
        "shorthand_property_identifier",
        "shorthand_property_identifier_pattern",
    }