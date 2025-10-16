"""Collision detection for XCompose key sequences."""

import os
import locale
from typing import List, Optional, Dict, Any
from pathlib import Path
from cur_types import XComposeEntry, XComposeBlock, Collision, KeySequence
from parser import parse_xcompose


def get_current_locale() -> str:
    """
    Get current system locale (e.g., en_US.UTF-8).

    Returns:
        Locale string or "en_US.UTF-8" as fallback
    """
    # Try environment variables first
    for var in ['LC_ALL', 'LC_CTYPE', 'LANG']:
        loc = os.environ.get(var)
        if loc:
            return loc

    # Try Python's locale module
    try:
        loc, _ = locale.getlocale()
        if loc:
            return loc
    except:
        pass

    # Fallback
    raise Exception("Could not determine system locale")


def load_system_compose(locale_name: str) -> Optional[List[XComposeEntry]]:
    """
    Load system XCompose file for locale.

    Args:
        locale_name: System locale (e.g., "en_US.UTF-8"), or None to auto-detect

    Returns:
        List of parsed entries, or None if not found/parse error
    """

    # Common locations for system Compose files
    paths = [
        Path(f"/usr/share/X11/locale/{locale_name}/Compose"),
        Path(f"/usr/share/X11/locale/{locale_name.split('.')[0]}/Compose")
    ]

    for path in paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                blocks = parse_xcompose(content)
                # Flatten all entries from all blocks
                entries = []
                for block in blocks:
                    entries.extend(block.entries)
                # Only return if we got at least some entries
                if entries:
                    return entries
            except Exception as e:
                # Parse errors are common in system files (includes, etc.)
                # Try next path
                continue

    return None


def build_trie(entries: List[XComposeEntry]) -> Dict[str, Any]:
    """
    Build prefix tree from entries.

    Args:
        entries: All XCompose entries

    Returns:
        Root node of trie (nested dicts)
    """
    root: Dict[str, Any] = {}

    for entry in entries:
        node = root
        for key in entry.keys:
            if key not in node:
                node[key] = {}
            node = node[key]

        # Mark this as a terminal node
        node['__entry__'] = entry

    return root


def find_collisions(entries: List[XComposeEntry],
                   system_entries: Optional[List[XComposeEntry]] = None) -> List[Collision]:
    """
    Detect all prefix collisions.

    Args:
        entries: Entries from XCompose-draft
        system_entries: Optional system XCompose entries

    Returns:
        List of detected collisions
    """
    collisions: List[Collision] = []

    # Check internal collisions in draft
    collisions.extend(find_internal_collisions(entries, "XCompose-draft"))

    # Check cross-system collisions if system entries provided
    if system_entries:
        collisions.extend(find_cross_collisions(entries, system_entries))

    return collisions


def find_internal_collisions(entries: List[XComposeEntry], source_file: str) -> List[Collision]:
    """
    Find collisions within a single list of entries.

    Args:
        entries: List of entries to check
        source_file: Name of source file for reporting

    Returns:
        List of collisions found
    """
    collisions: List[Collision] = []

    # Compare each pair of entries
    for i, entry1 in enumerate(entries):
        for entry2 in entries[i+1:]:
            if is_prefix(entry1.keys, entry2.keys):
                collisions.append(Collision(
                    prefix_seq=entry1.keys,
                    prefix_entry=entry1,
                    prefix_source_file=source_file,
                    longer_entry=entry2,
                    longer_source_file=source_file
                ))
            elif is_prefix(entry2.keys, entry1.keys):
                collisions.append(Collision(
                    prefix_seq=entry2.keys,
                    prefix_entry=entry2,
                    prefix_source_file=source_file,
                    longer_entry=entry1,
                    longer_source_file=source_file
                ))

    return collisions


def find_cross_collisions(draft_entries: List[XComposeEntry],
                         system_entries: List[XComposeEntry]) -> List[Collision]:
    """
    Find collisions between draft and system entries.

    Args:
        draft_entries: Entries from XCompose-draft
        system_entries: Entries from system Compose

    Returns:
        List of collisions found
    """
    collisions: List[Collision] = []

    for draft_entry in draft_entries:
        for system_entry in system_entries:
            if is_prefix(draft_entry.keys, system_entry.keys):
                collisions.append(Collision(
                    prefix_seq=draft_entry.keys,
                    prefix_entry=draft_entry,
                    prefix_source_file="XCompose-draft",
                    longer_entry=system_entry,
                    longer_source_file="system Compose"
                ))
            elif is_prefix(system_entry.keys, draft_entry.keys):
                collisions.append(Collision(
                    prefix_seq=system_entry.keys,
                    prefix_entry=system_entry,
                    prefix_source_file="system Compose",
                    longer_entry=draft_entry,
                    longer_source_file="XCompose-draft"
                ))

    return collisions


def is_prefix(seq1: KeySequence, seq2: KeySequence) -> bool:
    """
    Check if seq1 is a proper prefix of seq2.

    Args:
        seq1: First sequence
        seq2: Second sequence

    Returns:
        True if seq1 is a proper prefix of seq2
    """
    if len(seq1) >= len(seq2):
        return False

    return seq2[:len(seq1)] == seq1
