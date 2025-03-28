import string
from typing import List, Dict, Tuple
import unicodedata
import tempfile
import base64
import subprocess
from functools import lru_cache

# Constants
IDX_POINTS = []


def get_unicode_description(code_point):
    try:
        # Convert the code point string to an actual character
        if isinstance(code_point, str) and code_point.startswith("U+"):
            # Convert from format like 'U+1E00' to integer
            char = chr(int(code_point[2:], 16))
        elif isinstance(code_point, int):
            char = chr(code_point)
        else:
            char = code_point

        # Get the name (description) of the character
        name = unicodedata.name(char)
        return f"{code_point} = {name}"
    except ValueError as e:
        return f"Error: {e}"


for code_point in range(256, 0x1FFFF):
    desc = get_unicode_description(code_point).upper()
    if (
        ("LATIN " in desc or "MATHEMATICAL " in desc)
        and not "ARABIC" in desc
        and not "GREEK" in desc
        and not "CYRILLIC" in desc
        and not "HEBREW" in desc
        and not "HIRAGANA" in desc
        and not "KATAKANA" in desc
        and not "HANGUL" in desc
        and not "THAI" in desc
    ):
        IDX_POINTS.append(code_point)


def create_svg_template():
    return """<svg>
  <defs>
    <font id="fontleak" horiz-adv-x="0">
      <font-face font-family="fontlheak" units-per-em="1000" ascent="5" descent="5" />
      <missing-glyph />
      $GLYPHS$
    </font>
  </defs>
</svg>"""


def create_glyph(glyph_name, unicode_value, horiz_adv_x, path_data):
    """Create a glyph element with the given attributes."""
    return (
        '<glyph glyph-name="{}" unicode="&#x{:04X};" horiz-adv-x="{}" d="{}"/>'.format(
            glyph_name, unicode_value, horiz_adv_x, path_data
        )
    )


def generate_initial_glyphs(alphabet):
    """Generate the first 128 glyphs (0-127)."""
    glyphs = []
    unknown_glyphs = []
    char_glyphs = []

    for i in range(256):
        horiz = 0

        if chr(i) in alphabet:
            idx = alphabet.index(chr(i))
            glyph_name = "c{}".format(idx)
            path_data = "M{} 0z".format(i)
        else:
            glyph_name = "u0"
            path_data = "M1 0z"
            if False:  # not unknown_glyphs:
                unknown_glyphs.append(glyph_name)

        glyphs.append(create_glyph(glyph_name, i, horiz, path_data))

    for idx in range(len(alphabet)):
        glyph_name = "c{}".format(idx)
        char_glyphs.append(glyph_name)

    return glyphs, unknown_glyphs, char_glyphs


def generate_custom_glyphs(alphabet, idx_max):
    """Generate leak and index glyphs in the Private Use Area."""
    glyphs = []
    leak_glyphs = []
    index_glyphs = []

    alphabet_len = len(alphabet)
    # current_unicode = 128
    current_unicode = 0

    # leak_glyphs.append('lu')

    # 1. Add regular leak glyphs with increasing widths
    for i in range(alphabet_len):
        glyph_name = "l{}".format(i)
        horiz_adv_x = i + 1  # Start from width 1
        path_data = "M{} 0z".format(128 + i)

        glyphs.append(
            create_glyph(glyph_name, 0xF0000 + current_unicode, horiz_adv_x, path_data)
        )
        leak_glyphs.append(glyph_name)
        current_unicode += 1

    # 2. Add lu with width of alphabet_len + 2
    glyphs.append(
        create_glyph(
            "lu", 0xF0000 + current_unicode, alphabet_len + 1, f"M{current_unicode} 0z"
        )
    )
    current_unicode += 1

    # 3. Add index glyphs with width of len(alphabet)+2
    fill_null = 128 + alphabet_len + 1
    for i in range(fill_null, 256):
        glyph_name = "u0"
        path_data = "M1 0z"
        glyphs.append(create_glyph(glyph_name, i, 0, path_data))

    for i in range(idx_max):
        glyph_name = "i{}".format(i)
        horiz_adv_x = 0
        # horiz_adv_x = i # index_width
        path_data = "M{} 0z".format(256 + len(alphabet) + i + 1)

        glyphs.append(create_glyph(glyph_name, IDX_POINTS[i], horiz_adv_x, path_data))
        index_glyphs.append(glyph_name)

    return glyphs, leak_glyphs, index_glyphs


def save_font(filename, template, glyphs):
    """Save the generated font to a file."""
    content = template.replace("$GLYPHS$", "\n".join(glyphs))
    with open(filename, "w") as f:
        f.write(content)


# Import feagen functions as a library
def generate_class_definition(name: str, elements: List[str]) -> str:
    """Generate a feature class definition."""
    return "@{} = [{} {}];".format(name, " ".join(elements), "")


