from typing import Dict, Tuple


class IndexRenaming:
    META: Tuple[str, str] = ('META', 'META PLATFORMS INC CLASS A',)
    BASFY: Tuple[str, str] = ('BASFY', 'BASF SE FSPONSORED ADR 1 ADR REP 0.25 ORD SHS',)
    EADSY: Tuple[str, str] = ('EADSY', 'AIRBUS GROUP FSPONSORED ADR 1 ADR REP 0.25 ORD SHS',)

    mapping: Dict[str, Tuple[str, str]] = {
        'FB': META,
        'META': META,
        'BASFY': BASFY,
        'EADSY': EADSY,
    }

    def __init__(self, index:str, definition: str):
        self.raw_index = index
        self.raw_definition = definition

    def actual_definition(self) -> str:
        if self.raw_index in IndexRenaming.mapping:
            (index, definition) = IndexRenaming.mapping[self.raw_index]
        else:
            (index, definition) = (self.raw_index, self.raw_definition)

        return '{long} ({symbol})'.format(
            long=definition,
            symbol=index,
        )