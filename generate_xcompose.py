#!/usr/bin/env python3
"""XCompose generator with Russian keyboard transliteration and collision detection."""

import sys
import json
import argparse
from pathlib import Path
from typing import List, TextIO

from cur_types import Collision
from utils import escape_symbol
from parser import parse_xcompose
from formatter import format_blocks, format_key_sequence
from transliterator import transliterate_blocks
from collision import find_collisions, load_system_compose, get_current_locale


def report_collisions(collisions: List[Collision], out: TextIO = sys.stderr) -> None:
    """
    Report collisions to stderr.

    Args:
        collisions: List of detected collisions
        out: Output stream (default stderr)
    """
    if not collisions:
        return

    out.write(f"\n{'='*60}\n")
    out.write(f"WARNING: {len(collisions)} PREFIX COLLISION(S) DETECTED\n")
    out.write(f"{'='*60}\n\n")

    for i, collision in enumerate(collisions, 1):
        out.write(f"Collision #{i}:\n")
        out.write(f"  Prefix sequence: {format_key_sequence(collision.prefix_seq)}\n")
        out.write(f"    Line {collision.prefix_entry.line_number}, {collision.prefix_source_file}\n")
        out.write(f"    Symbol: {escape_symbol(collision.prefix_entry.symbol)}\n")
        out.write(f"  Is prefix of: {format_key_sequence(collision.longer_entry.keys)}\n")
        out.write(f"    Line {collision.longer_entry.line_number}, {collision.longer_source_file}\n")
        out.write(f"    Symbol: {escape_symbol(collision.longer_entry.symbol)}\n")
        out.write("\n")

    out.write(f"{'='*60}\n\n")


def main() -> int:
    """
    Main entry point for XCompose generator.

    Returns:
        Exit code (0 = success, 1 = error, 2 = collisions with --strict)
    """
    parser = argparse.ArgumentParser(
        description='Generate XCompose configuration with Russian transliteration and collision detection'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('XCompose-draft'),
        help='Source XCompose-draft file (default: XCompose-draft)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output XCompose file (default: stdout)'
    )
    parser.add_argument(
        '--translit',
        type=Path,
        default=Path('parallel-symbols.json'),
        help='Transliteration map JSON file (default: parallel-symbols.json)'
    )
    parser.add_argument(
        '--locale',
        type=str,
        default=None,
        help='System locale for collision checking (default: auto-detect)'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check for collisions, don\'t generate output'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code if collisions detected'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show verbose parsing details'
    )
    parser.add_argument(
        '--no-system-check',
        action='store_true',
        help='Skip cross-system collision detection'
    )

    args = parser.parse_args()

    # Parse XCompose-draft
    if args.verbose:
        print(f"Reading {args.input}...", file=sys.stderr)

    with open(args.input, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = parse_xcompose(content)

    # Flatten entries for collision detection
    entries = []
    for block in blocks:
        entries.extend(block.entries)

    if args.verbose:
        print(f"Parsed {len(entries)} entries from {len(blocks)} blocks", file=sys.stderr)

    # Load system Compose for collision detection
    system_entries = None
    if not args.no_system_check:
        locale_name = args.locale if args.locale else get_current_locale()
        if args.verbose:
            print(f"Loading system Compose for locale: {locale_name}...", file=sys.stderr)
        system_entries = load_system_compose(locale_name)
        if system_entries and args.verbose:
            print(f"Loaded {len(system_entries)} system entries", file=sys.stderr)

    # Detect collisions
    if args.verbose:
        print("Checking for collisions...", file=sys.stderr)
    collisions = find_collisions(entries, system_entries)

    # Report collisions
    if collisions:
        report_collisions(collisions, sys.stderr)

    # Exit if check-only
    if args.check_only:
        if collisions:
            return 2 if args.strict else 0
        return 0

    # Exit with error if strict mode and collisions found
    if args.strict and collisions:
        return 2

    # Load transliteration map
    translit_map = {}
    if args.translit.exists():
        with open(args.translit, 'r', encoding='utf-8') as f:
            translit_map = json.load(f)
        if args.verbose:
            print(f"Loaded transliteration map with {len(translit_map)} entries", file=sys.stderr)
    else:
        if args.verbose:
            print(f"Warning: Transliteration file not found: {args.translit}", file=sys.stderr)

    # Open output stream
    if args.output:
        out = open(args.output, 'w', encoding='utf-8')
    else:
        out = sys.stdout

    # Write include directive
    out.write('include "%L"\n\n')

    # Write base version
    out.write(format_blocks(blocks))
    out.write('\n\n')

    # Write transliterated version if we have a map
    if translit_map:
        out.write('########################################\n')
        out.write('#      RUSSIAN TRANSLIT VERSION        #\n')
        out.write('########################################\n\n')

        trans_blocks = transliterate_blocks(blocks, translit_map)
        out.write(format_blocks(trans_blocks))

    if args.output:
        out.close()
        if args.verbose:
            print(f"Output written to {args.output}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