def generate_lookup(name: str, rules: List[str]) -> List[str]:
    """Generate a lookup table with the given name and substitution rules."""
    return [
        "  lookup {} {{".format(name),
        *["    {};".format(rule) for rule in rules],
        "  }} {};".format(name),
    ]


def generate_feature_file(
    unknown_glyphs,
    char_glyphs,
    leak_glyphs,
    index_glyphs,
    idx_max,
    output_file="mylig.fea",
    strip=True,
):
    """Generate OpenType feature file for ligature substitutions."""
    # Define the character classes
    classes = [
        generate_class_definition("any", unknown_glyphs + char_glyphs),
        generate_class_definition("leaks", leak_glyphs),
    ]

    # Generate lookup tables
    if strip:
        lookups = ["sub u0 by NULL; sub @any by @any;"]
    else:
        lookups = []

    # Lookup: Handle other characters
    # idxn any -> idxn-1 (for n > 0)
    other_rules = []
    # Group rules by their final i value
    rule_groups = {}
    for i in range(1, idx_max):
        # This works, but the css is huge
        # if i % 2 == 0:  # Even numbers decrease by 2
        #     final_i = i - 2
        #     rule = f"sub i{i} @any @any by i{final_i}"
        # else:  # Odd numbers decrease by 1
        #     final_i = i - 1
        #     rule = f"sub i{i} @any by i{final_i}"

        final_i = i - 1
        rule = f"sub i{i} @any by i{final_i}"

        if final_i not in rule_groups:
            rule_groups[final_i] = []
        rule_groups[final_i].append(rule)

    # Create lookups for each group of rules
    for final_i, rules in reversed(rule_groups.items()):
        lookups.extend(generate_lookup(f"handle_others_{final_i}", rules))

    # Add direct substitutions for each character to leak glyph
    final_rules = []
    for char_glyph, leak_glyph in zip(char_glyphs, leak_glyphs):
        final_rules.append(f"sub i0 {char_glyph} by {leak_glyph}")

    # Add final substitution lookup
    lookups.extend(generate_lookup("final_substitution", final_rules))

    # Assemble the feature
    rlig_feature = ["feature liga {", *lookups, "} liga;"]

    # Join all parts and write to file
    output = "\n".join(classes + rlig_feature)

    with open(output_file, "w") as f:
        f.write(output)

    print("Feature file saved to {}".format(output_file))


def generate_font(
    output_font="myfont.svg",
    output_feature="mylig.fea",
    alphabet="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_",
    idx_max=2400,
    strip=True,
):
    """Main function to generate the font and feature file."""
    # Check if we can fit all glyphs in the Private Use Area
    total_glyphs_needed = len(alphabet) * 2 + idx_max + 2  # leak glyphs + index glyphs
    print("Total glyphs to generate: {}".format(total_glyphs_needed))

    template = create_svg_template()

    # Generate all glyphs
    glyphs = []
    initial_glyphs, unknown_glyphs, char_glyphs = generate_initial_glyphs(alphabet)
    custom_glyphs, leak_glyphs, index_glyphs = generate_custom_glyphs(alphabet, idx_max)

    glyphs.extend(initial_glyphs)
    glyphs.extend(custom_glyphs)

    # Save the font
    save_font(output_font, template, glyphs)
    print("Font saved to {}".format(output_font))

    # Generate the feature file
    generate_feature_file(
        unknown_glyphs=unknown_glyphs,
        char_glyphs=char_glyphs,
        leak_glyphs=leak_glyphs,
        index_glyphs=index_glyphs,
        idx_max=min(idx_max, len(IDX_POINTS)),
        output_file=output_feature,
        strip=strip,
    )


@lru_cache(maxsize=None)
def generate(
    alphabet: str, idx_max: int = 128, strip: bool = True, prefix: str = ""
) -> Tuple[str, list[int]]:
    """Returns data:base64 of the generated font"""
    # generate temporary file to save the font and .fea
    with tempfile.NamedTemporaryFile() as font_file:
        base_path = font_file.name
        svg_path = base_path + ".svg"
        fea_path = base_path + ".fea"
        ttf_path = base_path + ".ttf"
        otf_path = base_path + ".otf"

        generate_font(svg_path, fea_path, alphabet, idx_max, strip)

        # Convert SVG to TTF
        subprocess.run(["svg2ttf", svg_path, ttf_path], check=True)

        # Apply features to create OTF
        subprocess.run(
            ["uv", "run", "fonttools", "feaLib", "-o", otf_path, fea_path, ttf_path],
            check=True,
        )

        with open(otf_path, "rb") as otf_file:
            return "data:font/opentype;base64," + base64.b64encode(
                otf_file.read()
            ).decode("utf-8"), IDX_POINTS[:idx_max]


if __name__ == "__main__":
    generate_font()
