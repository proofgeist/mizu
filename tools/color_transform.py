#!/usr/bin/env python3
"""
Color transformation script for shadcn theme.

Reads a FileMaker template.xml (UTF-16 LE with BOM), applies ordered
find-and-replace on rgba color values within the CSS CDATA block,
and writes back preserving encoding exactly.

Usage:
    python3 tools/color_transform.py [--dry-run]
"""

import re
import sys
from collections import OrderedDict

TEMPLATE_PATH = "proof_shadcn_theme/template.xml"

# ─── shadcn target palette (FileMaker rgba format) ───────────────────
# background:          rgba(100%,100%,100%,1)          — page/card backgrounds
# foreground:          rgba(14.1%,14.1%,14.1%,1)       — primary text
# primary:             rgba(18%,18%,18%,1)              — buttons, active states
# primary-foreground:  rgba(98%,98%,98%,1)              — text on primary surfaces
# secondary:           rgba(96.1%,96.1%,96.1%,1)        — hover backgrounds, alt rows
# muted-foreground:    rgba(56.5%,56.5%,56.5%,1)        — placeholders, secondary labels
# border:              rgba(92.2%,92.2%,92.2%,1)         — all borders
# ring:                rgba(70.2%,70.2%,70.2%,1)         — focus ring
# destructive:         keep current red                   — error states

# ─── Color mapping ──────────────────────────────────────────────────
# Order matters: more specific values first to avoid partial replacements.
# Each entry: (old_rgba, new_rgba, category_description)

