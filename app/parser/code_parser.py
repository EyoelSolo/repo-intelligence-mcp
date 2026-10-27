from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_javascript
import tree_sitter_typescript


@dataclass
class Symbol:
    name: str
    kind: str
    file: str
    start_line: int
    end_line: int


@dataclass
class Import:
    source: str
    file: str
    start_line: int


class CodeParser:

    def __init__(self):
        self.javascript_language = Language(
            tree_sitter_javascript.language()
        )

        self.typescript_language = Language(
            tree_sitter_typescript.language_typescript()
        )

        self.tsx_language = Language(
            tree_sitter_typescript.language_tsx()
        )

    def get_parser(self, language: str) -> Parser:

        if language == "javascript":
            return Parser(self.javascript_language)

        if language == "typescript":
            return Parser(self.typescript_language)

        if language == "tsx":
            return Parser(self.tsx_language)

        raise ValueError(f"Unsupported language: {language}")

    def parse_file(
        self,
        path: Path,
        language: str,
    ):
        parser = self.get_parser(language)

        source = path.read_bytes()

        return parser.parse(source)

    def extract_symbols(
        self,
        path: Path,
        language: str,
    ) -> list[Symbol]:

        tree = self.parse_file(path, language)

        symbols: list[Symbol] = []

        def walk(node):

            node_type = node.type

            symbol_name = None
            symbol_kind = None

            if node_type in {
                "function_declaration",
                "generator_function_declaration",
            }:
                symbol_kind = "function"

                name_node = node.child_by_field_name("name")

                if name_node:
                    symbol_name = name_node.text.decode(
                        "utf-8",
                        errors="replace",
                    )

            elif node_type == "class_declaration":
                symbol_kind = "class"

                name_node = node.child_by_field_name("name")

                if name_node:
                    symbol_name = name_node.text.decode(
                        "utf-8",
                        errors="replace",
                    )

            elif node_type in {
                "interface_declaration",
                "type_alias_declaration",
                "enum_declaration",
            }:
                symbol_kind = "type"

                name_node = node.child_by_field_name("name")

                if name_node:
                    symbol_name = name_node.text.decode(
                        "utf-8",
                        errors="replace",
                    )

            elif node_type == "variable_declarator":
                value_node = node.child_by_field_name("value")
                if value_node is not None and value_node.type in {
                    "arrow_function",
                    "function_expression",
                }:
                    name_node = node.child_by_field_name("name")
                    if name_node is not None and name_node.type == "identifier":
                        symbol_kind = "function"
                        symbol_name = name_node.text.decode(
                            "utf-8",
                            errors="replace",
                        )

            elif node_type == "method_definition":
                symbol_kind = "method"

                name_node = node.child_by_field_name("name")

                if name_node:
                    symbol_name = name_node.text.decode(
                        "utf-8",
                        errors="replace",
                    )

            if symbol_name:
                symbols.append(
                    Symbol(
                        name=symbol_name,
                        kind=symbol_kind,
                        file=str(path),
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                    )
                )

            for child in node.children:
                walk(child)

        walk(tree.root_node)

        return symbols

    def extract_imports(
        self,
        path: Path,
        language: str,
    ) -> list[Import]:

        tree = self.parse_file(path, language)

        imports: list[Import] = []

        def walk(node):

            if node.type == "import_statement":

                source_node = node.child_by_field_name("source")

                if source_node:
                    value = source_node.text.decode(
                        "utf-8",
                        errors="replace",
                    )

                    imports.append(
                        Import(
                            source=value.strip("\"'"),
                            file=str(path),
                            start_line=node.start_point.row + 1,
                        )
                    )

            for child in node.children:
                walk(child)

        walk(tree.root_node)

        return imports
