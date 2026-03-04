#!/usr/bin/env python3
"""
Phase 2: Element-specific refinements for Mizu shadcn theme.

Applies targeted CSS rule modifications that can't be done with global
find-and-replace (semantically different elements need different treatment).
"""

import re
import sys


TEMPLATE_PATH = "proof_mizu_shadcn_theme/template.xml"


def read_template(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\xff\xfe":
        bom = raw[:2]
        text = raw[2:].decode("utf-16-le")
    else:
        bom = b""
        text = raw.decode("utf-16-le")
    return bom, text


def write_template(path, bom, text):
    with open(path, "wb") as f:
        f.write(bom)
        f.write(text.encode("utf-16-le"))


def find_css_cdata(text):
    marker = "<![CDATA[/* Object Styles */"
    start = text.find(marker) + len("<![CDATA[")
    end = text.find("]]>", start)
    return start, end


def replace_rule(css, selector, old_props, new_props):
    """Replace properties within a specific CSS rule block.

    Finds the rule matching `selector`, then replaces `old_props` with
    `new_props` within that rule only.
    """
    # Find the selector
    idx = css.find(selector)
    if idx == -1:
        print(f"  WARNING: selector not found: {selector}")
        return css, False

    # Find the opening and closing braces
    brace_start = css.find("{", idx)
    brace_end = css.find("}", brace_start)
    if brace_start == -1 or brace_end == -1:
        print(f"  WARNING: could not find braces for: {selector}")
        return css, False

    rule_content = css[brace_start:brace_end + 1]
    if old_props not in rule_content:
        print(f"  WARNING: props not found in {selector}: {old_props[:50]}...")
        return css, False

    new_rule = rule_content.replace(old_props, new_props, 1)
    css = css[:brace_start] + new_rule + css[brace_end + 1:]
    return css, True


def insert_props_in_rule(css, selector, new_props):
    """Insert new properties at the end of a rule block (before closing brace)."""
    idx = css.find(selector)
    if idx == -1:
        print(f"  WARNING: selector not found: {selector}")
        return css, False

    brace_start = css.find("{", idx)
    brace_end = css.find("}", brace_start)

    # Insert before the closing brace
    css = css[:brace_end] + new_props + "\n" + css[brace_end:]
    return css, True


def apply_input_full_border(css):
    """Convert bottom-border-only inputs to full-border with radius."""
    print("\n--- Input fields: bottom-border → full border ---")
    count = 0

    # Elements that currently have bottom-border-only
    for element in ["edit_box", "pop_up", "drop_down"]:
        selector = f"{element}:normal .self"

        # Change border styles from none to solid
        old = (
            "\tborder-top-style: none;\n"
            "\tborder-right-style: none;\n"
            "\tborder-bottom-style: solid;\n"
            "\tborder-left-style: none;"
        )
        new = (
            "\tborder-top-style: solid;\n"
            "\tborder-right-style: solid;\n"
            "\tborder-bottom-style: solid;\n"
            "\tborder-left-style: solid;\n"
            "\tborder-top-right-radius: 6pt 6pt;\n"
            "\tborder-bottom-right-radius: 6pt 6pt;\n"
            "\tborder-bottom-left-radius: 6pt 6pt;\n"
            "\tborder-top-left-radius: 6pt 6pt;"
        )

        css, ok = replace_rule(css, selector, old, new)
        if ok:
            print(f"  {element}: full border + 6pt radius")
            count += 1

    # Also update the border color from border gray to a slightly lighter
    # shade for normal state (shadcn inputs use border color)
    print(f"  Updated {count} input elements")
    return css


def apply_checkbox_radio_filled(css):
    """Make checkbox/radio dark-filled when checked (shadcn pattern)."""
    print("\n--- Checkbox/radio: dark filled when checked ---")

    # Checkbox checked icon: add dark background + white icon
    old = (
        "checkbox_set:checked .icon\n"
        "{\n"
        "\t-fm-icon: modern-check;\n"
        "\t-fm-icon-color: rgba(0%,0%,0%,1);\n"
        "}"
    )
    new = (
        "checkbox_set:checked .icon\n"
        "{\n"
        "\tbackground-color: rgba(18%,18%,18%,1);\n"
        "\tborder-top-color: rgba(18%,18%,18%,1);\n"
        "\tborder-right-color: rgba(18%,18%,18%,1);\n"
        "\tborder-bottom-color: rgba(18%,18%,18%,1);\n"
        "\tborder-left-color: rgba(18%,18%,18%,1);\n"
        "\t-fm-icon: modern-check;\n"
        "\t-fm-icon-color: rgba(100%,100%,100%,1);\n"
        "}"
    )
    css = css.replace(old, new, 1)
    print("  checkbox_set:checked — dark bg + white check")

    # Radio checked icon: add dark background + white icon
    old = (
        "radio_set:checked .icon\n"
        "{\n"
        "\t-fm-icon: radio;\n"
        "\t-fm-icon-color: rgba(0%,0%,0%,1);\n"
        "}"
    )
    new = (
        "radio_set:checked .icon\n"
        "{\n"
        "\tbackground-color: rgba(18%,18%,18%,1);\n"
        "\tborder-top-color: rgba(18%,18%,18%,1);\n"
        "\tborder-right-color: rgba(18%,18%,18%,1);\n"
        "\tborder-bottom-color: rgba(18%,18%,18%,1);\n"
        "\tborder-left-color: rgba(18%,18%,18%,1);\n"
        "\t-fm-icon: radio;\n"
        "\t-fm-icon-color: rgba(100%,100%,100%,1);\n"
        "}"
    )
    css = css.replace(old, new, 1)
    print("  radio_set:checked — dark bg + white dot")

    # Also handle FM-UUID instance overrides for checkbox/radio checked
    # Find all checkbox_set.FM-*:checked .icon and radio_set.FM-*:checked .icon
    pattern = re.compile(
        r'((?:checkbox_set|radio_set)\.FM-[^:]+:checked \.icon\n\{\n)'
        r'(\t-fm-icon: (?:modern-check|radio);\n'
        r'\t-fm-icon-color: rgba\(0%,0%,0%,1\);\n\})'
    )
    def replace_instance_checked(m):
        prefix = m.group(1)
        icon_line = "\t-fm-icon: modern-check;" if "checkbox" in m.group(0) else "\t-fm-icon: radio;"
        return (
            prefix
            + "\tbackground-color: rgba(18%,18%,18%,1);\n"
            + "\tborder-top-color: rgba(18%,18%,18%,1);\n"
            + "\tborder-right-color: rgba(18%,18%,18%,1);\n"
            + "\tborder-bottom-color: rgba(18%,18%,18%,1);\n"
            + "\tborder-left-color: rgba(18%,18%,18%,1);\n"
            + icon_line + "\n"
            + "\t-fm-icon-color: rgba(100%,100%,100%,1);\n"
            + "}"
        )

    css, instance_count = pattern.subn(replace_instance_checked, css)
    if instance_count:
        print(f"  {instance_count} FM-UUID instance overrides also updated")

    return css


def apply_filled_button_fixes(css):
    """Ensure filled primary buttons have correct light text on hover/press."""
    print("\n--- Filled buttons: ensure light text in all states ---")

    # Find filled button instances and fix their hover states
    # Pattern: button.FM-*:hover .self with background going to light color
    # but text color not explicitly set to dark
    # For filled buttons, hover should stay dark bg or go slightly lighter
    # Current issue: some filled buttons hover to rgba(96.1%) bg (light) but
    # don't set text color, so text stays white on light bg

    # Fix filled button hover states: if hover bg is light, set text color dark
    pattern = re.compile(
        r'(button\.FM-[A-F0-9-]+:hover \.self\n\{\n'
        r'\tbackground-image: none;\n'
        r'\tbackground-color: rgba\(96\.1%,96\.1%,96\.1%,1\);\n'
        r'\tborder-image-source: none;\n'
        r'\})'
    )

    def add_text_color_to_hover(m):
        # Replace closing brace with text color + closing brace
        block = m.group(1)
        return block.replace(
            "\tborder-image-source: none;\n}",
            "\tborder-image-source: none;\n"
            "\tcolor: rgba(14.1%,14.1%,14.1%,1);\n}"
        )

    css, count = pattern.subn(add_text_color_to_hover, css)
    print(f"  Added dark text color to {count} button hover states")

    # Fix icon colors for filled buttons: normal icon should be white
    # Find filled buttons (bg: 18%) and set their icon color to white
    lines = css.split("\n")
    i = 0
    icon_fixes = 0
    while i < len(lines):
        line = lines[i]
        # Find filled button normal .self blocks
        if re.match(r'button\.FM-[A-F0-9-]+:normal \.self', line):
            # Check if this is a filled button (has dark bg)
            block_end = i
            for j in range(i + 1, min(i + 30, len(lines))):
                if lines[j].strip() == "}":
                    block_end = j
                    break
            block = "\n".join(lines[i:block_end + 1])
            if "background-color: rgba(18%,18%,18%,1)" in block:
                # This is a filled button - find its icon rule
                uuid = re.search(r'FM-[A-F0-9-]+', line).group(0)
                icon_selector = f"button.{uuid}:normal .icon"
                icon_idx = css.find(icon_selector)
                if icon_idx != -1:
                    # Check if icon color is black and change to white
                    old_icon = f"{icon_selector}\n{{\n\t-fm-icon-color: rgba(0%,0%,0%,1);\n}}"
                    new_icon = f"{icon_selector}\n{{\n\t-fm-icon-color: rgba(100%,100%,100%,1);\n}}"
                    if old_icon in css:
                        css = css.replace(old_icon, new_icon, 1)
                        icon_fixes += 1
        i += 1

    print(f"  Fixed {icon_fixes} filled button icon colors to white")
    return css


def apply_placeholder_standardization(css):
    """Standardize placeholder text to muted-foreground."""
    print("\n--- Placeholder text: standardize to muted-foreground ---")

    # Some placeholders use rgba(80%,...), some rgba(70.2%,...)
    # Standardize to muted-foreground rgba(56.5%,...)
    old = "color: rgba(80%,80%,80%,1)"
    count_before = css.count(old)

    # Only replace in placeholder rules
    pattern = re.compile(
        r'(:placeholder \.self\n\{\n\tcolor: )rgba\(80%,80%,80%,1\)'
    )
    css, count = pattern.subn(r'\1rgba(56.5%,56.5%,56.5%,1)', css)
    print(f"  Updated {count} placeholder colors to muted-foreground")

    return css


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"Reading {TEMPLATE_PATH}...")
    bom, text = read_template(TEMPLATE_PATH)

    css_start, css_end = find_css_cdata(text)
    css = text[css_start:css_end]
    print(f"  CSS block: {len(css)} characters")

    # Apply refinements
    css = apply_input_full_border(css)
    css = apply_checkbox_radio_filled(css)
    css = apply_filled_button_fixes(css)
    css = apply_placeholder_standardization(css)

    if not dry_run:
        new_text = text[:css_start] + css + text[css_end:]
        write_template(TEMPLATE_PATH, bom, new_text)
        print(f"\nWritten to {TEMPLATE_PATH}")

        # Verify
        _, verify = read_template(TEMPLATE_PATH)
        if verify == new_text:
            print("Encoding verification: PASSED")
        else:
            print("ERROR: Encoding verification FAILED!")
            sys.exit(1)
    else:
        print("\nDry run complete.")


if __name__ == "__main__":
    main()
