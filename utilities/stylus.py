
import os
import re
import sys
from pathlib import Path
from medic.utilities.app_theme import get_theme_palette


def resource_path(relative_path):
    """Return the absolute path to a resource, works for dev and PyInstaller."""
    relative = Path(relative_path)
    candidates = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / relative)

    module_root = Path(__file__).resolve().parent.parent
    candidates.append(module_root / relative)
    candidates.append(Path.cwd() / relative)

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return str(candidates[0])


def _normalize_stylesheet_urls(css_content):
    def replace_url(match):
        raw_path = match.group(1).strip().strip('"\'')
        if not raw_path or raw_path.startswith((":", "qrc:", "file:", "data:")):
            return match.group(0)
        return f"url({resource_path(raw_path).replace(os.sep, '/')})"

    return re.sub(r"url\(([^)]+)\)", replace_url, css_content)



def load_stylesheets():
    """Load and combine all CSS files from the styles folder."""
    styles_dir = resource_path("styles")
    css_content = ""

    if os.path.exists(styles_dir):
        for file in sorted(os.listdir(styles_dir)):
            if file.endswith(".css"):
                css_file = os.path.join(styles_dir, file)
                with open(css_file, "r") as f:
                    css_content += f.read() + "\n"

    palette = get_theme_palette()
    replacements = {
        "#2F5D7C": palette["primary_main"],
        "#244A62": palette["primary_hover"],
        "#163B5C": palette["primary_pressed"],
        "#2a506b": palette["primary_border"],
        "#5B8FB8": palette["focus_border"],
        "#EEF5FA": palette["focus_fill"],
        "#234B69": palette["primary_hover"],
        "#193A52": palette["primary_border"],
        "#1D415B": palette["primary_pressed"],
        "#153347": palette["primary_pressed"],
    }
    for old, new in replacements.items():
        css_content = css_content.replace(old, new)

    return _normalize_stylesheet_urls(css_content)
