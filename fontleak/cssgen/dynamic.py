#!/usr/bin/env python3
from jinja2 import Template


def generate(
    id: str,
    step: int,
    step_map: list[int],
    template: Template,
    alphabet_size: int,
    font_path: str,
    host: str,
    host_leak: str,
    leak_selector: str,
    browser: str,
) -> str:
    if step > len(step_map):
        raise ValueError(
            f"Step {step} is greater than the number of steps in the step map."
        )

    # Simplified HTML width - just needs to fit the alphabet
    html_width = alphabet_size + 2

    width_containers = []
    for width in range(1, alphabet_size + 2):
        char_idx = html_width - width - 1
        width_containers.append({"width": width, "char_idx": char_idx, "host": host})

    step_char = f"\\{step_map[step]:x}"

    # Render template with context
    context = {
        "id": id,
        "step": step,
        "step_char": step_char,
        "html_width": html_width,
        "font_path": font_path,
        "width_containers": width_containers,
        "leak_selector": leak_selector,
        "host": host,
        "host_leak": host_leak,
        "browser": browser,
    }

    return template.render(**context)


def generate_staging(
    id: str,
    step: int,
    host: str,
    template: Template,
    browser: str,
) -> str:
    context = {
        "id": id,
        "step": step,
        "host": host,
        "browser": browser,
    }

    return template.render(**context)
