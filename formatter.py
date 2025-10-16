"""Output formatting for XCompose entries."""

from typing import List
from cur_types import XComposeEntry, XComposeBlock, KeySequence


def format_blocks(blocks: List[XComposeBlock]) -> str:
    """
    Format multiple blocks with headers.

    Args:
        blocks: List of blocks to format

    Returns:
        Formatted XCompose text
    """
    result = []

    for block in blocks:
        result.append(format_block(block))

    return '\n'.join(result)


def format_block(block: XComposeBlock) -> str:
    """
    Format single block with aligned columns.

    Args:
        block: Block to format

    Returns:
        Formatted XCompose text with header and aligned entries
    """
    lines = []

    # Add header if present
    if block.header:
        delimiter = '#' * (len(block.header) + 4)
        lines.append(delimiter)
        lines.append(f"# {block.header} #")
        lines.append(delimiter)
        lines.append("")

    # Calculate alignment width for this block
    key_width = calculate_key_width(block.entries)

    # Format each entry
    for entry in block.entries:
        lines.append(format_entry(entry, key_width))

    return '\n'.join(lines)


def format_entry(entry: XComposeEntry, key_width: int) -> str:
    """
    Format single entry with padding.

    Args:
        entry: Entry to format
        key_width: Width to pad key sequence to

    Returns:
        Formatted line like: <Multi_key> <i> <a>    : "𝑎" U1D44E # MATHEMATICAL ITALIC SMALL A
    """
    key_seq = format_key_sequence(entry.keys)
    padding = ' ' * (key_width - len(key_seq))

    return f'{key_seq}{padding} : "{entry.symbol}" {entry.unicode_point} # {entry.description}'


def calculate_key_width(entries: List[XComposeEntry]) -> int:
    """
    Calculate max key sequence width for alignment.

    Args:
        entries: List of entries in a block

    Returns:
        Maximum width of formatted key sequences
    """
    if not entries:
        return 0

    return max(len(format_key_sequence(entry.keys)) for entry in entries)


def format_key_sequence(keys: KeySequence) -> str:
    """
    Format key list as XCompose sequence: <key0> <key1> <key2>

    Args:
        keys: List of ALL keys (including first key like Multi_key, dead_tilde, etc.)

    Returns:
        Formatted key sequence string like "<Multi_key> <i> <a>" or "<dead_tilde> <space>"
    """
    formatted_keys = [f'<{key}>' for key in keys]
    return ' '.join(formatted_keys)
