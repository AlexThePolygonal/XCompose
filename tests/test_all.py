"""Tests for XCompose generator."""

import json
import sys
import importlib.util
import importlib.machinery
from pathlib import Path

# Import from merged generate-xcompose script
parent_dir = Path(__file__).parent.parent
script_path = str(parent_dir / "generate-xcompose")

spec = importlib.util.spec_from_loader(
    "generate_xcompose",
    importlib.machinery.SourceFileLoader("generate_xcompose", script_path)
)
gx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gx)

# Import all needed symbols from merged script
XComposeEntry = gx.XComposeEntry
XComposeBlock = gx.XComposeBlock
extract_unicode_info = gx.extract_unicode_info
escape_symbol = gx.escape_symbol
is_comment_line = gx.is_comment_line
is_empty_line = gx.is_empty_line
is_header_delimiter = gx.is_header_delimiter
parse_xcompose = gx.parse_xcompose
parse_line = gx.parse_line
extract_keys = gx.extract_keys
extract_quoted_string = gx.extract_quoted_string
format_blocks = gx.format_blocks
format_entry = gx.format_entry
calculate_key_width = gx.calculate_key_width
format_key_sequence = gx.format_key_sequence
transliterate_blocks = gx.transliterate_blocks
get_current_locale = gx.get_current_locale
load_system_compose = gx.load_system_compose
find_collisions = gx.find_collisions
is_prefix = gx.is_prefix


def test_utils():
    """Test utility functions."""
    print("Testing utils...")

    # Test extract_unicode_info
    point, desc = extract_unicode_info("α")
    assert point == "U3B1", f"Expected U3B1, got {point}"
    assert "ALPHA" in desc, f"Expected ALPHA in description, got {desc}"

    # Test escape_symbol - normal char
    assert escape_symbol("α") == "α"

    # Test escape_symbol - control char
    assert escape_symbol("\x00") == "U+0000"

    # Test escape_symbol - combining char
    result = escape_symbol("\u0301")  # Combining acute accent
    assert result.startswith("◌"), f"Expected combining char to start with ◌, got {result}"

    # Test is_comment_line
    assert is_comment_line("# comment")
    assert is_comment_line("  # comment")
    assert not is_comment_line("not a comment")

    # Test is_empty_line
    assert is_empty_line("")
    assert is_empty_line("   ")
    assert not is_empty_line("text")

    # Test is_header_delimiter
    assert is_header_delimiter("###")
    assert is_header_delimiter("######")
    assert not is_header_delimiter("## #")

    print("✓ Utils tests passed")


def test_parser():
    """Test parser functions."""
    print("Testing parser...")

    # Test extract_keys - now includes ALL keys
    keys = extract_keys("<Multi_key><i><a>")
    assert keys == ["Multi_key", "i", "a"], f"Expected ['Multi_key', 'i', 'a'], got {keys}"

    keys = extract_keys("<Multi_key> <i> <a>")
    assert keys == ["Multi_key", "i", "a"], f"Expected ['Multi_key', 'i', 'a'], got {keys}"

    # Test dead key sequences (system file format)
    keys = extract_keys("<dead_tilde> <space>")
    assert keys == ["dead_tilde", "space"], f"Expected ['dead_tilde', 'space'], got {keys}"

    # Test extract_quoted_string
    symbol = extract_quoted_string('"α"')
    assert symbol == "α", f"Expected α, got {symbol}"

    symbol = extract_quoted_string('"test \\" quote"')
    assert symbol == 'test " quote', f"Expected 'test \" quote', got {symbol}"

    # Test parse_line
    entry = parse_line('<Multi_key> <i> <a> : "𝑎" # comment', 1)
    assert entry.keys == ["Multi_key", "i", "a"]
    assert entry.symbol == "𝑎"

    # Test compact syntax
    entry = parse_line('<Multi_key><i><a>:"𝑎"# comment', 2)
    assert entry.keys == ["Multi_key", "i", "a"]
    assert entry.symbol == "𝑎"

    print("✓ Parser tests passed")


def test_parse_full_file():
    """Test parsing full XCompose file."""
    print("Testing full file parsing...")

    with open('tests/toy-xcompose.txt', 'r') as f:
        content = f.read()

    blocks = parse_xcompose(content)

    assert len(blocks) == 2, f"Expected 2 blocks, got {len(blocks)}"
    assert blocks[0].header == "MATHEMATICAL ITALIC"
    assert blocks[1].header == "GREEK LETTERS"

    # Check first block has entries
    assert len(blocks[0].entries) == 4, f"Expected 4 entries in first block, got {len(blocks[0].entries)}"

    # Check an entry - now includes Multi_key
    entry = blocks[0].entries[0]
    assert entry.keys == ["Multi_key", "i", "A"]
    assert entry.symbol == "𝐴"

    print("✓ Full file parsing passed")


