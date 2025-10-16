"""Utility functions for XCompose generator."""

import re
import unicodedata
from typing import Tuple


def extract_unicode_info(symbol: str) -> Tuple[str, str]:
    """
    Extract Unicode code point and description using unicodedata.

    Args:
        symbol: Unicode character(s)

    Returns:
        (unicode_point, description) e.g. ("U1D44E", "MATHEMATICAL ITALIC SMALL A")
        For multi-char strings: ("[U+XXXX U+YYYY]", "MULTI-CHAR")
    """
    if len(symbol) == 0:
        return "", "EMPTY"

    # Single character
    codepoint = ord(symbol)
    unicode_point = f"U{codepoint:X}"

    # Raise an error immediately if character is not defined
    description = unicodedata.name(symbol)

    return unicode_point, description


def escape_symbol(symbol: str) -> str:
    """
    Escape symbol for safe display, handling all problematic Unicode cases.

    Returns escaped representation for display, or original symbol if safe.
    """
    if len(symbol) != 1:
        return repr(symbol)  # Multi-char strings get repr

    cp = ord(symbol)

    # 1. COMBINING CHARACTERS (U+0300–U+036F, U+1AB0–U+1AFF, U+1DC0–U+1DFF, U+20D0–U+20FF, U+FE20–U+FE2F)
    # Add dotted circle ◌ (U+25CC) before combining chars to show combining action
    if (0x0300 <= cp <= 0x036F or    # Combining Diacritical Marks
        0x1AB0 <= cp <= 0x1AFF or    # Combining Diacritical Marks Extended
        0x1DC0 <= cp <= 0x1DFF or    # Combining Diacritical Marks Supplement
        0x20D0 <= cp <= 0x20FF or    # Combining Diacritical Marks for Symbols
        0xFE20 <= cp <= 0xFE2F):     # Combining Half Marks
        return f"◌{symbol}"

    # 2. CONTROL CHARACTERS (U+0000–U+001F, U+007F–U+009F)
    # Display as U+XXXX since they're invisible
    if (0x0000 <= cp <= 0x001F or
        0x007F <= cp <= 0x009F):
        return f"U+{cp:04X}"

    # 3. WHITESPACE VARIATIONS (invisible or indistinguishable from regular space)
    whitespace_map = {
        0x00A0: "NBSP",           # No-Break Space
        0x1680: "OGHAM-SPACE",    # Ogham Space Mark
        0x2000: "NQSP",           # En Quad
        0x2001: "MQSP",           # Em Quad
        0x2002: "ENSP",           # En Space
        0x2003: "EMSP",           # Em Space
        0x2004: "3/MSP",          # Three-Per-Em Space
        0x2005: "4/MSP",          # Four-Per-Em Space
        0x2006: "6/MSP",          # Six-Per-Em Space
        0x2007: "FSP",            # Figure Space
        0x2008: "PSP",            # Punctuation Space
        0x2009: "THSP",           # Thin Space
        0x200A: "HSP",            # Hair Space
        0x200B: "ZWSP",           # Zero Width Space
        0x202F: "NNBSP",          # Narrow No-Break Space
        0x205F: "MMSP",           # Medium Mathematical Space
        0x3000: "IDSP",           # Ideographic Space
        0xFEFF: "ZWNBSP",         # Zero Width No-Break Space (BOM)
    }
    if cp in whitespace_map:
        return f"U+{cp:04X}[{whitespace_map[cp]}]"

    # 4. BIDIRECTIONAL MARKS (invisible but affect rendering)
    bidi_map = {
        0x200E: "LRM",            # Left-to-Right Mark
        0x200F: "RLM",            # Right-to-Left Mark
        0x202A: "LRE",            # Left-to-Right Embedding
        0x202B: "RLE",            # Right-to-Left Embedding
        0x202C: "PDF",            # Pop Directional Formatting
        0x202D: "LRO",            # Left-to-Right Override
        0x202E: "RLO",            # Right-to-Left Override
        0x2066: "LRI",            # Left-to-Right Isolate
        0x2067: "RLI",            # Right-to-Left Isolate
        0x2068: "FSI",            # First Strong Isolate
        0x2069: "PDI",            # Pop Directional Isolate
    }
    if cp in bidi_map:
        return f"U+{cp:04X}[{bidi_map[cp]}]"

    # 5. ZERO-WIDTH JOINERS/NON-JOINERS (invisible, used for ligatures)
    if cp == 0x200C:
        return "U+200C[ZWNJ]"
    if cp == 0x200D:
        return "U+200D[ZWJ]"

    # 6. VARIATION SELECTORS (modify previous char rendering, invisible alone)
    if (0xFE00 <= cp <= 0xFE0F or      # Variation Selectors
        0xE0100 <= cp <= 0xE01EF):     # Variation Selectors Supplement
        return f"U+{cp:04X}[VS]"

    # 7. FORMAT CHARACTERS (formatting hints, not visible)
    format_map = {
        0x00AD: "SHY",            # Soft Hyphen
        0x034F: "CGJ",            # Combining Grapheme Joiner
        0x061C: "ALM",            # Arabic Letter Mark
        0x180E: "MVS",            # Mongolian Vowel Separator
        0x2060: "WJ",             # Word Joiner
        0x2061: "FUNC-APP",       # Function Application
        0x2062: "INV-TIMES",      # Invisible Times
        0x2063: "INV-SEP",        # Invisible Separator
        0x2064: "INV-PLUS",       # Invisible Plus
    }
    if cp in format_map:
        return f"U+{cp:04X}[{format_map[cp]}]"

    # 8. PRIVATE USE AREA (no standard glyph, system-dependent)
    if (0xE000 <= cp <= 0xF8FF or      # Private Use Area
        0xF0000 <= cp <= 0xFFFFD or    # Supplementary Private Use Area-A
        0x100000 <= cp <= 0x10FFFD):   # Supplementary Private Use Area-B
        return f"U+{cp:04X}[PUA]"

    # 9. NON-CHARACTERS (permanently reserved, invalid for interchange)
    if (cp & 0xFFFE == 0xFFFE or       # U+nFFFE and U+nFFFF
        0xFDD0 <= cp <= 0xFDEF):       # Non-characters in BMP
        return f"U+{cp:04X}[NONCHAR]"


    # 11. SURROGATES (UTF-16 artifacts, invalid in UTF-8)
    # This shouldn't occur in proper Python strings, but check anyway
    if 0xD800 <= cp <= 0xDFFF:
        return f"U+{cp:04X}[SURROGATE-INVALID]"
    
    # 10. UNASSIGNED CODE POINTS (valid range but no assigned character)
    # Check by attempting to get name
    try:
        unicodedata.name(symbol)
    except ValueError:
        return f"U+{cp:04X}[UNASSIGNED]"


    # 12. LINE/PARAGRAPH SEPARATORS (semantic whitespace, might break formatting)
    if cp == 0x2028:
        return "U+2028[LSEP]"
    if cp == 0x2029:
        return "U+2029[PSEP]"

    # If none of the problematic cases apply, return the symbol as-is
    return symbol

def is_comment_line(line: str) -> bool:
    """Check if line is a comment (starts with #)."""
    stripped = line.lstrip()
    return stripped.startswith('#')


def is_empty_line(line: str) -> bool:
    """Check if line is empty or whitespace only."""
    return not line.strip()


def is_header_delimiter(line: str) -> bool:
    """
    Check if line is a header delimiter (line of only # chars).

    Returns True if line contains only # and whitespace.
    """
    stripped = line.strip()
    return len(stripped) > 0 and all(c == '#' for c in stripped)
