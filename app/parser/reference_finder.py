from dataclasses import asdict, dataclass
from pathlib import Path
from platform import node

from app.config import Config
from app.parser.code_parser import CodeParser
from app.repository.scanner import RepositoryScanner



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

        if parent.type in {
            "member_expression",
            "optional_member_expression",
        }:
            property_node = parent.child_by_field_name("property")
            if property_node is not None and property_node.id == node.id:
                return "property_access"

        if parent.type in {
            "import_specifier",
            "export_specifier",
        }:
            return "import_or_export"

        return "identifier"
    
    def find_references(
        self,
        symbol_name: str,
        limit: int = 100,
    ) -> list[dict]:
        symbol_name = symbol_name.strip()
        if not symbol_name:
            return []

        limit = max(1, min(limit, 500))
        results: list[Reference] = []

        for file_info in self.scanner.scan():
            file_path = Path(file_info.absolute_path)

            try:
                tree = self.parser.parse_file(
                    file_path,
                    file_info.language,
                )
                source_lines = file_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).splitlines()
            except (OSError, UnicodeError, ValueError):
                continue

            def walk(node):
                if len(results) >= limit:
                    return

                if (
                    node.type in self.IDENTIFIER_TYPES
                    and node.text is not None
                    and node.text.decode(
                        "utf-8",
                        errors="replace",
                    ) == symbol_name
                ):
                    line_index = node.start_point.row

                    line_text = (
                        source_lines[line_index].strip()
                        if line_index < len(source_lines)
                        else ""
                    )

                    results.append(
                        Reference(
                            name=symbol_name,
                            file=Path(file_info.path).as_posix(),
                            line=line_index + 1,
                            kind=self.classify(node),
                            text=line_text,
                        )
                    )

                    return

                for child in node.children:
                    walk(child)

            walk(tree.root_node)

            if len(results) >= limit:
                break

        return [
            asdict(reference)
            for reference in results
        ]