def test_formatter():
    """Test formatter functions."""
    print("Testing formatter...")

    # Test format_key_sequence - now expects full key list
    seq = format_key_sequence(["Multi_key", "i", "a"])
    assert seq == "<Multi_key> <i> <a>", f"Expected '<Multi_key> <i> <a>', got {seq}"

    # Test with dead keys
    seq = format_key_sequence(["dead_tilde", "space"])
    assert seq == "<dead_tilde> <space>", f"Expected '<dead_tilde> <space>', got {seq}"

    # Test calculate_key_width
    entries = [
        XComposeEntry(["Multi_key", "i", "a"], "𝑎", "U1D44E", "DESC", 1),
        XComposeEntry(["Multi_key", "i", "b", "c"], "test", "U0000", "DESC", 2),
    ]
    width = calculate_key_width(entries)
    # "<Multi_key> <i> <a>" = 20 chars
    # "<Multi_key> <i> <b> <c>" = 23 chars
    assert width == 23, f"Expected width 23, got {width}"

    # Test format_entry
    entry = XComposeEntry(["Multi_key", "i", "a"], "𝑎", "U1D44E", "MATHEMATICAL ITALIC SMALL A", 1)
    formatted = format_entry(entry, 20)
    assert formatted.startswith("<Multi_key> <i> <a>")
    assert ' : "𝑎"' in formatted
    assert "U1D44E" in formatted

    print("✓ Formatter tests passed")


def test_transliterator():
    """Test transliterator."""
    print("Testing transliterator...")

    with open('tests/toy-translit.json', 'r') as f:
        translit_map = json.load(f)

    # Create test block
    entries = [
        XComposeEntry(["i", "a"], "𝑎", "U1D44E", "DESC", 1),
        XComposeEntry(["g", "b"], "test", "U0000", "DESC", 2),
        XComposeEntry(["X", "Y"], "unchanged", "U0000", "DESC", 3),  # Should not be in output
    ]
    blocks = [XComposeBlock("TEST", entries)]

    # Transliterate
    result = transliterate_blocks(blocks, translit_map)

    assert len(result) == 1, f"Expected 1 block, got {len(result)}"
    assert len(result[0].entries) == 2, f"Expected 2 changed entries, got {len(result[0].entries)}"

    # Check transliteration happened
    assert result[0].entries[0].keys == ["Cyrillic_i", "Cyrillic_a"]
    assert result[0].entries[1].keys == ["Cyrillic_g", "Cyrillic_b"]

    print("✓ Transliterator tests passed")


def test_collision_detection():
    """Test collision detection."""
    print("Testing collision detection...")

    # Test is_prefix
    assert is_prefix(["a"], ["a", "b"])
    assert is_prefix(["a", "b"], ["a", "b", "c"])
    assert not is_prefix(["a", "b"], ["a", "b"])  # Equal, not proper prefix
    assert not is_prefix(["a", "b"], ["a", "c"])  # Different
    assert not is_prefix(["a", "b", "c"], ["a", "b"])  # Longer, not prefix

    # Test collision detection with colliding entries
    entries_with_collision = [
        XComposeEntry(["i", "a"], "α", "U3B1", "ALPHA", 1),
        XComposeEntry(["i", "a", "b"], "β", "U3B2", "BETA", 2),
    ]
    collisions = find_collisions(entries_with_collision)
    assert len(collisions) == 1, f"Expected 1 collision, got {len(collisions)}"
    assert collisions[0].prefix_seq == ["i", "a"]

    # Test no collision
    entries_no_collision = [
        XComposeEntry(["i", "a"], "α", "U3B1", "ALPHA", 1),
        XComposeEntry(["i", "b"], "β", "U3B2", "BETA", 2),
    ]
    collisions = find_collisions(entries_no_collision)
    assert len(collisions) == 0, f"Expected 0 collisions, got {len(collisions)}"

    # Test locale detection
    try:
        locale_name = get_current_locale()
        print(f"  Detected locale: {locale_name}")

        # Test system compose loading
        system_entries = load_system_compose(locale_name)
        if system_entries:
            print(f"  Loaded {len(system_entries)} system entries")
            # Test cross-system collision detection
            test_entries = [
                XComposeEntry(["Multi_key", "apostrophe", "A"], "Á", "UC1", "TEST", 1),
            ]
            cross_collisions = find_collisions(test_entries, system_entries)
            print(f"  Found {len(cross_collisions)} cross-system collisions")
        else:
            print("  No system Compose file found (ok)")
    except Exception as e:
        print(f"  Could not load system Compose: {e}")

    print("✓ Collision detection tests passed")


def test_integration():
    """Integration test: parse, format, transliterate."""
    print("Testing integration...")

    with open('tests/toy-xcompose.txt', 'r') as f:
        content = f.read()

    with open('tests/toy-translit.json', 'r') as f:
        translit_map = json.load(f)

    # Parse
    blocks = parse_xcompose(content)

    # Format
    formatted = format_blocks(blocks)
    assert "MATHEMATICAL ITALIC" in formatted
    assert "GREEK LETTERS" in formatted
    assert "<Multi_key>" in formatted

    # Transliterate
    trans_blocks = transliterate_blocks(blocks, translit_map)
    trans_formatted = format_blocks(trans_blocks)

    # Check transliteration happened
    assert "Cyrillic_i" in trans_formatted or "Cyrillic_a" in trans_formatted

    print("✓ Integration test passed")


if __name__ == "__main__":
    try:
        test_utils()
        test_parser()
        test_parse_full_file()
        test_formatter()
        test_transliterator()
        test_collision_detection()
        test_integration()

        print("\n" + "="*50)
        print("ALL TESTS PASSED")
        print("="*50)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
