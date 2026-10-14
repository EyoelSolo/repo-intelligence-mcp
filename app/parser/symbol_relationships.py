from app.parser.reference_finder import ReferenceFinder
from app.parser.symbol_index import SymbolIndex


class SymbolRelationships:
    def __init__(
        self,
        symbol_index: SymbolIndex,
        reference_finder: ReferenceFinder,
    ):
        self.symbol_index = symbol_index
        self.reference_finder = reference_finder

    def find(self, symbol_name: str, limit: int = 100) -> dict:
        symbol_name = symbol_name.strip()

        if not symbol_name:
            return {
                "symbol": symbol_name,
                "definitions": [],
                "references": [],
                "total_definitions": 0,
                "total_references": 0,
            }

        limit = max(1, min(limit, 500))
        definitions = self.symbol_index.find(symbol_name)
        candidates = self.reference_finder.find_references(
            symbol_name=symbol_name,
            limit=limit,
        )
        definition_locations = {
            (
                item["file"].replace("\\", "/"),
                item["start_line"],
            )
            for item in definitions
        }