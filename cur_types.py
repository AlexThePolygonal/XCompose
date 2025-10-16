"""Core data structures and exceptions for XCompose generator."""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


# ============================================================================
# Core Data Structures
# ============================================================================

@dataclass
class XComposeEntry:
    """Single XCompose entry with parsed components."""
    keys: List[str]           # ["i", "a"] from <i> <a>
    symbol: str               # "𝑎"
    unicode_point: str        # "U1D44E"
    description: str          # "MATHEMATICAL ITALIC SMALL A"
    line_number: int          # Source line for error reporting


@dataclass
class XComposeBlock:
    """Block of XCompose entries with optional header."""
    header: str                        # Block header text
    entries: List[XComposeEntry]       # Entries in this block


@dataclass
class Collision:
    """Represents a prefix collision between two sequences."""
    prefix_seq: List[str]              # The prefix sequence
    prefix_entry: XComposeEntry        # Entry with the prefix
    prefix_source_file: str            # File where prefix_entry is from
    longer_entry: XComposeEntry        # Entry that has prefix as prefix
    longer_source_file: str            # File where longer_entry is from


class CollisionLocation(Enum):
    """Where a collision was detected."""
    INTERNAL = "internal"              # Within same file
    CROSS_SYSTEM = "cross_system"      # Between draft and system
    CROSS_TRANSLIT = "cross_translit"  # In transliterated version


# ============================================================================
# Type Aliases
# ============================================================================

KeySequence = List[str]
TranslitMap = Dict[str, str]
TrieNode = Dict[str, 'TrieNode']  # Recursive type for prefix tree


# ============================================================================
# Exceptions
# ============================================================================

class XComposeError(Exception):
    """Base exception for XCompose generator."""
    pass


class ParseError(XComposeError):
    """Parse error with line number and context."""

    def __init__(self, line_number: int, line_content: str, message: str):
        self.line_number = line_number
        self.line_content = line_content
        self.message = message
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.message}\n  {self.line_content}"


class CollisionError(XComposeError):
    """Collision detected in strict mode."""
    pass


class TranslitError(XComposeError):
    """Transliteration error."""
    pass