COLOR_MAP = OrderedDict([
    # ── Batch 1: Blue accents → primary (dark gray) ──────────────────
    # Main blue accent (232 occurrences - biggest single color)
    ("rgba(14.5098%,40.3922%,96.0784%,1)", "rgba(18%,18%,18%,1)"),
    # Blue accent with alpha (for subtle backgrounds)
    ("rgba(14.5098%,40.3922%,96.0784%,0.0740582)", "rgba(18%,18%,18%,0.07)"),
    # Saturated blues → primary
    ("rgba(0%,43.9216%,81.1765%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(0%,47.8431%,100%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(0%,25.4095%,80.0784%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(0%,40.1882%,84%,1)", "rgba(18%,18%,18%,1)"),
    # Darker blues → primary
    ("rgba(10.1961%,34.5098%,88.2353%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(2.7451%,19.6078%,58.8235%,1)", "rgba(14.1%,14.1%,14.1%,1)"),
    ("rgba(10.0502%,25.829%,46.7451%,1)", "rgba(14.1%,14.1%,14.1%,1)"),
    ("rgba(0%,16.0784%,22.3529%,1)", "rgba(14.1%,14.1%,14.1%,1)"),

    # ── Batch 2: Blue-tinted light backgrounds → secondary/neutral ───
    # Light blue tints → neutral near-white
    ("rgba(75.2941%,92.9412%,99.6078%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(89.0196%,94.902%,99.2157%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(96.0784%,97.2549%,98.0392%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(95.6863%,96.4706%,98.0392%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(95.6863%,96.8627%,97.6471%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(92.3695%,95.9839%,100%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(90.1961%,93.7255%,97.6471%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(70.1961%,89.4118%,98.8235%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(70.1961%,89.8039%,98.8235%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(98.0392%,98.0392%,100%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    # Cyan/teal-tinted colors → neutral
    ("rgba(30.1961%,78.8235%,96.0784%,1)", "rgba(70.2%,70.2%,70.2%,1)"),
    ("rgba(15.6863%,71.3726%,96.4706%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(16.0784%,71.3726%,96.4706%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(0%,72.9412%,98.4314%,1)", "rgba(70.2%,70.2%,70.2%,1)"),
    ("rgba(0%,73.3333%,98.4314%,1)", "rgba(70.2%,70.2%,70.2%,1)"),
    ("rgba(1.56863%,72.549%,98.4314%,1)", "rgba(70.2%,70.2%,70.2%,1)"),
    ("rgba(49.4118%,73.7255%,100%,1)", "rgba(70.2%,70.2%,70.2%,1)"),
    ("rgba(50.1961%,65.8824%,100%,1)", "rgba(70.2%,70.2%,70.2%,1)"),
    # Teal/green-blue mid-tones → muted-foreground
    ("rgba(12.549%,62.3529%,80.3922%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(12.9129%,62.6278%,80.7059%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(67.2722%,76.1324%,82.0392%,1)", "rgba(80%,80%,80%,1)"),

    # ── Batch 3: Purple/blue-cast grays → neutral grays ──────────────
    # Purple-cast grays used in borders and backgrounds
    ("rgba(78.4314%,78.0392%,80%,1)", "rgba(80%,80%,80%,1)"),
    ("rgba(78.4314%,77.6471%,80%,1)", "rgba(80%,80%,80%,1)"),
    ("rgba(93.7255%,93.7255%,95.6863%,1)", "rgba(92.2%,92.2%,92.2%,1)"),
    ("rgba(97.6471%,96.8627%,98.0392%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(97.7024%,97.1215%,98.1489%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    # Purple-cast mid-grays
    ("rgba(22.7451%,20.3922%,25.098%,1)", "rgba(22.3529%,22.3529%,22.3529%,1)"),
    ("rgba(22.9226%,20.6687%,25.1765%,1)", "rgba(22.3529%,22.3529%,22.3529%,1)"),
    ("rgba(40.7843%,40.3922%,41.1765%,1)", "rgba(38.3529%,38.3529%,38.3529%,1)"),
    ("rgba(45.098%,44.7059%,45.4902%,1)", "rgba(45.8824%,45.8824%,45.8824%,1)"),
    ("rgba(45.098%,44.7059%,45.4902%,0.4)", "rgba(45.8824%,45.8824%,45.8824%,0.4)"),
    ("rgba(45.9162%,56.2971%,60.4495%,0.579236)", "rgba(56.5%,56.5%,56.5%,0.58)"),
    ("rgba(69.0196%,74.5098%,77.2549%,1)", "rgba(74.1961%,74.1961%,74.1961%,1)"),
    ("rgba(96.3922%,15.4227%,83.3581%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(97.1487%,89.2283%,100%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(80.3922%,0%,67.451%,1)", "rgba(56.5%,56.5%,56.5%,1)"),

    # ── Batch 4: Text colors → foreground / muted-foreground ────────
    # Near-black text shades → foreground
    ("rgba(4.31373%,4.31373%,4.31373%,1)", "rgba(14.1%,14.1%,14.1%,1)"),
    ("rgba(6.27451%,6.27451%,6.27451%,1)", "rgba(14.1%,14.1%,14.1%,1)"),
    ("rgba(6.35294%,6.35294%,6.35294%,1)", "rgba(14.1%,14.1%,14.1%,1)"),
    ("rgba(8.62745%,8.62745%,8.62745%,1)", "rgba(14.1%,14.1%,14.1%,1)"),
    ("rgba(10.1961%,10.1961%,10.1961%,1)", "rgba(14.1%,14.1%,14.1%,1)"),
    ("rgba(20.3922%,20.3922%,20.3922%,1)", "rgba(14.1%,14.1%,14.1%,1)"),
    # Mid-gray text → muted-foreground
    ("rgba(43.5294%,43.5294%,43.5294%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(45.8824%,45.8824%,45.8824%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(51.7647%,51.7647%,51.7647%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(59.2157%,59.2157%,59.2157%,1)", "rgba(56.5%,56.5%,56.5%,1)"),
    ("rgba(60.3922%,60.3922%,60.3922%,1)", "rgba(56.5%,56.5%,56.5%,1)"),

    # ── Batch 5: Border grays → unified border color ────────────────
    ("rgba(87.8431%,87.8431%,87.8431%,1)", "rgba(92.2%,92.2%,92.2%,1)"),
    ("rgba(90.1961%,90.1961%,90.1961%,1)", "rgba(92.2%,92.2%,92.2%,1)"),
    ("rgba(92.1569%,92.1569%,92.1569%,1)", "rgba(92.2%,92.2%,92.2%,1)"),
    ("rgba(93.3333%,93.3333%,93.3333%,1)", "rgba(92.2%,92.2%,92.2%,1)"),
    ("rgba(95.6863%,95.6863%,95.6863%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(96.0784%,96.0784%,96.0784%,1)", "rgba(96.1%,96.1%,96.1%,1)"),
    ("rgba(96.4706%,96.4706%,96.4706%,1)", "rgba(96.1%,96.1%,96.1%,1)"),

    # ── Batch 6: Dark surfaces → foreground ──────────────────────────
    ("rgba(22.3529%,22.3529%,22.3529%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(25.8824%,25.8824%,25.8824%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(29.8039%,29.8039%,29.8039%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(30.1961%,30.1961%,30.1961%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(36.0784%,36.0784%,36.0784%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(38.0392%,38.0392%,38.0392%,1)", "rgba(18%,18%,18%,1)"),
    ("rgba(38.3529%,38.3529%,38.3529%,1)", "rgba(18%,18%,18%,1)"),
])

# Colors to leave alone (no mapping needed, just documenting):
# rgba(0%,0%,0%,0)          — transparent
# rgba(0%,0%,0%,1)          — pure black
# rgba(100%,100%,100%,0)    — transparent white
# rgba(100%,100%,100%,1)    — white
# rgba(0%,0%,0%,0.101825)   — shadow alpha
# rgba(0%,0%,0%,0.15)       — shadow alpha
# rgba(100%,80%,0%,1)       — yellow/warning
# rgba(42.3529%,10.1961%,9.41177%,1)    — destructive dark
# rgba(66.6667%,17.2549%,16.4706%,1)    — destructive
# rgba(78.8235%,20.3922%,19.6078%,1)    — destructive light
# rgba(78.8235%,20.7843%,19.6078%,1)    — destructive light variant
# rgba(14.1176%,14.1176%,14.1176%,1)    — already matches foreground target


def read_template(path):
    """Read UTF-16 LE file with BOM, return (bom_bytes, text)."""
    with open(path, "rb") as f:
        raw = f.read()

    # Check for BOM
    if raw[:2] == b"\xff\xfe":
        bom = raw[:2]
        text = raw[2:].decode("utf-16-le")
    else:
        bom = b""
        text = raw.decode("utf-16-le")

    return bom, text


def write_template(path, bom, text):
    """Write back with original BOM and encoding."""
    with open(path, "wb") as f:
        f.write(bom)
        f.write(text.encode("utf-16-le"))


def find_css_cdata(text):
    """Find the CSS CDATA block boundaries. Returns (start, end) of inner content."""
    # The CSS CDATA starts with "/* Object Styles */"
    marker = "<![CDATA[/* Object Styles */"
    start = text.find(marker)
    if start == -1:
        raise ValueError("Could not find CSS CDATA block")

    cdata_start = start + len("<![CDATA[")
    cdata_end = text.find("]]>", cdata_start)
    if cdata_end == -1:
        raise ValueError("Could not find end of CSS CDATA block")

    return cdata_start, cdata_end


def apply_color_map(css_text, color_map, dry_run=False):
    """Apply ordered color replacements to CSS text. Returns (new_text, stats)."""
    stats = OrderedDict()
    result = css_text

    for old_color, new_color in color_map.items():
        count = result.count(old_color)
        if count > 0:
            if not dry_run:
                result = result.replace(old_color, new_color)
            stats[old_color] = {"new": new_color, "count": count}

    return result, stats


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"Reading {TEMPLATE_PATH}...")
    bom, text = read_template(TEMPLATE_PATH)
    print(f"  File size: {len(text)} characters, BOM: {'yes' if bom else 'no'}")

    css_start, css_end = find_css_cdata(text)
    css_text = text[css_start:css_end]
    print(f"  CSS block: {len(css_text)} characters ({css_start}..{css_end})")

    # Count total rgba values before
    rgba_before = len(re.findall(r"rgba\([^)]+\)", css_text))
    print(f"  Total rgba values: {rgba_before}")

    # Apply replacements
    mode = "DRY RUN" if dry_run else "APPLYING"
    print(f"\n{mode} color replacements...")

    new_css, stats = apply_color_map(css_text, COLOR_MAP, dry_run=dry_run)

    total_replacements = 0
    for old_color, info in stats.items():
        print(f"  {info['count']:4d}x  {old_color}")
        print(f"     →  {info['new']}")
        total_replacements += info["count"]

    print(f"\nTotal replacements: {total_replacements}")

    if not dry_run:
        # Reconstruct file
        new_text = text[:css_start] + new_css + text[css_end:]

        # Verify unique rgba values remaining
        unique_after = sorted(set(re.findall(r"rgba\([^)]+\)", new_css)))
        print(f"\nUnique rgba values remaining: {len(unique_after)}")
        for v in unique_after:
            count = new_css.count(v)
            print(f"  {count:4d}x  {v}")

        write_template(TEMPLATE_PATH, bom, new_text)
        print(f"\nWritten to {TEMPLATE_PATH}")

        # Verify encoding roundtrip
        _, verify_text = read_template(TEMPLATE_PATH)
        if verify_text == new_text:
            print("Encoding verification: PASSED")
        else:
            print("ERROR: Encoding verification FAILED!")
            sys.exit(1)
    else:
        print("\nDry run complete. Use without --dry-run to apply.")


if __name__ == "__main__":
    main()
