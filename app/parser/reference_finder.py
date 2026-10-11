
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

    DEFINITION_TYPES = {
        "function_declaration",
        "generator_function_declaration",
        "class_declaration",
        "interface_declaration",
        "type_alias_declaration",
        "enum_declaration",
        "method_definition",
        "variable_declarator",
        "function_expression",
        "arrow_function",
    }