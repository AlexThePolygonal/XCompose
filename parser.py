"""Parser for XCompose files."""

from typing import List, Optional
from cur_types import XComposeEntry, XComposeBlock, ParseError
from utils import (
    is_comment_line,
    is_empty_line,
    is_header_delimiter,
    extract_unicode_info
)


def parse_xcompose(file_content: str) -> List[XComposeBlock]:
    """
    Parse an XCompose file into blocks of entries.
    If the XCompose is not delimited into blocks, return a single block with empty header.

    Args:
        file_content: Content of an XCompose file

    Returns:
        List of XComposeBlock objects

    Raises:
        ParseError: On malformed lines
    """
    lines = file_content.split('\n')
    blocks: List[XComposeBlock] = []
    current_entries: List[XComposeEntry] = []
    current_header = ""

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for block header delimiter
        header = detect_block_header(lines, i)
        if header is not None:
            # Save current block if it has entries
            if current_entries:
                blocks.append(XComposeBlock(header=current_header, entries=current_entries))
                current_entries = []

            # Start new block with this header
            current_header = header
            i += 3  # Skip delimiter, header, and closing delimiter
            continue

        # Skip empty lines and comment lines (but not headers)
        if is_empty_line(line) or is_comment_line(line):
            i += 1
            continue

        # Try to parse as XCompose entry
        entry = parse_line(line, i + 1)  # line_number is 1-indexed
        if entry is not None:
            current_entries.append(entry)

        i += 1

    # Add final block if it has entries
    if current_entries:
        blocks.append(XComposeBlock(header=current_header, entries=current_entries))

    # If no blocks were created, return a single empty block
    if not blocks:
        blocks.append(XComposeBlock(header="", entries=[]))

    return blocks


def detect_block_header(lines: List[str], index: int) -> Optional[str]:
    """
    Check if current position is a block header delimiter.

    A block header is:
    - Line of only # characters
    - Followed by a comment line (the header text)
    - Followed by another line of only # characters

    Args:
        lines: All lines from file
        index: Current line index

    Returns:
        Header text if this is a block delimiter, None otherwise
    """
    # Need at least 3 lines: delimiter, header, delimiter
    if index + 2 >= len(lines):
        return None

    line1 = lines[index]
    line2 = lines[index + 1]
    line3 = lines[index + 2]

    # Check pattern: ###, # HEADER #, ###
    if (is_header_delimiter(line1) and
        is_comment_line(line2) and
        is_header_delimiter(line3)):
        # Extract header text (remove # and whitespace)
        header = line2.strip('#').strip()
        return header

    return None


def parse_line(line: str, line_number: int) -> Optional[XComposeEntry]:
    """
    Parse single XCompose line.

    Expected format:
    <Multi_key><key1><key2>... : "symbol" # optional comment

    The syntax is liberal:
    - Keys can have no spaces between them
    - Symbol string can contain <>, ", escaped quotes, etc.
    - Comment can contain anything

    Args:
        line: Raw line from file
        line_number: Line number for error reporting

    Returns:
        XComposeEntry if valid XCompose line

    Raises:
        ParseError: If line is malformed XCompose syntax
    """
    # Split on first colon
    parts = line.split(':', 1)
    if len(parts) < 2:
        raise ParseError(line_number, line, "Missing colon separator")

    left = parts[0].strip()
    right = ":".join(parts[1:]).strip()

    # Extract keys (including Multi_key)
    keys = extract_keys(left)

    # Extract symbol from quoted string
    symbol = extract_quoted_string(right)

    # Get Unicode info
    if len(symbol) == 1:
        # Single character: get unicode info from unicodedata
        unicode_point, description = extract_unicode_info(symbol)
    else:
        # Multi-character: extract comment from original line
        comment = extract_comment(right)
        unicode_point = ""
        description = comment if comment else "MULTI-CHAR"

    return XComposeEntry(
        keys=keys,
        symbol=symbol,
        unicode_point=unicode_point,
        description=description,
        line_number=line_number
    )


def extract_keys(key_sequence: str) -> List[str]:
    """
    Extract individual keys from key sequence string.

    Handles liberal syntax: <Multi_key><a><b> or <Multi_key> <a> <b>
    Also handles sequences with dead keys (e.g., system Compose file)

    Args:
        key_sequence: String like "<Multi_key><i><a>" or "<dead_tilde> <space>"

    Returns:
        List of ALL keys: ["Multi_key", "i", "a"] or ["dead_tilde", "space"]
    """
    keys = []
    i = 0

    while i < len(key_sequence):
        if key_sequence[i] == '<':
            # Find matching >
            close_idx = key_sequence.find('>', i)
            if close_idx == -1:
                raise ValueError(f"Unclosed angle bracket at position {i}")

            key = key_sequence[i+1:close_idx]
            keys.append(key)

            i = close_idx + 1
        else:
            # Skip whitespace and other chars between brackets
            i += 1

    return keys


def extract_quoted_string(text: str) -> str:
    """
    Extract quoted string from text, handling escape sequences.

    Args:
        text: String starting with '"' (possibly with leading whitespace)

    Returns:
        The content of the quoted string (without quotes, with escapes processed)

    Raises:
        ValueError: If no quoted string found or unclosed quote
    """
    text = text.lstrip()

    if not text.startswith('"'):
        raise ValueError("Text must start with quote")

    i = 1  # Start after opening quote
    result = []

    while i < len(text):
        ch = text[i]

        if ch == '\\' and i + 1 < len(text):
            # Escape sequence - take next char literally
            next_ch = text[i + 1]
            result.append(next_ch)
            i += 2
        elif ch == '"':
            # Unescaped quote - end of string
            return ''.join(result)
        else:
            result.append(ch)
            i += 1

    raise ValueError("Unclosed quoted string")


def extract_comment(text: str) -> str:
    """
    Extract comment from text after quoted string.

    Args:
        text: String like '"symbol" # COMMENT' or '"symbol"'

    Returns:
        Comment text (without leading #) or empty string if no comment
    """
    # Skip past the quoted string first
    text = text.lstrip()
    if not text.startswith('"'):
        return ""

    i = 1  # Start after opening quote
    while i < len(text):
        ch = text[i]
        if ch == '\\' and i + 1 < len(text):
            i += 2
        elif ch == '"':
            # Found end of quoted string
            remaining = text[i+1:].lstrip()
            if remaining.startswith('#'):
                return remaining[1:].strip()
            return ""
        else:
            i += 1

    return ""