
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

    def __init__(
    self,
    scanner: RepositoryScanner,
    parser: CodeParser,
    ):
        self.scanner = scanner
        self.parser = parser

    def classify(self, node) -> str:
        parent = node.parent
        if parent is None:
            return "identifier"

        # Is this identifier the name declared by its parent?
        name_node = parent.child_by_field_name("name")
        if (
            parent.type in self.DEFINITION_TYPES
            and name_node is not None
            and name_node.id == node.id
        ):
            return "definition"
        if parent.type == "call_expression":
            function_node = parent.child_by_field_name("function")
            if function_node is not None and (
                function_node.id == node.id
                or function_node.start_byte <= node.start_byte
                and node.end_byte <= function_node.end_byte
            ):
                return "call"