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