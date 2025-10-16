"""Transliteration logic for XCompose entries."""

from typing import List
from cur_types import XComposeEntry, XComposeBlock, TranslitMap


def transliterate_blocks(blocks: List[XComposeBlock],
                        translit_map: TranslitMap) -> List[XComposeBlock]:
    """
    Transliterate all blocks, filtering unchanged entries.

    Args:
        blocks: Original blocks
        translit_map: Key mapping (QWERTY → Cyrillic)

    Returns:
        Transliterated blocks with only changed entries
    """
    result_blocks = []

    for block in blocks:
        transliterated_entries = []

        for entry in block.entries:
            # Apply transliteration to keys
            transliterated_keys = [translit_map.get(key, key) for key in entry.keys]

            # Only include if keys changed
            if transliterated_keys != entry.keys:
                transliterated_entries.append(XComposeEntry(
                    keys=transliterated_keys,
                    symbol=entry.symbol,
                    unicode_point=entry.unicode_point,
                    description=entry.description,
                    line_number=entry.line_number
                ))

        # Only include block if it has changed entries
        if transliterated_entries:
            result_blocks.append(XComposeBlock(
                header=block.header,
                entries=transliterated_entries
            ))

    return result_blocks
